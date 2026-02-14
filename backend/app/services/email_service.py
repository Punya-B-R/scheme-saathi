"""
Email sending service using Resend for welcome and scheme alert emails.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

from app.config import settings
from app.utils.email_templates import (
    get_alert_email,
    get_subject_line,
    get_welcome_email,
)
from app.utils.subscriber_db import (
    get_all_active_subscribers,
    log_alert_sent,
    update_last_emailed,
)

logger = logging.getLogger(__name__)

try:
    import resend
    resend.api_key = settings.RESEND_API_KEY
    HAS_RESEND = bool(settings.RESEND_API_KEY and settings.RESEND_API_KEY != "your_resend_api_key_here")
except Exception as e:
    HAS_RESEND = False
    logger.warning("Resend not configured: %s", e)


def send_welcome_email(subscriber: Dict[str, Any]) -> bool:
    """Send welcome email to new subscriber."""
    if not HAS_RESEND:
        logger.warning("Resend not configured; skipping welcome email")
        return False
    try:
        html = get_welcome_email(
            name=subscriber.get("name") or "there",
            state=subscriber.get("state") or "",
            occupation=subscriber.get("occupation") or "",
        )
        resend.Emails.send({
            "from": f"{settings.ALERT_FROM_NAME} <{settings.ALERT_FROM_EMAIL}>",
            "to": subscriber["email"],
            "subject": "Welcome to Scheme Saathi Alerts! 🎉",
            "html": html,
        })
        logger.info("Welcome email sent to %s", subscriber["email"])
        return True
    except Exception as e:
        logger.exception("Failed to send welcome email: %s", e)
        return False


def send_alert_email(subscriber: Dict[str, Any], new_schemes: List[Dict[str, Any]]) -> bool:
    """Send scheme alert email to subscriber."""
    if not HAS_RESEND or not new_schemes:
        return False
    try:
        subject = get_subject_line(
            schemes=new_schemes,
            state=subscriber.get("state") or "",
            occupation=subscriber.get("occupation") or "",
            language=subscriber.get("language") or "en",
        )
        html = get_alert_email(
            subscriber=subscriber,
            new_schemes=new_schemes,
            language=subscriber.get("language") or "en",
        )
        resend.Emails.send({
            "from": f"{settings.ALERT_FROM_NAME} <{settings.ALERT_FROM_EMAIL}>",
            "to": subscriber["email"],
            "subject": subject,
            "html": html,
        })
        update_last_emailed(subscriber["email"])
        log_alert_sent(subscriber["email"], len(new_schemes), "ok")
        logger.info("Alert email sent to %s (%d schemes)", subscriber["email"], len(new_schemes))
        return True
    except Exception as e:
        logger.exception("Failed to send alert email: %s", e)
        log_alert_sent(subscriber["email"], len(new_schemes), "error")
        return False


def _scheme_matches_subscriber(scheme: Dict[str, Any], subscriber: Dict[str, Any]) -> bool:
    """Check if a scheme matches a subscriber's state/occupation."""
    sub_state = (subscriber.get("state") or "").strip().lower()
    sub_occ = (subscriber.get("occupation") or "").strip().lower()
    elig = scheme.get("eligibility_criteria") or {}
    if isinstance(elig, dict):
        scheme_state = (elig.get("state") or "").strip().lower()
    else:
        scheme_state = ""
    scheme_text = (scheme.get("scheme_name") or "") + " " + (scheme.get("brief_description") or "")
    scheme_text_lower = scheme_text.lower()
    scheme_all_india = not scheme_state or scheme_state in ("all india", "any", "nationwide", "")
    state_match = scheme_all_india or (sub_state and sub_state in scheme_state) or (scheme_state and scheme_state in sub_state)
    occ_match = True
    if sub_occ:
        occ_keywords = {"farmer": ["farmer", "kisan", "agricultur"], "student": ["student", "scholarship", "education"], "senior citizen": ["senior", "pension", "vridh"], "entrepreneur": ["entrepreneur", "business", "msme", "udyam"]}
        for k, words in occ_keywords.items():
            if k in sub_occ:
                occ_match = any(w in scheme_text_lower for w in words)
                break
    return state_match and occ_match


def send_alerts_to_matching_subscribers(new_schemes: List[Dict[str, Any]]) -> int:
    """Send alert emails to all active subscribers with matching schemes."""
    if not HAS_RESEND or not new_schemes:
        return 0
    subscribers = get_all_active_subscribers()
    sent = 0
    for sub in subscribers:
        matching = [s for s in new_schemes if _scheme_matches_subscriber(s, sub)]
        if matching:
            if send_alert_email(sub, matching):
                sent += 1
            time.sleep(0.1)
    logger.info("Sent alerts to %d subscribers", sent)
    return sent


def check_new_schemes_since_last_visit(subscriber: Dict[str, Any], all_schemes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get schemes that are 'new' since subscriber's last visit (uses last_updated or fallback 7 days)."""
    from datetime import datetime, timedelta

    last_visit = subscriber.get("last_visited_at")
    if last_visit:
        try:
            cutoff = datetime.fromisoformat(last_visit.replace("Z", "+00:00"))
        except Exception:
            cutoff = datetime.now() - timedelta(days=7)
    else:
        cutoff = datetime.now() - timedelta(days=7)

    cutoff_str = cutoff.isoformat()[:10]
    new_schemes = []
    for s in all_schemes:
        updated = s.get("last_updated") or s.get("scraped_at") or ""
        if updated and updated[:10] >= cutoff_str:
            if _scheme_matches_subscriber(s, subscriber):
                new_schemes.append(s)
    return new_schemes
