"""Yard-Sale model — pairwise random wealth transfer.

The canonical agent-based model of wealth inequality emergence. Agents are
randomly paired each tick; a fraction of the poorer agent's wealth is
transferred based on a (potentially biased) coin toss.

Despite its simplicity, the Yard-Sale model reproduces key empirical
features of wealth distributions:
- Monotonically increasing Gini coefficient
- Pareto power-law tail (top ~5%)
- Wealth condensation without any production or consumption

Reference:
    Yakovenko, V. M., & Rosser, J. B. (2009). "Statistical mechanics of
    money, wealth, and income." Reviews of Modern Physics, 81(4), 1703.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np

from tragedy.agents.household import YardSaleAgent
from tragedy.core.engine import SimulationEngine
from tragedy.core.scheduler import SimulationStage, YARD_SALE_STAGES
from tragedy.metrics.inequality import gini_coefficient, lorenz_curve
from tragedy.models.base import BaseModel

logger = logging.getLogger(__name__)


@dataclass
class YardSaleModel(BaseModel):
    """Yard-Sale wealth transfer simulation model.

    Configuration:
        num_agents: Number of agents in the simulation.
        initial_wealth: Starting wealth for each agent.
        transfer_fraction: Fraction of poorer agent's wealth transferred each pairing.
        transfer_bias: Bias in favor of richer agent (-1 to 1, 0 = fair).
        collect_every: Collect metrics every N ticks.

    Typical results (1000 agents, 5% transfer, 0 bias, 5000 ticks):
        - Gini coefficient: 0.0 → ~0.85
        - Top 1% wealth share: ~40%
        - Pareto tail index α: ~1.5
    """

    name: str = "yard_sale"
    num_agents: int = 1000
    initial_wealth: float = 100.0
    transfer_fraction: float = 0.05
    transfer_bias: float = 0.0
    collect_every: int = 1

    # Internals
    stages: list[SimulationStage] = field(
        default_factory=lambda: list(YARD_SALE_STAGES)
    )

    def _create_agents(self) -> None:
        """Create N YardSaleAgent instances with equal initial wealth."""
        if self.engine is None:
            raise RuntimeError("Engine not set — call setup() first")

        for i in range(self.num_agents):
            agent = YardSaleAgent(
                agent_id=self.engine._next_agent_id,
                agent_type="YardSaleAgent",
                creation_tick=self.engine.tick,
                wealth=self.initial_wealth,
            )
            self.engine._next_agent_id += 1
            self.engine.agents.add(agent)

        # Store initial total for conservation checks
        self._initial_total_wealth = self.num_agents * self.initial_wealth
        logger.info(
            "Created %d agents with total wealth %.2f",
            self.num_agents,
            self._initial_total_wealth,
        )

    def _register_stages(self) -> None:
        """Register the transfer stage and metrics stage handlers."""
        if self.engine is None:
            raise RuntimeError("Engine not set")

        self.engine.register_stage(
            SimulationStage.CONSUMPTION,
            self._transfer_stage,
        )
        self.engine.register_stage(
            SimulationStage.ACCOUNTING,
            self._accounting_stage,
        )
        self.engine.register_stage(
            SimulationStage.METRICS,
            self._metrics_stage,
        )

    # ── Stage Handlers ───────────────────────────────────────────

    def _transfer_stage(self, engine: SimulationEngine) -> None:
        """Execute pairwise wealth transfers.

        At each tick, all agents are shuffled and paired. Each pair
        transfers a fraction of the poorer agent's wealth based on
        a biased coin toss.
        """
        agents = list(engine.agents)
        engine.rng.master_rng.shuffle(agents)
        if len(agents) % 2 != 0:
            agents.pop()

        fraction = self.transfer_fraction
        bias = self.transfer_bias

        for i in range(0, len(agents), 2):
            a1, a2 = agents[i], agents[i + 1]
            if not isinstance(a1, YardSaleAgent) or not isinstance(a2, YardSaleAgent):
                continue
            rng = engine.rng.agent_rng(a1.id)
            a1.participate_in_transfer(a2, fraction, bias, rng)

    def _accounting_stage(self, engine: SimulationEngine) -> None:
        """Check wealth conservation and clean up bankrupt agents."""
        # Verify wealth conservation
        current_total = sum(
            a.wealth
            for a in engine.agents
            if isinstance(a, YardSaleAgent)
        )
        drift = abs(current_total - self._initial_total_wealth)
        if drift > 0.01:
            logger.warning(
                "Wealth conservation drift: %.6f at tick %d",
                drift,
                engine.tick,
            )

        # Remove agents with zero or negative wealth (optional)
        # In the classic Yard-Sale, agents never go negative
        for agent in list(engine.agents):
            if isinstance(agent, YardSaleAgent) and agent.wealth <= 0:
                agent.wealth = 1e-10  # Minimum wealth floor

    def _metrics_stage(self, engine: SimulationEngine) -> None:
        """Collect inequality metrics for the current tick."""
        if engine.tick % self.collect_every != 0:
            return

        wealth = np.array(
            [a.wealth for a in engine.agents if isinstance(a, YardSaleAgent)],
            dtype=np.float64,
        )

        if len(wealth) == 0:
            return

        gini = gini_coefficient(wealth)
        engine.record_metric("gini", gini)
        engine.record_metric("total_wealth", float(np.sum(wealth)))
        engine.record_metric("mean_wealth", float(np.mean(wealth)))
        engine.record_metric("median_wealth", float(np.median(wealth)))
        engine.record_metric("min_wealth", float(np.min(wealth)))
        engine.record_metric("max_wealth", float(np.max(wealth)))

        # Top shares
        sorted_wealth = np.sort(wealth)[::-1]
        total_w = float(np.sum(sorted_wealth))
        if total_w > 0:
            engine.record_metric("top_1_pct_share",
                                float(np.sum(sorted_wealth[: max(1, len(wealth) // 100)]) / total_w))
            engine.record_metric("top_10_pct_share",
                                float(np.sum(sorted_wealth[: max(1, len(wealth) // 10)]) / total_w))
            engine.record_metric("bottom_50_pct_share",
                                float(np.sum(sorted_wealth[len(wealth) // 2 :]) / total_w))
