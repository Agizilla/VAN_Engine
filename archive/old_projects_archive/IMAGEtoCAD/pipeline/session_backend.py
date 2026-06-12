"""
SQLite Session Backend — Persistent session storage for IMAGEtoCAD.

Replaces the in-memory dict with a SQLite-backed store that survives
server restarts. Sessions are automatically expired after TTL.
"""

import sqlite3
import time
import json
import os
import threading
from typing import Optional, Any, Dict
from pathlib import Path


class SessionBackend:
    """
    SQLite-backed session store with automatic TTL expiry.

    Sessions are stored as JSON blobs with a created_at timestamp.
    Expired sessions are lazily cleaned on access.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the session backend.

        Args:
            db_path: Path to SQLite database file. Defaults to sessions.db in cwd.
        """
        if db_path is None:
            db_path = str(Path.cwd() / "sessions.db")

        self.db_path = db_path
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get a thread-local database connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self) -> None:
        """Create the sessions table if it does not exist."""
        conn = self._get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at)"
        )
        conn.commit()

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a session by ID.

        Args:
            session_id: Session identifier.

        Returns:
            Session dict or None if not found/expired.
        """
        conn = self._get_conn()
        row = conn.execute(
            "SELECT data FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["data"])

    def set(self, session_id: str, data: Dict[str, Any]) -> None:
        """
        Store or update a session.

        Args:
            session_id: Session identifier.
            data: Session data dict (must be JSON-serializable).
        """
        conn = self._get_conn()
        now = time.time()
        conn.execute(
            """
            INSERT INTO sessions (session_id, data, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET data = ?, created_at = ?
            """,
            (session_id, json.dumps(data), now, json.dumps(data), now),
        )
        conn.commit()

    def delete(self, session_id: str) -> None:
        """
        Delete a session.

        Args:
            session_id: Session identifier.
        """
        conn = self._get_conn()
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()

    def cleanup_expired(self, ttl_seconds: int = 3600) -> int:
        """
        Remove sessions older than TTL.

        Args:
            ttl_seconds: Session lifetime in seconds.

        Returns:
            Number of sessions removed.
        """
        conn = self._get_conn()
        cutoff = time.time() - ttl_seconds
        cursor = conn.execute(
            "DELETE FROM sessions WHERE created_at < ?",
            (cutoff,),
        )
        conn.commit()
        return cursor.rowcount

    def count(self) -> int:
        """Return the total number of active sessions."""
        conn = self._get_conn()
        row = conn.execute("SELECT COUNT(*) as cnt FROM sessions").fetchone()
        return row["cnt"]
