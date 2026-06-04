"""Simulation engine — the central orchestrator.

The SimulationEngine manages the simulation lifecycle: clock advancement,
stage dispatch, agent lifecycle, and event queue processing. It is
model-agnostic — specific economic models register their stage handlers.
"""

from __future__ import annotations

import heapq
import logging
import threading
import time
from collections.abc import Callable
from typing import Any

from tragedy.core.agent import Agent, AgentSet
from tragedy.core.random import RNGManager
from tragedy.core.scheduler import SimulationStage

logger = logging.getLogger(__name__)


class Event:
    """A deferred event to be executed at a future tick.

    Events are ordered by (tick, priority). Lower priority values execute first.
    """

    __slots__ = ("tick", "priority", "callback", "description")

    def __init__(
        self,
        tick: int,
        priority: int,
        callback: Callable[[], None],
        description: str = "",
    ) -> None:
        self.tick = tick
        self.priority = priority
        self.callback = callback
        self.description = description

    def __lt__(self, other: Event) -> bool:
        return (self.tick, self.priority) < (other.tick, other.priority)


class SimulationEngine:
    """Central orchestrator for agent-based economic simulations.

    The engine owns the agent population, the RNG manager, the event queue,
    and the stage handler registry. It advances the simulation tick-by-tick,
    dispatching each stage to its registered handler.

    Usage:
        engine = SimulationEngine(seed=42)
        engine.register_stage(SimulationStage.CONSUMPTION, my_transfer_handler)
        engine.register_stage(SimulationStage.METRICS, my_metrics_handler)
        engine.run(ticks=1000)
    """

    def __init__(self, seed: int = 42) -> None:
        # ── Core State ────────────────────────────────────────
        self.tick: int = 0
        self.running: bool = False
        self.paused: bool = False
        self.seed: int = seed

        # ── Agent Population ──────────────────────────────────
        self.agents = AgentSet()
        self._next_agent_id: int = 0

        # ── RNG ───────────────────────────────────────────────
        self.rng = RNGManager(master_seed=seed)

        # ── Stage Dispatch ────────────────────────────────────
        self._stage_handlers: dict[SimulationStage, list[Callable[[SimulationEngine], None]]] = {}
        self._active_stages: list[SimulationStage] = []

        # ── Event Queue ───────────────────────────────────────
        self._event_queue: list[Event] = []

        # ── Metrics ───────────────────────────────────────────
        self.metrics_history: dict[str, list[float]] = {}
        self._tick_start_time: float = 0.0
        self._tick_times: list[float] = []

        # ── Thread Safety ─────────────────────────────────────
        self._lock = threading.RLock()

        # ── Callbacks ─────────────────────────────────────────
        self._tick_callbacks: list[Callable[[int], None]] = []
        self._stop_callbacks: list[Callable[[], None]] = []

    # ── Agent Management ──────────────────────────────────────────

    def create_agent(self, agent_type: str = "Agent", **kwargs: Any) -> Agent:
        """Create and register a new agent.

        Args:
            agent_type: Type string for the agent (e.g. "Household", "Firm").
            **kwargs: Passed to the Agent constructor's attributes dict.

        Returns:
            The newly created Agent.
        """
        agent = Agent(
            agent_id=self._next_agent_id,
            agent_type=agent_type,
            creation_tick=self.tick,
        )
        agent.attributes.update(kwargs)
        self._next_agent_id += 1
        self.agents.add(agent)
        return agent

    def remove_agent(self, agent_or_id: Agent | int) -> Agent | None:
        """Remove an agent from the simulation."""
        return self.agents.remove(agent_or_id)

    # ── Stage Registration ────────────────────────────────────────

    def register_stage(
        self,
        stage: SimulationStage,
        handler: Callable[[SimulationEngine], None],
    ) -> None:
        """Register a handler for a simulation stage.

        Multiple handlers can be registered for the same stage;
        they execute in registration order.
        """
        if stage not in self._stage_handlers:
            self._stage_handlers[stage] = []
        self._stage_handlers[stage].append(handler)

    def set_active_stages(self, stages: list[SimulationStage]) -> None:
        """Set the ordered list of stages to execute each tick."""
        self._active_stages = list(stages)

    # ── Event Queue ───────────────────────────────────────────────

    def schedule_event(
        self,
        tick: int,
        callback: Callable[[], None],
        priority: int = 0,
        description: str = "",
    ) -> None:
        """Schedule a deferred event to execute at the given tick."""
        event = Event(tick, priority, callback, description)
        heapq.heappush(self._event_queue, event)

    def _process_events(self) -> None:
        """Execute all events scheduled for the current tick or earlier."""
        while self._event_queue and self._event_queue[0].tick <= self.tick:
            event = heapq.heappop(self._event_queue)
            try:
                event.callback()
            except Exception:
                logger.exception(
                    "Error executing event '%s' at tick %d",
                    event.description,
                    self.tick,
                )

    # ── Simulation Loop ───────────────────────────────────────────

    def step(self) -> None:
        """Advance the simulation by one tick."""
        if not self.running:
            return

        with self._lock:
            self._tick_start_time = time.perf_counter()

            # Process deferred events for this tick
            self._process_events()

            # Execute each active stage in order
            for stage in self._active_stages:
                handlers = self._stage_handlers.get(stage, [])
                for handler in handlers:
                    try:
                        handler(self)
                    except Exception:
                        logger.exception(
                            "Error in stage %s at tick %d",
                            stage.name,
                            self.tick,
                        )

            # Record tick timing
            elapsed = time.perf_counter() - self._tick_start_time
            self._tick_times.append(elapsed)

            # Fire tick callbacks
            for cb in self._tick_callbacks:
                try:
                    cb(self.tick)
                except Exception:
                    logger.exception("Error in tick callback at tick %d", self.tick)

            self.tick += 1

    def run(self, ticks: int | None = None) -> None:
        """Run the simulation continuously.

        Args:
            ticks: Maximum number of ticks to run. None = run until stopped.
        """
        self.running = True
        start_tick = self.tick

        try:
            while self.running:
                if ticks is not None and self.tick - start_tick >= ticks:
                    break
                if self.paused:
                    time.sleep(0.01)
                    continue
                self.step()
        finally:
            self.running = False
            for cb in self._stop_callbacks:
                try:
                    cb()
                except Exception:
                    logger.exception("Error in stop callback")

    def run_async(self, ticks: int | None = None) -> threading.Thread:
        """Start the simulation in a background thread.

        Args:
            ticks: Maximum ticks to run (None = unlimited).

        Returns:
            The thread running the simulation.
        """
        thread = threading.Thread(
            target=self.run, args=(ticks,), daemon=True, name="tragedy-engine"
        )
        thread.start()
        return thread

    def pause(self) -> None:
        """Pause the simulation."""
        self.paused = True
        logger.info("Simulation paused at tick %d", self.tick)

    def resume(self) -> None:
        """Resume a paused simulation."""
        self.paused = False
        logger.info("Simulation resumed at tick %d", self.tick)

    def stop(self) -> None:
        """Stop the simulation."""
        self.running = False
        logger.info("Simulation stopped at tick %d", self.tick)

    def reset(self) -> None:
        """Reset the simulation to initial state."""
        with self._lock:
            self.stop()
            self.tick = 0
            self.agents.clear()
            self._next_agent_id = 0
            self._event_queue.clear()
            self.metrics_history.clear()
            self._tick_times.clear()
            self._stage_handlers.clear()
            self._active_stages.clear()
            self._tick_callbacks.clear()
            self._stop_callbacks.clear()
            self.rng.reset()

    # ── Callbacks ─────────────────────────────────────────────────

    def on_tick(self, callback: Callable[[int], None]) -> None:
        """Register a callback fired after each tick completes."""
        self._tick_callbacks.append(callback)

    def on_stop(self, callback: Callable[[], None]) -> None:
        """Register a callback fired when the simulation stops."""
        self._stop_callbacks.append(callback)

    # ── Metrics Helpers ───────────────────────────────────────────

    def record_metric(self, name: str, value: float) -> None:
        """Record a scalar metric for the current tick."""
        if name not in self.metrics_history:
            self.metrics_history[name] = []
        self.metrics_history[name].append(value)

    def get_all_agent_attributes(self, attr: str) -> list[Any]:
        """Get a list of an attribute across all agents.

        Checks both the `attributes` dict and direct instance attributes.
        """
        result = []
        for agent in self.agents:
            if attr in agent.attributes:
                result.append(agent.attributes[attr])
            else:
                result.append(getattr(agent, attr, None))
        return result

    # ── Information ───────────────────────────────────────────────

    @property
    def agent_count(self) -> int:
        return len(self.agents)

    @property
    def tick_rate(self) -> float:
        """Average ticks per second over the last 100 ticks."""
        if not self._tick_times:
            return 0.0
        recent = self._tick_times[-100:]
        avg = sum(recent) / len(recent)
        return 1.0 / avg if avg > 0 else 0.0

    def __repr__(self) -> str:
        return (
            f"SimulationEngine(tick={self.tick}, agents={len(self.agents)}, "
            f"running={self.running}, paused={self.paused})"
        )
