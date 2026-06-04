"""Metrics query endpoints — time series, distribution, Lorenz curve data."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from tragedy.api.routes.simulation import get_state
from tragedy.api.schemas import MetricsQuery, TimeSeriesResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


@router.get("/timeseries")
async def get_timeseries(
    metrics: str = Query("", description="Comma-separated metric names (empty = all)"),
    from_tick: int = Query(0, ge=0),
    to_tick: int | None = Query(None),
    resolution: int = Query(1, ge=1),
) -> TimeSeriesResponse:
    """Get time series metrics from the current or most recent run."""
    state = get_state()
    collector = state.get("collector")

    if collector is None:
        raise HTTPException(status_code=400, detail="No simulation data available")

    metric_names = [m.strip() for m in metrics.split(",") if m.strip()] if metrics else []
    if not metric_names:
        metric_names = list(collector.series.keys())

    # Slice and subsample
    ticks = collector.ticks[from_tick:to_tick:resolution]
    series_data: dict[str, list[float | None]] = {}

    for name in metric_names:
        values = collector.series.get(name, [])
        sliced = values[from_tick:to_tick:resolution]
        series_data[name] = sliced

    return TimeSeriesResponse(ticks=ticks, series=series_data)


@router.get("/latest")
async def get_latest_metrics() -> dict:
    """Get the most recent metrics snapshot."""
    state = get_state()
    collector = state.get("collector")

    if collector is None:
        raise HTTPException(status_code=400, detail="No simulation data available")

    result: dict = {"tick": collector.ticks[-1] if collector.ticks else 0, "metrics": {}}
    for name, values in collector.series.items():
        if values:
            result["metrics"][name] = values[-1]

    return result


@router.get("/summary")
async def get_summary() -> dict:
    """Get a summary of all collected data."""
    state = get_state()
    collector = state.get("collector")
    engine = state["engine"]

    if collector is None:
        raise HTTPException(status_code=400, detail="No simulation data available")

    summary: dict = {
        "ticks_collected": len(collector.ticks),
        "current_tick": engine.tick if engine else 0,
        "agent_count": engine.agent_count if engine else 0,
        "metrics_available": list(collector.series.keys()),
    }

    # Latest values
    latest = {}
    for name, values in collector.series.items():
        if values:
            latest[name] = values[-1]
    summary["latest"] = latest

    return summary
