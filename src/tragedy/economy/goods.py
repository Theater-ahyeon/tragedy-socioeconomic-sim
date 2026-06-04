"""Goods, inventories, and production functions for economic models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class GoodCategory(Enum):
    CONSUMPTION = "consumption"
    CAPITAL = "capital"
    INTERMEDIATE = "intermediate"


@dataclass
class Good:
    """A type of good in the economy."""

    name: str
    category: GoodCategory = GoodCategory.CONSUMPTION
    durability: float = 1.0  # Fraction remaining after one tick (1.0 = non-perishable)
    substitutability: float = 0.5  # Elasticity vs alternatives (0 = unique, 1 = perfect substitute)

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Good):
            return NotImplemented
        return self.name == other.name


@dataclass
class ProductionFunction:
    """Maps input goods to an output good.

    Supports Leontief (fixed proportions), Cobb-Douglas, and CES forms.
    For Phase 1, uses simple linear production.
    """

    inputs: dict[str, float]  # Good name -> quantity coefficient
    output: str  # Output good name
    productivity: float = 1.0  # Total factor productivity
    returns_to_scale: Literal["constant", "increasing", "decreasing"] = "constant"

    def produce(self, input_quantities: dict[str, float]) -> float:
        """Compute output quantity given input quantities.

        Simple linear production for Phase 1.
        """
        # Leontief: output = productivity * min(input_qty[i] / coeff[i])
        ratios = []
        for good_name, coeff in self.inputs.items():
            if coeff == 0:
                continue
            qty = input_quantities.get(good_name, 0.0)
            ratios.append(qty / coeff)
        if not ratios:
            return 0.0
        min_ratio = min(ratios)
        output = self.productivity * min_ratio
        if self.returns_to_scale == "increasing":
            output = output**1.1
        elif self.returns_to_scale == "decreasing":
            output = output**0.9
        return output


@dataclass
class Inventory:
    """Stock of goods held by an agent (firm or household)."""

    holdings: dict[str, float] = field(default_factory=dict)
    capacity: float = float("inf")

    def add(self, good_name: str, quantity: float) -> None:
        """Add goods to inventory."""
        current = self.holdings.get(good_name, 0.0)
        self.holdings[good_name] = min(current + quantity, self.capacity)

    def remove(self, good_name: str, quantity: float) -> float:
        """Remove goods from inventory. Returns actual amount removed."""
        current = self.holdings.get(good_name, 0.0)
        removed = min(current, quantity)
        if removed > 0:
            self.holdings[good_name] = current - removed
        return removed

    def total(self) -> float:
        """Total quantity of all goods."""
        return sum(self.holdings.values())

    def has(self, good_name: str, quantity: float = 0.0) -> bool:
        """Check if inventory has at least the given quantity."""
        return self.holdings.get(good_name, 0.0) >= quantity
