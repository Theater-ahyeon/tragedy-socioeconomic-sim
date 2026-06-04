"""Inequality metrics — Numba-accelerated computation.

All functions in this module are pure numeric operations on numpy arrays,
designed to be JIT-compiled via Numba for performance on large agent populations.

Metrics:
- Gini coefficient: 0 = perfect equality, 1 = total concentration
- Lorenz curve: cumulative wealth share vs cumulative population share
- Pareto alpha: Hill estimator for the power-law tail index
"""

from __future__ import annotations

import numpy as np

try:
    from numba import njit
    _HAS_NUMBA = True
except ImportError:
    # Fallback: njit is a no-op decorator
    def njit(fn=None, *args, **kwargs):
        if fn is None:
            return lambda f: f
        return fn
    _HAS_NUMBA = False


@njit
def gini_coefficient(wealth: np.ndarray) -> float:
    """Compute the Gini coefficient from a wealth array.

    G = 1 - (2 / (n-1)) * Σ(i=1..n) ((n - i) / (n - 1)) * w_i / Σw
    Or equivalently (more efficient):
    G = (2 * Σ(i * w_i) - (n+1) * Σw_i) / (n * Σw_i)

    Args:
        wealth: 1D array of agent wealth values (must be non-negative).

    Returns:
        Gini coefficient in [0, 1]. Returns 0 for empty or single-element arrays.
    """
    n = len(wealth)
    if n <= 1:
        return 0.0

    total = np.sum(wealth)
    if total <= 0:
        return 0.0

    sorted_w = np.sort(wealth)
    indices = np.arange(1, n + 1)
    numerator = 2.0 * np.sum(indices * sorted_w) - (n + 1.0) * total
    return numerator / (n * total)


@njit
def lorenz_curve(wealth: np.ndarray, n_points: int = 100) -> tuple[np.ndarray, np.ndarray]:
    """Compute Lorenz curve points for a wealth distribution.

    The Lorenz curve plots the cumulative wealth share (y-axis) against
    the cumulative population share (x-axis). Perfect equality is the
    45-degree line. The Gini coefficient equals 2 * area between the
    equality line and the Lorenz curve.

    Args:
        wealth: 1D array of agent wealth values.
        n_points: Number of points on the curve.

    Returns:
        (population_shares, wealth_shares): Two arrays of length n_points,
        each normalized to [0, 1].
    """
    n = len(wealth)
    if n == 0:
        return np.linspace(0, 1, n_points), np.linspace(0, 1, n_points)

    total = np.sum(wealth)
    if total <= 0:
        return np.linspace(0, 1, n_points), np.linspace(0, 1, n_points)

    sorted_w = np.sort(wealth)
    cumsum = np.cumsum(sorted_w)

    pop_shares = np.linspace(0, 1, n_points)
    wealth_shares = np.zeros(n_points)

    for i in range(n_points):
        idx = int(pop_shares[i] * (n - 1))
        if idx >= n - 1:
            wealth_shares[i] = 1.0
        else:
            wealth_shares[i] = cumsum[idx] / total

    # Ensure endpoints
    wealth_shares[0] = 0.0
    wealth_shares[-1] = 1.0

    return pop_shares, wealth_shares


@njit
def pareto_alpha(wealth: np.ndarray, tail_fraction: float = 0.05) -> float:
    """Estimate the Pareto (power-law) tail index via the Hill estimator.

    The top tail_fraction of the wealth distribution typically follows
    a Pareto distribution: P(W > w) ~ w^(-α). Lower α means more extreme
    inequality (fatter tail). Empirically, α is usually between 1 and 3.

    Hill estimator: α̂ = k / Σ(i=1..k) ln(x_(i) / x_(k+1))
    where x_(i) are the top k order statistics.

    Args:
        wealth: 1D array of agent wealth values.
        tail_fraction: Fraction of top observations to use (default 5%).

    Returns:
        Estimated Pareto tail index α. Returns NaN if insufficient data.
    """
    n = len(wealth)
    k = max(1, int(n * tail_fraction))
    if n < k + 1:
        return np.nan

    sorted_w = np.sort(wealth)[::-1]  # Descending
    if sorted_w[k] <= 0:
        return np.nan

    log_ratios = np.log(sorted_w[:k]) - np.log(sorted_w[k])
    sum_logs = np.sum(log_ratios)
    if sum_logs <= 0:
        return np.nan

    return k / sum_logs


def wealth_deciles(wealth: np.ndarray) -> dict[str, float]:
    """Compute wealth decile boundaries and shares.

    Args:
        wealth: 1D array of agent wealth values.

    Returns:
        Dict with keys like 'p10', 'p50', 'p90', 'p99' and
        shares like 'top_1_pct', 'top_10_pct', 'bottom_50_pct'.
    """
    n = len(wealth)
    if n == 0:
        return {}

    sorted_w = np.sort(wealth)
    total = float(np.sum(sorted_w))

    result = {}
    for pct in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
        idx = int(n * pct / 100)
        result[f"p{pct}"] = float(sorted_w[min(idx, n - 1)])

    if total > 0:
        result["top_1_pct_share"] = float(np.sum(sorted_w[-max(1, n // 100):]) / total)
        result["top_10_pct_share"] = float(np.sum(sorted_w[-max(1, n // 10):]) / total)
        result["bottom_50_pct_share"] = float(np.sum(sorted_w[: n // 2]) / total)

    return result
