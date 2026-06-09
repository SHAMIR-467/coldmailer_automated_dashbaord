from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db, get_redis
from app.models import EmailLog, EmailLogStatus, Job, JobStatus, Lead, LeadEmailStatus
from app.schemas import DashboardStats, EmailStatusCounts, EmailsPerDay, LeadsPerJob

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _empty_stats(emails_sent_today: int = 0) -> DashboardStats:
    quota_pct = round((emails_sent_today / settings.DAILY_EMAIL_LIMIT) * 100, 2) if settings.DAILY_EMAIL_LIMIT else 0.0
    return DashboardStats(
        total_jobs=0,
        active_jobs=0,
        total_leads=0,
        leads_with_email=0,
        total_emails_sent=0,
        emails_sent_today=emails_sent_today,
        daily_limit=settings.DAILY_EMAIL_LIMIT,
        daily_quota_used_pct=quota_pct,
        emails_by_status=EmailStatusCounts(),
        emails_per_day=[],
        leads_per_job=[],
    )


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)) -> DashboardStats:
    today_key = f"emails_sent:{date.today().isoformat()}"
    try:
        redis_client = get_redis()
        emails_sent_today = int(await redis_client.get(today_key) or 0)
    except Exception:
        emails_sent_today = 0
    try:
        total_jobs = await db.scalar(select(func.count()).select_from(Job))
        active_jobs = await db.scalar(select(func.count()).select_from(Job).where(Job.status == JobStatus.running))
        total_leads = await db.scalar(select(func.count()).select_from(Lead))
        leads_with_email = await db.scalar(select(func.count()).select_from(Lead).where(Lead.email.is_not(None)))
        total_emails_sent = await db.scalar(select(func.count()).select_from(EmailLog).where(EmailLog.status == EmailLogStatus.sent))

        pending = await db.scalar(select(func.count()).select_from(Lead).where(Lead.email_status == LeadEmailStatus.pending))
        generated = await db.scalar(select(func.count()).select_from(EmailLog).where(EmailLog.status == EmailLogStatus.generated))
        sent = await db.scalar(select(func.count()).select_from(EmailLog).where(EmailLog.status == EmailLogStatus.sent))
        failed = await db.scalar(select(func.count()).select_from(EmailLog).where(EmailLog.status == EmailLogStatus.failed))

        seven_days_ago = date.today() - timedelta(days=6)
        per_day_rows = await db.execute(
            select(func.date(EmailLog.sent_at), func.count())
            .where(EmailLog.status == EmailLogStatus.sent, EmailLog.sent_at.is_not(None), func.date(EmailLog.sent_at) >= seven_days_ago)
            .group_by(func.date(EmailLog.sent_at))
            .order_by(func.date(EmailLog.sent_at))
        )
        counts_by_date = {str(row[0]): row[1] for row in per_day_rows.all()}
        emails_per_day = [
            EmailsPerDay(date=str(seven_days_ago + timedelta(days=index)), count=counts_by_date.get(str(seven_days_ago + timedelta(days=index)), 0))
            for index in range(7)
        ]

        leads_per_job_rows = await db.execute(
            select(Job.id, Job.keyword, func.count(Lead.id).label("lead_count"))
            .join(Lead, Lead.job_id == Job.id)
            .group_by(Job.id, Job.keyword)
            .order_by(func.count(Lead.id).desc())
            .limit(5)
        )
        leads_per_job = [
            LeadsPerJob(job_id=str(job_id), keyword=keyword, count=count)
            for job_id, keyword, count in leads_per_job_rows.all()
        ]
        quota_pct = round((emails_sent_today / settings.DAILY_EMAIL_LIMIT) * 100, 2) if settings.DAILY_EMAIL_LIMIT else 0.0
        return DashboardStats(
            total_jobs=total_jobs or 0,
            active_jobs=active_jobs or 0,
            total_leads=total_leads or 0,
            leads_with_email=leads_with_email or 0,
            total_emails_sent=total_emails_sent or 0,
            emails_sent_today=emails_sent_today,
            daily_limit=settings.DAILY_EMAIL_LIMIT,
            daily_quota_used_pct=quota_pct,
            emails_by_status=EmailStatusCounts(
                pending=pending or 0,
                generated=generated or 0,
                sent=sent or 0,
                failed=failed or 0,
            ),
            emails_per_day=emails_per_day,
            leads_per_job=leads_per_job,
        )
    except Exception:
        return _empty_stats(emails_sent_today)
