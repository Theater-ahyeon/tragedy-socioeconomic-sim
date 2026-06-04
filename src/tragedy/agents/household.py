"""Household agent implementations.

Phase 1: YardSaleAgent — a simple wealth-holding agent for pairwise
wealth transfer simulations (the Yard-Sale model).
"""

from __future__ import annotations

from typing import Any

from tragedy.core.agent import Agent


class YardSaleAgent(Agent):
    """An agent in the Yard-Sale wealth transfer model.

    Each agent holds a single wealth attribute. During each simulation tick,
    agents are randomly paired and a fraction of the poorer agent's wealth
    is transferred. The direction (who wins) is determined by a biased coin.

    Key properties of the Yard-Sale model:
    - Total wealth is conserved (no production or consumption)
    - Multiplicative asymmetry drives wealth condensation
    - Gini coefficient increases monotonically toward 1.0
    - Wealth distribution develops a Pareto power-law tail

    Reference: Yakovenko & Rosser (2009), "Statistical mechanics of
    money, wealth, and income." Reviews of Modern Physics.
    """

    __slots__ = ("wealth",)

    def __init__(
        self,
        agent_id: int,
        agent_type: str = "YardSaleAgent",
        creation_tick: int = 0,
        wealth: float = 0.0,
    ) -> None:
        super().__init__(
            agent_id=agent_id,
            agent_type=agent_type,
            creation_tick=creation_tick,
        )
        self.wealth = wealth

    def participate_in_transfer(
        self,
        other: YardSaleAgent,
        fraction: float,
        bias: float,
        rng: Any = None,
    ) -> None:
        """Execute a pairwise wealth transfer with another agent.

        The poorer agent risks losing `fraction` of their wealth.
        The direction is determined by the biased coin:
        - bias = 0: fair coin (50/50 win chance)
        - bias > 0: richer agent has advantage
        - bias < 0: poorer agent has advantage

        Args:
            other: The paired agent.
            fraction: Fraction of the poorer agent's wealth to transfer.
            bias: Coin bias in favor of the richer agent (-1 to 1).
            rng: Numpy random Generator for reproducibility.
        """
        if self.wealth <= 0 and other.wealth <= 0:
            return

        # Identify poorer and richer agent
        poorer = self if self.wealth <= other.wealth else other
        richer = other if poorer is self else self

        transfer_amount = poorer.wealth * fraction
        if transfer_amount <= 0:
            return

        # Determine who wins: biased coin
        if rng is not None:
            coin = rng.random()
        else:
            import random
            coin = random.random()

        # Probability that the richer agent wins
        p_richer_wins = 0.5 + bias * 0.5

        if coin < p_richer_wins:
            # Richer agent wins the transfer
            poorer.wealth -= transfer_amount
            richer.wealth += transfer_amount
        else:
            # Poorer agent wins the transfer
            poorer.wealth += transfer_amount
            richer.wealth -= transfer_amount
