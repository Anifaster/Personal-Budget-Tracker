"""Unit tests: python -m unittest -v"""
import datetime as dt
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

import calculations as calc
from ledger import Ledger
from models import TransactionType as TT, ValidationError, parse_amount
from storage import JsonStorage, StorageError

D = dt.date


class ParseAmountTests(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(parse_amount("12,50"), Decimal("12.50"))
        self.assertEqual(parse_amount("1 234,56"), Decimal("1234.56"))
        self.assertEqual(parse_amount("1,234.56"), Decimal("1234.56"))
        self.assertEqual(parse_amount("0.005"), Decimal("0.01"))  # ROUND_HALF_UP

    def test_rejects_bad_input(self):
        for bad in ("", "abc", "-5", "0", "0.00", "NaN", "Infinity", "1e5", "1.2.3"):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                parse_amount(bad)


class CalculationTests(unittest.TestCase):
    def setUp(self):
        self.ledger = Ledger()
        self.ledger.add(TT.INCOME, "1000", "Salary", D(2026, 1, 5))
        self.ledger.add(TT.EXPENSE, "0.10", "Food", D(2026, 1, 6))
        self.ledger.add(TT.EXPENSE, "0.20", "food", D(2026, 2, 1))
        self.ledger.add(TT.EXPENSE, "300", "Rent", D(2026, 2, 2))

    def test_exact_arithmetic(self):
        # With floats 0.1 + 0.2 != 0.3; with Decimal it is exact.
        txs = self.ledger.transactions
        self.assertEqual(calc.total(txs, TT.EXPENSE), Decimal("300.30"))
        self.assertEqual(calc.balance(txs), Decimal("699.70"))

    def test_empty_is_decimal_zero(self):
        self.assertEqual(calc.balance([]), Decimal("0.00"))
        self.assertIsInstance(calc.balance([]), Decimal)

    def test_category_filter_is_case_insensitive(self):
        rows = calc.filter_transactions(self.ledger.transactions, category="FOOD")
        self.assertEqual(len(rows), 2)
        self.assertEqual(calc.balance(rows), Decimal("-0.30"))

    def test_date_and_type_filter(self):
        rows = calc.filter_transactions(
            self.ledger.transactions, tx_type=TT.EXPENSE, start=D(2026, 2, 1), end=D(2026, 2, 28)
        )
        self.assertEqual([t.category for t in rows], ["Food", "Rent"])

    def test_groupings(self):
        txs = self.ledger.transactions
        self.assertEqual(list(calc.totals_by_category(txs, TT.EXPENSE)), ["Rent", "Food"])
        months = calc.monthly_summary(txs)
        self.assertEqual(months["2026-01"].net, Decimal("999.90"))
        self.assertEqual(calc.balance_history(txs)[-1][1], Decimal("699.70"))


class StorageTests(unittest.TestCase):
    def test_round_trip_keeps_precision(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = JsonStorage(Path(tmp) / "data.json")
            ledger = Ledger()
            ledger.add(TT.EXPENSE, "19.99", "Food", D(2026, 3, 1), "lunch ☕")
            store.save(ledger.transactions)
            self.assertEqual(store.load(), ledger.transactions)

    def test_missing_file_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(JsonStorage(Path(tmp) / "nope.json").load(), [])

    def test_corrupt_file_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaises(StorageError):
                JsonStorage(path).load()

    def test_remove(self):
        ledger = Ledger()
        tx = ledger.add(TT.INCOME, "5", "Gift", D(2026, 1, 1))
        ledger.remove(tx.id)
        self.assertEqual(ledger.transactions, [])
        with self.assertRaises(ValidationError):
            ledger.remove(tx.id)


if __name__ == "__main__":
    unittest.main()
