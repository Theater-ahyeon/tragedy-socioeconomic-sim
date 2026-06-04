"""WebSocket streaming for real-time simulation visualization.

The SimulationStream manages connected clients and broadcasts simulation
snapshots at a configurable frame rate, decoupled from the simulation tick
rate. This prevents visualization backpressure from slowing the simulation.

Architecture:
  Simulation (background thread)
      │  on_tick callback
      │  collector.collect() → snapshot queued
      ▼
  SimulationStream (async task on main event loop)
      │  polls latest snapshot at frame_interval
      │  broadcasts JSON to all connected WebSocket clients
      ▼
  Frontend (React + Canvas/D3)
      renders snapshots at 10-20 FPS
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


class SimulationStream:
    """Manages WebSocket connections and broadcasts simulation snapshots.

    Not intended for instantiation by users — created by the API app.
    """

    def __init__(self, frame_interval_ms: int = 50) -> None:
        self.connections: set[WebSocket] = set()
        self.frame_interval: float = frame_interval_ms / 1000.0
        self._latest_snapshot: dict[str, Any] | None = None
        self._running: bool = False
        self._task: asyncio.Task | None = None
        self._collector_ref: Any = None  # Reference to MetricCollector

    def set_collector(self, collector: Any) -> None:
        """Set the collector reference for polling."""
        self._collector_ref = collector

    def set_snapshot(self, snapshot: dict[str, Any]) -> None:
        """Queue a snapshot for broadcast (called from simulation thread)."""
        self._latest_snapshot = snapshot

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.connections.add(websocket)
        logger.info("WebSocket client connected (total: %d)", len(self.connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected client."""
        self.connections.discard(websocket)
        logger.info("WebSocket client disconnected (total: %d)", len(self.connections))

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send a message to all connected clients."""
        if not self.connections:
            return

        payload = json.dumps(message)
        dead: list[WebSocket] = []

        for ws in self.connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.connections.discard(ws)

    async def stream_loop(self) -> None:
        """Background task: poll latest snapshot and broadcast at frame rate."""
        self._running = True
        logger.info("WebSocket stream loop started (interval=%dms)", self.frame_interval * 1000)

        while self._running:
            # Poll the collector for the latest data
            snapshot = self._latest_snapshot
            if snapshot and self.connections:
                await self.broadcast(snapshot)

            await asyncio.sleep(self.frame_interval)

    def start(self) -> None:
        """Start the stream loop as an asyncio background task."""
        try:
            loop = asyncio.get_running_loop()
            self._task = loop.create_task(self.stream_loop())
        except RuntimeError:
            # No running event loop — will be started by app lifespan
            pass

    def stop(self) -> None:
        """Stop the stream loop."""
        self._running = False
        if self._task:
            self._task.cancel()

    @property
    def client_count(self) -> int:
        return len(self.connections)


# Global stream instance
_simulation_stream = SimulationStream()


def get_stream() -> SimulationStream:
    """Get the global simulation stream instance."""
    return _simulation_stream


@router.websocket("/ws/simulation")
async def simulation_websocket(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time simulation data.

    Server → Client messages:
        {"type": "snapshot", "tick": N, "metrics": {...}, ...}
        {"type": "event", "tick": N, "event": "bankruptcy", "data": {...}}

    Client → Server messages:
        {"type": "command", "action": "pause"}
        {"type": "command", "action": "resume"}
        {"type": "command", "action": "set_speed", "value": 100}
    """
    stream = get_stream()
    await stream.connect(websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Invalid JSON"})
                )
                continue

            # Handle client commands
            if message.get("type") == "command":
                action = message.get("action", "")
                from tragedy.api.routes.simulation import get_state

                state = get_state()
                engine = state.get("engine")

                if action == "pause" and engine:
                    engine.pause()
                elif action == "resume" and engine:
                    engine.resume()
                elif action == "stop" and engine:
                    engine.stop()
                elif action == "set_speed" and engine:
                    # Speed control TBD — adjust frame interval
                    value = message.get("value", 100)
                    stream.frame_interval = 1.0 / max(value, 1)

    except WebSocketDisconnect:
        await stream.disconnect(websocket)
