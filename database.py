import sqlite3
from datetime import datetime
from pathlib import Path

from config import DATABASE_PATH, MAX_HISTORY


def _conn() -> sqlite3.Connection:
    path = Path(DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(path))


def init_db() -> None:
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processed_messages (
                id_message TEXT PRIMARY KEY,
                processed_at TEXT NOT NULL
            )
        """)
        conn.commit()


def is_processed(id_message: str) -> bool:
    with _conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM processed_messages WHERE id_message = ?", (id_message,)
        ).fetchone()
        return row is not None


def mark_processed(id_message: str) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO processed_messages (id_message, processed_at) VALUES (?, ?)",
            (id_message, datetime.utcnow().isoformat()),
        )
        conn.commit()


def append(chat_id: str, role: str, content: str) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO conversations (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (chat_id, role, content, datetime.utcnow().isoformat()),
        )
        conn.commit()


def tail(chat_id: str, n: int = MAX_HISTORY) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM (
                SELECT role, content, created_at
                FROM conversations
                WHERE chat_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ) ORDER BY created_at ASC
            """,
            (chat_id, n),
        ).fetchall()
    return [{"role": row[0], "content": row[1]} for row in rows]
