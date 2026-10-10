# ============================================
# RAKSHANA 24/7 — Legal Reference Routes
# ============================================
# Comprehensive Indian cyber law database

from flask import Blueprint, request, jsonify

legal_bp = Blueprint("legal", __name__)

# ─── Cyber Laws Database ──────────────────────────────────
CYBER_LAWS = [
    {
        "id": "stalking",
        "title": "Cyber Stalking",
        "category": "IPC / BNS",
        "sections": "Section 354D IPC — Stalking | Section 78 BNS (New Law)",
        "description": (
            "If someone repeatedly contacts you, monitors your internet or phone usage, "
            "watches or follows you using electronic means, or tracks your movements — "
            "this is a criminal offence."
        ),
        "punishment": "Up to 3 years imprisonment + fine (first offence). Up to 5 years for repeat offenders.",
        "keywords": ["stalking", "following", "monitoring", "spyware", "whatsapp", "instagram", "location", "tracking"],
        "tags": ["WhatsApp", "Instagram", "Location tracking", "Spyware"],
    },
    {
        "id": "morphed_images",
        "title": "Morphed / Manipulated Images & Deepfakes",
        "category": "IT ACT",
        "sections": "Section 66E IT Act — Privacy Violation | Section 67/67A — Obscene Content",
        "description": (
            "Publishing or sharing someone's morphed, manipulated, or AI-generated (deepfake) "
            "intimate images is a serious criminal offence. This includes creating, distributing, "
            "or even possessing such content."
        ),
        "punishment": "Section 66E: Up to 3 years + ₹2 lakh fine. Section 67A: Up to 7 years + ₹10 lakh fine.",
        "keywords": ["morphed", "images", "deepfakes", "manipulated", "photos", "revenge", "porn", "ai", "generated", "privacy"],
        "tags": ["Deepfakes", "Morphed photos", "Revenge porn", "AI-generated"],
    },
    {
        "id": "harassment",
        "title": "Online Harassment & Abuse",
        "category": "IPC / BNS",
        "sections": "Section 354A IPC — Sexual Harassment | Section 509 IPC — Insult to Modesty",
        "description": (
            "Sending unwanted sexual messages, lewd comments, threats, or abusive content "
            "online is punishable. This covers DMs, comments, emails, and any electronic communication."
        ),
        "punishment": "Up to 3 years imprisonment + fine.",
        "keywords": ["harassment", "abuse", "threatening", "messages", "online", "social", "media", "trolling"],
        "tags": ["Social media", "DMs", "Comments", "Emails"],
    },
    {
        "id": "blackmail",
        "title": "Cyber Blackmail & Sextortion",
        "category": "IPC / BNS",
        "sections": "Section 384/385 IPC — Extortion | Section 506 IPC — Criminal Intimidation",
        "description": (
            "Threatening to publish intimate images or private information unless demands "
            "(money, favours) are met is criminal extortion. The threat alone is punishable, "
            "even without execution."
        ),
        "punishment": "Up to 7 years imprisonment + fine for extortion. Up to 2 years for criminal intimidation.",
        "keywords": ["blackmail", "extortion", "sextortion", "threatening", "intimate", "images", "money", "demand"],
        "tags": ["Sextortion", "Blackmail", "Threats", "Intimate images"],
    },
    {
        "id": "doxxing",
        "title": "Doxxing — Leaking Personal Information",
        "category": "IT ACT",
        "sections": "Section 66C IT Act — Identity Theft | Section 72 IT Act — Breach of Confidentiality",
        "description": (
            "Publishing someone's personal information (address, phone, photos, workplace) "
            "online without consent — especially to harass or endanger — is a criminal "
            "offence under multiple sections."
        ),
        "punishment": "Up to 3 years imprisonment + ₹1 lakh fine.",
        "keywords": ["doxxing", "personal", "information", "sharing", "leaking", "address", "phone", "number"],
        "tags": ["Doxxing", "Personal info", "Identity theft", "Phone numbers"],
    },
    {
        "id": "identity_theft",
        "title": "Identity Theft & Impersonation",
        "category": "IT ACT",
        "sections": "Section 66C IT Act — Identity Theft | Section 66D — Cheating by Personation",
        "description": (
            "Using someone's identity, creating fake profiles, or impersonating someone "
            "online for fraudulent or malicious purposes is a criminal offence."
        ),
        "punishment": "Up to 3 years imprisonment + ₹1 lakh fine.",
        "keywords": ["identity", "theft", "impersonation", "fake", "profile", "account"],
        "tags": ["Fake profiles", "Impersonation", "Identity theft"],
    },
    {
        "id": "defamation",
        "title": "Online Defamation",
        "category": "IPC / BNS",
        "sections": "Section 499/500 IPC — Defamation | Section 356 BNS",
        "description": (
            "Publishing false statements about someone online with intent to damage their "
            "reputation is defamation. This includes social media posts, blog posts, "
            "and online reviews made with malicious intent."
        ),
        "punishment": "Up to 2 years imprisonment + fine.",
        "keywords": ["defamation", "false", "statements", "reputation", "social", "media"],
        "tags": ["Social media", "False claims", "Reputation damage"],
    },
    {
        "id": "voyeurism",
        "title": "Voyeurism & Non-consensual Recording",
        "category": "IPC / BNS",
        "sections": "Section 354C IPC — Voyeurism | Section 77 BNS",
        "description": (
            "Recording or capturing images of a woman engaged in a private act without "
            "her consent, or disseminating such recordings, is a criminal offence."
        ),
        "punishment": "First offence: Up to 3 years. Second offence: Up to 7 years.",
        "keywords": ["voyeurism", "recording", "camera", "hidden", "private", "consent"],
        "tags": ["Hidden cameras", "Non-consensual recording", "Privacy violation"],
    },
]

# ─── Constitutional Rights ────────────────────────────────
RIGHTS = [
    {
        "id": "privacy",
        "title": "Right to Privacy",
        "article": "Article 21",
        "description": (
            "Your personal data, images, conversations, and location are protected. "
            "No one can share them without your consent."
        ),
    },
    {
        "id": "dignity",
        "title": "Right to Dignity",
        "article": "Article 21",
        "description": (
            "Online harassment, morphing, stalking, and defamation are violations "
            "of this fundamental right."
        ),
    },
    {
        "id": "fir",
        "title": "Right to File FIR",
        "article": "CrPC Section 154",
        "description": (
            "Police MUST register your FIR. If they refuse, approach the Superintendent "
            "of Police or file through cybercrime.gov.in directly."
        ),
    },
    {
        "id": "zero_fir",
        "title": "Right to Zero FIR",
        "article": "CrPC (Amendment)",
        "description": (
            "You can file an FIR at ANY police station in India — not just your local one. "
            "This is called a Zero FIR. The police must accept it."
        ),
    },
    {
        "id": "free_legal_aid",
        "title": "Right to Free Legal Aid",
        "article": "Article 39A",
        "description": (
            "If you cannot afford a lawyer, the state must provide one. Contact your nearest "
            "District Legal Services Authority (DLSA)."
        ),
    },
]

# ─── Helplines ────────────────────────────────────────────
HELPLINES = [
    {"name": "National Cyber Crime Helpline", "number": "1930", "type": "phone"},
    {"name": "Women Helpline", "number": "181", "type": "phone"},
    {"name": "Cyber Crime Portal", "url": "https://cybercrime.gov.in", "type": "website"},
    {"name": "National Commission for Women", "number": "7827-170-170", "type": "phone"},
    {"name": "Emergency", "number": "112", "type": "phone"},
]


# ─── Endpoints ────────────────────────────────────────────

@legal_bp.route("/laws", methods=["GET"])
def get_laws():
    """Get all cyber laws. Supports search via `q` query param."""
    query = request.args.get("q", "").lower().strip()

    if query:
        results = [
            law for law in CYBER_LAWS
            if any(kw.startswith(query) or query in kw for kw in law["keywords"])
            or query in law["title"].lower()
            or query in law["description"].lower()
        ]
    else:
        results = CYBER_LAWS

    return jsonify({"laws": results, "total": len(results)}), 200


@legal_bp.route("/laws/<law_id>", methods=["GET"])
def get_law(law_id):
    """Get a specific law by ID."""
    law = next((l for l in CYBER_LAWS if l["id"] == law_id), None)
    if not law:
        return jsonify({"error": "Law not found"}), 404
    return jsonify({"law": law}), 200


@legal_bp.route("/rights", methods=["GET"])
def get_rights():
    """Get constitutional rights database."""
    return jsonify({"rights": RIGHTS}), 200


@legal_bp.route("/helplines", methods=["GET"])
def get_helplines():
    """Get emergency helplines and resources."""
    return jsonify({"helplines": HELPLINES}), 200


@legal_bp.route("/for-incident/<incident_type>", methods=["GET"])
def laws_for_incident(incident_type):
    """Get applicable laws for a specific incident type."""
    from app.services.legal_mapper import map_incident_to_laws

    laws = map_incident_to_laws(incident_type)
    return jsonify({
        "incident_type": incident_type,
        "applicable_laws": laws,
        "helplines": HELPLINES,
    }), 200
