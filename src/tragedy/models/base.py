"""Base model class — template for all economic simulation models.

Each model assembles agents, markets, and stage handlers into a complete
simulation configuration that can be loaded into the SimulationEngine.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from tragedy.core.engine import SimulationEngine
from tragedy.core.scheduler import SimulationStage


@dataclass
class BaseModel(ABC):
    """Abstract base for all economic simulation models.

    A model defines:
    1. What agents exist (types, counts, initial state)
    2. What markets they interact through
    3. What stages execute each tick and in what order
    4. What metrics to collect

    Usage:
        model = YardSaleModel(num_agents=1000, initial_wealth=100.0)
        model.setup(engine)
        engine.run(ticks=5000)
    """

    name: str = "base"
    seed: int = 42
    engine: SimulationEngine | None = None

    # Stage configuration — subclasses override this
    stages: list[SimulationStage] = field(default_factory=list)

    def setup(self, engine: SimulationEngine) -> None:
        """Initialize the model on an engine.

        This method:
        1. Stores the engine reference
        2. Creates all agents
        3. Registers all stage handlers
        4. Sets the active stage order

        Args:
            engine: The simulation engine to configure.
        """
        self.engine = engine
        self.engine.set_active_stages(self.stages)
        self._create_agents()
        self._register_stages()

    @abstractmethod
    def _create_agents(self) -> None:
        """Create and initialize all agents for this model."""
        ...

    @abstractmethod
    def _register_stages(self) -> None:
        """Register all stage handlers with the engine."""
        ...

    def teardown(self) -> None:
        """Clean up model resources."""
        if self.engine:
            self.engine.reset()
