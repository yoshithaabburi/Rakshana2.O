# ============================================
# RAKSHANA 24/7 — Anonymous Reports Routes
# ============================================
# PRD: "Reports submitted via anonymising proxy.
#        No IP logged server-side."

import json

from flask import Blueprint, request, jsonify

from app import db
from app.models.report import Report
from app.utils.encryption import generate_anonymous_token
from app.services.legal_mapper import map_incident_to_laws

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/submit", methods=["POST"])
def submit_report():
    """
    Submit an anonymous cyber crime report.

    – No authentication required
    – No IP address logged
    – No user_id linked
    – Returns anonymous token for status tracking
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    incident_type = data.get("incident_type", "").strip()
    description = data.get("description", "").strip()
    platform = data.get("platform", "").strip()
    evidence_urls = data.get("evidence_urls", [])
    language = data.get("language", "en")

    # Validation
    valid_types = [
        "stalking", "morphed_image", "harassment",
        "blackmail", "doxxing", "other",
    ]
    if incident_type not in valid_types:
        return jsonify({
            "error": f"Invalid incident type. Must be one of: {valid_types}",
        }), 400

    if not description:
        return jsonify({"error": "Description is required"}), 400

    if len(description) < 10:
        return jsonify({"error": "Please provide more detail (min 10 characters)"}), 400

    # Map to applicable laws
    applicable_laws = map_incident_to_laws(incident_type)

    # Generate anonymous token
    anonymous_token = generate_anonymous_token()

    # Create report — NO user_id, NO IP address
    report = Report(
        incident_type=incident_type,
        platform=platform,
        description=description,
        evidence_urls=json.dumps(evidence_urls) if evidence_urls else None,
        applicable_laws=json.dumps(applicable_laws),
        anonymous_token=anonymous_token,
        language=language,
        status="submitted",
    )

    db.session.add(report)
    db.session.commit()

    return jsonify({
        "message": "Report submitted anonymously. Your data is encrypted.",
        "anonymous_token": anonymous_token,
        "applicable_laws": applicable_laws,
        "status": "submitted",
        "next_steps": [
            "Save your anonymous token to check report status later",
            "Consider taking screenshots of the offending content",
            "Visit cybercrime.gov.in for official filing",
        ],
    }), 201


@reports_bp.route("/status/<anonymous_token>", methods=["GET"])
def check_status(anonymous_token):
    """
    Check report status using anonymous token.

    No authentication needed — the token IS the credential.
    """
    report = Report.query.filter_by(anonymous_token=anonymous_token).first()

    if not report:
        return jsonify({"error": "Report not found. Check your anonymous token."}), 404

    return jsonify({
        "report": report.to_dict(),
    }), 200


@reports_bp.route("/types", methods=["GET"])
def get_report_types():
    """Get available report incident types with descriptions."""
    types = [
        {
            "value": "stalking",
            "label": "Cyber Stalking",
            "description": "Someone repeatedly contacts, monitors, or tracks you online",
            "laws": ["Section 354D IPC", "Section 78 BNS"],
        },
        {
            "value": "morphed_image",
            "label": "Morphed / Deepfake Images",
            "description": "Someone created or shared manipulated images of you",
            "laws": ["Section 66E IT Act", "Section 67/67A IT Act"],
        },
        {
            "value": "harassment",
            "label": "Online Harassment & Abuse",
            "description": "Unwanted sexual messages, threats, or abusive content",
            "laws": ["Section 354A IPC", "Section 509 IPC"],
        },
        {
            "value": "blackmail",
            "label": "Blackmail / Sextortion",
            "description": "Threatening to publish private content unless demands are met",
            "laws": ["Section 384/385 IPC", "Section 506 IPC"],
        },
        {
            "value": "doxxing",
            "label": "Doxxing / Info Leak",
            "description": "Personal information published online without consent",
            "laws": ["Section 66C IT Act", "Section 72 IT Act"],
        },
        {
            "value": "other",
            "label": "Other",
            "description": "Any other form of cyber crime or harassment",
            "laws": [],
        },
    ]

    return jsonify({"types": types}), 200
