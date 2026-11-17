"""Small local SQLite store for translation history and community feedback."""
from __future__ import annotations
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(os.getenv("SANKETSETU_DB", Path(__file__).parent / "data" / "sanketsetu.sqlite3"))


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            confidence REAL,
            created_at TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'live'
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")


def save_history(text: str, confidence: float | None = None, source: str = "live") -> dict:
    created = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        cur = conn.execute("INSERT INTO history(text, confidence, created_at, source) VALUES (?, ?, ?, ?)", (text[:500], confidence, created, source[:20]))
        row = conn.execute("SELECT * FROM history WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(row)


def get_history(limit: int = 100) -> list[dict]:
    with _connect() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM history ORDER BY id DESC LIMIT ?", (min(max(limit, 1), 200),)).fetchall()]


def delete_history(item_id: int) -> bool:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM history WHERE id=?", (item_id,))
        return cur.rowcount > 0


def clear_history() -> int:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM history")
        return cur.rowcount


def save_feedback(rating: int, message: str) -> dict:
    created = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        cur = conn.execute("INSERT INTO feedback(rating, message, created_at) VALUES (?, ?, ?)", (rating, message[:2000], created))
        return {"id": cur.lastrowid, "rating": rating, "created_at": created}
