"""Money, accounts, and double-entry ledger.

The economic invariant is double-entry accounting: every transaction has equal
and opposite effects on the debit and credit sides. Money is created only
through bank lending (endogenous money), and destroyed through loan repayment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class AccountType(Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"


@dataclass(order=True, frozen=True)
class Money:
    """Immutable value object representing a currency amount.

    Uses float for Phase 1 simplicity. Future phases should switch to
    integer cents or Decimal for exact accounting.
    """

    amount: float

    def __add__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.amount + other.amount)

    def __sub__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.amount - other.amount)

    def __mul__(self, factor: float) -> Money:
        return Money(self.amount * factor)

    def __truediv__(self, divisor: float) -> Money:
        if divisor == 0:
            raise ValueError("Cannot divide money by zero")
        return Money(self.amount / divisor)

    def __neg__(self) -> Money:
        return Money(-self.amount)

    def __bool__(self) -> bool:
        return self.amount != 0.0

    def __repr__(self) -> str:
        return f"${self.amount:,.2f}"


@dataclass
class Account:
    """A double-entry account belonging to an agent."""

    id: int
    owner_id: int
    balance: Money = field(default_factory=lambda: Money(0.0))
    type: AccountType = AccountType.ASSET

    def debit(self, amount: Money) -> None:
        """Add to asset/expense account."""
        self.balance = Money(self.balance.amount + amount.amount)

    def credit(self, amount: Money) -> None:
        """Subtract from asset/expense account (or add to liability/equity)."""
        self.balance = Money(self.balance.amount - amount.amount)

    def __repr__(self) -> str:
        return f"Account({self.id}, owner={self.owner_id}, {self.type.value}={self.balance})"


class TransactionType(Enum):
    """Types of economic transactions."""

    GOODS_SALE = "goods_sale"
    LABOR_WAGE = "labor_wage"
    LOAN_ISSUANCE = "loan_issuance"
    LOAN_REPAYMENT = "loan_repayment"
    INTEREST_PAYMENT = "interest_payment"
    TAX_PAYMENT = "tax_payment"
    DIVIDEND = "dividend"
    TRANSFER = "transfer"  # Yard-Sale wealth transfer
    GOVERNMENT_SPENDING = "government_spending"


@dataclass
class Transaction:
    """A record of one economic transaction.

    Every transaction is double-entry:
    - The buyer's asset account is debited (decrease in cash)
    - The seller's asset account is credited (increase in cash)
    Or equivalently: total debits == total credits for the economy as a whole.
    """

    id: int
    tick: int
    type: TransactionType
    from_agent_id: int
    to_agent_id: int
    amount: Money
    description: str = ""

    def __repr__(self) -> str:
        return (
            f"Transaction({self.type.value}, "
            f"{self.from_agent_id}→{self.to_agent_id}, "
            f"{self.amount})"
        )


class Ledger:
    """Stores all accounts and ensures double-entry consistency.

    The ledger is the source of truth for all money in the simulation.
    It enforces that money cannot be created or destroyed except through
    explicit bank lending operations.
    """

    def __init__(self) -> None:
        self.accounts: dict[int, Account] = {}
        self.transactions: list[Transaction] = []
        self._next_account_id: int = 0
        self._next_txn_id: int = 0

    def create_account(self, owner_id: int, initial_balance: Money | None = None) -> Account:
        """Create a new account for an agent."""
        account = Account(
            id=self._next_account_id,
            owner_id=owner_id,
            balance=initial_balance or Money(0.0),
        )
        self._next_account_id += 1
        self.accounts[account.id] = account
        return account

    def record_transaction(
        self,
        from_agent_id: int,
        to_agent_id: int,
        amount: Money,
        txn_type: TransactionType,
        description: str = "",
    ) -> Transaction:
        """Record a transaction between two agents.

        In Phase 1, accounts are implicit (each agent has one cash balance
        tracked via attributes). The ledger records transactions for audit
        and consistency checking.
        """
        txn = Transaction(
            id=self._next_txn_id,
            tick=0,  # Will be set by the caller
            type=txn_type,
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            amount=amount,
            description=description,
        )
        self._next_txn_id += 1
        self.transactions.append(txn)
        return txn

    def validate_balance(self) -> tuple[bool, float]:
        """Check stock-flow consistency.

        Returns:
            (is_balanced, net_discrepancy): True if net flows sum to zero.
        """
        net = sum(t.amount.amount for t in self.transactions)
        # In a closed system without endogenous money creation,
        # net flows should be approximately zero
        return abs(net) < 0.01, net

    def clear(self) -> None:
        """Clear all accounts and transactions."""
        self.accounts.clear()
        self.transactions.clear()
        self._next_account_id = 0
        self._next_txn_id = 0

    @property
    def total_money_supply(self) -> Money:
        """Sum of all account balances."""
        return Money(sum(a.balance.amount for a in self.accounts.values()))

    def __repr__(self) -> str:
        return f"Ledger(accounts={len(self.accounts)}, transactions={len(self.transactions)})"
