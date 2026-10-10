# ============================================
# RAKSHANA 24/7 — Celery Tasks
# ============================================
# PRD: "Each user gets their own periodic scan task.
#        Failed tasks retry automatically.
#        Workers scale horizontally."

import logging
from datetime import datetime, timedelta, timezone

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.workers.tasks.scan_user",
    max_retries=3,
    default_retry_delay=60,
    queue="scans",
)
def scan_user(self, user_id: str):
    """
    Run the full scan pipeline for a single user.

    This is the core Celery task — each user gets their own
    periodic scan dispatched by the beat scheduler.

    Retries up to 3 times on failure with exponential backoff.
    """
    try:
        from app import create_app, db
        from app.services.scanner import run_scan_pipeline

        app = create_app()
        with app.app_context():
            logger.info(f"Starting scan for user {user_id}")
            results = run_scan_pipeline(user_id)
            logger.info(
                f"Scan completed for user {user_id}: "
                f"max_score={results.get('max_threat_score', 0)}, "
                f"alerts={results.get('alerts_generated', 0)}"
            )
            return results

    except Exception as exc:
        logger.error(f"Scan failed for user {user_id}: {exc}")
        # Exponential backoff: 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(
    name="app.workers.tasks.scan_all_active_users",
    queue="scans",
)
def scan_all_active_users():
    """
    Hourly task: dispatch individual scan tasks for all active users.

    PRD: "Celery allows us to schedule and distribute individual scan
    tasks per user, retry on failure, and fan out workload."
    """
    try:
        from app import create_app, db
        from app.models.user import User

        app = create_app()
        with app.app_context():
            # Get all active users with scanning enabled
            active_users = User.query.filter_by(
                is_active=True, scan_enabled=True
            ).all()

            dispatched = 0
            for user in active_users:
                # Check if the user is due for a scan
                if user.last_scan_at:
                    next_scan = user.last_scan_at + timedelta(
                        hours=user.scan_interval_hours
                    )
                    if datetime.now(timezone.utc) < next_scan:
                        continue  # Not yet due

                # Dispatch individual scan task
                scan_user.delay(user.id)
                dispatched += 1

            logger.info(
                f"Dispatched {dispatched} scan tasks for "
                f"{len(active_users)} active users"
            )
            return {"dispatched": dispatched, "total_active": len(active_users)}

    except Exception as e:
        logger.error(f"Failed to dispatch scans: {e}")
        return {"error": str(e)}


@celery_app.task(
    name="app.workers.tasks.send_notification",
    max_retries=3,
    default_retry_delay=30,
    queue="alerts",
)
def send_notification_task(user_id: str, alert_id: str):
    """
    Send notification for a specific alert.
    Runs as a separate task so notification failures don't block scanning.
    """
    try:
        from app import create_app, db
        from app.models.user import User
        from app.models.alert import Alert
        from app.services.notification_service import send_alert_notification

        app = create_app()
        with app.app_context():
            user = User.query.get(user_id)
            alert = Alert.query.get(alert_id)

            if not user or not alert:
                logger.error(f"User or alert not found: {user_id}, {alert_id}")
                return

            send_alert_notification(user, alert)
            db.session.commit()

            logger.info(f"Notification sent for alert {alert_id}")

    except Exception as exc:
        logger.error(f"Notification failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.workers.tasks.cleanup_old_scan_results",
    queue="maintenance",
)
def cleanup_old_scan_results():
    """
    Daily maintenance: clean up scan results older than 30 days.
    Keeps the database lean.
    """
    try:
        from app import create_app, db
        from app.models.scan_result import ScanResult

        app = create_app()
        with app.app_context():
            cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            old_results = ScanResult.query.filter(
                ScanResult.created_at < cutoff
            ).delete()
            db.session.commit()

            logger.info(f"Cleaned up {old_results} old scan results")
            return {"deleted": old_results}

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {"error": str(e)}


@celery_app.task(
    name="app.workers.tasks.register_user_scan",
    queue="scans",
)
def register_user_scan(user_id: str):
    """
    Register a new user's first scan.
    Called after user registration to run an initial scan immediately.
    """
    logger.info(f"Running initial scan for new user {user_id}")
    return scan_user(user_id)
