"""Yard-Sale wealth transfer model with multi-agent collaboration.

Phase 1.5 enhancements:
- Network-constrained trading (Watts-Strogatz small-world) instead of random global pairing
- Heterogeneous strategies: each agent has personal savings_rate and risk_tolerance
- AgentMemory: long-term tracking of trades, wealth, and neighbor observations
- Imitation learning: agents copy successful neighbors' strategies with noise
- Extended metrics: network topology, strategy diversity, memory-derived stats

Reference:
    Yakovenko, V. M., & Rosser, J. B. (2009). "Statistical mechanics of
    money, wealth, and income." Reviews of Modern Physics, 81(4), 1703.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from tragedy.agents.household import YardSaleAgent
from tragedy.core.engine import SimulationEngine
from tragedy.core.scheduler import SimulationStage, YARD_SALE_STAGES
from tragedy.core.space import Network
from tragedy.metrics.inequality import gini_coefficient, lorenz_curve
from tragedy.models.base import BaseModel

logger = logging.getLogger(__name__)


@dataclass
class YardSaleModel(BaseModel):
    """Yard-Sale wealth transfer model with multi-agent collaboration.

    Configuration:
        num_agents: Number of agents.
        initial_wealth: Starting wealth per agent.
        collect_every: Collect metrics every N ticks.

    # Network interaction (Phase 1.5)
        network_type: "random_global" or "watts_strogatz"
        ws_k: Watts-Strogatz neighbor count (even, >= 2).
        ws_p: Watts-Strogatz rewiring probability.
        trades_per_tick: How many distinct neighbors each agent trades with.

    # Heterogeneous strategies (Phase 1.5)
        heterogeneous_strategy: If True, agents have personal parameters.
        savings_rate_mean / std: Distribution of transfer fractions.
        risk_tolerance_mean / std: Distribution of coin biases.

    # Imitation learning (Phase 1.5)
        imitation_enabled: Enable strategy copying.
        imitation_interval: Imitate every N ticks.
        imitation_probability: Chance of copying per agent.
        imitation_noise: Gaussian noise on copied parameters.
    """

    name: str = "yard_sale"

    # Agent configuration
    num_agents: int = 1000
    initial_wealth: float = 100.0
    collect_every: int = 1

    # Backward-compatible aliases (map to savings_rate_mean / risk_tolerance_mean)
    transfer_fraction: float | None = None
    transfer_bias: float | None = None

    # Network interaction
    network_type: str = "random_global"  # "random_global" | "watts_strogatz"
    ws_k: int = 4
    ws_p: float = 0.1
    trades_per_tick: int = 1

    # Heterogeneous strategies
    heterogeneous_strategy: bool = True
    savings_rate_mean: float = 0.05
    savings_rate_std: float = 0.02
    risk_tolerance_mean: float = 0.0
    risk_tolerance_std: float = 0.05

    # Imitation learning
    imitation_enabled: bool = True
    imitation_interval: int = 20
    imitation_probability: float = 0.3
    imitation_noise: float = 0.01

    # Internals
    stages: list[SimulationStage] = field(
        default_factory=lambda: list(YARD_SALE_STAGES)
    )
    _network: Network | None = None
    _agent_id_to_node: dict[int, int] = field(default_factory=dict)
    _node_id_to_agent: dict[int, int] = field(default_factory=dict)
    _traded_this_tick: set[int] = field(default_factory=set)
    _initial_total_wealth: float = 0.0

    def __post_init__(self) -> None:
        """Apply backward-compatible parameter aliases."""
        if self.transfer_fraction is not None:
            self.savings_rate_mean = self.transfer_fraction
            self.savings_rate_std = 0.0  # No variance with legacy API
        if self.transfer_bias is not None:
            self.risk_tolerance_mean = self.transfer_bias
            self.risk_tolerance_std = 0.0
        if self.transfer_fraction is not None or self.transfer_bias is not None:
            self.heterogeneous_strategy = False
            self.imitation_enabled = False

    # ── Setup ──────────────────────────────────────────────────

    def _create_agents(self) -> None:
        """Create agents with heterogeneous strategies and optional network."""
        if self.engine is None:
            raise RuntimeError("Engine not set — call setup() first")

        rng = self.engine.rng.master_rng

        for i in range(self.num_agents):
            # Initialize personal strategy parameters
            if self.heterogeneous_strategy:
                sr = max(0.001, min(1.0, rng.normal(self.savings_rate_mean, self.savings_rate_std)))
                rt = max(-1.0, min(1.0, rng.normal(self.risk_tolerance_mean, self.risk_tolerance_std)))
            else:
                sr = self.savings_rate_mean
                rt = self.risk_tolerance_mean

            agent = YardSaleAgent(
                agent_id=self.engine._next_agent_id,
                agent_type="YardSaleAgent",
                creation_tick=self.engine.tick,
                wealth=self.initial_wealth,
                savings_rate=sr,
                risk_tolerance=rt,
            )
            self.engine._next_agent_id += 1
            self.engine.agents.add(agent)

        self._initial_total_wealth = self.num_agents * self.initial_wealth
        logger.info(
            "Created %d agents with total wealth %.2f (heterogeneous=%s)",
            self.num_agents,
            self._initial_total_wealth,
            self.heterogeneous_strategy,
        )

        # Create social network if configured
        self._setup_network()

    def _setup_network(self) -> None:
        """Create the interaction network topology."""
        if self.network_type == "watts_strogatz":
            from tragedy.network.social import watts_strogatz_network

            rng = self.engine.rng.master_rng
            self._network = watts_strogatz_network(
                num_nodes=self.num_agents,
                k=self.ws_k,
                p=self.ws_p,
                rng=rng,
            )
            # Agent IDs map 1:1 to network nodes (both start from 0)
            for i in range(self.num_agents):
                self._agent_id_to_node[i] = i
                self._node_id_to_agent[i] = i
            logger.info(
                "Created Watts-Strogatz network: %d nodes, k=%d, p=%.2f, "
                "mean degree=%.1f",
                self.num_agents,
                self.ws_k,
                self.ws_p,
                np.mean([self._network.degree(n) for n in range(self._network.num_nodes)]),
            )
        else:
            self._network = None
            logger.info("Using random global pairing (no network)")

    def _register_stages(self) -> None:
        """Register all stage handlers."""
        if self.engine is None:
            raise RuntimeError("Engine not set")

        self.engine.register_stage(SimulationStage.CONSUMPTION, self._transfer_stage)
        if self.imitation_enabled:
            self.engine.register_stage(SimulationStage.STRATEGY_ADAPTATION, self._imitation_stage)
        self.engine.register_stage(SimulationStage.ACCOUNTING, self._accounting_stage)
        self.engine.register_stage(SimulationStage.METRICS, self._metrics_stage)

    # ── Transfer Stage ─────────────────────────────────────────

    def _transfer_stage(self, engine: SimulationEngine) -> None:
        """Execute pairwise wealth transfers.

        When a network is configured, agents trade with randomly selected
        network neighbors only. Otherwise, global random pairing is used.
        """
        if self._network is not None:
            self._network_transfer(engine)
        else:
            self._global_transfer(engine)

    def _global_transfer(self, engine: SimulationEngine) -> None:
        """Original random global pairing."""
        agents = list(engine.agents)
        engine.rng.master_rng.shuffle(agents)
        if len(agents) % 2 != 0:
            agents.pop()

        for i in range(0, len(agents), 2):
            a1, a2 = agents[i], agents[i + 1]
            if not isinstance(a1, YardSaleAgent) or not isinstance(a2, YardSaleAgent):
                continue
            wealth_before = a1.wealth
            rng = engine.rng.agent_rng(a1.id)
            gain = a1.participate_in_transfer(a2, rng=rng)
            a1.memory.record_trade(engine.tick, a2.id, gain, wealth_before)
            a2.memory.record_trade(engine.tick, a1.id, -gain, wealth_before)
            a1.observe_neighbor(a2.id, a2.wealth)
            a2.observe_neighbor(a1.id, a1.wealth)

    def _network_transfer(self, engine: SimulationEngine) -> None:
        """Network-constrained trading: agents trade with neighbors only."""
        self._traded_this_tick.clear()
        rng = engine.rng.master_rng

        for agent in engine.agents:
            if not isinstance(agent, YardSaleAgent):
                continue
            if agent.id in self._traded_this_tick:
                continue

            node = self._agent_id_to_node.get(agent.id)
            if node is None:
                continue

            neighbors = self._network.neighbors(node)
            if not neighbors:
                continue

            # Trade with up to trades_per_tick distinct neighbors
            n_trades = min(self.trades_per_tick, len(neighbors))
            chosen = list(rng.choice(neighbors, size=n_trades, replace=False))

            for chosen_node in chosen:
                partner_id = self._node_id_to_agent.get(int(chosen_node))
                if partner_id is None or partner_id in self._traded_this_tick:
                    continue
                partner = engine.agents.get(partner_id)
                if partner is None or not isinstance(partner, YardSaleAgent):
                    continue

                wealth_before = agent.wealth
                agent_rng = engine.rng.agent_rng(agent.id)
                gain = agent.participate_in_transfer(partner, rng=agent_rng)
                agent.memory.record_trade(engine.tick, partner.id, gain, wealth_before)
                partner.memory.record_trade(engine.tick, agent.id, -gain, wealth_before)

                # Mutual observation
                agent.observe_neighbor(partner.id, partner.wealth)
                partner.observe_neighbor(agent.id, agent.wealth)

                self._traded_this_tick.add(agent.id)
                self._traded_this_tick.add(partner.id)

    # ── Imitation Stage ────────────────────────────────────────

    def _imitation_stage(self, engine: SimulationEngine) -> None:
        """Observe neighbors and imitate the most successful one."""
        if engine.tick % self.imitation_interval != 0:
            return

        rng = engine.rng.master_rng

        for agent in engine.agents:
            if not isinstance(agent, YardSaleAgent):
                continue
            if rng.random() > self.imitation_probability:
                continue

            # Find the richest observed neighbor
            observations = agent.memory.last_observed_neighbors
            if not observations:
                continue

            richest_id = max(observations, key=observations.get)
            target = engine.agents.get(richest_id)
            if target is None or not isinstance(target, YardSaleAgent):
                continue

            # Imitate with noise
            agent_rng = engine.rng.agent_rng(agent.id)
            agent.imitate(target, noise=self.imitation_noise, rng=agent_rng)

        # Record params after imitation
        for agent in engine.agents:
            if isinstance(agent, YardSaleAgent):
                agent.record_params_to_memory()

    # ── Accounting Stage ───────────────────────────────────────

    def _accounting_stage(self, engine: SimulationEngine) -> None:
        """Check wealth conservation and clean up."""
        current_total = sum(
            a.wealth for a in engine.agents if isinstance(a, YardSaleAgent)
        )
        drift = abs(current_total - self._initial_total_wealth)
        if drift > 0.01:
            logger.warning(
                "Wealth conservation drift: %.6f at tick %d",
                drift,
                engine.tick,
            )

        # Minimum wealth floor
        for agent in engine.agents:
            if isinstance(agent, YardSaleAgent) and agent.wealth <= 0:
                agent.wealth = 1e-10

    # ── Metrics Stage ──────────────────────────────────────────

    def _metrics_stage(self, engine: SimulationEngine) -> None:
        """Collect all metrics including network and strategy stats."""
        if engine.tick % self.collect_every != 0:
            return

        wealth = np.array(
            [a.wealth for a in engine.agents if isinstance(a, YardSaleAgent)],
            dtype=np.float64,
        )
        if len(wealth) == 0:
            return

        # Core inequality metrics
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
        n = len(wealth)
        if total_w > 0:
            engine.record_metric("top_1_pct_share", float(np.sum(sorted_wealth[: max(1, n // 100)]) / total_w))
            engine.record_metric("top_10_pct_share", float(np.sum(sorted_wealth[: max(1, n // 10)]) / total_w))
            engine.record_metric("bottom_50_pct_share", float(np.sum(sorted_wealth[n // 2:]) / total_w))

        # Strategy diversity metrics
        if self.heterogeneous_strategy:
            sr = np.array([a.savings_rate for a in engine.agents if isinstance(a, YardSaleAgent)])
            rt = np.array([a.risk_tolerance for a in engine.agents if isinstance(a, YardSaleAgent)])
            engine.record_metric("mean_savings_rate", float(np.mean(sr)))
            engine.record_metric("std_savings_rate", float(np.std(sr)))
            engine.record_metric("mean_risk_tolerance", float(np.mean(rt)))
            engine.record_metric("std_risk_tolerance", float(np.std(rt)))

        # Memory-derived metrics
        win_rates = []
        volatilities = []
        for agent in engine.agents:
            if isinstance(agent, YardSaleAgent):
                win_rates.append(agent.memory.win_rate)
                volatilities.append(agent.memory.wealth_volatility)
        if win_rates:
            engine.record_metric("mean_win_rate", float(np.mean(win_rates)))
        if volatilities:
            engine.record_metric("mean_wealth_volatility", float(np.mean(volatilities)))

        # Network topology metrics
        if self._network is not None:
            from tragedy.network.social import compute_clustering_coefficient, compute_degree_gini

            degrees = [self._network.degree(n) for n in range(self._network.num_nodes)]
            engine.record_metric("network_mean_degree", float(np.mean(degrees)))
            engine.record_metric("network_clustering", compute_clustering_coefficient(self._network))
            engine.record_metric("network_degree_gini", compute_degree_gini(self._network))
