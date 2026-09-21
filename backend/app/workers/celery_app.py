"""Phase 39: Celery app for background processing of expensive pipeline
steps (resume parsing, full matching+scoring). Kept separate from the
FastAPI app so the API process never blocks on OCR/embedding calls.

Start a worker with:
    celery -A app.workers.celery_app worker --loglevel=info
"""

from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "resume_analyzer",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    result_expires=3600,
)
celery_app.autodiscover_tasks(["app.workers"])
