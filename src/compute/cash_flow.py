"""Framework 2 — Cash Flow & Allocation Efficiency."""

from dataclasses import dataclass
from datetime import date
from typing import Optional

import pandas as pd

from src.ingest.ynab import YNABData
from src.schema.models import Transaction


# Category group -> allocation rollup (for Sankey)
ROLLUP_MAP = {
    "🏠 Core": "needs",
    "🔁 True": "needs",
    "Credit Card Payments": "debt",
    "📺 Subs": "wants",
    "🌿 QoL": "wants",
    "📈 LT": "savings",
    "🚧 Projects": "savings",
    "Business/Passthrough Accounts": "other",
    "Hidden Categories": "wants",
    "Inflow": "income",
}


@dataclass
class MonthlyAllocation:
    """Planned vs actual for a month."""

    period: str
    category_group: str
    category: str
    planned: float
    actual: float
    variance: float
    rollup: str


@dataclass
class VarianceDriver:
    """Top merchant/category contributing to variance."""

    merchant_or_category: str
    category: str
    period: str
    variance: float
    transaction_count: int


@dataclass
class UncategorizedItem:
    """Transaction needing categorization."""

    transaction_id: str
    date: date
    payee: str
    amount: float
    account: str
    memo: Optional[str]
    category_raw: Optional[str]


def _parse_month(period: str) -> Optional[tuple[int, int]]:
    """Parse 'Jan 2025' -> (2025, 1)."""
    try:
        from datetime import datetime

        dt = datetime.strptime(period.strip(), "%b %Y")
        return dt.year, dt.month
    except ValueError:
        return None


def get_monthly_allocation(data: YNABData) -> list[MonthlyAllocation]:
    """Budget vs actual by month and category."""
    # Aggregate budget by period, category
    budget_by_period: dict[tuple[str, str, str], float] = {}
    for b in data.budgets:
        key = (b.period, b.category_group, b.category)
        budget_by_period[key] = b.assigned  # planned amount

    # Aggregate actual (activity) from budget - YNAB Plan already has Activity
    actual_by_period: dict[tuple[str, str, str], float] = {}
    for b in data.budgets:
        key = (b.period, b.category_group, b.category)
        actual_by_period[key] = b.activity

    result: list[MonthlyAllocation] = []
    seen = set()
    for b in data.budgets:
        key = (b.period, b.category_group, b.category)
        if key in seen:
            continue
        seen.add(key)
        planned = budget_by_period.get(key, 0.0)
        actual = actual_by_period.get(key, 0.0)
        variance = actual - planned  # positive = overspent vs plan
        rollup = ROLLUP_MAP.get(b.category_group, "other")
        result.append(
            MonthlyAllocation(
                period=b.period,
                category_group=b.category_group,
                category=b.category,
                planned=planned,
                actual=actual,
                variance=variance,
                rollup=rollup,
            )
        )
    return result


def get_variance_drivers(
    data: YNABData,
    allocation: Optional[list[MonthlyAllocation]] = None,
    top_n: int = 15,
) -> list[VarianceDriver]:
    """Top merchants/categories contributing to budget variance."""
    if allocation is None:
        allocation = get_monthly_allocation(data)

    # From allocation: category + period with largest absolute variance
    drivers = []
    for a in allocation:
        if a.variance == 0:
            continue
        drivers.append(
            VarianceDriver(
                merchant_or_category=a.category,
                category=a.category_group,
                period=a.period,
                variance=a.variance,
                transaction_count=0,
            )
        )

    # Sort by absolute variance, take top_n
    drivers.sort(key=lambda d: abs(d.variance), reverse=True)
    return drivers[:top_n]


def get_uncategorized_inbox(data: YNABData) -> list[UncategorizedItem]:
    """Transactions with empty category or 'Ready to Assign' needing attention."""
    items: list[UncategorizedItem] = []
    for t in data.transactions:
        if t.is_transfer:
            continue
        cat = t.category_normalized or t.category_raw
        is_ready = "Ready to Assign" in (cat or "") or "Inflow" in (t.category_group or "")
        is_empty = not cat or not cat.strip()
        if is_empty or (is_ready and t.amount < 0):
            items.append(
                UncategorizedItem(
                    transaction_id=t.id,
                    date=t.date_posted,
                    payee=t.payee_raw,
                    amount=t.amount,
                    account=t.account_id,
                    memo=t.memo,
                    category_raw=cat,
                )
            )
    return sorted(items, key=lambda x: x.date, reverse=True)


def get_allocation_sankey_data(data: YNABData, period: Optional[str] = None) -> dict:
    """Prepare data for Sankey: Income -> Taxes -> Needs -> Wants -> Debt -> Savings."""
    allocation = get_monthly_allocation(data)
    if period:
        allocation = [a for a in allocation if a.period == period]
    else:
        # Use latest month
        periods = sorted(set(a.period for a in allocation), reverse=True)
        if periods:
            allocation = [a for a in allocation if a.period == periods[0]]

    income = sum(a.actual for a in allocation if a.rollup == "income")
    needs = sum(a.actual for a in allocation if a.rollup == "needs")
    wants = sum(a.actual for a in allocation if a.rollup == "wants")
    debt = sum(a.actual for a in allocation if a.rollup == "debt")
    savings = sum(a.actual for a in allocation if a.rollup == "savings")

    # Outflows are negative in YNAB activity
    if income <= 0:
        # Infer income from Inflow category in transactions
        for t in data.transactions:
            if t.amount > 0 and (t.category_group == "Inflow" or "Ready to Assign" in (t.category_raw or "")):
                income += t.amount
        # Approximate from budget if needed
        if income <= 0:
            income = abs(needs) + abs(wants) + abs(debt) + abs(savings)

    return {
        "income": max(0, income),
        "needs": abs(needs),
        "wants": abs(wants),
        "debt": abs(debt),
        "savings": abs(savings),
    }


def get_fixed_cost_ratio(data: YNABData, period: Optional[str] = None) -> Optional[float]:
    """Fixed-cost ratio (fixed / income) when income is known."""
    sankey = get_allocation_sankey_data(data, period)
    income = sankey.get("income", 0)
    if income <= 0:
        return None
    needs = sankey.get("needs", 0)
    return needs / income if income else None
