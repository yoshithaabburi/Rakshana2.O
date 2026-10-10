# ============================================
# RAKSHANA 24/7 — User Management Routes
# ============================================
# PRD: "User Owns Their Data: Full export and delete available at any time."

import json
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.user import User

users_bp = Blueprint("users", __name__)


@users_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """Get full user profile with sensitive data."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"user": user.to_dict(include_sensitive=True)}), 200


@users_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """Update user profile — language, display name, scan settings."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()

    if "display_name" in data:
        user.display_name = data["display_name"]
    if "language" in data and data["language"] in ("en", "te", "kn", "hi"):
        user.language = data["language"]
    if "scan_interval_hours" in data:
        interval = int(data["scan_interval_hours"])
        if interval >= 1:
            user.scan_interval_hours = interval
    if "scan_enabled" in data:
        user.scan_enabled = bool(data["scan_enabled"])
    if "phone_number" in data:
        user.phone_number = data["phone_number"]  # Encrypts automatically
    if "social_handles" in data:
        user.social_handles = data["social_handles"]  # Encrypts automatically
    if "trusted_contacts" in data:
        user.trusted_contacts = json.dumps(data["trusted_contacts"])

    db.session.commit()

    return jsonify({
        "message": "Profile updated",
        "user": user.to_dict(include_sensitive=True),
    }), 200


@users_bp.route("/export", methods=["GET"])
@jwt_required()
def export_data():
    """
    Export all user data — PRD privacy principle.

    Returns all user data, alerts, scan results in one JSON payload.
    "User Owns Their Data: Full export and delete available at any time."
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    alerts = [a.to_dict() for a in user.alerts.all()]
    scan_results = [s.to_dict() for s in user.scan_results.all()]

    export = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user": user.to_dict(include_sensitive=True),
        "alerts": alerts,
        "scan_results": scan_results,
        "total_alerts": len(alerts),
        "total_scans": len(scan_results),
    }

    return jsonify(export), 200


@users_bp.route("/delete", methods=["DELETE"])
@jwt_required()
def delete_account():
    """
    Delete user account and all associated data.

    PRD: "Deletion cascades to all encrypted records within 24 hours."
    We delete immediately for hackathon scope.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Cascade delete — alerts and scan results removed via relationship
    db.session.delete(user)
    db.session.commit()

    return jsonify({
        "message": "Account and all associated data permanently deleted.",
    }), 200


@users_bp.route("/trusted-contacts", methods=["PUT"])
@jwt_required()
def update_trusted_contacts():
    """Update trusted contacts list (encrypted)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    contacts = data.get("contacts", [])

    if not isinstance(contacts, list):
        return jsonify({"error": "Contacts must be a list"}), 400

    user.trusted_contacts = json.dumps(contacts)
    db.session.commit()

    return jsonify({"message": f"Updated {len(contacts)} trusted contacts"}), 200
