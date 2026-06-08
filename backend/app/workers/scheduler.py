from celery.schedules import crontab

from app.workers.celery_app import celery_app

celery_app.conf.beat_schedule = {
    "check-running-jobs": {
        "task": "app.workers.scraper_task.check_stalled_jobs",
        "schedule": crontab(minute="*/10"),
    },
    "reset-daily-email-counter": {
        "task": "app.workers.email_task.reset_daily_counter",
        "schedule": crontab(hour=0, minute=0),
    },
    "retry-failed-emails": {
        "task": "app.workers.email_task.retry_failed_emails",
        "schedule": crontab(hour="*/2"),
    },
}
