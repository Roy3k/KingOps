"""Obligations — debts and recurring fixed costs."""

from dataclasses import dataclass
from datetime import date
from typing import Optional

import pandas as pd

from src.compute.cash_flow import _parse_month, get_actual_periods
from src.ingest.ynab import YNABData

# Category keyword -> bucket, first match wins. Matched against the lowercased category name.
OBLIGATION_RULES = [
    ("mortgage", "Housing"),
    ("rent", "Housing"),
    ("heloc interest", "Debt service"),
    ("credit card interest", "Debt service"),
    ("tax", "Taxes"),
    ("car payment", "Auto"),
    ("auto loan", "Auto"),
    ("auto insurance", "Auto"),
    ("auto registration", "Auto"),
    ("auto maintenance", "Auto"),
    ("gas & fuel", "Auto"),
    ("insurance", "Insurance"),
    ("utilities", "Utilities"),
    ("internet", "Utilities"),
    ("phones", "Utilities"),
    ("tuition", "Education"),
]

BUCKET_ORDER = ["Housing", "Debt service", "Taxes", "Auto", "Insurance", "Utilities", "Education"]


@dataclass
class Debt:
    """A liability with what it costs and how it moved over the window."""

    name: str
    liability_type: str
    balance: float
    rate: Optional[float]
    est_monthly_interest: Optional[float]  # balance x APR / 12
    avg_monthly_paid: float  # payments and credits into the account
    avg_monthly_added: float  # charges, draws, interest and fees
    balance_change: float  # positive = owed more than at the start of the window
    balance_as_of: date


def _bucket(category: str) -> Optional[str]:
    name = category.lower()
    for keyword, bucket in OBLIGATION_RULES:
        if keyword in name:
            return bucket
    return None


def _window_start(data: YNABData, months: int) -> Optional[date]:
    periods = get_actual_periods(data)[-months:]
    ym = _parse_month(periods[0]) if periods else None
    return date(ym[0], ym[1], 1) if ym else None


def get_debts(data: YNABData, months: int = 6) -> list[Debt]:
    """Every liability, largest first, with payment and borrowing activity over the last `months`."""
    start = _window_start(data, months)
    n_months = min(months, len(get_actual_periods(data))) or 1
    debts: list[Debt] = []
    for l in data.liabilities:
        window = [
            t.amount
            for t in data.transactions
            if t.account_id == l.linked_account_id and start and start <= t.date_posted <= data.as_of
        ]
        paid = sum(a for a in window if a > 0)
        added = -sum(a for a in window if a < 0)
        debts.append(
            Debt(
                name=l.name,
                liability_type=l.liability_type,
                balance=l.principal_balance,
                rate=l.rate,
                est_monthly_interest=l.principal_balance * l.rate / 12 if l.rate else None,
                avg_monthly_paid=paid / n_months,
                avg_monthly_added=added / n_months,
                balance_change=added - paid,
                balance_as_of=l.balance_as_of,
            )
        )
    return sorted(debts, key=lambda d: d.balance, reverse=True)


def get_recurring_obligations(data: YNABData, months: int = 6) -> pd.DataFrame:
    """Fixed-cost categories (housing, debt interest, taxes, auto, utilities, tuition) by month.

    Columns: Bucket, Category, one per period (oldest first), Average, Set aside
    (money still sitting in the category at the latest period).
    """
    periods = get_actual_periods(data)[-months:]
    columns = ["Bucket", "Category", *periods, "Average", "Set aside"]
    rows: dict[tuple[str, str], dict] = {}
    for b in data.budgets:
        bucket = _bucket(b.category)
        if b.period not in periods or bucket is None or b.category_group == "Credit Card Payments":
            continue
        row = rows.setdefault((bucket, b.category), {"Bucket": bucket, "Category": b.category, "Set aside": 0.0})
        row[b.period] = row.get(b.period, 0.0) - b.activity
        if b.period == periods[-1]:
            row["Set aside"] = b.available
    if not rows:
        return pd.DataFrame(columns=columns)
    table = pd.DataFrame(rows.values()).reindex(columns=columns).fillna(0.0)
    table["Average"] = table[periods].mean(axis=1)
    table = table[(table[periods].abs().sum(axis=1) > 0) | (table["Set aside"] > 0)]
    order = {b: i for i, b in enumerate(BUCKET_ORDER)}
    return (
        table.assign(_o=table["Bucket"].map(order))
        .sort_values(["_o", "Average"], ascending=[True, False])
        .drop(columns="_o")
        .reset_index(drop=True)
    )
