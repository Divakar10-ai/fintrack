# 💰 FinTrack — Personal Finance Tracker

> A professional, zero-dependency CLI tool to track income, expenses, and budgets — all stored locally.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-pytest-orange?style=flat-square)](tests/)

---

## ✨ Features

- **Add** income and expense transactions with categories and dates
- **List** transactions with flexible filters (type, category, month)
- **Summary** with net balance and per-category spending breakdown
- **Budgets** — set monthly limits and track progress with visual bars
- **Export** transactions to CSV for spreadsheet analysis
- **Zero external dependencies** — only Python 3.10+ and the standard library

---

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/fintrack.git
cd fintrack

# Install (editable mode)
pip install -e .
```

The `fintrack` command is now available globally.

---

## 📖 Usage

### Add Transactions

```bash
# Add an expense
fintrack add expense 45.50 "Grocery run" --category food

# Add income with a specific date
fintrack add income 3000 "Monthly salary" --category salary --date 2024-08-01
```

### List Transactions

```bash
# List recent transactions (default: last 20)
fintrack list

# Filter by type and month
fintrack list --type expense --month 2024-08

# Filter by category
fintrack list --category food
```

### Financial Summary

```bash
# Summary for the current month
fintrack summary

# Summary for a specific month
fintrack summary --month 2024-07
```

```
────────────────────────────────────────────────────────────────────────
  📊  SUMMARY — 2024-08
────────────────────────────────────────────────────────────────────────
  Income                      $3,500.00
  Expenses                    $1,245.00
  ··············································
  Net                      ▲  $2,255.00
────────────────────────────────────────────────────────────────────────

  Spending by category

  housing        ████████████░░░░░░    $800.00
  food           ████████░░░░░░░░░░    $315.00
  transport      ███░░░░░░░░░░░░░░░░    $130.00
```

### Budgets

```bash
# Set a monthly budget for a category
fintrack budget set food 400
fintrack budget set housing 900

# Check budget vs. actual spending
fintrack budget status

# List all budgets
fintrack budget list
```

### Export to CSV

```bash
# Export all transactions
fintrack export report.csv

# Export a specific month
fintrack export july.csv --month 2024-07
```

### Delete & Clear

```bash
# Delete a transaction by ID
fintrack delete 12

# Clear all data (requires confirmation)
fintrack clear
```

---

## 🗂 Project Structure

```
fintrack/
├── fintrack/
│   ├── __init__.py
│   ├── main.py        # CLI entry point (argparse)
│   ├── tracker.py     # Core logic + SQLite storage
│   └── display.py     # Terminal formatting & colours
├── tests/
│   └── test_tracker.py
├── pyproject.toml
├── .gitignore
└── README.md
```

---

## 🧪 Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# With coverage report
pytest --cov=fintrack --cov-report=term-missing
```

---

## 🗄 Data Storage

All data is stored in a local SQLite database at `~/.fintrack/data.db`. No cloud, no accounts, no tracking.

---

## 📄 License

MIT © 2024 — see [LICENSE](LICENSE) for details.
