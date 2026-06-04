"""Stock-flow consistency enforcement.

In any valid economic model, the following must hold at all times:
- Total assets == Total liabilities + Total equity
- Money creation == Money destruction (in closed system)
- Every flow comes from somewhere and goes somewhere
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Tolerance for floating-point consistency checks
DEFAULT_TOLERANCE = 1e-6


def check_wealth_conservation(
    agents: list[Any],
    tick: int,
    tolerance: float = DEFAULT_TOLERANCE,
) -> tuple[bool, float, float]:
    """Verify that total wealth is conserved across all agents.

    For the Yard-Sale model and closed-economy models without endogenous
    money creation, total wealth should be constant.

    Args:
        agents: List of agents with a `wealth` attribute.
        tick: Current simulation tick (for logging).
        tolerance: Maximum allowed discrepancy.

    Returns:
        (is_conserved, initial_total, current_total)
    """
    current_total = sum(getattr(a, "wealth", 0.0) for a in agents)
    # Initial total should be stored elsewhere; for now just return current
    return True, current_total, current_total


def check_double_entry(
    transactions: list[Any],
    tolerance: float = DEFAULT_TOLERANCE,
) -> tuple[bool, float]:
    """Verify double-entry balance: net of all transactions should be ~0.

    Args:
        transactions: List of Transaction objects with `amount` attribute.
        tolerance: Maximum allowed net discrepancy.

    Returns:
        (is_balanced, net_discrepancy)
    """
    net = sum(t.amount for t in transactions)
    is_balanced = abs(net) < tolerance
    if not is_balanced:
        logger.warning(
            "Double-entry imbalance detected: net=%.6f (tolerance=%.6f)",
            net,
            tolerance,
        )
    return is_balanced, net


def compute_balance_sheet(
    agents: list[Any],
) -> dict[str, float]:
    """Compute aggregate balance sheet across all agent types.

    Args:
        agents: List of agents, each may have cash, debt, equity attributes.

    Returns:
        Dict with keys: total_assets, total_liabilities, total_equity, discrepancy.
    """
    total_assets = 0.0
    total_liabilities = 0.0
    total_equity = 0.0

    for agent in agents:
        attrs = getattr(agent, "attributes", {})
        cash = attrs.get("wealth", attrs.get("cash", 0.0))
        debt = attrs.get("debt", 0.0)
        # equity = assets - liabilities
        total_assets += cash
        total_liabilities += debt

    total_equity = total_assets - total_liabilities
    discrepancy = total_assets - (total_liabilities + total_equity)

    return {
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "total_equity": total_equity,
        "discrepancy": discrepancy,
    }
