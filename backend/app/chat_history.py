"""
Chat history in DB: get messages for a chat, append messages, create/list chats.
"""

from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db_models import Chat, Message, User  # pyright: ignore[reportMissingImports]


async def get_chat_history(db: AsyncSession, chat_id: int, user_id: int) -> List[Dict[str, Any]]:
    """Return list of {role, content} for the chat if it belongs to the user."""
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id).options(selectinload(Chat.messages))
    )
    chat = result.scalar_one_or_none()
    if not chat:
        return []
    return [{"role": m.role, "content": m.content} for m in chat.messages]


async def append_message(db: AsyncSession, chat_id: int, user_id: int, role: str, content: str) -> bool:
    """Append a message to the chat if it belongs to the user. Returns True on success."""
    result = await db.execute(select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id))
    chat = result.scalar_one_or_none()
    if not chat:
        return False
    msg = Message(chat_id=chat_id, role=role, content=content)
    db.add(msg)
    await db.flush()
    return True


def title_from_first_message(first_message: str | None) -> str:
    """Derive a short title from the first user message (max 50 chars)."""
    if not first_message or not (first_message := first_message.strip()):
        return "New Conversation"
    if len(first_message) <= 50:
        return first_message
    return first_message[:47].rstrip() + "..."


async def create_chat(db: AsyncSession, user_id: int, title: str = "New Conversation") -> Chat | None:
    """Create a new chat for the user."""
    chat = Chat(user_id=user_id, title=title[:512] if title else "New Conversation")
    db.add(chat)
    await db.flush()
    await db.refresh(chat)
    return chat


async def get_or_create_chat_for_message(
    db: AsyncSession,
    user_id: int,
    chat_id: int | None,
    first_message: str | None = None,
) -> tuple[Chat | None, List[Dict[str, Any]]]:
    """
    If chat_id given and valid, return (chat, history). Else create new chat and return (chat, []).
    When creating a new chat, use first_message to set a relevant title (truncated to 50 chars).
    """
    if chat_id:
        result = await db.execute(
            select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id).options(selectinload(Chat.messages))
        )
        chat = result.scalar_one_or_none()
        if chat:
            history = [{"role": m.role, "content": m.content} for m in chat.messages]
            return chat, history
    title = title_from_first_message(first_message)
    chat = await create_chat(db, user_id, title=title)
    return chat, []


async def list_chats(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
    """List chats for the user (id, title, created_at, updated_at)."""
    result = await db.execute(select(Chat).where(Chat.user_id == user_id).order_by(Chat.updated_at.desc()))
    chats = result.scalars().all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in chats
    ]


async def get_chat_with_messages(db: AsyncSession, chat_id: int, user_id: int) -> Dict[str, Any] | None:
    """Get one chat with messages if it belongs to the user."""
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id).options(selectinload(Chat.messages))
    )
    chat = result.scalar_one_or_none()
    if not chat:
        return None
    return {
        "id": chat.id,
        "title": chat.title,
        "created_at": chat.created_at.isoformat() if chat.created_at else None,
        "updated_at": chat.updated_at.isoformat() if chat.updated_at else None,
        "messages": [
            {"role": m.role, "content": m.content, "timestamp": m.created_at.isoformat() if m.created_at else None}
            for m in chat.messages
        ],
    }


async def update_chat_title(db: AsyncSession, chat_id: int, user_id: int, title: str) -> bool:
    result = await db.execute(select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id))
    chat = result.scalar_one_or_none()
    if not chat:
        return False
    chat.title = title[:512]
    await db.flush()
    return True


async def delete_chat(db: AsyncSession, chat_id: int, user_id: int) -> bool:
    result = await db.execute(select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id))
    chat = result.scalar_one_or_none()
    if not chat:
        return False
    await db.delete(chat)
    await db.flush()
    return True
