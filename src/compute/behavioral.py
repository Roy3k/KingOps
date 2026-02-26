"""Framework 7 — Behavioral Leakage Detection."""

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

from src.ingest.ynab import YNABData
from src.schema.models import Transaction


# Merchant normalization rules (can be extended via config file)
MERCHANT_NORMALIZE_MAP = {
    "amzn mktp": "Amazon",
    "amazon.com": "Amazon",
    "amazon": "Amazon",
    "starbucks": "Starbucks",
    "netflix": "Netflix",
    "spotify": "Spotify",
    "apple": "Apple",
    "comcast": "Comcast",
    "t-mobile": "T-Mobile",
}


@dataclass
class SubscriptionItem:
    """Recurring subscription with renewal info."""

    name: str
    category: str
    last_amount: float
    last_date: date
    renewal_note: Optional[str]  # e.g. "ends 1/7/27"
    renewal_date: Optional[date]
    merchant_normalized: Optional[str]


@dataclass
class FragmentationMetrics:
    """Fragmentation metrics."""

    accounts_used_monthly: int
    merchants_per_category: dict[str, int]
    uncategorized_count: int
    uncategorized_rate: float
    total_transactions: int


def _normalize_merchant(payee: str) -> str:
    """Normalize merchant name."""
    if not payee:
        return ""
    lower = payee.lower().strip()
    for k, v in MERCHANT_NORMALIZE_MAP.items():
        if k in lower:
            return v
    return payee


def _extract_renewal_from_category(category: str) -> tuple[Optional[str], Optional[date]]:
    """Extract renewal note and date from category like 'Paramount+ (ends 1/7/27)'."""
    if not category:
        return None, None
    match = re.search(r"\(ends?\s+(\d{1,2}/\d{1,2}/\d{2,4})\)", category, re.I)
    if match:
        from datetime import datetime

        try:
            dt_str = match.group(1)
            dt = datetime.strptime(dt_str, "%m/%d/%Y")
            return f"ends {dt_str}", dt.date()
        except ValueError:
            try:
                dt = datetime.strptime(dt_str, "%m/%d/%y")
                return f"ends {dt_str}", dt.date()
            except ValueError:
                return f"ends {dt_str}", None
    return None, None


def get_subscription_inventory(data: YNABData) -> list[SubscriptionItem]:
    """Extract subscription inventory from Subs category and hidden subs."""
    subs: dict[str, SubscriptionItem] = {}
    subs_cat_groups = ["📺 Subs", "Hidden Categories"]

    for t in data.transactions:
        if t.is_transfer or t.amount >= 0:
            continue
        cat_group = t.category_group or ""
        if cat_group not in subs_cat_groups:
            continue
        cat = t.category_normalized or t.category_raw or ""
        key = cat or t.payee_raw
        if not key:
            continue
        renewal_note, renewal_date = _extract_renewal_from_category(cat)
        if key not in subs or t.date_posted > subs[key].last_date:
            subs[key] = SubscriptionItem(
                name=key,
                category=cat_group,
                last_amount=abs(t.amount),
                last_date=t.date_posted,
                renewal_note=renewal_note,
                renewal_date=renewal_date,
                merchant_normalized=_normalize_merchant(t.payee_raw),
            )
    return sorted(subs.values(), key=lambda s: s.last_amount, reverse=True)


def get_fragmentation_metrics(data: YNABData, as_of_month: Optional[tuple[int, int]] = None) -> FragmentationMetrics:
    """Compute fragmentation: accounts used monthly, merchants per category, uncategorized rate."""
    txs = data.transactions
    if as_of_month:
        y, m = as_of_month
        txs = [t for t in txs if t.date_posted.year == y and t.date_posted.month == m]
    txs = [t for t in txs if not t.is_transfer]

    accounts_used = len(set(t.account_id for t in txs))
    merchants_by_cat: dict[str, set[str]] = {}
    uncategorized = 0
    for t in txs:
        cat = t.category_normalized or t.category_raw or "Uncategorized"
        if cat in ("Uncategorized", "Ready to Assign", "") or "Inflow" in (t.category_group or ""):
            if t.amount < 0:
                uncategorized += 1
        else:
            merchants_by_cat.setdefault(cat, set()).add(_normalize_merchant(t.payee_raw) or t.payee_raw)
    merchants_per_cat = {k: len(v) for k, v in merchants_by_cat.items()}
    total = len(txs)
    rate = uncategorized / total if total else 0.0
    return FragmentationMetrics(
        accounts_used_monthly=accounts_used,
        merchants_per_category=merchants_per_cat,
        uncategorized_count=uncategorized,
        uncategorized_rate=rate,
        total_transactions=total,
    )


def get_uncategorized_queue(data: YNABData) -> list[Transaction]:
    """Transactions with empty category or Ready to Assign (outflows)."""
    return [
        t
        for t in data.transactions
        if not t.is_transfer
        and t.amount < 0
        and (
            not (t.category_normalized or t.category_raw)
            or "Ready to Assign" in (t.category_raw or "")
        )
    ]


def get_category_volatility(data: YNABData, months: int = 6) -> dict[str, list[float]]:
    """Rolling variance by category (monthly spend amounts)."""
    from collections import defaultdict

    by_month_cat: dict[tuple[int, int], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for t in data.transactions:
        if t.is_transfer or t.amount >= 0:
            continue
        cat = t.category_normalized or t.category_raw or "Uncategorized"
        key = (t.date_posted.year, t.date_posted.month)
        by_month_cat[key][cat] += abs(t.amount)

    # Get unique categories
    all_cats = set()
    for d in by_month_cat.values():
        all_cats.update(d.keys())

    # Build monthly series per category
    months_sorted = sorted(by_month_cat.keys(), reverse=True)[:months]
    result: dict[str, list[float]] = {}
    for cat in all_cats:
        result[cat] = [by_month_cat[m].get(cat, 0) for m in months_sorted]
    return result
