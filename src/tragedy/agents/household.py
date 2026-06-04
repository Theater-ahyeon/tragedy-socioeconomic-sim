"""Household agent implementations.

Phase 1: YardSaleAgent — a simple wealth-holding agent for pairwise
wealth transfer simulations (the Yard-Sale model).

Phase 1.5: Added agent memory, heterogeneous strategies (savings_rate,
risk_tolerance), neighbor observation, and imitation learning.
"""

from __future__ import annotations

from typing import Any

from tragedy.agents.memory import AgentMemory
from tragedy.core.agent import Agent


class YardSaleAgent(Agent):
    """An agent in the Yard-Sale wealth transfer model with memory.

    Each agent holds wealth and personal behavioral parameters that
    determine its trading strategy. With memory and imitation, agents
    can observe successful neighbors and copy their strategies.

    Attributes:
        wealth: Current wealth (float).
        savings_rate: Fraction of wealth to risk per trade (0 to 1).
        risk_tolerance: Coin bias — positive favors richer, negative favors poorer.
        memory: Personal history of trades, wealth, and observations.

    Reference:
        Yakovenko & Rosser (2009), "Statistical mechanics of money,
        wealth, and income." Reviews of Modern Physics, 81(4), 1703.
    """

    __slots__ = ("wealth", "savings_rate", "risk_tolerance", "memory")

    def __init__(
        self,
        agent_id: int,
        agent_type: str = "YardSaleAgent",
        creation_tick: int = 0,
        wealth: float = 0.0,
        savings_rate: float = 0.05,
        risk_tolerance: float = 0.0,
    ) -> None:
        super().__init__(
            agent_id=agent_id,
            agent_type=agent_type,
            creation_tick=creation_tick,
        )
        self.wealth = wealth
        self.savings_rate = savings_rate
        self.risk_tolerance = risk_tolerance
        self.memory = AgentMemory(agent_id=agent_id)

    # ── Trading ────────────────────────────────────────────────

    def participate_in_transfer(
        self,
        other: YardSaleAgent,
        fraction: float | None = None,
        bias: float | None = None,
        rng: Any = None,
    ) -> float:
        """Execute a pairwise wealth transfer with another agent.

        Uses this agent's personal savings_rate and risk_tolerance unless
        overridden by explicit fraction/bias parameters.

        Args:
            other: The paired agent.
            fraction: Override transfer fraction (None = use self.savings_rate).
            bias: Override coin bias (None = use self.risk_tolerance).
            rng: Numpy random Generator for reproducibility.

        Returns:
            The amount this agent gained (positive) or lost (negative).
        """
        if self.wealth <= 0 and other.wealth <= 0:
            return 0.0

        fraction = fraction if fraction is not None else self.savings_rate
        bias = bias if bias is not None else self.risk_tolerance

        # Clamp to valid ranges
        fraction = max(0.001, min(1.0, fraction))
        bias = max(-1.0, min(1.0, bias))

        # Identify poorer and richer agent
        poorer = self if self.wealth <= other.wealth else other
        richer = other if poorer is self else self

        transfer_amount = poorer.wealth * fraction
        if transfer_amount <= 0:
            return 0.0

        # Biased coin
        if rng is not None:
            coin = rng.random()
        else:
            import random
            coin = random.random()

        p_richer_wins = 0.5 + bias * 0.5

        if coin < p_richer_wins:
            # Richer agent wins
            poorer.wealth -= transfer_amount
            richer.wealth += transfer_amount
            gain = transfer_amount if self is richer else -transfer_amount
        else:
            # Poorer agent wins
            poorer.wealth += transfer_amount
            richer.wealth -= transfer_amount
            gain = transfer_amount if self is poorer else -transfer_amount

        return gain

    # ── Observation & Imitation ────────────────────────────────

    def observe_neighbor(self, neighbor_id: int, neighbor_wealth: float) -> None:
        """Record a neighbor's current wealth for later comparison."""
        self.memory.observe_neighbor(neighbor_id, neighbor_wealth)

    def imitate(
        self,
        target: YardSaleAgent,
        noise: float = 0.01,
        rng: Any = None,
    ) -> None:
        """Copy behavioral parameters from a target agent with Gaussian noise.

        Noise prevents behavioral collapse — without it, all agents would
        converge to identical strategies.

        Args:
            target: The agent to imitate.
            noise: Std dev of Gaussian noise added to copied parameters.
            rng: Numpy random Generator.
        """
        if rng is not None:
            self.savings_rate = max(0.001, min(1.0, target.savings_rate + rng.normal(0, noise)))
            self.risk_tolerance = max(-1.0, min(1.0, target.risk_tolerance + rng.normal(0, noise)))
        else:
            import random
            self.savings_rate = max(0.001, min(1.0, target.savings_rate + random.gauss(0, noise)))
            self.risk_tolerance = max(-1.0, min(1.0, target.risk_tolerance + random.gauss(0, noise)))

    def record_params_to_memory(self) -> None:
        """Store current behavioral parameters in memory history."""
        self.memory.record_params(self.savings_rate, self.risk_tolerance)
