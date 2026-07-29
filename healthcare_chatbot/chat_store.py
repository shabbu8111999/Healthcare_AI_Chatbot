"""
Small persistence layer just for the sidebar's chat list.

This is separate from the LangGraph checkpointer. The checkpointer
already stores the real conversation state (messages, retrieved
context, and so on) and survives restarts on its own. This file just
keeps a title and a couple of timestamps per thread id, so the sidebar
has something to show and sort by. Both live in the same sqlite file.
"""

import sqlite3
from datetime import datetime, timezone

from config import CHECKPOINT_DB_PATH


def _get_connection():
    conn = sqlite3.connect(CHECKPOINT_DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            thread_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


# one connection, reused for the life of the app, same pattern as the
# checkpointer's own connection in graph/workflow.py
_connection = _get_connection()


def make_title(message: str) -> str:
    # short title from the first message, same idea as how Claude
    # names a new chat from whatever you first ask it
    cleaned = " ".join(message.strip().split())
    if len(cleaned) <= 48:
        return cleaned
    return cleaned[:45].rstrip() + "..."


def create_session(thread_id: str, first_message: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    title = make_title(first_message)
    _connection.execute(
        "INSERT OR IGNORE INTO chat_sessions (thread_id, title, created_at, updated_at) "
        "VALUES (?, ?, ?, ?)",
        (thread_id, title, now, now),
    )
    _connection.commit()


def touch_session(thread_id: str) -> None:
    # bumps updated_at so the sidebar can show the most recently used
    # chat first, same behavior as Claude's own chat list
    now = datetime.now(timezone.utc).isoformat()
    _connection.execute(
        "UPDATE chat_sessions SET updated_at = ? WHERE thread_id = ?",
        (now, thread_id),
    )
    _connection.commit()


def rename_session(thread_id: str, new_title: str) -> None:
    _connection.execute(
        "UPDATE chat_sessions SET title = ? WHERE thread_id = ?",
        (new_title.strip()[:80], thread_id),
    )
    _connection.commit()


def delete_session(thread_id: str) -> None:
    _connection.execute("DELETE FROM chat_sessions WHERE thread_id = ?", (thread_id,))
    _connection.commit()


def list_sessions() -> list:
    cursor = _connection.execute(
        "SELECT thread_id, title, created_at, updated_at FROM chat_sessions "
        "ORDER BY updated_at DESC"
    )
    rows = cursor.fetchall()
    return [
        {"thread_id": r[0], "title": r[1], "created_at": r[2], "updated_at": r[3]}
        for r in rows
    ]


def session_exists(thread_id: str) -> bool:
    cursor = _connection.execute(
        "SELECT 1 FROM chat_sessions WHERE thread_id = ?", (thread_id,)
    )
    return cursor.fetchone() is not None