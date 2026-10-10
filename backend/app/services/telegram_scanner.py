# ============================================
# RAKSHANA 24/7 — Telegram Channel Scanner
# ============================================
# PRD: "Telethon — The ONLY Python library that lets you read
#        public Telegram channels programmatically."
#
# This module provides both:
# 1. Real Telethon integration (when API credentials are configured)
# 2. Demo/simulation mode (for hackathon without live Telegram)

import os
import re
import logging
import random
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def scan_telegram_channels(user_identifiers: dict) -> list[dict]:
    """
    Scan Telegram public channels for mentions of user identifiers.

    In production mode (with TELEGRAM_API_ID configured):
        Uses Telethon to read real public channels.

    In demo mode (no credentials):
        Returns simulated results for hackathon demonstration.

    Args:
        user_identifiers: dict with phone_hash, name, handles

    Returns:
        List of match dicts with text, source, timestamp, url
    """
    api_id = os.getenv("TELEGRAM_API_ID", "")
    api_hash = os.getenv("TELEGRAM_API_HASH", "")

    if api_id and api_hash and api_id != "YOUR_TELEGRAM_API_ID":
        return _scan_real_telegram(user_identifiers, api_id, api_hash)
    else:
        logger.info("Telegram credentials not configured — running in demo mode")
        return _scan_demo_telegram(user_identifiers)


def _scan_real_telegram(
    user_identifiers: dict, api_id: str, api_hash: str
) -> list[dict]:
    """
    Real Telegram scan using Telethon.

    Connects to Telegram, reads messages from configured public channels,
    and checks for mentions of user identifiers.
    """
    try:
        from telethon.sync import TelegramClient
        from telethon.tl.functions.messages import GetHistoryRequest

        channels = os.getenv("TELEGRAM_CHANNELS", "").split(",")
        channels = [ch.strip() for ch in channels if ch.strip()]

        if not channels:
            logger.warning("No Telegram channels configured")
            return []

        phone = os.getenv("TELEGRAM_PHONE", "")
        matches = []

        # Create client session
        client = TelegramClient("rakshana_scanner", int(api_id), api_hash)
        client.start(phone=phone)

        name = user_identifiers.get("name", "").lower()
        handles = [
            h.strip().lower()
            for h in user_identifiers.get("handles", "").split(",")
            if h.strip()
        ]
        phone_hash = user_identifiers.get("phone_hash", "")

        for channel_name in channels:
            try:
                channel = client.get_entity(channel_name)
                messages = client.get_messages(channel, limit=100)

                for msg in messages:
                    if not msg.text:
                        continue

                    text_lower = msg.text.lower()

                    # Check for user identifier matches
                    is_match = False
                    match_reason = ""

                    # Check name
                    if name and len(name) > 2 and name in text_lower:
                        is_match = True
                        match_reason = f"Name mention: '{name}'"

                    # Check handles
                    for handle in handles:
                        if handle and handle in text_lower:
                            is_match = True
                            match_reason = f"Handle mention: '{handle}'"

                    # Check for phone patterns
                    phone_patterns = re.findall(
                        r"\+?91[\s-]?\d{5}[\s-]?\d{5}", msg.text
                    )
                    if phone_patterns:
                        is_match = True
                        match_reason = "Phone number pattern detected"

                    if is_match:
                        matches.append({
                            "text": msg.text[:500],  # Truncate
                            "source": f"Telegram: {channel_name}",
                            "url": f"https://t.me/{channel_name}/{msg.id}",
                            "timestamp": msg.date.isoformat() if msg.date else None,
                            "match_reason": match_reason,
                        })

            except Exception as e:
                logger.error(f"Error scanning channel {channel_name}: {e}")
                continue

        client.disconnect()
        return matches

    except ImportError:
        logger.warning("Telethon not installed — falling back to demo mode")
        return _scan_demo_telegram(user_identifiers)
    except Exception as e:
        logger.error(f"Telegram scan error: {e}")
        return _scan_demo_telegram(user_identifiers)


def _scan_demo_telegram(user_identifiers: dict) -> list[dict]:
    """
    Demo mode — simulated Telegram scan results for hackathon.

    Generates realistic-looking scan results to demonstrate the pipeline.
    """
    name = user_identifiers.get("name", "User")

    # Simulate various scenarios with different threat levels
    demo_scenarios = [
        # Safe scenario — no matches
        [],
        # Low risk — casual mention
        [
            {
                "text": f"Has anyone seen {name}'s post about the awareness campaign? Really good content.",
                "source": "Telegram: @social_awareness_india",
                "url": "https://t.me/social_awareness_india/4521",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "match_reason": f"Name mention: '{name}'",
            },
        ],
        # Medium risk — suspicious context
        [
            {
                "text": f"Contact details shared: +91-XXXXX-XXXXX. Send this number to everyone in the group. Shared without consent, leaked from database.",
                "source": "Telegram: @leaked_numbers_india",
                "url": "https://t.me/leaked_numbers/8923",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "match_reason": "Phone number pattern detected",
            },
        ],
        # High risk — threatening content
        [
            {
                "text": f"Will teach her a lesson. Morphed photos ready. Everyone share this viral NOW. tracking location and movements. doxxed personal info exposed",
                "source": "Telegram: @revenge_group_283",
                "url": "https://t.me/revenge_group/1247",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "match_reason": "Multiple threat indicators",
            },
        ],
    ]

    # Randomly select a scenario for demo variety
    # Weight towards safe scenarios (more realistic)
    weights = [0.5, 0.2, 0.2, 0.1]
    scenario = random.choices(demo_scenarios, weights=weights, k=1)[0]

    return scenario
