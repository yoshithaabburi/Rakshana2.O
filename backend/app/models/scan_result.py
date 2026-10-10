# ============================================
# RAKSHANA 24/7 — Scan Result Model
# ============================================
# Stores raw results from each scanning sub-task
# (Telegram, paste site, image search)

import uuid
from datetime import datetime, timezone

from app import db


class ScanResult(db.Model):
    """Individual scan result from a monitoring sub-task."""

    __tablename__ = "scan_results"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)

    # Scan metadata
    scan_type = db.Column(db.String(30), nullable=False)  # telegram, paste_site, image_search
    scan_status = db.Column(db.String(20), default="completed")  # pending, running, completed, failed
    scan_duration_ms = db.Column(db.Integer, nullable=True)

    # Results
    matches_found = db.Column(db.Integer, default=0)
    raw_matches = db.Column(db.Text, nullable=True)  # JSON array of raw match data
    threat_score = db.Column(db.Integer, default=0)  # 0-100, computed by NLP scorer

    # Context
    source_channel = db.Column(db.String(255), nullable=True)
    context_snippet = db.Column(db.Text, nullable=True)  # Redacted snippet of surrounding text

    # Alert linkage
    alert_generated = db.Column(db.Boolean, default=False)
    alert_id = db.Column(db.String(36), nullable=True)

    # Timestamps
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        import json

        return {
            "id": self.id,
            "user_id": self.user_id,
            "scan_type": self.scan_type,
            "scan_status": self.scan_status,
            "scan_duration_ms": self.scan_duration_ms,
            "matches_found": self.matches_found,
            "threat_score": self.threat_score,
            "source_channel": self.source_channel,
            "context_snippet": self.context_snippet,
            "alert_generated": self.alert_generated,
            "alert_id": self.alert_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        return f"<ScanResult {self.id} type={self.scan_type} score={self.threat_score}>"
