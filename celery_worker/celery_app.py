import tasks.tasks_media
import tasks.cleanup_media_files
import tasks.convert_media
import tasks.delete_blacklisted_tokens
import tasks.send_email
from celery import Celery
from celery.schedules import crontab
from core.settings import settings

celery_app = Celery(
    "media_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=400,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "expire-subscriptions": {
            "task": "delete_blacklisted_tokens",
            "schedule": crontab(minute=0),
        },
        "cleanup-old-files-every-30-minutes": {
            "task": "cleanup_old_converted_files",
            "schedule": crontab(minute="*/30"),
            "args": (3600,),
        },
    },
)


app = celery_app
