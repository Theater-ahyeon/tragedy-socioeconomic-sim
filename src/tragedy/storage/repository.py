"""Repository pattern for simulation metrics CRUD operations.

Abstracts the SQL database behind domain-level methods so that the
storage backend can be swapped without changing API code.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from tragedy.storage.database import Database

logger = logging.getLogger(__name__)


class MetricRepository:
    """Repository for simulation runs and metrics.

    Usage:
        repo = MetricRepository(db)
        run_id = await repo.create_run("yard_sale", config, seed=42)
        await repo.insert_metrics(run_id, tick=100, metrics={"gini": 0.42})
        series = await repo.query_series(run_id, "gini")
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    # ── Run Management ──────────────────────────────────────────

    @staticmethod
    def _hash_config(config: dict) -> str:
        """Compute a deterministic hash of a config dict."""
        raw = json.dumps(config, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    async def create_run(
        self,
        model_name: str,
        config: dict,
        seed: int = 42,
        agent_count: int = 0,
        max_tick: int | None = None,
    ) -> int:
        """Create a new simulation run record.

        Returns:
            The run ID.
        """
        config_hash = self._hash_config(config)
        await self.db.execute(
            """INSERT INTO runs (model_name, config_hash, seed, max_tick, agent_count)
               VALUES (?, ?, ?, ?, ?)""",
            (model_name, config_hash, seed, max_tick, agent_count),
        )
        await self.db.commit()
        row = await self.db.fetch_one("SELECT last_insert_rowid() as id")
        run_id = row["id"]
        logger.info("Created run %d: %s (hash=%s)", run_id, model_name, config_hash)
        return run_id

    async def finish_run(self, run_id: int, final_tick: int) -> None:
        """Mark a run as finished."""
        await self.db.execute(
            "UPDATE runs SET status = 'finished', finished_at = datetime('now') WHERE id = ?",
            (run_id,),
        )
        await self.db.commit()

    async def fail_run(self, run_id: int, error: str) -> None:
        """Mark a run as failed."""
        await self.db.execute(
            "UPDATE runs SET status = 'failed' WHERE id = ?",
            (run_id,),
        )
        await self.db.commit()

    # ── Metrics ─────────────────────────────────────────────────

    async def insert_metrics(
        self, run_id: int, tick: int, metrics: dict[str, float]
    ) -> None:
        """Insert a batch of metric values for a tick.

        Args:
            run_id: The run to associate metrics with.
            tick: The simulation tick.
            metrics: Dict mapping metric_name -> value.
        """
        rows = [(run_id, tick, name, value) for name, value in metrics.items()]
        await self.db.conn.executemany(
            "INSERT INTO metrics (run_id, tick, metric_name, value) VALUES (?, ?, ?, ?)",
            rows,
        )
        await self.db.commit()

    async def query_series(
        self,
        run_id: int,
        metric_names: list[str] | None = None,
        from_tick: int = 0,
        to_tick: int | None = None,
    ) -> dict[str, list[dict]]:
        """Query time series metrics.

        Args:
            run_id: The run ID.
            metric_names: Specific metrics to query (None = all).
            from_tick: Start tick (inclusive).
            to_tick: End tick (inclusive). None = all.

        Returns:
            Dict mapping metric_name -> list of {tick, value} dicts.
        """
        if metric_names:
            placeholders = ",".join("?" * len(metric_names))
            name_filter = f"AND metric_name IN ({placeholders})"
            params: tuple = (run_id, *metric_names, from_tick)
        else:
            name_filter = ""
            params = (run_id, from_tick)

        if to_tick is not None:
            tick_filter = "AND tick <= ?"
            params = (*params, to_tick)
        else:
            tick_filter = ""

        sql = f"""SELECT tick, metric_name, value
                   FROM metrics
                   WHERE run_id = ? {name_filter}
                     AND tick >= ? {tick_filter}
                   ORDER BY tick, metric_name"""

        rows = await self.db.fetch_all(sql, params)

        result: dict[str, list[dict]] = {}
        for row in rows:
            name = row["metric_name"]
            if name not in result:
                result[name] = []
            result[name].append({"tick": row["tick"], "value": row["value"]})
        return result

    async def get_latest_tick(self, run_id: int) -> int:
        """Get the latest tick with metrics for a run."""
        row = await self.db.fetch_one(
            "SELECT MAX(tick) as max_tick FROM metrics WHERE run_id = ?",
            (run_id,),
        )
        return row["max_tick"] if row and row["max_tick"] is not None else 0

    async def list_runs(self) -> list[dict]:
        """List all runs, most recent first."""
        return await self.db.fetch_all(
            "SELECT * FROM runs ORDER BY started_at DESC"
        )

    # ── Snapshots ───────────────────────────────────────────────

    async def insert_snapshot(self, run_id: int, tick: int, data: dict) -> None:
        """Store a JSON snapshot for a tick."""
        await self.db.execute(
            "INSERT INTO snapshots (run_id, tick, data) VALUES (?, ?, ?)",
            (run_id, tick, json.dumps(data)),
        )
        await self.db.commit()

    async def get_snapshot(self, run_id: int, tick: int) -> dict | None:
        """Retrieve a snapshot for a specific tick."""
        row = await self.db.fetch_one(
            "SELECT data FROM snapshots WHERE run_id = ? AND tick = ?",
            (run_id, tick),
        )
        if row:
            return json.loads(row["data"])
        return None
