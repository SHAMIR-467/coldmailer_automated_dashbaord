import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from uuid import UUID

from celery import chord, group
from sqlalchemy import select

from redis import Redis

from app.config import settings
from app.database import SessionLocal
from app.models import Job, JobStatus, Lead
from app.services.city_generator import generate_cities_for_keyword
from app.services.google_maps import scrape_google_maps
from app.workers.celery_app import celery_app

logger = logging.getLogger("scraper")


def _redis() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)


def _heartbeat(job_id: str) -> None:
    _redis().setex(f"task_heartbeat:{job_id}", 600, str(time.time()))


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def scrape_city_task(self, job_id: str, city: str, keyword: str, batch_size: int) -> int:
    started = time.perf_counter()
    session = SessionLocal()
    try:
        logger.info("Scrape task started", extra={"job_id": job_id, "extra": {"city": city}})
        _heartbeat(job_id)
        job = session.get(Job, UUID(job_id))
        if not job or job.status == JobStatus.paused:
            return 0
        if job.status != JobStatus.running:
            job.status = JobStatus.running
            session.commit()

        results = asyncio.run(scrape_google_maps(keyword, city, batch_size))
        _heartbeat(job_id)
        new_leads: list[Lead] = []
        for result in results:
            email = result.get("email")
            duplicate_query = select(Lead.id).where(Lead.job_id == job.id, Lead.business_name == result["business_name"], Lead.city == city)
            if email:
                duplicate_query = select(Lead.id).where(Lead.job_id == job.id, Lead.email == email)
            duplicate = session.execute(duplicate_query).scalar_one_or_none()
            if duplicate:
                continue
            new_leads.append(
                Lead(
                    job_id=job.id,
                    business_name=result["business_name"],
                    email=email,
                    phone=result.get("phone"),
                    address=result.get("address"),
                    website=result.get("website"),
                    category=result.get("category"),
                    city=result.get("city") or city,
                    rating=result.get("rating"),
                    review_count=result.get("review_count"),
                    maps_url=result.get("maps_url"),
                )
            )

        if new_leads:
            session.bulk_save_objects(new_leads)
            job.total_extracted += len(new_leads)
        job.current_city_index += 1
        if job.current_city_index >= len(job.cities):
            job.status = JobStatus.done
        session.commit()

        from app.workers.email_task import process_email_batch

        process_email_batch.delay(job_id)
        logger.info("Scrape task succeeded", extra={"job_id": job_id, "extra": {"city": city, "lead_count": len(new_leads), "seconds": round(time.perf_counter() - started, 2)}})
        return len(new_leads)
    except Exception as exc:
        session.rollback()
        logger.exception("Scrape task failed", extra={"job_id": job_id, "extra": {"city": city, "seconds": round(time.perf_counter() - started, 2)}})
        raise self.retry(exc=exc)
    finally:
        session.close()


@celery_app.task
def start_job_scraping(job_id: str) -> None:
    started = time.perf_counter()
    session = SessionLocal()
    try:
        logger.info("Start job scraping", extra={"job_id": job_id})
        _heartbeat(job_id)
        job = session.get(Job, UUID(job_id))
        if not job:
            return
        if not job.cities:
            job.cities = asyncio.run(generate_cities_for_keyword(job.keyword))
            session.commit()
        job.status = JobStatus.running
        session.commit()

        signatures = [
            scrape_city_task.s(str(job.id), city, job.keyword, job.batch_size)
            for city in job.cities[job.current_city_index :]
        ]
        if not signatures:
            update_job_complete.delay(str(job.id))
            return

        for index in range(0, len(signatures), 3):
            batch = signatures[index : index + 3]
            callback = update_job_complete.si(str(job.id)) if index + 3 >= len(signatures) else noop.si()
            chord(group(batch))(callback)
        logger.info("Job scraping dispatched", extra={"job_id": job_id, "extra": {"seconds": round(time.perf_counter() - started, 2)}})
    finally:
        session.close()


@celery_app.task
def update_job_complete(job_id: str) -> None:
    session = SessionLocal()
    try:
        job = session.get(Job, UUID(job_id))
        if job and job.status != JobStatus.failed:
            job.status = JobStatus.done
            session.commit()
    finally:
        session.close()


@celery_app.task
def noop() -> None:
    return None


@celery_app.task
def check_stalled_jobs() -> None:
    session = SessionLocal()
    try:
        redis = _redis()
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
        jobs = session.execute(select(Job).where(Job.status == JobStatus.running)).scalars().all()
        for job in jobs:
            heartbeat = redis.get(f"task_heartbeat:{job.id}")
            stale_heartbeat = not heartbeat or (time.time() - float(heartbeat)) > 300
            stale_db = job.updated_at and job.updated_at < cutoff
            if (stale_heartbeat or stale_db) and job.current_city_index < len(job.cities):
                city = job.cities[job.current_city_index]
                logger.warning("Restarting stalled scrape task", extra={"job_id": str(job.id), "extra": {"city": city, "stale_heartbeat": stale_heartbeat}})
                scrape_city_task.delay(str(job.id), city, job.keyword, job.batch_size)
    finally:
        session.close()
