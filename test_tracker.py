"""
Tests for FinTrack core logic.
Uses an in-memory SQLite database to avoid touching real data.
"""

import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from fintrack.tracker import FinanceTracker, init_db


@pytest.fixture
def tracker(tmp_path):
    """Provide a FinanceTracker backed by a temp database."""
    db_file = tmp_path / "test.db"
    with patch("fintrack.tracker.DB_PATH", db_file):
        with patch("fintrack.tracker.get_connection") as mock_conn:
            conn = sqlite3.connect(str(db_file))
            conn.row_factory = sqlite3.Row
            init_db(conn)
            mock_conn.return_value = conn
            t = FinanceTracker()
            t.conn = conn
            yield t
            conn.close()


# ── add_transaction ───────────────────────────────────────────────────────────

class TestAddTransaction:
    def test_add_expense(self, tracker):
        result = tracker.add_transaction("expense", 50.0, "Coffee", "food")
        assert result["id"] == 1

    def test_add_income(self, tracker):
        result = tracker.add_transaction("income", 3000.0, "Salary", "salary")
        assert result["id"] == 1

    def test_custom_date(self, tracker):
        tracker.add_transaction("expense", 20.0, "Lunch", "food", "2024-06-15")
        txs = tracker.get_transactions()
        assert txs[0]["date"] == "2024-06-15"

    def test_invalid_amount_zero(self, tracker):
        with pytest.raises(ValueError, match="positive"):
            tracker.add_transaction("expense", 0, "Free thing", "other")

    def test_invalid_amount_negative(self, tracker):
        with pytest.raises(ValueError, match="positive"):
            tracker.add_transaction("expense", -10, "Refund", "other")

    def test_invalid_date_format(self, tracker):
        with pytest.raises(ValueError, match="Invalid date"):
            tracker.add_transaction("expense", 10.0, "Test", "other", "15-06-2024")


# ── get_transactions ──────────────────────────────────────────────────────────

class TestGetTransactions:
    def _seed(self, tracker):
        tracker.add_transaction("expense", 30.0, "Groceries", "food", "2024-07-10")
        tracker.add_transaction("expense", 15.0, "Bus", "transport", "2024-07-11")
        tracker.add_transaction("income",  500.0, "Freelance", "freelance", "2024-07-12")
        tracker.add_transaction("expense", 200.0, "Rent", "housing", "2024-06-01")

    def test_list_all(self, tracker):
        self._seed(tracker)
        assert len(tracker.get_transactions(limit=100)) == 4

    def test_filter_by_type(self, tracker):
        self._seed(tracker)
        expenses = tracker.get_transactions(t_type="expense", limit=100)
        assert all(t["type"] == "expense" for t in expenses)
        assert len(expenses) == 3

    def test_filter_by_category(self, tracker):
        self._seed(tracker)
        food = tracker.get_transactions(category="food")
        assert len(food) == 1
        assert food[0]["description"] == "Groceries"

    def test_filter_by_month(self, tracker):
        self._seed(tracker)
        july = tracker.get_transactions(month="2024-07", limit=100)
        assert len(july) == 3

    def test_limit(self, tracker):
        self._seed(tracker)
        result = tracker.get_transactions(limit=2)
        assert len(result) == 2


# ── delete_transaction ────────────────────────────────────────────────────────

class TestDeleteTransaction:
    def test_delete_existing(self, tracker):
        result = tracker.add_transaction("expense", 10.0, "Coffee", "food")
        tracker.delete_transaction(result["id"])
        assert tracker.get_transactions() == []

    def test_delete_nonexistent(self, tracker):
        with pytest.raises(ValueError, match="No transaction found"):
            tracker.delete_transaction(9999)


# ── get_summary ───────────────────────────────────────────────────────────────

class TestGetSummary:
    def test_net_positive(self, tracker):
        tracker.add_transaction("income",  1000.0, "Salary", "salary", "2024-08-01")
        tracker.add_transaction("expense",  300.0, "Rent",   "housing", "2024-08-02")
        s = tracker.get_summary("2024-08")
        assert s["income"]   == 1000.0
        assert s["expenses"] == 300.0
        assert s["net"]      == 700.0

    def test_net_negative(self, tracker):
        tracker.add_transaction("income",  200.0, "Side job", "freelance", "2024-08-05")
        tracker.add_transaction("expense", 500.0, "Rent",     "housing",   "2024-08-06")
        s = tracker.get_summary("2024-08")
        assert s["net"] == -300.0

    def test_empty_month(self, tracker):
        s = tracker.get_summary("2099-01")
        assert s["income"] == 0.0
        assert s["expenses"] == 0.0

    def test_by_category(self, tracker):
        tracker.add_transaction("expense", 100.0, "Groceries", "food",    "2024-08-01")
        tracker.add_transaction("expense",  50.0, "Bus",       "transport","2024-08-02")
        s = tracker.get_summary("2024-08")
        assert s["by_category"]["food"] == 100.0
        assert s["by_category"]["transport"] == 50.0


# ── budgets ───────────────────────────────────────────────────────────────────

class TestBudgets:
    def test_set_and_list(self, tracker):
        tracker.set_budget("food", 400.0)
        budgets = tracker.list_budgets()
        assert len(budgets) == 1
        assert budgets[0]["category"] == "food"
        assert budgets[0]["amount"]   == 400.0

    def test_update_budget(self, tracker):
        tracker.set_budget("food", 400.0)
        tracker.set_budget("food", 600.0)
        budgets = tracker.list_budgets()
        assert len(budgets) == 1
        assert budgets[0]["amount"] == 600.0

    def test_invalid_budget(self, tracker):
        with pytest.raises(ValueError, match="positive"):
            tracker.set_budget("food", -50.0)

    def test_budget_status_over(self, tracker):
        tracker.set_budget("food", 100.0)
        # Patch today to a known month
        import datetime
        with patch("fintrack.tracker.date") as mock_date:
            mock_date.today.return_value = datetime.date(2024, 8, 1)
            mock_date.side_effect = lambda *a, **kw: datetime.date(*a, **kw)
            tracker.add_transaction("expense", 150.0, "Groceries", "food", "2024-08-10")
            statuses = tracker.get_budget_status()
        food_status = next(s for s in statuses if s["category"] == "food")
        assert food_status["budget"] == 100.0
        assert food_status["spent"]  == 150.0


# ── export_csv ────────────────────────────────────────────────────────────────

class TestExportCSV:
    def test_export_creates_file(self, tracker, tmp_path):
        tracker.add_transaction("expense", 20.0, "Coffee", "food", "2024-07-01")
        out = tmp_path / "out.csv"
        path = tracker.export_csv(str(out))
        assert out.exists()
        content = out.read_text()
        assert "Coffee" in content

    def test_export_headers(self, tracker, tmp_path):
        out = tmp_path / "out.csv"
        tracker.export_csv(str(out))
        content = out.read_text()
        for col in ["id", "date", "type", "category", "amount", "description"]:
            assert col in content


# ── clear_all ─────────────────────────────────────────────────────────────────

class TestClearAll:
    def test_clear(self, tracker):
        tracker.add_transaction("expense", 10.0, "Test", "other", "2024-01-01")
        tracker.set_budget("food", 200.0)
        tracker.clear_all()
        assert tracker.get_transactions() == []
        assert tracker.list_budgets() == []
