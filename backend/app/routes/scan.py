# ============================================
# RAKSHANA 24/7 — Scan Routes
# ============================================
# Trigger scans, view scan history, scan transparency

from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.user import User
from app.models.scan_result import ScanResult

scan_bp = Blueprint("scan", __name__)


@scan_bp.route("/trigger", methods=["POST"])
@jwt_required()
def trigger_scan():
    """
    Manually trigger a scan for the current user.

    In production this dispatches to Celery. For hackathon demo,
    we run the scan pipeline synchronously and return results.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    if not user.scan_enabled:
        return jsonify({"error": "Scanning is disabled for your account"}), 403

    # Import scan service
    from app.services.scanner import run_scan_pipeline

    results = run_scan_pipeline(user_id)

    # Update user's last scan time
    user.last_scan_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        "message": "Scan completed",
        "results": results,
        "scanned_at": user.last_scan_at.isoformat(),
    }), 200


@scan_bp.route("/history", methods=["GET"])
@jwt_required()
def scan_history():
    """
    Get scan history for the current user.

    PRD: "Users can see exactly what was scanned, when, and what was found."
    """
    user_id = get_jwt_identity()

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    scan_type = request.args.get("type")

    query = ScanResult.query.filter_by(user_id=user_id)

    if scan_type:
        query = query.filter_by(scan_type=scan_type)

    query = query.order_by(ScanResult.created_at.desc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "scan_results": [s.to_dict() for s in paginated.items],
        "total": paginated.total,
        "page": paginated.page,
        "per_page": paginated.per_page,
        "pages": paginated.pages,
    }), 200


@scan_bp.route("/status", methods=["GET"])
@jwt_required()
def scan_status():
    """Get current scan status — last scan time, next scan estimate, scan types available."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Get latest scan per type
    latest_telegram = ScanResult.query.filter_by(
        user_id=user_id, scan_type="telegram"
    ).order_by(ScanResult.created_at.desc()).first()

    latest_paste = ScanResult.query.filter_by(
        user_id=user_id, scan_type="paste_site"
    ).order_by(ScanResult.created_at.desc()).first()

    latest_image = ScanResult.query.filter_by(
        user_id=user_id, scan_type="image_search"
    ).order_by(ScanResult.created_at.desc()).first()

    return jsonify({
        "scan_enabled": user.scan_enabled,
        "scan_interval_hours": user.scan_interval_hours,
        "last_scan_at": user.last_scan_at.isoformat() if user.last_scan_at else None,
        "current_threat_score": user.current_threat_score,
        "scan_sources": {
            "telegram": {
                "last_scan": latest_telegram.to_dict() if latest_telegram else None,
                "available": True,
            },
            "paste_site": {
                "last_scan": latest_paste.to_dict() if latest_paste else None,
                "available": True,
            },
            "image_search": {
                "last_scan": latest_image.to_dict() if latest_image else None,
                "available": False,  # Out of scope for hackathon
            },
        },
    }), 200


@scan_bp.route("/demo", methods=["GET"])
@jwt_required()
def demo_scan():
    """
    Quick demo scan result — returns pre-computed NLP threat scoring results.

    Useful for hackathon presentations to demonstrate the scoring engine
    without waiting for the full pipeline.
    """
    from app.services.threat_scorer import score_threat

    demo_texts = {
        "safe": "The weather in Hyderabad is lovely today. Let's meet for coffee.",
        "watch": "Contact details shared: +91-XXXXX-XXXXX. Phone number leaked without consent from database dump.",
        "alert": "Will teach her a lesson. Morphed photos ready to share. Tracking her location and movements.",
        "critical": "Deepfake nude images uploaded. Blackmail extortion demand: pay money or photos go viral immediately to everyone now.",
    }

    results = {}
    for level, text in demo_texts.items():
        results[level] = score_threat(text)

    return jsonify({
        "message": "NLP Threat Scoring Engine Demo",
        "demo_results": results,
    }), 200


@scan_bp.route("/analyze", methods=["POST"])
def analyze_content():
    """
    Analyze uploaded text or file for threat scoring.

    Accepts:
      - JSON body with {"text": "..."} for direct text analysis
      - Multipart form with file upload (.txt, .png, .jpg, .pdf)
      - Multipart form with "text" field

    Returns threat score, explanation, matched keywords, and applicable laws.
    """
    from app.services.threat_scorer import score_threat

    text_to_analyze = ""
    filename = ""

    # Check if it's a file upload
    if request.files and "file" in request.files:
        file = request.files["file"]
        filename = file.filename or "uploaded_file"
        allowed_extensions = {"txt", "png", "jpg", "jpeg", "pdf", "csv", "html"}
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext not in allowed_extensions:
            return jsonify({
                "error": f"Unsupported file type: .{ext}. Allowed: {', '.join(allowed_extensions)}"
            }), 400

        try:
            file_content = file.read()

            if ext == "txt" or ext == "csv" or ext == "html":
                # Text files — read directly
                text_to_analyze = file_content.decode("utf-8", errors="ignore")
            elif ext in ("png", "jpg", "jpeg"):
                # Image files — extract any text-like content description
                # In production this would use Google Vision API OCR
                # For hackathon demo, we analyze the filename and any form text
                text_to_analyze = request.form.get("text", "")
                if not text_to_analyze:
                    text_to_analyze = f"Image uploaded: {filename}"
                    # Simulate image analysis results
                    return jsonify({
                        "score": 45,
                        "threat_type": "potential_image_threat",
                        "explanation": (
                            "CAUTION: Image uploaded for analysis. In production, this image would be "
                            "processed through Google Vision API for: (1) Reverse image search to check "
                            "if it appears on suspicious sites, (2) Explicit content detection, "
                            "(3) Face matching against your registered photo. "
                            "For the hackathon demo, please paste the text content from the screenshot "
                            "into the text box for NLP threat analysis."
                        ),
                        "matched_keywords": ["image analysis", "visual scan"],
                        "confidence": 30,
                        "filename": filename,
                        "file_type": ext,
                        "applicable_laws": [
                            {"section": "66E", "act": "IT Act 2000", "title": "Privacy Violation — Capturing/publishing private images"},
                            {"section": "354C", "act": "IPC", "title": "Voyeurism"},
                            {"section": "67/67A", "act": "IT Act 2000", "title": "Publishing obscene/sexually explicit material"},
                        ],
                    }), 200
            elif ext == "pdf":
                # PDF — extract text (basic)
                text_to_analyze = file_content.decode("utf-8", errors="ignore")
                # Remove PDF binary headers
                import re as _re
                text_to_analyze = _re.sub(r"[^\x20-\x7E\n\r]", " ", text_to_analyze)
                text_to_analyze = " ".join(text_to_analyze.split())

        except Exception as e:
            return jsonify({"error": f"Failed to process file: {str(e)}"}), 500

    elif request.is_json:
        data = request.get_json()
        text_to_analyze = data.get("text", "")
    else:
        # Form data
        text_to_analyze = request.form.get("text", "")

    if not text_to_analyze or len(text_to_analyze.strip()) < 3:
        return jsonify({
            "error": "Please provide text or upload a file to analyze (minimum 3 characters)"
        }), 400

    # Run NLP threat scoring
    result = score_threat(text_to_analyze)

    # Map threat types to applicable Indian cyber laws
    law_mapping = {
        "doxxing": [
            {"section": "72", "act": "IT Act 2000", "title": "Breach of Confidentiality and Privacy"},
            {"section": "43A", "act": "IT Act 2000", "title": "Compensation for failure to protect data"},
            {"section": "66E", "act": "IT Act 2000", "title": "Privacy Violation"},
        ],
        "stalking": [
            {"section": "354D", "act": "IPC", "title": "Stalking"},
            {"section": "66A", "act": "IT Act 2000", "title": "Offensive messages through communication service"},
        ],
        "morphed_image": [
            {"section": "66E", "act": "IT Act 2000", "title": "Privacy Violation — Capturing/publishing private images"},
            {"section": "67/67A", "act": "IT Act 2000", "title": "Publishing obscene/sexually explicit material"},
            {"section": "354C", "act": "IPC", "title": "Voyeurism"},
        ],
        "harassment": [
            {"section": "354A", "act": "IPC", "title": "Sexual Harassment"},
            {"section": "509", "act": "IPC", "title": "Word/gesture/act intended to insult modesty of a woman"},
            {"section": "66A", "act": "IT Act 2000", "title": "Offensive messages through communication service"},
        ],
        "blackmail": [
            {"section": "384/385", "act": "IPC", "title": "Extortion and putting person in fear of injury"},
            {"section": "66E", "act": "IT Act 2000", "title": "Privacy Violation"},
            {"section": "67", "act": "IT Act 2000", "title": "Publishing obscene information"},
        ],
    }

    result["applicable_laws"] = law_mapping.get(result.get("threat_type", ""), [])
    result["filename"] = filename if filename else None
    result["analyzed_text_length"] = len(text_to_analyze)

    # Add action recommendations based on score
    score = result["score"]
    if score >= 90:
        result["recommended_actions"] = [
            "📸 Take screenshots of all evidence immediately",
            "🚨 File a complaint at cybercrime.gov.in",
            "📞 Call Women Helpline: 181 or Cyber Crime: 1930",
            "👥 Notify your trusted contacts",
            "🔒 Change passwords on all accounts",
        ]
    elif score >= 70:
        result["recommended_actions"] = [
            "📸 Screenshot and save the evidence",
            "📝 Document the date, time, and platform",
            "🚨 File an anonymous report below",
            "🔒 Review your privacy settings",
        ]
    elif score >= 40:
        result["recommended_actions"] = [
            "👁️ Monitor the situation closely",
            "📸 Save screenshots as precaution",
            "🔒 Tighten your privacy settings",
        ]
    else:
        result["recommended_actions"] = [
            "✅ No immediate action needed",
            "🔒 Keep your accounts secure",
        ]

    return jsonify(result), 200
