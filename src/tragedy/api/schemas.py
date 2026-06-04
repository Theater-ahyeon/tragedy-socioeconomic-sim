"""Pydantic request/response schemas for the Tragedy API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SimulationStartRequest(BaseModel):
    """Request to start a new simulation run."""

    config_id: str = Field(..., description="Configuration file name (e.g. 'yard_sale')")
    max_ticks: int | None = Field(None, description="Maximum ticks to run (None = unlimited)")
    collect_every: int = Field(1, ge=1, description="Collect metrics every N ticks")


class SimulationStatus(BaseModel):
    """Current simulation state."""

    running: bool
    paused: bool
    tick: int
    agent_count: int
    tick_rate: float = Field(0.0, description="Average ticks per second")
    model_name: str = ""
    uptime_seconds: float = 0.0


class ConfigCreate(BaseModel):
    """Request to create a new configuration."""

    name: str = Field(..., description="Configuration name")
    content: dict[str, Any] = Field(..., description="Configuration YAML content as dict")


class ConfigResponse(BaseModel):
    """Configuration file response."""

    name: str
    content: dict[str, Any]


class MetricsQuery(BaseModel):
    """Query parameters for metrics time series."""

    metrics: list[str] = Field(default_factory=list, description="Metric names to query (empty = all)")
    from_tick: int = Field(0, ge=0)
    to_tick: int | None = None
    resolution: int = Field(1, ge=1, description="Return every Nth data point")


class TimeSeriesResponse(BaseModel):
    """Time series metrics response."""

    ticks: list[int]
    series: dict[str, list[float | None]]


class SnapshotMessage(BaseModel):
    """WebSocket snapshot message."""

    type: str = "snapshot"
    tick: int
    metrics: dict[str, float] = Field(default_factory=dict)
    lorenz: dict[str, list[float]] | None = None
    distribution: dict[str, list[float]] | None = None


class EventMessage(BaseModel):
    """WebSocket event message."""

    type: str = "event"
    tick: int
    event: str
    data: dict[str, Any] = Field(default_factory=dict)


class CommandMessage(BaseModel):
    """WebSocket command from client."""

    type: str = "command"
    action: str = Field(..., description="pause | resume | stop | set_speed")
    value: Any = None
