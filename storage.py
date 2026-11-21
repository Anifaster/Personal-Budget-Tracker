"""Persistence layer: saves/loads transactions as JSON.

Amounts are stored as strings (e.g. "12.50") so Decimal precision survives
the round trip. Writes are atomic (temp file + rename), so a crash or power
loss mid-save can never leave a half-written data file behind.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from models import Transaction, ValidationError

SCHEMA_VERSION = 1


class StorageError(Exception):
    """Raised when the data file cannot be read or written."""


class JsonStorage:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> list[Transaction]:
        """Return all saved transactions ([] if the file doesn't exist yet)."""
        if not self.path.exists():
            return []
        try:
            with open(self.path, encoding="utf-8") as fh:
                payload = json.load(fh)
            records = payload["transactions"]
            transactions = [Transaction.from_dict(r) for r in records]
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValidationError) as exc:
            raise StorageError(f"Could not read '{self.path}': {exc}") from exc

        ids = [t.id for t in transactions]
        if len(ids) != len(set(ids)):
            raise StorageError(f"'{self.path}' contains duplicate record IDs.")
        return transactions

    def save(self, transactions: list[Transaction]) -> None:
        """Atomically write all transactions to disk."""
        payload = {
            "version": SCHEMA_VERSION,
            "transactions": [t.to_dict() for t in transactions],
        }
        tmp_name = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(
                dir=self.path.parent, prefix=self.path.name + ".", suffix=".tmp"
            )
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2, ensure_ascii=False)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_name, self.path)  # atomic on the same filesystem
        except OSError as exc:
            if tmp_name:
                Path(tmp_name).unlink(missing_ok=True)
            raise StorageError(f"Could not save '{self.path}': {exc}") from exc
