"""Simulation control endpoints — start, pause, resume, stop, step, status."""

from __future__ import annotations

import logging
import threading
from typing import Any

from fastapi import APIRouter, HTTPException

from tragedy.api.schemas import SimulationStartRequest, SimulationStatus
from tragedy.api.websocket import SimulationStream

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])

# Global simulation state (shared across routes)
_simulation_state: dict[str, Any] = {
    "engine": None,
    "model": None,
    "collector": None,
    "stream": None,
    "thread": None,
    "model_name": "",
    "start_time": 0.0,
}


def get_state() -> dict[str, Any]:
    return _simulation_state


@router.post("/start")
async def start_simulation(request: SimulationStartRequest) -> dict[str, Any]:
    """Start a new simulation with the given configuration."""
    import time

    from tragedy.models.yard_sale import YardSaleModel
    from tragedy.core.engine import SimulationEngine
    from tragedy.metrics.collector import MetricCollector
    from tragedy.api.websocket import get_stream
    from tragedy.utils.config import config_to_model_params, load_config, merge_configs

    state = get_state()

    if state["engine"] is not None and state["engine"].running:
        raise HTTPException(status_code=409, detail="Simulation is already running")

    # Load configuration
    try:
        config_path = f"configs/{request.config_id}.yaml"
        defaults = load_config("configs/defaults.yaml")
        model_config = load_config(config_path)
        config = merge_configs(defaults, model_config)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    # Create engine
    seed = config.get("model", {}).get("seed", 42)
    engine = SimulationEngine(seed=seed)

    # Create model
    params = config_to_model_params(config)
    model_name = request.config_id

    if model_name == "yard_sale":
        model = YardSaleModel(**params)  # type: ignore[arg-type]
    else:
        raise HTTPException(status_code=400, detail=f"Unknown model: {model_name}")

    model.setup(engine)

    # Create collector
    collector = MetricCollector()

    # Wire up WebSocket streaming pipeline
    stream = get_stream()
    stream.set_collector(collector)
    stream.start()

    # Wire collector to engine tick callback → pushes snapshots to stream
    engine.on_tick(
        lambda tick: _on_tick(tick, engine, collector, request.collect_every, stream)
    )

    # Start in background thread — save thread handle for clean shutdown
    state["engine"] = engine
    state["model"] = model
    state["collector"] = collector
    state["stream"] = stream
    state["model_name"] = model_name
    state["start_time"] = time.time()

    thread = engine.run_async(ticks=request.max_ticks)
    state["thread"] = thread

    logger.info("Started %s simulation (seed=%d, max_ticks=%s)",
                model_name, seed, request.max_ticks)

    return {
        "status": "started",
        "model": model_name,
        "seed": seed,
        "agents": len(engine.agents),
    }


@router.post("/pause")
async def pause_simulation() -> dict[str, str]:
    """Pause the running simulation."""
    state = get_state()
    engine = state["engine"]
    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation running")
    engine.pause()
    return {"status": "paused", "tick": engine.tick}


@router.post("/resume")
async def resume_simulation() -> dict[str, str]:
    """Resume a paused simulation."""
    state = get_state()
    engine = state["engine"]
    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation running")
    engine.resume()
    return {"status": "running", "tick": engine.tick}


@router.post("/stop")
async def stop_simulation() -> dict[str, Any]:
    """Stop the simulation and return final results."""
    import time

    state = get_state()
    engine = state["engine"]
    collector = state["collector"]

    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation running")

    final_tick = engine.tick
    engine.stop()

    # Wait for engine thread to finish
    thread = state.get("thread")
    if thread and thread.is_alive():
        thread.join(timeout=5.0)

    # Collect final results
    result = {
        "status": "stopped",
        "final_tick": final_tick,
        "total_ticks": final_tick,
        "agent_count": engine.agent_count,
        "uptime_seconds": time.time() - state["start_time"],
    }

    if collector:
        result["metrics"] = {
            name: values[-1] if values else None
            for name, values in collector.series.items()
        }

    state["engine"] = None
    state["model"] = None
    state["collector"] = None
    state["thread"] = None

    return result


@router.post("/step")
async def step_simulation() -> dict[str, Any]:
    """Advance the simulation by one tick (must be paused)."""
    state = get_state()
    engine = state["engine"]
    if engine is None:
        raise HTTPException(status_code=400, detail="No simulation running")
    if not engine.paused:
        raise HTTPException(status_code=400, detail="Simulation must be paused to step")
    engine.step()
    return {"tick": engine.tick}


@router.get("/status")
async def get_status() -> SimulationStatus:
    """Get the current simulation status."""
    import time

    state = get_state()
    engine = state["engine"]

    if engine is None:
        return SimulationStatus(
            running=False,
            paused=False,
            tick=0,
            agent_count=0,
            model_name="",
        )

    return SimulationStatus(
        running=engine.running,
        paused=engine.paused,
        tick=engine.tick,
        agent_count=engine.agent_count,
        tick_rate=engine.tick_rate,
        model_name=state.get("model_name", ""),
        uptime_seconds=time.time() - state.get("start_time", time.time()),
    )


def _on_tick(
    tick: int,
    engine: Any,
    collector: Any,
    collect_every: int,
    stream: Any = None,
) -> None:
    """Tick callback: collect metrics and push to WebSocket stream."""
    snapshot = collector.collect(engine, collect_every)
    if snapshot and stream:
        stream.set_snapshot(snapshot)
