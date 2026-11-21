"""Ledger: the in-memory collection of transactions (add / remove).

Knows nothing about files or the UI; it only guarantees that every record it
holds is valid and has a unique ID.
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Iterable

from models import (
    Transaction,
    TransactionType,
    ValidationError,
    normalize_category,
    parse_amount,
)


def _order(t: Transaction) -> tuple[dt.date, int]:
    return (t.date, t.id)


class Ledger:
    def __init__(self, transactions: Iterable[Transaction] = ()):
        self._items: list[Transaction] = sorted(transactions, key=_order)

    @property
    def transactions(self) -> list[Transaction]:
        """A copy of all records, sorted by date then ID."""
        return list(self._items)

    def add(
        self,
        tx_type: TransactionType,
        amount: str | Decimal,
        category: str,
        date: dt.date,
        description: str = "",
    ) -> Transaction:
        """Validate and add a new record (income adds, expense subtracts)."""
        next_id = max((t.id for t in self._items), default=0) + 1
        tx = Transaction(
            id=next_id,
            date=date,
            type=tx_type,
            category=normalize_category(category),
            amount=parse_amount(amount),
            description=description.strip(),
        )
        self._items.append(tx)
        self._items.sort(key=_order)
        return tx

    def remove(self, tx_id: int) -> Transaction:
        """Delete a record by ID and return it."""
        for i, tx in enumerate(self._items):
            if tx.id == tx_id:
                return self._items.pop(i)
        raise ValidationError(f"No record with ID {tx_id}.")
