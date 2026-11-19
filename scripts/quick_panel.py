"""Quick panel — net worth, debts, fixed costs and 6-month category spending as text.

    python scripts/quick_panel.py [months]
"""

import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.compute.balance_sheet import compute_net_worth  # noqa: E402
from src.compute.cash_flow import get_actual_periods, get_period_income, get_spending_by_category  # noqa: E402
from src.compute.obligations import get_debts, get_recurring_obligations  # noqa: E402
from src.ingest.ynab import load_ynab_data  # noqa: E402


def main() -> None:
    months = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8")) or {}
    data = load_ynab_data(ROOT, config)
    pd.options.display.float_format = "{:,.0f}".format
    pd.set_option("display.width", 250, "display.max_rows", 500)

    nw = compute_net_worth(data, as_of=data.as_of)
    print(f"KingOps quick panel — data as of {data.as_of:%b %d, %Y}\n")
    print(f"Net worth ${nw.net_worth:,.0f}  =  assets ${nw.total_assets:,.0f}  −  liabilities ${nw.total_liabilities:,.0f}\n")

    print("ASSETS")
    assets = pd.DataFrame([{"Account": a.name, "Kind": a.asset_type, "Balance": a.value} for a in data.assets])
    print(assets.sort_values("Balance", ascending=False).to_string(index=False), "\n")

    print(f"DEBTS (activity = last {months} months)")
    print(
        pd.DataFrame(
            [
                {
                    "Debt": d.name,
                    "Balance": d.balance,
                    "APR %": (d.rate or 0) * 100,
                    "Est interest/mo": d.est_monthly_interest or 0,
                    "Paid/mo": d.avg_monthly_paid,
                    "Added/mo": d.avg_monthly_added,
                    "Change": d.balance_change,
                }
                for d in get_debts(data, months)
            ]
        ).to_string(index=False),
        "\n",
    )

    print("RECURRING FIXED COSTS")
    print(get_recurring_obligations(data, months).to_string(index=False), "\n")

    spending = get_spending_by_category(data, months)
    periods = get_actual_periods(data)[-months:]
    print("SPENDING BY GROUP")
    by_group = spending.groupby("Category Group")[[*periods, "Average"]].sum().sort_values("Average", ascending=False)
    by_group.loc["Total spending"] = by_group.sum()
    by_group.loc["Income"] = [*(get_period_income(data, p) for p in periods), sum(get_period_income(data, p) for p in periods) / len(periods)]
    print(by_group.to_string(), "\n")

    print("SPENDING BY CATEGORY")
    print(spending.to_string(index=False))


if __name__ == "__main__":
    main()
