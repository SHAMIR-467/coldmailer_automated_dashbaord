from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models import Job, JobStatus, Lead
from app.rate_limit import limiter
from app.schemas import CreateJobRequest, JobDetailResponse, JobListResponse, JobResponse
from app.services.city_generator import generate_cities_for_keyword
from app.workers.celery_app import celery_app
from app.workers.scraper_task import start_job_scraping

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _job_progress(job: Job) -> float:
    if not job.cities:
        return 0.0
    return round((job.current_city_index / len(job.cities)) * 100, 2)


def _revoke_job_tasks(job_id: UUID) -> None:
    try:
        inspector = celery_app.control.inspect()
        task_groups = [inspector.active() or {}, inspector.reserved() or {}, inspector.scheduled() or {}]
        job_id_text = str(job_id)
        for workers in task_groups:
            for tasks in workers.values():
                for task in tasks:
                    request = task.get("request", task)
                    args = str(request.get("args", task.get("args", "")))
                    if job_id_text in args:
                        celery_app.control.revoke(request.get("id") or task.get("id"), terminate=False)
    except Exception:
        return


def _queue_job(job_id: UUID) -> None:
    try:
        start_job_scraping.delay(str(job_id))
    except Exception:
        return


@router.post("", response_model=JobResponse, status_code=201)
@limiter.limit("10/minute")
async def create_job(request: Request, payload: CreateJobRequest, db: AsyncSession = Depends(get_db)) -> Job:
    cities = payload.cities or await generate_cities_for_keyword(payload.keyword)
    job = Job(
        keyword=payload.keyword,
        cities=cities,
        status=JobStatus.pending,
        batch_size=settings.SCRAPE_BATCH_SIZE,
        daily_limit=settings.DAILY_EMAIL_LIMIT,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    _queue_job(job.id)
    return job


@router.get("", response_model=JobListResponse)
async def list_jobs(db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    total = await db.scalar(select(func.count()).select_from(Job))
    result = await db.execute(select(Job).order_by(Job.created_at.desc()))
    return {"items": result.scalars().all(), "total": total or 0}


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(job_id: UUID, db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    result = await db.execute(
        select(Job).where(Job.id == job_id).options(selectinload(Job.leads), selectinload(Job.email_logs))
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {**JobResponse.model_validate(job).model_dump(), "progress": _job_progress(job), "leads": job.leads, "email_logs": job.email_logs}


@router.get("/{job_id}/cities")
async def get_job_cities(job_id: UUID, db: AsyncSession = Depends(get_db)) -> list[dict[str, object]]:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    lead_counts = await db.execute(
        select(Lead.city, func.count(Lead.id)).where(Lead.job_id == job_id).group_by(Lead.city)
    )
    counts = {city: count for city, count in lead_counts.all()}
    cities = []
    for index, city in enumerate(job.cities):
        if index < job.current_city_index:
            status = "done"
        elif index == job.current_city_index and job.status == JobStatus.running:
            status = "running"
        elif index == job.current_city_index and job.status in {JobStatus.pending, JobStatus.paused}:
            status = "pending"
        else:
            status = "not_started"
        cities.append({"city": city, "status": status, "leads_found": counts.get(city, 0)})
    return cities


@router.post("/{job_id}/start", response_model=JobResponse)
async def start_job(job_id: UUID, db: AsyncSession = Depends(get_db)) -> Job:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status == JobStatus.paused:
        job.status = JobStatus.running
    elif job.status == JobStatus.pending:
        job.status = JobStatus.running
    await db.commit()
    await db.refresh(job)
    _queue_job(job.id)
    return job


@router.post("/{job_id}/pause", response_model=JobResponse)
async def pause_job(job_id: UUID, db: AsyncSession = Depends(get_db)) -> Job:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = JobStatus.paused
    _revoke_job_tasks(job.id)
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/{job_id}/resume", response_model=JobResponse)
async def resume_job(job_id: UUID, db: AsyncSession = Depends(get_db)) -> Job:
    return await start_job(job_id, db)


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: UUID, db: AsyncSession = Depends(get_db)) -> Response:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = JobStatus.failed
    _revoke_job_tasks(job.id)
    await db.commit()
    return Response(status_code=204)
