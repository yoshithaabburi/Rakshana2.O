# ============================================
# RAKSHANA 24/7 — Alerts Routes
# ============================================
# PRD: Alert inbox, graduated severity, action tracking

from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.alert import Alert

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.route("/", methods=["GET"])
@jwt_required()
def get_alerts():
    """
    Get user's alerts with filtering and pagination.

    Query params:
      - severity: safe|watch|alert|critical
      - is_read: true|false
      - page: int (default 1)
      - per_page: int (default 20)
      - sort: newest|oldest|score (default newest)
    """
    user_id = get_jwt_identity()

    query = Alert.query.filter_by(user_id=user_id, is_dismissed=False)

    # Filter by severity
    severity = request.args.get("severity")
    if severity:
        query = query.filter_by(severity=severity)

    # Filter by read status
    is_read = request.args.get("is_read")
    if is_read is not None:
        query = query.filter_by(is_read=is_read.lower() == "true")

    # Sorting
    sort = request.args.get("sort", "newest")
    if sort == "oldest":
        query = query.order_by(Alert.detected_at.asc())
    elif sort == "score":
        query = query.order_by(Alert.threat_score.desc())
    else:
        query = query.order_by(Alert.detected_at.desc())

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)  # Cap at 100

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "alerts": [a.to_dict() for a in paginated.items],
        "total": paginated.total,
        "page": paginated.page,
        "per_page": paginated.per_page,
        "pages": paginated.pages,
        "has_next": paginated.has_next,
        "has_prev": paginated.has_prev,
        "unread_count": Alert.query.filter_by(
            user_id=user_id, is_read=False, is_dismissed=False
        ).count(),
    }), 200


@alerts_bp.route("/<alert_id>", methods=["GET"])
@jwt_required()
def get_alert(alert_id):
    """Get single alert detail."""
    user_id = get_jwt_identity()
    alert = Alert.query.filter_by(id=alert_id, user_id=user_id).first()

    if not alert:
        return jsonify({"error": "Alert not found"}), 404

    return jsonify({"alert": alert.to_dict()}), 200


@alerts_bp.route("/<alert_id>/read", methods=["PUT"])
@jwt_required()
def mark_read(alert_id):
    """Mark alert as read."""
    user_id = get_jwt_identity()
    alert = Alert.query.filter_by(id=alert_id, user_id=user_id).first()

    if not alert:
        return jsonify({"error": "Alert not found"}), 404

    alert.is_read = True
    alert.read_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({"message": "Alert marked as read", "alert": alert.to_dict()}), 200


@alerts_bp.route("/<alert_id>/action", methods=["PUT"])
@jwt_required()
def take_action(alert_id):
    """
    Record action taken on an alert.

    Actions: screenshot, reported, contacted, dismissed
    """
    user_id = get_jwt_identity()
    alert = Alert.query.filter_by(id=alert_id, user_id=user_id).first()

    if not alert:
        return jsonify({"error": "Alert not found"}), 404

    data = request.get_json()
    action = data.get("action", "")

    valid_actions = ["screenshot", "reported", "contacted", "dismissed"]
    if action not in valid_actions:
        return jsonify({"error": f"Invalid action. Must be one of: {valid_actions}"}), 400

    alert.action_taken = action
    if action == "dismissed":
        alert.is_dismissed = True
    if action == "reported":
        alert.is_reported = True

    alert.is_read = True
    alert.read_at = alert.read_at or datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        "message": f"Action '{action}' recorded",
        "alert": alert.to_dict(),
    }), 200


@alerts_bp.route("/summary", methods=["GET"])
@jwt_required()
def alerts_summary():
    """Get alert summary stats for the user."""
    user_id = get_jwt_identity()

    total = Alert.query.filter_by(user_id=user_id).count()
    unread = Alert.query.filter_by(user_id=user_id, is_read=False, is_dismissed=False).count()
    critical = Alert.query.filter_by(user_id=user_id, severity="critical", is_dismissed=False).count()
    alert_count = Alert.query.filter_by(user_id=user_id, severity="alert", is_dismissed=False).count()
    watch = Alert.query.filter_by(user_id=user_id, severity="watch", is_dismissed=False).count()

    return jsonify({
        "total": total,
        "unread": unread,
        "by_severity": {
            "critical": critical,
            "alert": alert_count,
            "watch": watch,
        },
    }), 200
