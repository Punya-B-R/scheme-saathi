"""
HTML email templates for welcome and scheme alert emails.
"""

from __future__ import annotations

from typing import Any, Dict, List

# App URL for links (frontend) - set via FRONTEND_URL env or config
def _get_app_url() -> str:
    try:
        from app.config import settings
        return (settings.FRONTEND_URL or "https://schemesaathi.in").rstrip("/")
    except Exception:
        return "https://schemesaathi.in"


APP_URL = _get_app_url()


def get_welcome_email(name: str, state: str, occupation: str) -> str:
    """Returns HTML for welcome email."""
    display_name = name or "there"
    profile_parts = []
    if state:
        profile_parts.append(f"State: {state}")
    if occupation:
        profile_parts.append(f"Occupation: {occupation}")
    profile_html = "<br>".join(profile_parts) if profile_parts else "We'll learn from your chats."

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0; font-family: Arial, sans-serif; background:#f1f5f9;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px; margin:0 auto; background:#fff;">
<tr>
<td style="background: linear-gradient(135deg, #2563eb, #7c3aed); padding:24px; text-align:center;">
<span style="color:#fff; font-size:24px; font-weight:bold;">Scheme Saathi</span>
</td>
</tr>
<tr>
<td style="padding:32px 24px;">
<h2 style="color:#1e293b; font-size:20px; margin:0 0 16px;">Hi {display_name}!</h2>
<p style="color:#64748b; line-height:1.6; margin:0 0 16px;">
You're now subscribed to scheme alerts.
</p>
<div style="background:#f8fafc; border-radius:8px; padding:16px; border-left:4px solid #2563eb; margin:16px 0;">
<p style="color:#475569; margin:0; font-size:14px;">{profile_html}</p>
</div>
<p style="color:#64748b; line-height:1.6; margin:16px 0;">
We'll notify you when new government schemes are added that match your profile.
</p>
<p style="margin:24px 0;">
<a href="{APP_URL}/chat" style="background:#2563eb; color:#fff; padding:12px 24px; border-radius:8px; text-decoration:none; display:inline-block; font-weight:600;">Discover Schemes Now</a>
</p>
<p style="color:#94a3b8; font-size:12px; margin-top:32px;">
<a href="{APP_URL}/chat" style="color:#2563eb;">Unsubscribe</a> · Powered by Scheme Saathi
</p>
</td>
</tr>
</table>
</body>
</html>
"""


def get_alert_email(
    subscriber: Dict[str, Any],
    new_schemes: List[Dict[str, Any]],
    language: str = "en",
) -> str:
    """Returns HTML for new schemes alert email."""
    name = subscriber.get("name") or "there"
    schemes_html = ""
    for s in new_schemes[:5]:
        scheme_name = s.get("scheme_name") or s.get("name") or "Government Scheme"
        category = s.get("category") or "Government"
        benefits = s.get("benefits") or {}
        if isinstance(benefits, dict):
            financial = benefits.get("financial_benefit") or benefits.get("summary", "")[:80]
        else:
            financial = str(benefits)[:80]
        elig = s.get("eligibility_criteria") or {}
        if isinstance(elig, dict):
            raw = elig.get("raw_eligibility_text", "")[:100]
        else:
            raw = str(elig)[:100]
        state_label = (elig.get("state") if isinstance(elig, dict) else None) or "All India"
        if not financial:
            financial = "Check eligibility for benefits"
        schemes_html += f"""
<div style="border:1px solid #e2e8f0; border-radius:8px; padding:16px; margin-bottom:12px;">
<div style="display:flex; justify-content:space-between; align-items:flex-start;">
<strong style="color:#1e293b; font-size:15px;">{scheme_name}</strong>
<span style="background:#dbeafe; color:#1d4ed8; padding:2px 8px; border-radius:100px; font-size:12px;">{category}</span>
</div>
<p style="color:#16a34a; font-weight:600; margin:8px 0 4px;">{financial}</p>
<p style="color:#64748b; font-size:13px; margin:0 0 12px;">{raw}</p>
<a href="{APP_URL}/chat" style="color:#2563eb; font-size:13px;">Chat to learn more →</a>
</div>
"""

    count = len(new_schemes)
    badge = f'<span style="background:#dcfce7; color:#16a34a; padding:4px 12px; border-radius:100px; font-size:14px; font-weight:600;">{count} New Scheme{"s" if count != 1 else ""}</span>'

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0; font-family: Arial, sans-serif; background:#f1f5f9;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px; margin:0 auto; background:#fff;">
<tr>
<td style="background: linear-gradient(135deg, #2563eb, #7c3aed); padding:24px; text-align:center;">
<span style="color:#fff; font-size:24px; font-weight:bold;">Scheme Saathi</span>
</td>
</tr>
<tr>
<td style="padding:32px 24px;">
<h2 style="color:#1e293b; font-size:20px; margin:0 0 8px;">Hi {name}! We found new schemes for you.</h2>
<p style="color:#64748b; line-height:1.6; margin:0 0 16px;">{badge}</p>
{schemes_html}
<p style="color:#94a3b8; font-size:12px; margin-top:32px;">
You're receiving this because you subscribed to Scheme Saathi alerts.
</p>
<p><a href="{APP_URL}/chat" style="color:#2563eb; font-size:13px;">Unsubscribe</a></p>
</td>
</tr>
</table>
</body>
</html>
"""


def get_subject_line(
    schemes: List[Dict[str, Any]],
    state: str = "",
    occupation: str = "",
    language: str = "en",
) -> str:
    """Returns email subject line."""
    count = len(schemes)
    if count == 0:
        return "New government schemes – Scheme Saathi"
    emoji = "🌾" if occupation and "farmer" in str(occupation).lower() else "📢"
    if occupation and state:
        return f"{count} new scheme{'s' if count != 1 else ''} for {occupation}s in {state} {emoji}"
    if state:
        return f"New government schemes available in {state} {emoji}"
    if occupation:
        return f"{count} new {occupation} schemes you qualify for 🎓"
    return f"{count} new government scheme{'s' if count != 1 else ''} – Scheme Saathi 📢"
