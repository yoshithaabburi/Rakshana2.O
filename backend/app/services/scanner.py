# ============================================
# RAKSHANA 24/7 — Scanner Pipeline Service
# ============================================
# PRD: "Three sub-tasks run in parallel:
#   (a) Telegram public channel scan via Telethon
#   (b) Paste site scrape via BS4
#   (c) Reverse image search via Google Vision"
#
# For hackathon scope: Telegram + Paste site are functional.
# Image search is architecture-ready but not connected.

import json
import time
import logging
from datetime import datetime, timezone

from app import db
from app.models.user import User
from app.models.alert import Alert
from app.models.scan_result import ScanResult
from app.services.threat_scorer import score_threat
from app.services.legal_mapper import map_incident_to_laws
from app.services.telegram_scanner import scan_telegram_channels
from app.services.paste_scanner import scan_paste_sites
from app.services.notification_service import send_alert_notification

logger = logging.getLogger(__name__)


def run_scan_pipeline(user_id: str) -> dict:
    """
    Execute the full scan pipeline for a user.

    PRD Data Flow Step 4-6:
    4. Celery worker picks up scan task. Three sub-tasks run in parallel.
    5. Each sub-task returns raw matches. NLP scoring module evaluates context.
    6. If score > 40: dashboard update. > 70: push alert. > 90: trusted contact.

    Returns summary of all scan results.
    """
    user = User.query.get(user_id)
    if not user:
        logger.error(f"User {user_id} not found for scan")
        return {"error": "User not found"}

    # Build user identifiers for matching
    identifiers = {
        "phone_hash": user.phone_hash,
        "name": user.display_name or "",
        "handles": user.social_handles or "",
    }

    results = {
        "user_id": user_id,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "scan_results": [],
        "alerts_generated": 0,
        "max_threat_score": 0,
    }

    # ── Sub-task A: Telegram scan ──
    telegram_result = _run_telegram_scan(user_id, identifiers)
    results["scan_results"].append(telegram_result)

    # ── Sub-task B: Paste site scan ──
    paste_result = _run_paste_scan(user_id, identifiers)
    results["scan_results"].append(paste_result)

    # ── Sub-task C: Image search (architecture-ready) ──
    image_result = _run_image_scan_stub(user_id)
    results["scan_results"].append(image_result)

    # ── Calculate max threat score across all scans ──
    all_scores = [r["threat_score"] for r in results["scan_results"]]
    max_score = max(all_scores) if all_scores else 0
    results["max_threat_score"] = max_score

    # ── Update user's current threat score ──
    user.current_threat_score = max_score
    user.last_scan_at = datetime.now(timezone.utc)

    # ── Generate alerts based on thresholds ──
    alerts_count = 0
    for scan in results["scan_results"]:
        if scan["threat_score"] >= 40:  # Watch threshold
            alert = _create_alert_from_scan(user_id, scan)
            if alert:
                alerts_count += 1

                # Send notifications based on severity
                if scan["threat_score"] >= 70:
                    send_alert_notification(user, alert)
                if scan["threat_score"] >= 90:
                    _notify_trusted_contacts(user, alert)

    results["alerts_generated"] = alerts_count
    db.session.commit()

    logger.info(
        f"Scan completed for user {user_id}: "
        f"max_score={max_score}, alerts={alerts_count}"
    )

    return results


def _run_telegram_scan(user_id: str, identifiers: dict) -> dict:
    """Run Telegram channel scan sub-task."""
    start_time = time.time()

    try:
        raw_matches = scan_telegram_channels(identifiers)
        duration_ms = int((time.time() - start_time) * 1000)

        # Score each match
        max_score = 0
        scored_matches = []
        for match in raw_matches:
            score_result = score_threat(
                match.get("text", ""),
                identifiers,
            )
            match["threat_assessment"] = score_result
            scored_matches.append(match)
            max_score = max(max_score, score_result["score"])

        # Save scan result
        scan_result = ScanResult(
            user_id=user_id,
            scan_type="telegram",
            scan_status="completed",
            scan_duration_ms=duration_ms,
            matches_found=len(raw_matches),
            raw_matches=json.dumps(scored_matches),
            threat_score=max_score,
            source_channel="Telegram public channels",
            completed_at=datetime.now(timezone.utc),
        )
        db.session.add(scan_result)

        return {
            "scan_type": "telegram",
            "status": "completed",
            "matches": len(raw_matches),
            "threat_score": max_score,
            "duration_ms": duration_ms,
            "details": scored_matches,
        }

    except Exception as e:
        logger.error(f"Telegram scan failed: {e}")
        duration_ms = int((time.time() - start_time) * 1000)

        scan_result = ScanResult(
            user_id=user_id,
            scan_type="telegram",
            scan_status="failed",
            scan_duration_ms=duration_ms,
            matches_found=0,
            threat_score=0,
            completed_at=datetime.now(timezone.utc),
        )
        db.session.add(scan_result)

        return {
            "scan_type": "telegram",
            "status": "failed",
            "matches": 0,
            "threat_score": 0,
            "error": str(e),
        }


def _run_paste_scan(user_id: str, identifiers: dict) -> dict:
    """Run paste site scan sub-task."""
    start_time = time.time()

    try:
        raw_matches = scan_paste_sites(identifiers)
        duration_ms = int((time.time() - start_time) * 1000)

        max_score = 0
        scored_matches = []
        for match in raw_matches:
            score_result = score_threat(
                match.get("text", ""),
                identifiers,
            )
            match["threat_assessment"] = score_result
            scored_matches.append(match)
            max_score = max(max_score, score_result["score"])

        scan_result = ScanResult(
            user_id=user_id,
            scan_type="paste_site",
            scan_status="completed",
            scan_duration_ms=duration_ms,
            matches_found=len(raw_matches),
            raw_matches=json.dumps(scored_matches),
            threat_score=max_score,
            source_channel="Paste sites",
            completed_at=datetime.now(timezone.utc),
        )
        db.session.add(scan_result)

        return {
            "scan_type": "paste_site",
            "status": "completed",
            "matches": len(raw_matches),
            "threat_score": max_score,
            "duration_ms": duration_ms,
            "details": scored_matches,
        }

    except Exception as e:
        logger.error(f"Paste scan failed: {e}")
        duration_ms = int((time.time() - start_time) * 1000)

        scan_result = ScanResult(
            user_id=user_id,
            scan_type="paste_site",
            scan_status="failed",
            scan_duration_ms=duration_ms,
            matches_found=0,
            threat_score=0,
            completed_at=datetime.now(timezone.utc),
        )
        db.session.add(scan_result)

        return {
            "scan_type": "paste_site",
            "status": "failed",
            "matches": 0,
            "threat_score": 0,
            "error": str(e),
        }


def _run_image_scan_stub(user_id: str) -> dict:
    """Image search stub — architecture-ready, out of scope for hackathon."""
    scan_result = ScanResult(
        user_id=user_id,
        scan_type="image_search",
        scan_status="skipped",
        scan_duration_ms=0,
        matches_found=0,
        threat_score=0,
        source_channel="Reverse image search (not active)",
        completed_at=datetime.now(timezone.utc),
    )
    db.session.add(scan_result)

    return {
        "scan_type": "image_search",
        "status": "skipped",
        "matches": 0,
        "threat_score": 0,
        "note": "Reverse image search is architecture-ready but not active for hackathon demo.",
    }


def _create_alert_from_scan(user_id: str, scan_data: dict) -> Alert | None:
    """Create an alert from a scan result that exceeded the watch threshold."""
    score = scan_data.get("threat_score", 0)
    if score < 40:
        return None

    scan_type = scan_data.get("scan_type", "unknown")
    details = scan_data.get("details", [])

    # Find the highest-scoring match for the alert
    best_match = None
    best_score_data = None
    for match in details:
        assessment = match.get("threat_assessment", {})
        if assessment.get("score", 0) >= 40:
            if not best_match or assessment["score"] > best_score_data.get("score", 0):
                best_match = match
                best_score_data = assessment

    if not best_match or not best_score_data:
        return None

    # Determine threat type and map to laws
    threat_type = best_score_data.get("threat_type", "other")
    applicable_laws = map_incident_to_laws(threat_type)

    alert = Alert(
        user_id=user_id,
        threat_score=best_score_data["score"],
        threat_type=threat_type,
        source_type=scan_type,
        source_name=best_match.get("source", f"Scan: {scan_type}"),
        source_url=best_match.get("url", ""),
        title=f"Potential {threat_type.replace('_', ' ').title()} Detected",
        description=best_score_data.get("explanation", "Threat detected during scan"),
        explanation=best_score_data.get("explanation", ""),
        matched_content=", ".join(best_score_data.get("matched_keywords", [])[:5]),
        applicable_laws=json.dumps(applicable_laws),
    )
    alert.classify_severity()

    # Determine notification type based on score
    if score >= 90:
        alert.notification_type = "whatsapp"
    elif score >= 70:
        alert.notification_type = "sms"
    else:
        alert.notification_type = "dashboard"

    alert.notification_sent = True

    db.session.add(alert)
    return alert


def _notify_trusted_contacts(user: User, alert: Alert):
    """Notify user's trusted contacts for critical alerts (score > 90)."""
    if not user.trusted_contacts:
        return

    try:
        contacts = json.loads(user.trusted_contacts)
        for contact_phone in contacts:
            # In production: send SMS/WhatsApp via Twilio
            logger.info(
                f"CRITICAL ALERT: Notifying trusted contact {contact_phone[:4]}*** "
                f"about alert {alert.id} for user {user.id}"
            )
        alert.trusted_contact_notified = True
    except Exception as e:
        logger.error(f"Failed to notify trusted contacts: {e}")
