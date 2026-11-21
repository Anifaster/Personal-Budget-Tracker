"""Data model and input-parsing helpers.

All money values are `decimal.Decimal`, quantized to cents. Floats are never
used for stored or calculated amounts, so there are no binary rounding errors
(e.g. 0.1 + 0.2 == 0.3 holds exactly).
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

CENT = Decimal("0.01")
ZERO = Decimal("0.00")

_AMOUNT_RE = re.compile(r"[0-9]*\.?[0-9]+")
_DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y")


class ValidationError(ValueError):
    """Raised when user-supplied or loaded data is invalid."""


class TransactionType(str, Enum):
    INCOME = "income"      # adds to the balance
    EXPENSE = "expense"    # subtracts from the balance


# --------------------------------------------------------------------------- #
# Parsing helpers
# --------------------------------------------------------------------------- #
def parse_amount(raw: str | int | Decimal) -> Decimal:
    """Convert input to a positive Decimal rounded to cents (ROUND_HALF_UP).

    Accepted: '1250', '12.5', '12,50', '1 234,56', '1,234.56'.
    A lone comma is treated as the decimal separator; if both ',' and '.'
    appear, commas are treated as thousands separators.
    The value never passes through float.
    """
    text = format(raw, "f") if isinstance(raw, Decimal) else str(raw)
    text = text.strip().replace(" ", "").replace("\u00a0", "")
    if "," in text and "." in text:
        text = text.replace(",", "")
    else:
        text = text.replace(",", ".")

    # The regex rejects negatives, 'NaN', 'Infinity' and scientific notation.
    if not _AMOUNT_RE.fullmatch(text):
        raise ValidationError(f"'{raw}' is not a valid amount. Enter a positive number, e.g. 12.50")

    value = Decimal(text).quantize(CENT, rounding=ROUND_HALF_UP)
    if value <= 0:
        raise ValidationError("Amount must be greater than zero.")
    return value


def parse_date(raw: str) -> dt.date:
    """Parse 'YYYY-MM-DD' or 'DD.MM.YYYY'."""
    for fmt in _DATE_FORMATS:
        try:
            return dt.datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            continue
    raise ValidationError(f"'{raw}' is not a valid date. Use YYYY-MM-DD (or DD.MM.YYYY).")


def normalize_category(raw: str) -> str:
    """Trim, collapse whitespace and capitalize so 'food ' and 'Food' match."""
    name = " ".join(str(raw).split()).capitalize()
    if not name:
        raise ValidationError("Category cannot be empty.")
    return name


# --------------------------------------------------------------------------- #
# Transaction
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Transaction:
    """One income or expense record. `amount` is always positive."""

    id: int
    date: dt.date
    type: TransactionType
    category: str
    amount: Decimal
    description: str = ""

    @property
    def signed_amount(self) -> Decimal:
        """+amount for income, -amount for expense."""
        return self.amount if self.type is TransactionType.INCOME else -self.amount

    # -- serialization: Decimal <-> str keeps full precision in JSON ---------
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "type": self.type.value,
            "category": self.category,
            "amount": str(self.amount),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        try:
            return cls(
                id=int(data["id"]),
                date=dt.date.fromisoformat(data["date"]),
                type=TransactionType(data["type"]),
                category=normalize_category(data["category"]),
                amount=parse_amount(data["amount"]),
                description=str(data.get("description", "")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationError(f"Invalid record {data!r}: {exc}") from exc
