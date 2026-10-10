# ============================================
# RAKSHANA 24/7 — Dashboard Routes
# ============================================
# PRD: Protection status dashboard, threat timeline

from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from app import db
from app.models.user import User
from app.models.alert import Alert
from app.models.scan_result import ScanResult

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/", methods=["GET"])
@jwt_required()
def get_dashboard():
    """
    Get complete dashboard data.

    PRD Screen 2: One dominant element — large circular shield indicator.
    Below it: last scan timestamp and recent activity feed.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Protection status
    threat_score = user.current_threat_score
    if threat_score >= 90:
        status = "critical"
        status_text = "Critical Alert"
        status_color = "red"
    elif threat_score >= 70:
        status = "alert"
        status_text = "Alert Active"
        status_color = "amber"
    elif threat_score >= 40:
        status = "watching"
        status_text = "Monitoring"
        status_color = "amber"
    else:
        status = "safe"
        status_text = "Protected"
        status_color = "green"

    # Recent alerts (last 5)
    recent_alerts = Alert.query.filter_by(
        user_id=user_id, is_dismissed=False
    ).order_by(Alert.detected_at.desc()).limit(5).all()

    # Recent scans (last 5)
    recent_scans = ScanResult.query.filter_by(
        user_id=user_id
    ).order_by(ScanResult.created_at.desc()).limit(5).all()

    # Unread alert count
    unread_count = Alert.query.filter_by(
        user_id=user_id, is_read=False, is_dismissed=False
    ).count()

    # Today's scan count
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    scans_today = ScanResult.query.filter(
        ScanResult.user_id == user_id,
        ScanResult.created_at >= today_start,
    ).count()

    return jsonify({
        "protection_status": {
            "threat_score": threat_score,
            "status": status,
            "status_text": status_text,
            "status_color": status_color,
        },
        "last_scan_at": user.last_scan_at.isoformat() if user.last_scan_at else None,
        "scan_enabled": user.scan_enabled,
        "scans_today": scans_today,
        "unread_alerts": unread_count,
        "recent_alerts": [a.to_dict() for a in recent_alerts],
        "recent_scans": [s.to_dict() for s in recent_scans],
    }), 200


@dashboard_bp.route("/timeline", methods=["GET"])
@jwt_required()
def threat_timeline():
    """
    Get 7-day threat score timeline for Chart.js graph.

    PRD Screen 4: "A 7-day Chart.js line graph showing threat score trend."
    """
    user_id = get_jwt_identity()
    days = request.args.get("days", 7, type=int)
    days = min(days, 30)  # Cap at 30 days

    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)

    # Get daily max threat scores
    daily_scores = (
        db.session.query(
            func.date(ScanResult.created_at).label("date"),
            func.max(ScanResult.threat_score).label("max_score"),
            func.avg(ScanResult.threat_score).label("avg_score"),
            func.count(ScanResult.id).label("scan_count"),
        )
        .filter(
            ScanResult.user_id == user_id,
            ScanResult.created_at >= start_date,
        )
        .group_by(func.date(ScanResult.created_at))
        .order_by(func.date(ScanResult.created_at))
        .all()
    )

    # Build timeline data (fill in missing days with 0)
    timeline = []
    for i in range(days):
        date = (start_date + timedelta(days=i)).date()
        date_str = date.isoformat()

        # Find matching day in results
        day_data = next(
            (d for d in daily_scores if str(d.date) == date_str),
            None,
        )

        timeline.append({
            "date": date_str,
            "max_score": day_data.max_score if day_data else 0,
            "avg_score": round(day_data.avg_score, 1) if day_data else 0,
            "scan_count": day_data.scan_count if day_data else 0,
        })

    # Daily alert counts
    daily_alerts = (
        db.session.query(
            func.date(Alert.detected_at).label("date"),
            func.count(Alert.id).label("count"),
        )
        .filter(
            Alert.user_id == user_id,
            Alert.detected_at >= start_date,
        )
        .group_by(func.date(Alert.detected_at))
        .all()
    )

    alert_map = {str(d.date): d.count for d in daily_alerts}
    for day in timeline:
        day["alert_count"] = alert_map.get(day["date"], 0)

    return jsonify({
        "timeline": timeline,
        "days": days,
        "current_score": User.query.get(user_id).current_threat_score,
    }), 200


@dashboard_bp.route("/stats", methods=["GET"])
@jwt_required()
def dashboard_stats():
    """Get aggregate statistics for the dashboard."""
    user_id = get_jwt_identity()

    total_scans = ScanResult.query.filter_by(user_id=user_id).count()
    total_alerts = Alert.query.filter_by(user_id=user_id).count()
    total_threats = Alert.query.filter(
        Alert.user_id == user_id,
        Alert.threat_score >= 40,
    ).count()

    # Threat type distribution
    type_dist = (
        db.session.query(
            Alert.threat_type,
            func.count(Alert.id).label("count"),
        )
        .filter(Alert.user_id == user_id)
        .group_by(Alert.threat_type)
        .all()
    )

    # Source distribution
    source_dist = (
        db.session.query(
            Alert.source_type,
            func.count(Alert.id).label("count"),
        )
        .filter(Alert.user_id == user_id)
        .group_by(Alert.source_type)
        .all()
    )

    return jsonify({
        "total_scans": total_scans,
        "total_alerts": total_alerts,
        "total_threats": total_threats,
        "threat_types": {t.threat_type: t.count for t in type_dist},
        "source_types": {s.source_type: s.count for s in source_dist},
    }), 200
