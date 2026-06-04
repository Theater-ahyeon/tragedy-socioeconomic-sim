"""Metrics collection and analysis for economic simulations."""

from tragedy.metrics.collector import MetricCollector
from tragedy.metrics.inequality import gini_coefficient, lorenz_curve, pareto_alpha

__all__ = [
    "MetricCollector",
    "gini_coefficient",
    "lorenz_curve",
    "pareto_alpha",
]
