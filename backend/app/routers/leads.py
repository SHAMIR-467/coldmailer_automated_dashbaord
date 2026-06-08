import csv
import io
import math
from collections.abc import Iterable
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import EmailLog, Lead, LeadEmailStatus
from app.schemas import LeadListResponse, LeadResponse

router = APIRouter(tags=["leads"])


def _lead_payload(lead: Lead, latest_email_log: EmailLog | None = None) -> dict:
    data = LeadResponse.model_validate(lead).model_dump()
    data["latest_email_log"] = latest_email_log
    return data


@router.get("/jobs/{job_id}/leads", response_model=LeadListResponse)
async def list_job_leads(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=500),
    has_email: bool | None = None,
    city: str | None = None,
    email_status: LeadEmailStatus | None = None,
) -> dict[str, object]:
    filters = [Lead.job_id == job_id]
    if has_email is True:
        filters.append(Lead.email.is_not(None))
    elif has_email is False:
        filters.append(Lead.email.is_(None))
    if city:
        filters.append(Lead.city == city)
    if email_status:
        filters.append(Lead.email_status == email_status)

    total = await db.scalar(select(func.count()).select_from(Lead).where(*filters))
    offset = (page - 1) * size
    result = await db.execute(select(Lead).where(*filters).order_by(Lead.scraped_at.desc()).offset(offset).limit(size))
    items = [_lead_payload(lead) for lead in result.scalars().all()]
    return {"items": items, "total": total or 0, "page": page, "size": size, "pages": math.ceil((total or 0) / size)}


@router.get("/jobs/{job_id}/leads/export")
async def export_job_leads(job_id: UUID, db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    result = await db.execute(
        select(Lead)
        .where(Lead.job_id == job_id, Lead.email.is_not(None))
        .order_by(Lead.scraped_at.desc())
    )
    leads = result.scalars().all()
    columns = [
        "business_name",
        "email",
        "phone",
        "address",
        "website",
        "category",
        "city",
        "rating",
        "review_count",
        "email_status",
        "maps_url",
    ]

    def stream_csv() -> Iterable[str]:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(columns)
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        for lead in leads:
            writer.writerow([getattr(lead, column) for column in columns])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    return StreamingResponse(
        stream_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=leads_{job_id}.csv"},
    )


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    latest_log = await db.scalar(
        select(EmailLog).where(EmailLog.lead_id == lead_id).order_by(EmailLog.created_at.desc()).limit(1)
    )
    return _lead_payload(lead, latest_log)
