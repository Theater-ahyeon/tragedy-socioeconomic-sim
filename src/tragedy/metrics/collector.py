"""MetricCollector — bridges simulation state to storage and streaming.

The collector runs at the METRICS stage of each tick (or every Nth tick
as configured). It extracts current agent state, computes aggregate
statistics, and makes them available for database storage and WebSocket
broadcast.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from tragedy.metrics.inequality import gini_coefficient, lorenz_curve, pareto_alpha

logger = logging.getLogger(__name__)


@dataclass
class MetricCollector:
    """Collects and aggregates economic metrics from simulation state.

    The collector is model-agnostic — it inspects agent attributes
    to determine what metrics can be computed.

    Usage:
        collector = MetricCollector()
        snapshot = collector.collect(engine)
        # snapshot can be stored to DB or broadcast via WebSocket
    """

    # Accumulated time series
    series: dict[str, list[float]] = field(default_factory=dict)
    ticks: list[int] = field(default_factory=list)

    def collect(self, engine: Any, collect_every: int = 1) -> dict[str, Any] | None:
        """Collect metrics for the current tick.

        Args:
            engine: The SimulationEngine instance.
            collect_every: Only collect every Nth tick.

        Returns:
            A snapshot dict suitable for serialization, or None if skipped.
        """
        if engine.tick % collect_every != 0:
            return None

        agents = list(engine.agents)
        if not agents:
            return None

        self.ticks.append(engine.tick)

        snapshot: dict[str, Any] = {
            "tick": engine.tick,
            "agent_count": len(agents),
            "metrics": {},
        }

        # Extract wealth array if agents have wealth
        wealth_values = [
            a.attributes.get("wealth", getattr(a, "wealth", 0.0))
            for a in agents
        ]
        wealth = np.array(wealth_values, dtype=np.float64)

        if len(wealth) > 0 and np.sum(wealth) > 0:
            # Inequality metrics
            gini = float(gini_coefficient(wealth))
            snapshot["metrics"]["gini"] = gini
            self._record("gini", gini)

            # Pareto alpha
            alpha = float(pareto_alpha(wealth))
            if not np.isnan(alpha):
                snapshot["metrics"]["pareto_alpha"] = alpha
                self._record("pareto_alpha", alpha)

            # Distribution stats
            snapshot["metrics"]["total_wealth"] = float(np.sum(wealth))
            snapshot["metrics"]["mean_wealth"] = float(np.mean(wealth))
            snapshot["metrics"]["median_wealth"] = float(np.median(wealth))
            snapshot["metrics"]["min_wealth"] = float(np.min(wealth))
            snapshot["metrics"]["max_wealth"] = float(np.max(wealth))

            self._record("total_wealth", snapshot["metrics"]["total_wealth"])
            self._record("mean_wealth", snapshot["metrics"]["mean_wealth"])
            self._record("median_wealth", snapshot["metrics"]["median_wealth"])

            # Top shares
            sorted_w = np.sort(wealth)[::-1]
            total_w = float(np.sum(sorted_w))
            n = len(wealth)
            top1 = float(np.sum(sorted_w[: max(1, n // 100)]) / total_w)
            top10 = float(np.sum(sorted_w[: max(1, n // 10)]) / total_w)
            bottom50 = float(np.sum(sorted_w[n // 2 :]) / total_w)
            snapshot["metrics"]["top_1_pct_share"] = top1
            snapshot["metrics"]["top_10_pct_share"] = top10
            snapshot["metrics"]["bottom_50_pct_share"] = bottom50
            self._record("top_1_pct_share", top1)
            self._record("top_10_pct_share", top10)
            self._record("bottom_50_pct_share", bottom50)

            # Lorenz curve data (for frontend rendering)
            pop, wel = lorenz_curve(wealth, n_points=50)
            snapshot["lorenz"] = {
                "population": pop.tolist(),
                "wealth": wel.tolist(),
            }

            # Distribution histogram
            if np.max(wealth) > 0:
                # Log-scale bins for the long tail
                log_min = max(0, np.log10(max(np.min(wealth), 1e-10)))
                log_max = np.log10(max(np.max(wealth), 1.0))
                bins = np.logspace(log_min, log_max, 50)
                hist, edges = np.histogram(wealth, bins=bins)
                snapshot["distribution"] = {
                    "bins": edges.tolist(),
                    "counts": hist.tolist(),
                }

        return snapshot

    def _record(self, name: str, value: float) -> None:
        """Record a scalar metric."""
        if name not in self.series:
            self.series[name] = []
        self.series[name].append(value)

    def to_dataframe(self):
        """Convert collected time series to a pandas DataFrame."""
        import pandas as pd

        data = {"tick": self.ticks}
        data.update(self.series)
        return pd.DataFrame(data)

    def reset(self) -> None:
        """Clear all collected data."""
        self.series.clear()
        self.ticks.clear()
