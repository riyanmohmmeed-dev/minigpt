"""Optional SQLite storage for chat history."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .config import settings


class ChatStorage:
    """SQLite-backed chat session and message storage."""

    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        with self._conn() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
                """
            )

    def create_session(self, session_id: str) -> None:
        with self._conn() as c:
            c.execute("INSERT OR IGNORE INTO sessions (id) VALUES (?)", (session_id,))

    def append_message(self, session_id: str, role: str, content: str) -> None:
        with self._conn() as c:
            c.execute("INSERT OR IGNORE INTO sessions (id) VALUES (?)", (session_id,))
            c.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content),
            )

    def get_messages(self, session_id: str) -> list[dict[str, Any]]:
        with self._conn() as c:
            c.execute(
                "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id",
                (session_id,),
            )
            rows = c.fetchall()
        return [{"role": r, "content": c} for r, c in rows]


_storage: ChatStorage | None = None


def get_storage() -> ChatStorage | None:
    """Return ChatStorage if enabled, else None."""
    global _storage
    if not settings.enable_storage:
        return None
    if _storage is None:
        _storage = ChatStorage(settings.storage_path)
    return _storage
