"""Celery application — асинхронная очередь задач (брокер Redis)."""
from celery import Celery

from app.config import settings

celery_app = Celery(
    "returns",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    task_track_started=True,
    task_default_retry_delay=10,  # повтор через 10 секунд при сбое
    task_max_retries=3,
)
