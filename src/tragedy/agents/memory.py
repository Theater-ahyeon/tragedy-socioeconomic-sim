"""Agent memory system for long-term state tracking and learning.

Each agent maintains a personal history of trades, wealth snapshots, and
behavioral parameter evolution. This enables:
- Imitation learning: identify which neighbors are most successful
- Strategy analysis: track how behavioral parameters evolve over time
- Network effects: observe and remember trading partners' outcomes
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TradeRecord:
    """A single trade event in an agent's memory."""

    tick: int
    partner_id: int
    amount: float  # positive = gain, negative = loss
    wealth_before: float
    wealth_after: float


@dataclass
class AgentMemory:
    """Personal history for one agent.

    Stores a ring-buffer of recent trades, wealth snapshots, and
    observations of neighbor wealth. Used by imitation learning to
    identify successful strategies.

    Attributes:
        agent_id: Owner agent ID.
        max_history: Maximum number of entries to retain per buffer.
        trade_log: Recent trade records (ring buffer).
        win_count / loss_count: Cumulative trade outcome counters.
        cumulative_gain / cumulative_loss: Total monetary outcomes.
        wealth_snapshots: Periodic wealth recordings.
        last_observed_neighbors: Neighbor ID → last known wealth.
        param_history: Strategy parameter evolution over time.
    """

    agent_id: int
    max_history: int = 1000

    # Trade records (ring buffer — oldest dropped when full)
    trade_log: list[TradeRecord] = field(default_factory=list)
    win_count: int = 0
    loss_count: int = 0
    cumulative_gain: float = 0.0
    cumulative_loss: float = 0.0

    # Wealth tracking
    wealth_snapshots: list[float] = field(default_factory=list)
    snapshot_interval: int = 10  # Record wealth every N ticks

    # Neighbor observation (for imitation)
    last_observed_neighbors: dict[int, float] = field(default_factory=dict)

    # Strategy parameter history
    param_history: dict[str, list[float]] = field(
        default_factory=lambda: {
            "savings_rate": [],
            "risk_tolerance": [],
        }
    )

    # ── Recording Methods ──────────────────────────────────────

    def record_trade(
        self,
        tick: int,
        partner_id: int,
        amount: float,
        wealth_before: float,
    ) -> None:
        """Record a completed trade in memory."""
        record = TradeRecord(
            tick=tick,
            partner_id=partner_id,
            amount=amount,
            wealth_before=wealth_before,
            wealth_after=wealth_before + amount,
        )
        self.trade_log.append(record)
        if len(self.trade_log) > self.max_history:
            self.trade_log = self.trade_log[-self.max_history:]

        if amount > 0:
            self.win_count += 1
            self.cumulative_gain += amount
        else:
            self.loss_count += 1
            self.cumulative_loss += abs(amount)

    def record_wealth_snapshot(self, tick: int, wealth: float) -> None:
        """Record a periodic wealth snapshot."""
        if tick % self.snapshot_interval == 0:
            self.wealth_snapshots.append(wealth)
            if len(self.wealth_snapshots) > self.max_history:
                self.wealth_snapshots = self.wealth_snapshots[-self.max_history:]

    def observe_neighbor(self, neighbor_id: int, neighbor_wealth: float) -> None:
        """Record a neighbor's current wealth for later comparison."""
        self.last_observed_neighbors[neighbor_id] = neighbor_wealth

    def record_params(self, savings_rate: float, risk_tolerance: float) -> None:
        """Record current behavioral parameters."""
        self.param_history["savings_rate"].append(savings_rate)
        self.param_history["risk_tolerance"].append(risk_tolerance)
        for key in self.param_history:
            if len(self.param_history[key]) > self.max_history:
                self.param_history[key] = self.param_history[key][-self.max_history:]

    # ── Analysis Methods ───────────────────────────────────────

    @property
    def total_trades(self) -> int:
        return self.win_count + self.loss_count

    @property
    def win_rate(self) -> float:
        total = self.total_trades
        return self.win_count / total if total > 0 else 0.0

    @property
    def net_gain(self) -> float:
        return self.cumulative_gain - self.cumulative_loss

    @property
    def wealth_volatility(self) -> float:
        """Standard deviation of wealth snapshots."""
        if len(self.wealth_snapshots) < 2:
            return 0.0
        mean = sum(self.wealth_snapshots) / len(self.wealth_snapshots)
        variance = sum((w - mean) ** 2 for w in self.wealth_snapshots) / len(self.wealth_snapshots)
        return variance**0.5
