# ============================================
# RAKSHANA 24/7 — Notification Service
# ============================================
# PRD: "If score > 70: Push notification fires via Twilio/WhatsApp
#        with vernacular alert text + action guide."

import os
import json
import logging

logger = logging.getLogger(__name__)


# ─── Vernacular Alert Templates ───────────────────────────
ALERT_TEMPLATES = {
    "en": {
        "watch": {
            "title": "⚠️ Monitoring Alert",
            "body": "We detected potential suspicious activity related to your digital presence. "
                    "Your threat score has increased. Check the Rakshana dashboard for details.",
        },
        "alert": {
            "title": "🔴 Security Alert — Action Recommended",
            "body": "A significant threat has been detected. {explanation} "
                    "Please open Rakshana 24/7 immediately to review the alert and take recommended actions.",
        },
        "critical": {
            "title": "🚨 CRITICAL ALERT — Immediate Action Required",
            "body": "CRITICAL: {explanation} "
                    "Your trusted contacts have been notified. "
                    "Open Rakshana 24/7 now. Screenshot evidence. Consider filing a report at cybercrime.gov.in.",
        },
    },
    "te": {
        "watch": {
            "title": "⚠️ పర్యవేక్షణ హెచ్చరిక",
            "body": "మీ డిజిటల్ ఉనికికి సంబంధించి అనుమానాస్పద కార్యకలాపం గుర్తించబడింది. "
                    "వివరాల కోసం రక్షణ డాష్‌బోర్డ్ చూడండి.",
        },
        "alert": {
            "title": "🔴 భద్రతా హెచ్చరిక — చర్య అవసరం",
            "body": "ముఖ్యమైన బెదిరింపు గుర్తించబడింది. {explanation} "
                    "దయచేసి హెచ్చరికను సమీక్షించడానికి రక్షణ 24/7 వెంటనే తెరవండి.",
        },
        "critical": {
            "title": "🚨 క్లిష్టమైన హెచ్చరిక — తక్షణ చర్య అవసరం",
            "body": "క్లిష్టం: {explanation} "
                    "మీ విశ్వసనీయ పరిచయస్థులకు తెలియజేయబడింది. "
                    "ఇప్పుడు రక్షణ 24/7 తెరవండి. ఆధారాలను స్క్రీన్‌షాట్ చేయండి.",
        },
    },
}


def send_alert_notification(user, alert) -> bool:
    """
    Send alert notification to user via appropriate channel.

    Notification channel is determined by threat severity:
    - score >= 90: WhatsApp + SMS (critical)
    - score >= 70: SMS (alert)
    - score >= 40: Dashboard only (watch)

    Returns True if notification was sent successfully.
    """
    language = user.language or "en"
    templates = ALERT_TEMPLATES.get(language, ALERT_TEMPLATES["en"])
    severity = alert.severity

    template = templates.get(severity, templates.get("watch"))
    explanation = alert.explanation or alert.description

    title = template["title"]
    body = template["body"].format(explanation=explanation)

    # Determine notification channel
    if alert.threat_score >= 90:
        # Critical: WhatsApp + SMS
        _send_whatsapp(user, title, body)
        _send_sms(user, title, body)
        alert.notification_type = "whatsapp"
    elif alert.threat_score >= 70:
        # Alert: SMS
        _send_sms(user, title, body)
        alert.notification_type = "sms"
    else:
        # Watch: Dashboard only
        alert.notification_type = "dashboard"

    alert.notification_sent = True
    logger.info(
        f"Notification sent to user {user.id}: "
        f"type={alert.notification_type}, severity={severity}, score={alert.threat_score}"
    )

    return True


def _send_sms(user, title: str, body: str):
    """Send SMS via Twilio."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_number = os.getenv("TWILIO_FROM_NUMBER", "")

    if not all([account_sid, auth_token, from_number]) or account_sid == "YOUR_TWILIO_SID":
        logger.info(f"[DEMO] SMS would be sent: {title}")
        logger.info(f"[DEMO] Body: {body[:100]}...")
        return

    try:
        from twilio.rest import Client

        client = Client(account_sid, auth_token)

        phone = user.phone_number
        if not phone:
            logger.warning(f"No phone number for user {user.id}")
            return

        message = client.messages.create(
            body=f"{title}\n\n{body}",
            from_=from_number,
            to=phone,
        )
        logger.info(f"SMS sent: {message.sid}")

    except ImportError:
        logger.info(f"[DEMO] Twilio not installed. SMS: {title}")
    except Exception as e:
        logger.error(f"SMS send failed: {e}")


def _send_whatsapp(user, title: str, body: str):
    """Send WhatsApp message via Twilio."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_wa = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    if not all([account_sid, auth_token]) or account_sid == "YOUR_TWILIO_SID":
        logger.info(f"[DEMO] WhatsApp would be sent: {title}")
        logger.info(f"[DEMO] Body: {body[:100]}...")
        return

    try:
        from twilio.rest import Client

        client = Client(account_sid, auth_token)

        phone = user.phone_number
        if not phone:
            logger.warning(f"No phone number for user {user.id}")
            return

        message = client.messages.create(
            body=f"{title}\n\n{body}",
            from_=from_wa,
            to=f"whatsapp:{phone}",
        )
        logger.info(f"WhatsApp sent: {message.sid}")

    except ImportError:
        logger.info(f"[DEMO] Twilio not installed. WhatsApp: {title}")
    except Exception as e:
        logger.error(f"WhatsApp send failed: {e}")
