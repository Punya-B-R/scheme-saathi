import logging

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.db_models import User  # pyright: ignore[reportMissingImports]
from app.supabase_auth import verify_supabase_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_auth_header(authorization: str | None = Header(None, alias="Authorization")) -> str | None:
    return authorization


class UserResponse(BaseModel):
    id: int
    email: str


async def get_current_user_id(
    authorization: str | None = Depends(_get_auth_header),
    db: AsyncSession = Depends(get_db),
) -> int | None:
    """
    Verify Supabase JWT from Authorization: Bearer <token>, get or create User by supabase_user_id,
    return internal user id. Returns None if no/invalid token.
    """
    if not authorization or not authorization.startswith("Bearer "):
        logger.debug("No Authorization header; treating as anonymous.")
        return None
    token = authorization[7:].strip()
    parsed = verify_supabase_token(token)
    if not parsed:
        logger.warning("JWT verification failed; treating as anonymous.")
        return None
    sub, email = parsed
    try:
        result = await db.execute(select(User).where(User.supabase_user_id == sub))
        user = result.scalar_one_or_none()
        if user:
            logger.info("Found existing user id=%s for sub=%s", user.id, sub)
            return user.id
        user = User(
            email=email or f"supabase-{sub}@local",
            password_hash=None,
            supabase_user_id=sub,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        logger.info("Created new user id=%s for sub=%s email=%s", user.id, sub, email)
        return user.id
    except Exception as exc:
        logger.exception("DB error in get_current_user_id: %s", exc)
        return None


async def require_current_user_id(
    user_id: int | None = Depends(get_current_user_id),
) -> int:
    """Return user id from Bearer token or raise 401."""
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


@router.get("/me", response_model=UserResponse)
async def me(user_id: int = Depends(require_current_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return UserResponse(id=user.id, email=user.email)
