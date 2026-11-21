"""Calculations and filtering. Pure functions: no I/O, no printing.

Everything here uses Decimal. `sum()` is always given a Decimal start value so
an empty sequence yields Decimal("0.00") rather than the int 0.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict
from decimal import Decimal
from typing import Iterable, NamedTuple

from models import ZERO, Transaction, TransactionType, normalize_category

Transactions = Iterable[Transaction]


class MonthTotals(NamedTuple):
    income: Decimal
    expenses: Decimal

    @property
    def net(self) -> Decimal:
        return self.income - self.expenses


# --------------------------------------------------------------------------- #
# Filtering
# --------------------------------------------------------------------------- #
def filter_transactions(
    transactions: Transactions,
    *,
    category: str | None = None,
    tx_type: TransactionType | None = None,
    start: dt.date | None = None,
    end: dt.date | None = None,
) -> list[Transaction]:
    """Return records matching ALL given criteria (None = don't filter on it).

    Category matching is case-insensitive; `start` and `end` are inclusive.
    """
    wanted = normalize_category(category).casefold() if category else None
    result = []
    for t in transactions:
        if wanted and t.category.casefold() != wanted:
            continue
        if tx_type and t.type is not tx_type:
            continue
        if start and t.date < start:
            continue
        if end and t.date > end:
            continue
        result.append(t)
    return result


def list_categories(transactions: Transactions) -> list[str]:
    """Sorted unique category names."""
    return sorted({t.category for t in transactions})


# --------------------------------------------------------------------------- #
# Totals
# --------------------------------------------------------------------------- #
def total(transactions: Transactions, tx_type: TransactionType) -> Decimal:
    """Sum of all amounts of one type."""
    return sum((t.amount for t in transactions if t.type is tx_type), ZERO)


def balance(transactions: Transactions) -> Decimal:
    """Income minus expenses."""
    return sum((t.signed_amount for t in transactions), ZERO)


def totals_by_category(transactions: Transactions, tx_type: TransactionType) -> dict[str, Decimal]:
    """Category -> total for one type, largest first."""
    sums: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for t in transactions:
        if t.type is tx_type:
            sums[t.category] += t.amount
    return dict(sorted(sums.items(), key=lambda kv: kv[1], reverse=True))


def monthly_summary(transactions: Transactions) -> dict[str, MonthTotals]:
    """'YYYY-MM' -> (income, expenses), in chronological order."""
    income: dict[str, Decimal] = defaultdict(lambda: ZERO)
    expenses: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for t in transactions:
        bucket = income if t.type is TransactionType.INCOME else expenses
        bucket[f"{t.date:%Y-%m}"] += t.amount
    months = sorted(set(income) | set(expenses))  # built before any default lookups
    return {m: MonthTotals(income[m], expenses[m]) for m in months}


def balance_history(transactions: Transactions) -> list[tuple[dt.date, Decimal]]:
    """Running balance at the end of each day that has activity."""
    history: list[tuple[dt.date, Decimal]] = []
    running = ZERO
    for t in sorted(transactions, key=lambda t: (t.date, t.id)):
        running += t.signed_amount
        if history and history[-1][0] == t.date:
            history[-1] = (t.date, running)
        else:
            history.append((t.date, running))
    return history
