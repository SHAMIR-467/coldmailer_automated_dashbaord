import asyncio
import logging
import time
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from redis import Redis
from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models import EmailLog, EmailLogStatus, Job, Lead, LeadEmailStatus
from app.services.email_service import is_bounce_error, send_email
from app.services.ollama_service import generate_cold_email
from app.workers.celery_app import celery_app

logger = logging.getLogger("email")
RATE_LIMIT_KEYWORDS = ("421", "450")


def _redis() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)


def _daily_counter_key(day: date | None = None) -> str:
    return f"emails_sent:{(day or date.today()).isoformat()}"


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def generate_and_send_email_task(self, lead_id: str) -> None:
    started = time.perf_counter()
    session = SessionLocal()
    log: EmailLog | None = None
    try:
        logger.info("Email task started", extra={"lead_id": lead_id})
        lead = session.get(Lead, UUID(lead_id))
        if not lead:
            return
        if not lead.email:
            lead.email_status = LeadEmailStatus.failed
            session.commit()
            logger.info("Email skipped, missing address", extra={"lead_id": lead_id})
            return
        if lead.email_status == LeadEmailStatus.bounced:
            logger.info("Email skipped, lead already bounced", extra={"lead_id": lead_id})
            return

        job = session.get(Job, lead.job_id)
        if not job:
            lead.email_status = LeadEmailStatus.failed
            session.commit()
            return

        redis_client = _redis()
        key = _daily_counter_key()
        current_count = int(redis_client.get(key) or 0)
        if current_count + 1 > settings.DAILY_EMAIL_LIMIT:
            generate_and_send_email_task.apply_async(args=[lead_id], countdown=86400)
            return

        generated = asyncio.run(generate_cold_email(lead, job.keyword))
        subject = generated["subject"]
        body = generated["body"]
        log = EmailLog(
            lead_id=lead.id,
            job_id=job.id,
            subject=subject,
            body=body,
            status=EmailLogStatus.generated,
            ollama_model=settings.OLLAMA_MODEL,
        )
        session.add(log)
        lead.email_status = LeadEmailStatus.generated
        session.commit()

        sent = asyncio.run(send_email(lead.email, subject, body))
        if not sent:
            raise RuntimeError("SMTP send returned False")
        log.status = EmailLogStatus.sent
        log.sent_at = datetime.now(timezone.utc)
        lead.email_status = LeadEmailStatus.sent
        job.total_emailed += 1
        sent_count = redis_client.incr(key)
        if sent_count == 1:
            redis_client.expire(key, 86400)
        session.commit()
        logger.info("Email sent", extra={"lead_id": lead_id, "job_id": str(job.id), "extra": {"seconds": round(time.perf_counter() - started, 2)}})
    except (ConnectionError, TimeoutError) as exc:
        session.rollback()
        logger.warning("Email transient failure", extra={"lead_id": lead_id, "extra": {"error": str(exc)}})
        raise self.retry(exc=exc)
    except Exception as exc:
        session.rollback()
        error_text = str(exc).lower()
        lead = session.get(Lead, UUID(lead_id))
        if any(keyword in error_text for keyword in RATE_LIMIT_KEYWORDS):
            logger.warning("SMTP rate limited, retrying", extra={"lead_id": lead_id, "extra": {"error": str(exc)}})
            raise self.retry(exc=exc, countdown=60)
        if log:
            log.status = EmailLogStatus.failed
            log.error_message = str(exc)
        if lead:
            lead.email_status = LeadEmailStatus.bounced if is_bounce_error(exc) else LeadEmailStatus.failed
        logger.exception("Email failed", extra={"lead_id": lead_id, "extra": {"error": str(exc), "bounced": bool(lead and lead.email_status == LeadEmailStatus.bounced)}})
        session.commit()
    finally:
        session.close()


@celery_app.task
def process_email_batch(job_id: str) -> None:
    session = SessionLocal()
    try:
        pending = session.execute(
            select(Lead)
            .where(Lead.job_id == UUID(job_id), Lead.email.is_not(None), Lead.email_status == LeadEmailStatus.pending)
            .limit(21)
        ).scalars().all()
        for index, lead in enumerate(pending[:20]):
            generate_and_send_email_task.apply_async(args=[str(lead.id)], countdown=index * 5)
        if len(pending) > 20:
            process_email_batch.apply_async(args=[job_id], countdown=120)
    finally:
        session.close()


@celery_app.task
def reset_daily_counter() -> None:
    _redis().delete(_daily_counter_key())


@celery_app.task
def retry_failed_emails() -> None:
    session = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        failed_logs = session.execute(
            select(EmailLog).where(EmailLog.status == EmailLogStatus.failed, EmailLog.created_at >= cutoff).limit(100)
        ).scalars().all()
        for log in failed_logs:
            generate_and_send_email_task.delay(str(log.lead_id))
    finally:
        session.close()
