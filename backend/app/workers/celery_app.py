from celery import Celery

from app.config import settings

celery_app = Celery(
    "leadgen",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.scraper_task", "app.workers.email_task", "app.workers.scheduler"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.scraper_task.*": {"queue": "scraping"},
        "app.workers.email_task.*": {"queue": "emailing"},
    },
)
