import enum
import uuid

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    paused = "paused"
    done = "done"
    failed = "failed"


class LeadEmailStatus(str, enum.Enum):
    pending = "pending"
    generated = "generated"
    sent = "sent"
    failed = "failed"
    bounced = "bounced"


class EmailLogStatus(str, enum.Enum):
    generated = "generated"
    sent = "sent"
    failed = "failed"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    keyword: Mapped[str] = mapped_column(String(500), nullable=False)
    cities: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default=text("'{}'::text[]"))
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus, name="job_status"), nullable=False, default=JobStatus.pending)
    total_extracted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_emailed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    batch_size: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    daily_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=20000)
    current_city_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    leads: Mapped[list["Lead"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    email_logs: Mapped[list["EmailLog"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    business_name: Mapped[str] = mapped_column(String(500), nullable=False)
    email: Mapped[str | None] = mapped_column(String(500))
    phone: Mapped[str | None] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(1000))
    category: Mapped[str | None] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(200), nullable=False)
    rating: Mapped[float | None] = mapped_column(Float)
    review_count: Mapped[int | None] = mapped_column(Integer)
    maps_url: Mapped[str | None] = mapped_column(Text)
    scraped_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    email_status: Mapped[LeadEmailStatus] = mapped_column(
        Enum(LeadEmailStatus, name="lead_email_status"), nullable=False, default=LeadEmailStatus.pending
    )

    job: Mapped[Job] = relationship(back_populates="leads")
    email_logs: Mapped[list["EmailLog"]] = relationship(back_populates="lead", cascade="all, delete-orphan")


class EmailLog(Base):
    __tablename__ = "email_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    lead_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at = mapped_column(DateTime(timezone=True))
    status: Mapped[EmailLogStatus] = mapped_column(Enum(EmailLogStatus, name="email_log_status"), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    ollama_model: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    lead: Mapped[Lead] = relationship(back_populates="email_logs")
    job: Mapped[Job] = relationship(back_populates="email_logs")


class CityKeyword(Base):
    __tablename__ = "city_keywords"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    keyword: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    cities: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default=text("'{}'::text[]"))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

