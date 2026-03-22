"""
FinTrack - Personal Finance Tracker
A CLI tool to manage expenses, income, and budgets.
"""

import argparse
import sys
from fintrack.tracker import FinanceTracker
from fintrack.display import Display


def main():
    parser = argparse.ArgumentParser(
        prog="fintrack",
        description="💰 FinTrack — Personal Finance Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fintrack add expense 45.50 "Groceries" --category food
  fintrack add income 3000 "Monthly Salary" --category salary
  fintrack list
  fintrack summary
  fintrack budget set food 400
  fintrack budget status
  fintrack export report.csv
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- ADD ---
    add_parser = subparsers.add_parser("add", help="Add a transaction")
    add_parser.add_argument("type", choices=["expense", "income"], help="Transaction type")
    add_parser.add_argument("amount", type=float, help="Amount (e.g. 49.99)")
    add_parser.add_argument("description", type=str, help="Short description")
    add_parser.add_argument("--category", "-c", type=str, default="general", help="Category tag")
    add_parser.add_argument("--date", "-d", type=str, default=None, help="Date (YYYY-MM-DD), default: today")

    # --- LIST ---
    list_parser = subparsers.add_parser("list", help="List transactions")
    list_parser.add_argument("--type", "-t", choices=["expense", "income"], help="Filter by type")
    list_parser.add_argument("--category", "-c", type=str, help="Filter by category")
    list_parser.add_argument("--month", "-m", type=str, help="Filter by month (YYYY-MM)")
    list_parser.add_argument("--limit", "-n", type=int, default=20, help="Max rows to show")

    # --- DELETE ---
    del_parser = subparsers.add_parser("delete", help="Delete a transaction by ID")
    del_parser.add_argument("id", type=int, help="Transaction ID")

    # --- SUMMARY ---
    sum_parser = subparsers.add_parser("summary", help="Show financial summary")
    sum_parser.add_argument("--month", "-m", type=str, help="Month (YYYY-MM), default: current")

    # --- BUDGET ---
    budget_parser = subparsers.add_parser("budget", help="Manage category budgets")
    budget_sub = budget_parser.add_subparsers(dest="budget_cmd")

    set_b = budget_sub.add_parser("set", help="Set a budget for a category")
    set_b.add_argument("category", type=str)
    set_b.add_argument("amount", type=float)

    budget_sub.add_parser("status", help="Show budget vs spending")
    budget_sub.add_parser("list", help="List all budgets")

    # --- EXPORT ---
    exp_parser = subparsers.add_parser("export", help="Export transactions to CSV")
    exp_parser.add_argument("filename", type=str, help="Output file (e.g. report.csv)")
    exp_parser.add_argument("--month", "-m", type=str, help="Filter by month (YYYY-MM)")

    # --- CLEAR ---
    subparsers.add_parser("clear", help="Clear all data (with confirmation)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    tracker = FinanceTracker()
    display = Display()

    if args.command == "add":
        result = tracker.add_transaction(
            t_type=args.type,
            amount=args.amount,
            description=args.description,
            category=args.category.lower(),
            date_str=args.date
        )
        display.success(f"Added {args.type}: ${args.amount:.2f} — {args.description} (ID: {result['id']})")

    elif args.command == "list":
        transactions = tracker.get_transactions(
            t_type=args.type,
            category=args.category,
            month=args.month,
            limit=args.limit
        )
        display.print_transactions(transactions)

    elif args.command == "delete":
        tracker.delete_transaction(args.id)
        display.success(f"Transaction #{args.id} deleted.")

    elif args.command == "summary":
        data = tracker.get_summary(month=args.month)
        display.print_summary(data)

    elif args.command == "budget":
        if args.budget_cmd == "set":
            tracker.set_budget(args.category.lower(), args.amount)
            display.success(f"Budget set: {args.category} → ${args.amount:.2f}/month")
        elif args.budget_cmd == "status":
            data = tracker.get_budget_status()
            display.print_budget_status(data)
        elif args.budget_cmd == "list":
            budgets = tracker.list_budgets()
            display.print_budgets(budgets)
        else:
            budget_parser.print_help()

    elif args.command == "export":
        path = tracker.export_csv(args.filename, month=args.month)
        display.success(f"Exported to {path}")

    elif args.command == "clear":
        confirm = input("⚠️  This will delete ALL data. Type 'yes' to confirm: ")
        if confirm.strip().lower() == "yes":
            tracker.clear_all()
            display.success("All data cleared.")
        else:
            display.info("Cancelled.")


if __name__ == "__main__":
    main()
