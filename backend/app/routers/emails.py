import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import EmailLog, EmailLogStatus, Lead
from app.rate_limit import limiter
from app.schemas import EmailLogListResponse, EmailLogResponse, EmailLogWithLeadResponse
from app.workers.email_task import generate_and_send_email_task

router = APIRouter(tags=["emails"])


@router.get("/emails", response_model=EmailLogListResponse)
async def list_email_logs(
    db: AsyncSession = Depends(get_db),
    job_id: UUID | None = None,
    status: EmailLogStatus | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=500),
) -> dict[str, object]:
    filters = []
    if job_id:
        filters.append(EmailLog.job_id == job_id)
    if status:
        filters.append(EmailLog.status == status)

    total = await db.scalar(select(func.count()).select_from(EmailLog).where(*filters))
    offset = (page - 1) * size
    result = await db.execute(
        select(EmailLog, Lead.business_name)
        .join(Lead, Lead.id == EmailLog.lead_id)
        .where(*filters)
        .order_by(EmailLog.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    items = []
    for log, business_name in result.all():
        payload = EmailLogResponse.model_validate(log).model_dump()
        payload["lead_business_name"] = business_name
        items.append(payload)
    return {"items": items, "total": total or 0, "page": page, "size": size, "pages": math.ceil((total or 0) / size)}


@router.post("/emails/{email_log_id}/resend", response_model=EmailLogResponse)
@limiter.limit("30/minute")
async def resend_email(request: Request, email_log_id: UUID, db: AsyncSession = Depends(get_db)) -> EmailLog:
    email_log = await db.get(EmailLog, email_log_id)
    if not email_log:
        raise HTTPException(status_code=404, detail="Email log not found")
    email_log.status = EmailLogStatus.generated
    email_log.error_message = None
    await db.commit()
    await db.refresh(email_log)
    generate_and_send_email_task.delay(str(email_log.lead_id))
    return email_log


@router.get("/jobs/{job_id}/emails/stats")
async def get_job_email_stats(job_id: UUID, db: AsyncSession = Depends(get_db)) -> dict[str, float | int]:
    total_generated = await db.scalar(select(func.count()).select_from(EmailLog).where(EmailLog.job_id == job_id))
    total_sent = await db.scalar(
        select(func.count()).select_from(EmailLog).where(EmailLog.job_id == job_id, EmailLog.status == EmailLogStatus.sent)
    )
    total_failed = await db.scalar(
        select(func.count()).select_from(EmailLog).where(EmailLog.job_id == job_id, EmailLog.status == EmailLogStatus.failed)
    )
    generated = total_generated or 0
    sent = total_sent or 0
    return {
        "total_generated": generated,
        "total_sent": sent,
        "total_failed": total_failed or 0,
        "success_rate": round((sent / generated) * 100, 2) if generated else 0.0,
    }
