"""SQLite database connection and schema management.

Uses aiosqlite for async compatibility with FastAPI. The database stores
simulation metrics as time series and run metadata for reproducibility.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    seed INTEGER NOT NULL,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at TEXT,
    max_tick INTEGER,
    agent_count INTEGER,
    status TEXT NOT NULL DEFAULT 'running'
);

CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    tick INTEGER NOT NULL,
    metric_name TEXT NOT NULL,
    value REAL NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);

CREATE INDEX IF NOT EXISTS idx_metrics_run_tick ON metrics(run_id, tick);
CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(run_id, metric_name);

CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    tick INTEGER NOT NULL,
    data TEXT NOT NULL,  -- JSON blob
    FOREIGN KEY (run_id) REFERENCES runs(id)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_run_tick ON snapshots(run_id, tick);
"""


class Database:
    """Async SQLite database manager for simulation data.

    Usage:
        db = Database("data/tragedy.db")
        await db.initialize()
        # ... use with MetricRepository ...
        await db.close()
    """

    def __init__(self, path: str = "data/tragedy.db") -> None:
        self.path = Path(path)
        self.conn: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Create the database directory and initialize the schema."""
        os.makedirs(self.path.parent, exist_ok=True)
        self.conn = await aiosqlite.connect(str(self.path))
        self.conn.row_factory = aiosqlite.Row
        await self.conn.executescript(SCHEMA_SQL)
        await self.conn.commit()
        logger.info("Database initialized at %s", self.path)

    async def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            await self.conn.close()
            self.conn = None
            logger.info("Database connection closed")

    async def execute(self, sql: str, params: tuple | None = None):
        """Execute a SQL statement."""
        if self.conn is None:
            raise RuntimeError("Database not initialized")
        return await self.conn.execute(sql, params or ())

    async def fetch_all(self, sql: str, params: tuple | None = None) -> list[dict]:
        """Fetch all rows from a query."""
        if self.conn is None:
            raise RuntimeError("Database not initialized")
        cursor = await self.conn.execute(sql, params or ())
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def fetch_one(self, sql: str, params: tuple | None = None) -> dict | None:
        """Fetch a single row from a query."""
        if self.conn is None:
            raise RuntimeError("Database not initialized")
        cursor = await self.conn.execute(sql, params or ())
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def commit(self) -> None:
        """Commit the current transaction."""
        if self.conn:
            await self.conn.commit()
