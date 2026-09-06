"""Simple SQLite-backed result cache keyed by (district_id, month)."""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path

from app.config import CACHE_DB_PATH as CONFIG_CACHE_DB_PATH

logger = logging.getLogger(__name__)


class CacheManager:
    """SQLite-backed cache for environment computation results.

    Stores the fully assembled, schema-valid ``EnvironmentResponse`` as JSON
    so a cache hit can be returned without recalculation.
    """

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path else CONFIG_CACHE_DB_PATH
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS environment_cache (
                    district TEXT NOT NULL,
                    month TEXT NOT NULL,
                    result TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (district, month)
                )
                """
            )

    def get_cached(self, district_id: str, month: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT result FROM environment_cache WHERE district = ? AND month = ?",
                (district_id, month),
            ).fetchone()
        if row is None:
            return None
        try:
            return json.loads(row["result"])
        except json.JSONDecodeError:
            logger.error("Corrupt cache entry for %s/%s; ignoring", district_id, month)
            return None

    def set_cached(self, district_id: str, month: str, result: dict) -> None:
        from datetime import datetime, timezone

        payload = json.dumps(result)
        created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO environment_cache (district, month, result, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(district, month) DO UPDATE SET
                    result = excluded.result,
                    created_at = excluded.created_at
                """,
                (district_id, month, payload, created_at),
            )
        logger.info("Cache set: district=%s month=%s", district_id, month)

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM environment_cache")


# Module-level singleton used by the API layer.
cache_manager = CacheManager()