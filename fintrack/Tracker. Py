"""
Core logic for FinTrack: storage, retrieval, budgets, and export.
Uses a local SQLite database for persistence.
"""

import sqlite3
import csv
import os
from datetime import date, datetime
from pathlib import Path


DB_PATH = Path.home() / ".fintrack" / "data.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            type        TEXT    NOT NULL CHECK(type IN ('income', 'expense')),
            amount      REAL    NOT NULL,
            description TEXT    NOT NULL,
            category    TEXT    NOT NULL DEFAULT 'general',
            date        TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS budgets (
            category    TEXT PRIMARY KEY,
            amount      REAL NOT NULL
        );
    """)
    conn.commit()


class FinanceTracker:
    def __init__(self):
        self.conn = get_connection()
        init_db(self.conn)

    # ------------------------------------------------------------------ #
    #  Transactions
    # ------------------------------------------------------------------ #

    def add_transaction(
        self,
        t_type: str,
        amount: float,
        description: str,
        category: str = "general",
        date_str: str | None = None,
    ) -> dict:
        if amount <= 0:
            raise ValueError("Amount must be positive.")

        tx_date = date_str if date_str else date.today().isoformat()
        # basic format check
        try:
            datetime.strptime(tx_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: '{tx_date}'. Use YYYY-MM-DD.")

        cur = self.conn.execute(
            "INSERT INTO transactions (type, amount, description, category, date) VALUES (?,?,?,?,?)",
            (t_type, amount, description, category, tx_date),
        )
        self.conn.commit()
        return {"id": cur.lastrowid}

    def get_transactions(
        self,
        t_type: str | None = None,
        category: str | None = None,
        month: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        query = "SELECT * FROM transactions WHERE 1=1"
        params: list = []

        if t_type:
            query += " AND type = ?"
            params.append(t_type)
        if category:
            query += " AND category = ?"
            params.append(category.lower())
        if month:
            query += " AND strftime('%Y-%m', date) = ?"
            params.append(month)

        query += " ORDER BY date DESC, id DESC LIMIT ?"
        params.append(limit)

        rows = self.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def delete_transaction(self, tx_id: int):
        cur = self.conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        self.conn.commit()
        if cur.rowcount == 0:
            raise ValueError(f"No transaction found with ID {tx_id}.")

    # ------------------------------------------------------------------ #
    #  Summary
    # ------------------------------------------------------------------ #

    def get_summary(self, month: str | None = None) -> dict:
        if not month:
            month = date.today().strftime("%Y-%m")

        rows = self.conn.execute(
            """
            SELECT type, category, SUM(amount) as total, COUNT(*) as count
            FROM transactions
            WHERE strftime('%Y-%m', date) = ?
            GROUP BY type, category
            ORDER BY type, total DESC
            """,
            (month,),
        ).fetchall()

        income = 0.0
        expenses = 0.0
        by_category: dict[str, float] = {}

        for r in rows:
            if r["type"] == "income":
                income += r["total"]
            else:
                expenses += r["total"]
                by_category[r["category"]] = by_category.get(r["category"], 0) + r["total"]

        return {
            "month": month,
            "income": income,
            "expenses": expenses,
            "net": income - expenses,
            "by_category": by_category,
        }

    # ------------------------------------------------------------------ #
    #  Budgets
    # ------------------------------------------------------------------ #

    def set_budget(self, category: str, amount: float):
        if amount <= 0:
            raise ValueError("Budget amount must be positive.")
        self.conn.execute(
            "INSERT INTO budgets (category, amount) VALUES (?,?) ON CONFLICT(category) DO UPDATE SET amount=excluded.amount",
            (category, amount),
        )
        self.conn.commit()

    def list_budgets(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM budgets ORDER BY category").fetchall()
        return [dict(r) for r in rows]

    def get_budget_status(self) -> list[dict]:
        month = date.today().strftime("%Y-%m")
        budgets = {r["category"]: r["amount"] for r in self.conn.execute("SELECT * FROM budgets")}

        spending = {}
        rows = self.conn.execute(
            """
            SELECT category, SUM(amount) as spent
            FROM transactions
            WHERE type='expense' AND strftime('%Y-%m', date) = ?
            GROUP BY category
            """,
            (month,),
        ).fetchall()
        for r in rows:
            spending[r["category"]] = r["spent"]

        result = []
        all_cats = set(budgets) | set(spending)
        for cat in sorted(all_cats):
            budget = budgets.get(cat)
            spent = spending.get(cat, 0.0)
            result.append({
                "category": cat,
                "budget": budget,
                "spent": spent,
                "remaining": (budget - spent) if budget else None,
                "over": (spent > budget) if budget else False,
            })
        return result

    # ------------------------------------------------------------------ #
    #  Export
    # ------------------------------------------------------------------ #

    def export_csv(self, filename: str, month: str | None = None) -> str:
        transactions = self.get_transactions(month=month, limit=100_000)
        path = os.path.abspath(filename)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "date", "type", "category", "amount", "description"])
            writer.writeheader()
            writer.writerows(transactions)
        return path

    # ------------------------------------------------------------------ #
    #  Clear
    # ------------------------------------------------------------------ #

    def clear_all(self):
        self.conn.executescript("DELETE FROM transactions; DELETE FROM budgets;")
        self.conn.commit()
