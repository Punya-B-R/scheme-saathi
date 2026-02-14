"""
SQLite database for email subscription and scheme alert subscribers.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = BACKEND_ROOT / "subscribers.db"

logger = logging.getLogger(__name__)


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create subscribers and alerts_log tables if they do not exist."""
    conn = _get_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                state TEXT,
                occupation TEXT,
                caste_category TEXT,
                income_level TEXT,
                language TEXT DEFAULT 'en',
                subscribed_at TEXT NOT NULL,
                last_emailed_at TEXT,
                last_visited_at TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                schemes_count INTEGER,
                sent_at TEXT NOT NULL,
                status TEXT
            )
        """)
        conn.commit()
        logger.info("Subscriber database initialized at %s", DB_PATH)
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return dict(row) if row else {}


def add_subscriber(
    email: str,
    name: str = "",
    state: str = "",
    occupation: str = "",
    language: str = "en",
    user_context: Optional[Dict[str, Any]] = None,
) -> bool:
    """Add or update a subscriber. Returns True if new, False if already existed."""
    ctx = user_context or {}
    state = state or ctx.get("state", "")
    occupation = occupation or ctx.get("occupation", "")
    name = name or ctx.get("name", "")
    caste = ctx.get("caste_category", "") or ctx.get("caste", "")
    income = ctx.get("income_level", "") or ctx.get("income", "")
    lang = language or ctx.get("language", "en")

    now = datetime.now().isoformat()
    conn = _get_conn()
    try:
        cur = conn.execute(
            "SELECT id FROM subscribers WHERE email = ?",
            (email.lower().strip(),),
        )
        existing = cur.fetchone()
        if existing:
            conn.execute(
                """
                UPDATE subscribers SET
                    name = COALESCE(NULLIF(?, ''), name),
                    state = COALESCE(NULLIF(?, ''), state),
                    occupation = COALESCE(NULLIF(?, ''), occupation),
                    caste_category = COALESCE(NULLIF(?, ''), caste_category),
                    income_level = COALESCE(NULLIF(?, ''), income_level),
                    language = ?,
                    last_visited_at = ?,
                    is_active = 1
                WHERE email = ?
                """,
                (name, state, occupation, caste, income, lang, now, email.lower().strip()),
            )
            conn.commit()
            return False
        conn.execute(
            """
            INSERT INTO subscribers (
                email, name, state, occupation, caste_category, income_level,
                language, subscribed_at, last_visited_at, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                email.lower().strip(),
                name,
                state,
                occupation,
                caste,
                income,
                lang,
                now,
                now,
            ),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def get_subscriber(email: str) -> Optional[Dict[str, Any]]:
    """Get subscriber by email."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            "SELECT * FROM subscribers WHERE email = ?",
            (email.lower().strip(),),
        )
        row = cur.fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def get_all_active_subscribers() -> List[Dict[str, Any]]:
    """Get all active subscribers."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            "SELECT * FROM subscribers WHERE is_active = 1 ORDER BY subscribed_at DESC"
        )
        return [_row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_subscribers_by_context(
    state: Optional[str] = None,
    occupation: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get active subscribers matching state/occupation filters (empty means any)."""
    conn = _get_conn()
    try:
        sql = "SELECT * FROM subscribers WHERE is_active = 1"
        params: List[Any] = []
        if state:
            sql += " AND (state = ? OR state IS NULL OR state = '')"
            params.append(state)
        if occupation:
            sql += " AND (occupation = ? OR occupation IS NULL OR occupation = '')"
            params.append(occupation)
        sql += " ORDER BY subscribed_at DESC"
        cur = conn.execute(sql, params)
        return [_row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def update_last_emailed(email: str) -> None:
    """Update last_emailed_at for a subscriber."""
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE subscribers SET last_emailed_at = ? WHERE email = ?",
            (datetime.now().isoformat(), email.lower().strip()),
        )
        conn.commit()
    finally:
        conn.close()


def update_last_visited(email: str) -> None:
    """Update last_visited_at for a subscriber."""
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE subscribers SET last_visited_at = ? WHERE email = ?",
            (datetime.now().isoformat(), email.lower().strip()),
        )
        conn.commit()
    finally:
        conn.close()


def unsubscribe(email: str) -> None:
    """Mark subscriber as inactive."""
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE subscribers SET is_active = 0 WHERE email = ?",
            (email.lower().strip(),),
        )
        conn.commit()
    finally:
        conn.close()


def log_alert_sent(email: str, schemes_count: int, status: str = "ok") -> None:
    """Log that an alert email was sent."""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO alerts_log (email, schemes_count, sent_at, status) VALUES (?, ?, ?, ?)",
            (email.lower().strip(), schemes_count, datetime.now().isoformat(), status),
        )
        conn.commit()
    finally:
        conn.close()


init_db()
