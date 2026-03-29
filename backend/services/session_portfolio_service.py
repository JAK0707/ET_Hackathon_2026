"""
session_portfolio_service.py
Persists user portfolio holdings in SQLite so every chat request
automatically has portfolio context — no need to re-submit holdings each time.
Drop this at: backend/services/session_portfolio_service.py
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path


DB_PATH = Path("./marketmind.db")


class SessionPortfolioService:
    """
    Lightweight KV store on top of SQLite for user portfolio persistence.
    Uses the same DB as the rest of the app (marketmind.db).
    """

    def __init__(self, db_path: str | Path = DB_PATH) -> None:
        self.db_path = Path(db_path)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_portfolios (
                    user_id   TEXT PRIMARY KEY,
                    holdings  TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            conn.commit()

    def save(self, user_id: str, holdings: list[dict]) -> None:
        """Upsert holdings for a user."""
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO user_portfolios (user_id, holdings, updated_at)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(user_id) DO UPDATE SET
                    holdings   = excluded.holdings,
                    updated_at = excluded.updated_at
            """, (user_id, json.dumps(holdings)))
            conn.commit()

    def load(self, user_id: str) -> list[dict]:
        """Return persisted holdings for a user, or [] if none."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT holdings FROM user_portfolios WHERE user_id = ?",
                (user_id,)
            ).fetchone()
        if row:
            try:
                return json.loads(row[0])
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def clear(self, user_id: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "DELETE FROM user_portfolios WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()

    def all_users(self) -> list[str]:
        with self._conn() as conn:
            rows = conn.execute("SELECT user_id FROM user_portfolios").fetchall()
        return [r[0] for r in rows]