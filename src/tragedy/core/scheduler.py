"""Simulation stage definitions and scheduling.

Economic simulations require ordered stages within each tick: production must
happen before consumption, markets must clear before balance sheets update, etc.
The SimulationStage enum defines this fixed activation order.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Any, Protocol


class SimulationStage(Enum):
    """Ordered stages executed within each simulation tick.

    Each stage represents a distinct phase of economic activity. Not all models
    use all stages — simpler models (Yard-Sale) use only a subset. The engine
    dispatches to registered stage handlers in enum definition order.
    """

    PRODUCTION = auto()          # Firms produce goods; depreciation; innovation
    LABOR_MATCHING = auto()      # Workers matched to firms; wage bargaining
    GOODS_PRICING = auto()       # Firms set prices based on costs + markup
    CONSUMPTION = auto()         # Households consume goods
    INVESTMENT = auto()          # Firms invest in capital expansion
    CREDIT_MATCHING = auto()     # Banks issue loans to firms
    FINANCIAL_SETTLEMENT = auto()  # Interest, debt service, dividends
    TAXATION = auto()            # Government taxes & spending; monetary policy
    ACCOUNTING = auto()          # Balance sheet update; bankruptcy check; entry/exit
    STRATEGY_ADAPTATION = auto() # Observe neighbors, imitate successful strategies
    METRICS = auto()             # Collect and record all aggregate statistics


class StageHandler(Protocol):
    """Protocol for stage handler callables."""

    def __call__(self, engine: Any) -> None: ...


# Default stage order for each model type.
# Models can override this by providing their own stage list.
YARD_SALE_STAGES = [
    SimulationStage.CONSUMPTION,         # Network-based pairwise transfer
    SimulationStage.STRATEGY_ADAPTATION, # Observe neighbors, imitate successful
    SimulationStage.ACCOUNTING,          # Conservation check, cleanup
    SimulationStage.METRICS,             # Collect Gini, Lorenz, network metrics
]

SUGARSCAPE_STAGES = [
    SimulationStage.PRODUCTION,    # Sugar growback
    SimulationStage.CONSUMPTION,   # Agent movement + sugar harvesting
    SimulationStage.ACCOUNTING,    # Aging, death, replacement
    SimulationStage.METRICS,
]

KS_MACRO_STAGES = [
    SimulationStage.PRODUCTION,
    SimulationStage.LABOR_MATCHING,
    SimulationStage.GOODS_PRICING,
    SimulationStage.CONSUMPTION,
    SimulationStage.INVESTMENT,
    SimulationStage.CREDIT_MATCHING,
    SimulationStage.FINANCIAL_SETTLEMENT,
    SimulationStage.TAXATION,
    SimulationStage.ACCOUNTING,
    SimulationStage.METRICS,
]
