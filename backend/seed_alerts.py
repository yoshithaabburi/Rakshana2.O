import json
import logging
from datetime import datetime, timedelta, timezone
from app import create_app, db
from app.models.user import User
from app.models.alert import Alert

app = create_app()

def seed_demo_alerts():
    with app.app_context():
        # Find the demo user
        demo_user = User.query.filter_by(email="demo@rakshana.in").first()
        if not demo_user:
            print("Demo user not found. Cannot seed alerts.")
            return

        # Clear existing unread alerts for demo user just in case
        print(f"Adding advanced priority alerts for {demo_user.email}...")

        base_time = datetime.now(timezone.utc)

        dummy_alerts = [
            {
                "threat_score": 95,
                "threat_type": "blackmail",
                "severity": "critical",
                "source_type": "telegram",
                "source_name": "Telegram: @leaked_x_bot",
                "source_url": "https://t.me/fake_bot",
                "title": "High-Risk Blackmail Indicator Detected",
                "description": "A message matching extortion and morphing threat patterns was detected targeting your profile.",
                "explanation": "CRITICAL: Detected 'morphed photos ready to share' and 'leaked' context indicating an active extortion attempt.",
                "matched_content": "Will teach her a lesson. [REDACTED]... photos ready to share...",
                "applicable_laws": json.dumps([{"section": "384 IPC", "act": "IPC", "title": "Extortion"}]),
                "is_read": False,
                "detected_at": base_time - timedelta(minutes=5)
            },
            {
                "threat_score": 75,
                "threat_type": "stalking",
                "severity": "alert",
                "source_type": "forum",
                "source_name": "Darkweb Forum X",
                "source_url": "",
                "title": "Location Tracking Discussion Found",
                "description": "Discussion indicating monitoring or stalking your movements was found online.",
                "explanation": "ALERT: Found consistent phrases matching physical location tracking and stalking.",
                "matched_content": "Tracking her location and monitoring movements near [REDACTED]",
                "applicable_laws": json.dumps([{"section": "354D", "act": "IPC", "title": "Stalking"}]),
                "is_read": False,
                "detected_at": base_time - timedelta(hours=2)
            },
            {
                "threat_score": 45,
                "threat_type": "doxxing",
                "severity": "watch",
                "source_type": "paste_site",
                "source_name": "Pastebin Fragment",
                "source_url": "https://pastebin.com/xxx",
                "title": "Potential Phone Number Leak",
                "description": "Your public information was seen aggregated in a suspicious paste file.",
                "explanation": "WATCH: Phone number found alongside name. Doesn't contain explicit threats but poses a privacy risk.",
                "matched_content": "[REDACTED] number leaked without consent",
                "applicable_laws": json.dumps([{"section": "72", "act": "IT Act", "title": "Breach of Confidentiality"}]),
                "is_read": True,
                "detected_at": base_time - timedelta(days=1)
            },
            {
                "threat_score": 15,
                "threat_type": "none",
                "severity": "safe",
                "source_type": "social_media",
                "source_name": "Public Twitter Mention",
                "source_url": "https://twitter.com/abc",
                "title": "Routine Profile Mention",
                "description": "You were mentioned in a public tweet. No abusive context detected.",
                "explanation": "SAFE: Mention detected, but NLP analysis shows no signs of harassment, threats, or abuse.",
                "matched_content": "Just watched the new video by [REDACTED].",
                "applicable_laws": "[]",
                "is_read": True,
                "detected_at": base_time - timedelta(days=3)
            }
        ]

        # Insert them
        for data in dummy_alerts:
            alert = Alert(
                user_id=demo_user.id,
                threat_score=data["threat_score"],
                threat_type=data["threat_type"],
                severity=data["severity"],
                source_type=data["source_type"],
                source_name=data["source_name"],
                source_url=data["source_url"],
                title=data["title"],
                description=data["description"],
                explanation=data["explanation"],
                matched_content=data["matched_content"],
                applicable_laws=data["applicable_laws"],
                is_read=data["is_read"],
                detected_at=data["detected_at"]
            )
            db.session.add(alert)

        db.session.commit()
        print("Successfully seeded alerts prioritizing UI display.")

if __name__ == "__main__":
    seed_demo_alerts()
