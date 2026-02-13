"""
Chats API: list chats, get chat with messages, create chat, delete chat.
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException

from app.auth_router import require_current_user_id
from app.chat_history import create_chat, delete_chat, get_chat_with_messages, list_chats, update_chat_title
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("")
async def create_new_chat(
    user_id: int = Depends(require_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    chat = await create_chat(db, user_id)
    return {
        "id": chat.id,
        "title": chat.title,
        "created_at": chat.created_at.isoformat() if chat.created_at else None,
        "updated_at": chat.updated_at.isoformat() if chat.updated_at else None,
    }


@router.get("")
async def list_user_chats(
    user_id: int = Depends(require_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    return await list_chats(db, user_id)


@router.get("/{chat_id}")
async def get_chat(
    chat_id: int,
    user_id: int = Depends(require_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    chat = await get_chat_with_messages(db, chat_id, user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.patch("/{chat_id}")
async def patch_chat_title(
    chat_id: int,
    body: dict,
    user_id: int = Depends(require_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    title = body.get("title")
    if not title or not isinstance(title, str):
        raise HTTPException(status_code=400, detail="title required")
    ok = await update_chat_title(db, chat_id, user_id, title)
    if not ok:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"ok": True}


@router.delete("/{chat_id}")
async def remove_chat(
    chat_id: int,
    user_id: int = Depends(require_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    ok = await delete_chat(db, chat_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"ok": True}
