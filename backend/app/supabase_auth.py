import logging
from typing import Optional, Tuple

import jwt as pyjwt
from jwt import PyJWKClient, PyJWKClientError

from app.config import settings

logger = logging.getLogger(__name__)


_jwk_client: Optional[PyJWKClient] = None


def _get_jwk_client() -> Optional[PyJWKClient]:
    """Return a cached PyJWKClient pointing at the Supabase JWKS endpoint."""
    global _jwk_client
    if _jwk_client is not None:
        return _jwk_client

    url = (settings.SUPABASE_URL or "").strip().rstrip("/")
    if not url:
        return None

    jwks_url = f"{url}/auth/v1/.well-known/jwks.json"
    _jwk_client = PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)
    logger.info("JWKS client initialised: %s", jwks_url)
    return _jwk_client

_JWKS_ALGORITHMS = [
    "HS256", "HS384", "HS512",
    "RS256", "RS384", "RS512",
    "ES256", "ES384", "ES512",
    "PS256", "PS384", "PS512",
    "EdDSA",
]

_HMAC_ALGORITHMS = ["HS256", "HS384", "HS512"]


def verify_supabase_token(token: str) -> Optional[Tuple[str, str]]:
    """
    Verify a Supabase-issued JWT and return ``(supabase_user_id, email)``.

    Returns ``None`` when verification fails or required settings are missing.
    """

    try:
        unverified_header = pyjwt.get_unverified_header(token)
        logger.info("JWT header: alg=%s kid=%s", unverified_header.get("alg"), unverified_header.get("kid"))
    except Exception as hdr_err:
        logger.warning("Could not decode JWT header: %s", hdr_err)

    client = _get_jwk_client()
    if client is not None:
        try:
            signing_key = client.get_signing_key_from_jwt(token)
            payload = pyjwt.decode(
                token,
                signing_key.key,
                algorithms=_JWKS_ALGORITHMS,
                options={"verify_aud": False},
            )
            logger.info("JWT verified via JWKS (alg from key).")
            return _extract_claims(payload)
        except PyJWKClientError as exc:
            logger.warning("JWKS key fetch failed: %s – falling back to HS256.", exc)
        except pyjwt.exceptions.PyJWTError as exc:
            logger.warning("JWKS verification failed: %s – falling back to HS256.", exc)

    secret = (settings.SUPABASE_JWT_SECRET or "").strip()
    if secret:
        try:
            payload = pyjwt.decode(
                token,
                secret,
                algorithms=_HMAC_ALGORITHMS,
                options={"verify_aud": False},
            )
            logger.info("JWT verified via legacy HS256 secret.")
            return _extract_claims(payload)
        except pyjwt.exceptions.PyJWTError as exc:
            logger.warning("HS256 verification failed: %s", exc)

    if not client and not secret:
        logger.warning(
            "Neither SUPABASE_URL nor SUPABASE_JWT_SECRET is configured; "
            "cannot verify any JWT."
        )

    return None


def _extract_claims(payload: dict) -> Optional[Tuple[str, str]]:
    """Pull ``sub`` (user id) and ``email`` from the decoded JWT payload."""
    sub = payload.get("sub")
    if not sub or not isinstance(sub, str):
        logger.warning("JWT valid but missing 'sub' claim.")
        return None
    email = ""
    raw_email = payload.get("email")
    if isinstance(raw_email, str):
        email = raw_email.strip()
    logger.info("JWT verified: sub=%s email=%s", sub, email or "(none)")
    return (sub, email or "supabase-user@local")
