"""Market abstractions for economic matching.

Markets are where agents interact: buyers and sellers are matched according
to a mechanism, and transactions are generated as a result.

Market types:
- BilateralMarket: Random pairwise matching (Yard-Sale transfer)
- PostedPriceMarket: Sellers post prices, buyers choose best deal
- AuctionMarket: Double auction / Walrasian tatonnement
- BargainingMarket: Bilateral negotiation with outside options (labor)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MarketType(Enum):
    BILATERAL = "bilateral"
    POSTED_PRICE = "posted_price"
    AUCTION = "auction"
    BARGAINING = "bargaining"


@dataclass
class Market(ABC):
    """Abstract market with a matching mechanism.

    Args:
        name: Unique market identifier.
        good: The good being traded (None for labor/credit markets).
        mechanism_type: The type of matching mechanism used.
    """

    name: str
    good: str | None = None
    mechanism_type: MarketType = MarketType.BILATERAL

    @abstractmethod
    def match(
        self,
        buyers: Any,  # AgentSet
        sellers: Any,  # AgentSet
        rng: Any,  # numpy Generator
        **kwargs: Any,
    ) -> list[Any]:  # list[Transaction]
        """Match buyers and sellers, returning a list of transactions."""
        ...


class BilateralMarket(Market):
    """Random pairwise matching — used for Yard-Sale wealth transfers.

    Agents are randomly paired. In each pair, a transfer occurs based on
    the mechanism rules (e.g., fraction of poorer agent's wealth).
    """

    def __init__(
        self,
        name: str = "bilateral",
        transfer_fn: Callable[[Any, Any, Any], tuple[float, float]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, mechanism_type=MarketType.BILATERAL, **kwargs)
        self.transfer_fn = transfer_fn

    def match(
        self,
        buyers: Any,
        sellers: Any,
        rng: Any,
        **kwargs: Any,
    ) -> list[Any]:
        """Match agents into random pairs and execute transfers.

        For Yard-Sale, buyers and sellers are the same AgentSet (or sellers
        is None). Agents are shuffled and paired.
        """
        # In Yard-Sale, all agents participate from one pool
        agents = list(buyers)
        rng.shuffle(agents)
        if len(agents) % 2 != 0:
            agents.pop()  # Drop the last unpaired agent

        transactions = []
        for i in range(0, len(agents), 2):
            a1, a2 = agents[i], agents[i + 1]
            if self.transfer_fn:
                delta1, delta2 = self.transfer_fn(a1, a2, rng)
                a1.attributes["wealth"] = a1.attributes.get("wealth", 0.0) + delta1
                a2.attributes["wealth"] = a2.attributes.get("wealth", 0.0) + delta2

        return transactions


class PostedPriceMarket(Market):
    """Sellers post prices, buyers choose the best option.

    Used for consumption goods markets. Firms set prices; households
    search across firms and buy from the cheapest (with noise for
    bounded rationality).
    """

    def __init__(self, name: str = "goods", good: str | None = None) -> None:
        super().__init__(name=name, good=good, mechanism_type=MarketType.POSTED_PRICE)

    def match(
        self,
        buyers: Any,
        sellers: Any,
        rng: Any,
        **kwargs: Any,
    ) -> list[Any]:
        """Match each buyer to a seller based on posted prices."""
        # Phase 3 implementation
        return []


class BargainingMarket(Market):
    """Bilateral bargaining with outside options — used for labor markets.

    Workers and firms negotiate wages. Workers have a reservation wage;
    firms have a maximum willingness to pay. The outcome depends on
    relative bargaining power.
    """

    def __init__(self, name: str = "labor") -> None:
        super().__init__(name=name, mechanism_type=MarketType.BARGAINING)

    def match(
        self,
        buyers: Any,
        sellers: Any,
        rng: Any,
        **kwargs: Any,
    ) -> list[Any]:
        """Match workers to firms with wage bargaining."""
        # Phase 3 implementation
        return []
