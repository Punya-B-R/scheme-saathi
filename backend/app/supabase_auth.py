
"""
Verify Supabase-issued JWTs and extract user identity (sub, email).
Backend uses this to trust the frontend's Bearer token and map to internal user id.
"""

from typing import Optional, Tuple

from jose import JWTError, jwt

from app.config import settings


def verify_supabase_token(token: str) -> Optional[Tuple[str, str]]:
    """
    Verify JWT signed by Supabase and return (sub, email).
    sub is the Supabase user UUID. Returns None if invalid or SUPABASE_JWT_SECRET not set.
    """
    secret = (settings.SUPABASE_JWT_SECRET or "").strip()
    if not secret:
        return None
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        sub = payload.get("sub")
        if not sub or not isinstance(sub, str):
            return None
        email = (payload.get("email") or "").strip() if isinstance(payload.get("email"), str) else ""
        return (sub, email or "supabase-user@local")
    except JWTError:
        return None
