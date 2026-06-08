from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import EmailLogStatus, JobStatus, LeadEmailStatus


class CreateJobRequest(BaseModel):
    keyword: str = Field(min_length=2, max_length=500)
    cities: list[str] | None = None


class JobCreate(CreateJobRequest):
    batch_size: int | None = Field(default=None, ge=1, le=100)
    daily_limit: int | None = Field(default=None, ge=1)


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    keyword: str
    cities: list[str]
    status: JobStatus
    total_extracted: int
    total_emailed: int
    batch_size: int
    daily_limit: int
    current_city_index: int
    created_at: datetime
    updated_at: datetime


class EmailLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lead_id: UUID
    job_id: UUID
    subject: str
    body: str
    sent_at: datetime | None
    status: EmailLogStatus
    error_message: str | None
    ollama_model: str
    created_at: datetime


class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    business_name: str
    email: str | None
    phone: str | None
    address: str | None
    website: str | None
    category: str | None
    city: str
    rating: float | None
    review_count: int | None
    maps_url: str | None
    scraped_at: datetime
    email_status: LeadEmailStatus
    latest_email_log: EmailLogResponse | None = None


class JobListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[JobResponse]
    total: int


class LeadListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[LeadResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int = 0


class JobDetailResponse(JobResponse):
    progress: float
    leads: list[LeadResponse] = Field(default_factory=list)
    email_logs: list[EmailLogResponse] = Field(default_factory=list)


class EmailLogWithLeadResponse(EmailLogResponse):
    lead_business_name: str | None = None


class EmailLogListResponse(BaseModel):
    items: list[EmailLogWithLeadResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int = 0


class EmailStatusCounts(BaseModel):
    pending: int = 0
    generated: int = 0
    sent: int = 0
    failed: int = 0


class EmailsPerDay(BaseModel):
    date: str
    count: int


class LeadsPerJob(BaseModel):
    job_id: str
    keyword: str
    count: int


class DashboardStats(BaseModel):
    total_jobs: int
    active_jobs: int
    total_leads: int
    leads_with_email: int
    total_emails_sent: int
    emails_sent_today: int
    daily_limit: int
    daily_quota_used_pct: float
    emails_by_status: EmailStatusCounts
    emails_per_day: list[EmailsPerDay]
    leads_per_job: list[LeadsPerJob]
