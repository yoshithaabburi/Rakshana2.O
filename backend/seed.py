# ============================================
# RAKSHANA 24/7 — Database Seeder
# ============================================
# Seeds the database with demo data for hackathon presentation.

import json
import random
from datetime import datetime, timedelta, timezone

import bcrypt

from app import create_app, db
from app.models.user import User
from app.models.alert import Alert
from app.models.scan_result import ScanResult
from app.models.report import Report
from app.utils.encryption import generate_anonymous_token
from app.services.legal_mapper import map_incident_to_laws


def seed_database():
    """Seed the database with demo data."""

    app = create_app("development")

    with app.app_context():
        print("🗑️  Clearing existing data...")
        Alert.query.delete()
        ScanResult.query.delete()
        Report.query.delete()
        User.query.delete()
        db.session.commit()

        print("👤 Creating demo users...")

        # ── Demo User 1: Main demo account ──
        demo_password = bcrypt.hashpw(
            "rakshana123".encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        user1 = User(
            email="demo@rakshana.in",
            password_hash=demo_password,
            display_name="Priya Sharma",
            language="en",
            scan_interval_hours=4,
            scan_enabled=True,
            is_active=True,
            is_verified=True,
            current_threat_score=25,
            last_scan_at=datetime.now(timezone.utc) - timedelta(minutes=2),
        )
        user1.phone_number = "+919876543210"
        user1.social_handles = "@priya_sharma,priya.sharma"

        db.session.add(user1)
        db.session.flush()

        # ── Demo User 2: Telugu user ──
        user2 = User(
            email="ravi@rakshana.in",
            password_hash=demo_password,
            display_name="రవి కుమార్",
            language="te",
            scan_interval_hours=4,
            scan_enabled=True,
            is_active=True,
            is_verified=True,
            current_threat_score=0,
            last_scan_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        user2.phone_number = "+919123456789"

        db.session.add(user2)
        db.session.flush()

        print("🔍 Creating demo scan results...")

        # ── Scan results for last 7 days ──
        scan_types = ["telegram", "paste_site"]
        for day in range(7):
            scan_time = datetime.now(timezone.utc) - timedelta(days=day)
            threat_score = random.choice([0, 0, 0, 10, 20, 35, 50, 65])

            for scan_type in scan_types:
                scan = ScanResult(
                    user_id=user1.id,
                    scan_type=scan_type,
                    scan_status="completed",
                    scan_duration_ms=random.randint(500, 3000),
                    matches_found=1 if threat_score > 30 else 0,
                    threat_score=threat_score + random.randint(-5, 5),
                    source_channel=f"{'Telegram channels' if scan_type == 'telegram' else 'Paste sites'}",
                    started_at=scan_time,
                    completed_at=scan_time + timedelta(seconds=random.randint(1, 5)),
                )
                db.session.add(scan)

        # Add today's scan — clean
        for scan_type in scan_types:
            scan = ScanResult(
                user_id=user1.id,
                scan_type=scan_type,
                scan_status="completed",
                scan_duration_ms=random.randint(500, 2000),
                matches_found=0,
                threat_score=0,
                source_channel=f"{'Telegram channels' if scan_type == 'telegram' else 'Paste sites'}",
                context_snippet="No matches found — digital presence is clear.",
                started_at=datetime.now(timezone.utc) - timedelta(minutes=2),
                completed_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            )
            db.session.add(scan)

        print("🚨 Creating demo alerts...")

        # ── Demo alerts ──
        alerts_data = [
            {
                "threat_score": 85,
                "threat_type": "doxxing",
                "source_type": "telegram",
                "source_name": "Telegram: @leaked_db_india",
                "title": "Personal Information Detected on Telegram",
                "description": "Your phone number was found in a public Telegram channel that shares leaked databases.",
                "explanation": "HIGH ALERT: Your phone number appeared in a channel known for sharing leaked personal data. This may indicate a data breach.",
                "matched_content": "phone number, leaked, database, personal details",
                "is_read": False,
                "days_ago": 2,
            },
            {
                "threat_score": 45,
                "threat_type": "stalking",
                "source_type": "paste_site",
                "source_name": "Pastebin: /AbCdEfGh",
                "title": "Social Handle Mentioned in Paste Site",
                "description": "Your social media handle was found mentioned alongside monitoring/tracking keywords.",
                "explanation": "CAUTION: Your handle was found in a paste alongside words indicating possible surveillance behaviour.",
                "matched_content": "tracking, monitoring, social handle",
                "is_read": True,
                "days_ago": 5,
            },
            {
                "threat_score": 20,
                "threat_type": "harassment",
                "source_type": "telegram",
                "source_name": "Telegram: @college_group_hyd",
                "title": "Name Mentioned in Group Discussion",
                "description": "Your name was mentioned in a college group discussion. Context appears non-threatening.",
                "explanation": "LOW RISK: Name mention detected but context appears to be casual conversation.",
                "matched_content": "name mention",
                "is_read": True,
                "days_ago": 6,
            },
        ]

        for alert_data in alerts_data:
            days_ago = alert_data.pop("days_ago")
            is_read = alert_data.pop("is_read")

            laws = map_incident_to_laws(alert_data["threat_type"])

            alert = Alert(
                user_id=user1.id,
                applicable_laws=json.dumps(laws),
                is_read=is_read,
                read_at=(
                    datetime.now(timezone.utc) - timedelta(days=days_ago - 1)
                    if is_read
                    else None
                ),
                detected_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
                notification_sent=True,
                notification_type="dashboard" if alert_data["threat_score"] < 70 else "sms",
                **alert_data,
            )
            alert.classify_severity()
            db.session.add(alert)

        print("📝 Creating demo reports...")

        # ── Demo anonymous reports ──
        reports_data = [
            {
                "incident_type": "morphed_image",
                "platform": "Instagram",
                "description": "Someone created a fake profile using manipulated images. The images appear to be AI-generated deepfakes.",
                "status": "submitted",
                "language": "en",
            },
            {
                "incident_type": "harassment",
                "platform": "WhatsApp",
                "description": "Receiving threatening messages from an unknown number. Multiple abusive messages sent late at night.",
                "status": "forwarded",
                "forwarded_to": "cybercrime.gov.in",
                "language": "en",
            },
        ]

        for report_data in reports_data:
            laws = map_incident_to_laws(report_data["incident_type"])
            forwarded_to = report_data.pop("forwarded_to", None)

            report = Report(
                anonymous_token=generate_anonymous_token(),
                applicable_laws=json.dumps(laws),
                forwarded_to=forwarded_to,
                forwarded_at=(
                    datetime.now(timezone.utc) - timedelta(hours=12)
                    if forwarded_to
                    else None
                ),
                **report_data,
            )
            db.session.add(report)

        db.session.commit()

        print("\n" + "=" * 50)
        print("  ✅ Database seeded successfully!")
        print("=" * 50)
        print(f"  👤 Users:    {User.query.count()}")
        print(f"  🔍 Scans:    {ScanResult.query.count()}")
        print(f"  🚨 Alerts:   {Alert.query.count()}")
        print(f"  📝 Reports:  {Report.query.count()}")
        print("=" * 50)
        print("\n  Demo credentials:")
        print("  📧 Email:    demo@rakshana.in")
        print("  🔑 Password: rakshana123")
        print("=" * 50 + "\n")


if __name__ == "__main__":
    seed_database()
