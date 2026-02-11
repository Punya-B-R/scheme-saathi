"""
In-memory session store for WhatsApp (and other) conversations.
Key: user identifier (e.g. WhatsApp wa_id). Value: list of {role, content}.
For production, replace with Redis or a database.
"""

import logging
from collections import OrderedDict
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Max messages to keep per user (user + assistant pairs; last N messages total)
MAX_HISTORY_PER_USER = 20


class SessionStore:
    """In-memory conversation history per user. Thread-safe for single-process use."""

    def __init__(self, max_history: int = MAX_HISTORY_PER_USER):
        self._store: Dict[str, List[Dict[str, Any]]] = {}
        self._max_history = max_history

    def get_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Return list of {role, content} for the user. Latest last."""
        return list(self._store.get(user_id, []))

    def append(self, user_id: str, role: str, content: str) -> None:
        """Append one message and trim to max history."""
        if user_id not in self._store:
            self._store[user_id] = []
        self._store[user_id].append({"role": role, "content": content})
        # Keep last N messages
        if len(self._store[user_id]) > self._max_history:
            self._store[user_id] = self._store[user_id][-self._max_history :]

    def clear(self, user_id: str) -> None:
        """Clear history for one user."""
        self._store.pop(user_id, None)


# Global singleton for WhatsApp (and future channels)
session_store = SessionStore()
