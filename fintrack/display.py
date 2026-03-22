"""
Terminal display helpers for FinTrack.
Uses ANSI color codes — no external dependencies required.
"""

from __future__ import annotations


# ── ANSI colour palette ──────────────────────────────────────────────────────
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    GREEN   = "\033[32m"
    RED     = "\033[31m"
    YELLOW  = "\033[33m"
    CYAN    = "\033[36m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    WHITE   = "\033[97m"
    BG_RED  = "\033[41m"


def _col(text: str, *codes: str) -> str:
    return "".join(codes) + str(text) + C.RESET


def _bar(ratio: float, width: int = 20) -> str:
    filled = int(min(ratio, 1.0) * width)
    bar = "█" * filled + "░" * (width - filled)
    color = C.GREEN if ratio < 0.75 else (C.YELLOW if ratio < 1.0 else C.RED)
    return _col(bar, color)


class Display:

    # ── generic helpers ──────────────────────────────────────────────────────

    def success(self, msg: str):
        print(f"  {_col('✔', C.GREEN, C.BOLD)}  {msg}")

    def info(self, msg: str):
        print(f"  {_col('ℹ', C.CYAN)}  {msg}")

    def error(self, msg: str):
        print(f"  {_col('✘', C.RED, C.BOLD)}  {msg}")

    def _divider(self, char: str = "─", width: int = 72):
        print(_col(char * width, C.DIM))

    def _header(self, title: str):
        self._divider()
        print(f"  {_col(title, C.BOLD, C.WHITE)}")
        self._divider()

    # ── transactions ─────────────────────────────────────────────────────────

    def print_transactions(self, transactions: list[dict]):
        if not transactions:
            self.info("No transactions found.")
            return

        self._header("📋  TRANSACTIONS")

        col = "{:<6} {:<12} {:<10} {:<14} {:<10} {}"
        header = col.format("ID", "DATE", "TYPE", "CATEGORY", "AMOUNT", "DESCRIPTION")
        print(_col(f"  {header}", C.DIM))
        self._divider()

        for tx in transactions:
            amount_str = f"${tx['amount']:,.2f}"
            color = C.GREEN if tx["type"] == "income" else C.RED
            type_label = _col(f"{tx['type']:<10}", color, C.BOLD)
            amount_label = _col(f"{amount_str:<10}", color)
            cat_label = _col(f"{tx['category']:<14}", C.CYAN)
            id_label = _col(f"{tx['id']:<6}", C.DIM)
            date_label = f"{tx['date']:<12}"
            desc_label = tx["description"]
            print(f"  {id_label}{date_label}{type_label}{cat_label}{amount_label}{desc_label}")

        self._divider()
        print(f"  {_col(str(len(transactions)) + ' transaction(s)', C.DIM)}\n")

    # ── summary ──────────────────────────────────────────────────────────────

    def print_summary(self, data: dict):
        self._header(f"📊  SUMMARY — {data['month']}")

        income   = data["income"]
        expenses = data["expenses"]
        net      = data["net"]

        net_color = C.GREEN if net >= 0 else C.RED
        net_icon  = "▲" if net >= 0 else "▼"

        print(f"  {'Income':<20} {_col(f'${income:>10,.2f}', C.GREEN, C.BOLD)}")
        print(f"  {'Expenses':<20} {_col(f'${expenses:>10,.2f}', C.RED, C.BOLD)}")
        self._divider("·")
        print(f"  {'Net':<20} {_col(f'{net_icon} ${abs(net):>10,.2f}', net_color, C.BOLD)}")
        self._divider()

        if data["by_category"]:
            print(f"\n  {_col('Spending by category', C.BOLD, C.WHITE)}\n")
            sorted_cats = sorted(data["by_category"].items(), key=lambda x: -x[1])
            max_val = sorted_cats[0][1] if sorted_cats else 1
            for cat, total in sorted_cats:
                ratio = total / max_val if max_val else 0
                bar = _bar(ratio, width=18)
                print(f"  {_col(f'{cat:<14}', C.CYAN)} {bar}  {_col(f'${total:,.2f}', C.RED)}")

        print()

    # ── budgets ───────────────────────────────────────────────────────────────

    def print_budgets(self, budgets: list[dict]):
        if not budgets:
            self.info("No budgets set. Use: fintrack budget set <category> <amount>")
            return

        self._header("💼  BUDGETS")
        for b in budgets:
            print(f"  {_col(b['category']:<20, C.CYAN)} ${b['amount']:,.2f}/month")
        print()

    def print_budget_status(self, statuses: list[dict]):
        if not statuses:
            self.info("No budget data available.")
            return

        self._header("📈  BUDGET STATUS — This Month")

        col = "{:<16} {:>10} {:>10} {:>10}"
        header = col.format("CATEGORY", "BUDGET", "SPENT", "LEFT")
        print(_col(f"  {header}", C.DIM))
        self._divider()

        for s in statuses:
            cat     = _col(f"{s['category']:<16}", C.CYAN)
            budget  = f"${s['budget']:>9,.2f}" if s["budget"] else _col(f"{'—':>10}", C.DIM)
            spent   = _col(f"${s['spent']:>9,.2f}", C.RED if s["over"] else C.WHITE)
            left    = (
                _col(f"${s['remaining']:>9,.2f}", C.RED if s["over"] else C.GREEN)
                if s["remaining"] is not None
                else _col(f"{'N/A':>10}", C.DIM)
            )
            flag = _col("  ⚠ OVER BUDGET", C.RED, C.BOLD) if s["over"] else ""
            print(f"  {cat}{budget}{spent}{left}{flag}")

            if s["budget"] and s["spent"] > 0:
                ratio = s["spent"] / s["budget"]
                print(f"  {' ' * 16}  {_bar(ratio, 28)}")

        self._divider()
        print()
