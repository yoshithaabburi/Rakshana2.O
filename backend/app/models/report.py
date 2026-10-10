# ============================================
# RAKSHANA 24/7 — Anonymous Report Model
# ============================================
# PRD: "Reports submitted via anonymising proxy. No IP logged server-side."

import uuid
from datetime import datetime, timezone

from app import db


class Report(db.Model):
    """Anonymous cyber crime report — no user linkage, no IP logging."""

    __tablename__ = "reports"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Report content
    incident_type = db.Column(db.String(50), nullable=False)
    # stalking, morphed_image, harassment, blackmail, doxxing, other
    platform = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=False)
    evidence_urls = db.Column(db.Text, nullable=True)  # JSON array

    # Legal mapping
    applicable_laws = db.Column(db.Text, nullable=True)  # JSON

    # Status tracking (for the reporter via anonymous token)
    anonymous_token = db.Column(db.String(64), unique=True, nullable=False)
    status = db.Column(db.String(30), default="submitted")
    # submitted, under_review, forwarded, resolved
    status_message = db.Column(db.Text, nullable=True)

    # Forwarding
    forwarded_to = db.Column(db.String(100), nullable=True)  # cybercrime.gov.in
    forwarded_at = db.Column(db.DateTime, nullable=True)

    # Language
    language = db.Column(db.String(10), default="en")

    # Timestamps — NO user_id, NO IP address
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        import json

        return {
            "id": self.id,
            "incident_type": self.incident_type,
            "platform": self.platform,
            "description": self.description,
            "evidence_urls": json.loads(self.evidence_urls) if self.evidence_urls else [],
            "applicable_laws": json.loads(self.applicable_laws) if self.applicable_laws else [],
            "anonymous_token": self.anonymous_token,
            "status": self.status,
            "status_message": self.status_message,
            "forwarded_to": self.forwarded_to,
            "forwarded_at": self.forwarded_at.isoformat() if self.forwarded_at else None,
            "language": self.language,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Report {self.id} type={self.incident_type} status={self.status}>"
