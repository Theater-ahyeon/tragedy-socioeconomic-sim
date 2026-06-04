"""Economy layer — economic primitives for agent-based models."""

from tragedy.economy.accounting import check_double_entry, check_wealth_conservation, compute_balance_sheet
from tragedy.economy.goods import Good, GoodCategory, Inventory, ProductionFunction
from tragedy.economy.markets import (
    BargainingMarket,
    BilateralMarket,
    Market,
    MarketType,
    PostedPriceMarket,
)
from tragedy.economy.money import (
    Account,
    AccountType,
    Ledger,
    Money,
    Transaction,
    TransactionType,
)

__all__ = [
    # Money & Accounting
    "Money",
    "Account",
    "AccountType",
    "Ledger",
    "Transaction",
    "TransactionType",
    # Goods & Production
    "Good",
    "GoodCategory",
    "Inventory",
    "ProductionFunction",
    # Markets
    "Market",
    "MarketType",
    "BilateralMarket",
    "PostedPriceMarket",
    "BargainingMarket",
    # Consistency
    "check_double_entry",
    "check_wealth_conservation",
    "compute_balance_sheet",
]
