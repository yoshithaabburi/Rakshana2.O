# ============================================
# RAKSHANA 24/7 — Celery Application
# ============================================
# PRD: "Celery distributed task queue. Each user gets their own
#        periodic scan task. Failed tasks retry automatically."

import os

from celery import Celery
from celery.schedules import crontab

from dotenv import load_dotenv

load_dotenv()


def make_celery(app=None):
    """Create Celery instance, optionally bound to Flask app."""
    celery = Celery(
        "rakshana",
        broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
    )

    celery.conf.update(
        # Task settings
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Asia/Kolkata",
        enable_utc=True,

        # Retry settings
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        task_default_retry_delay=60,  # 1 minute
        task_max_retries=3,

        # Worker settings
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=100,

        # Beat schedule — periodic scanning
        beat_schedule={
            "scan-all-users": {
                "task": "app.workers.tasks.scan_all_active_users",
                "schedule": crontab(
                    minute=0,
                    hour=f"*/{os.getenv('SCAN_INTERVAL_HOURS', '4')}",
                ),
                "options": {"queue": "scans"},
            },
            "cleanup-old-scans": {
                "task": "app.workers.tasks.cleanup_old_scan_results",
                "schedule": crontab(minute=0, hour=3),  # Daily at 3 AM
                "options": {"queue": "maintenance"},
            },
        },
        task_queues={
            "scans": {"exchange": "scans", "routing_key": "scan"},
            "alerts": {"exchange": "alerts", "routing_key": "alert"},
            "maintenance": {"exchange": "maintenance", "routing_key": "maint"},
        },
    )

    if app:
        celery.conf.update(app.config)

        class ContextTask(celery.Task):
            """Ensure Flask app context is available in Celery tasks."""

            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask

    return celery


# Create global celery instance
celery_app = make_celery()
