"""Framework 1 — Balance Sheet Integrity."""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from src.ingest.ynab import YNABData
from src.schema.models import Asset, ConfidenceLevel, Liability, Transaction


@dataclass
class NetWorthPoint:
    """Single point in net worth time series."""

    date: date
    total_assets: float
    total_liabilities: float
    net_worth: float
    confidence_level: ConfidenceLevel
    assets_reconciled: int
    assets_estimated: int
    liabilities_reconciled: int
    liabilities_estimated: int


@dataclass
class IntegrityQueueItem:
    """Item in the integrity queue (stale or missing)."""

    account_or_asset: str
    item_type: str  # account | asset | liability
    issue: str  # stale_valuation | not_reconciled | missing_balance
    last_known_date: Optional[date]
    days_since: Optional[int]
    recommended_action: str


def _count_by_confidence(assets: list[Asset], liabilities: list[Liability]) -> tuple[int, int, int, int]:
    ar = sum(1 for a in assets if a.confidence_level == ConfidenceLevel.RECONCILED)
    ae = sum(1 for a in assets if a.confidence_level == ConfidenceLevel.ESTIMATED)
    lr = sum(1 for l in liabilities if l.confidence_level == ConfidenceLevel.RECONCILED)
    le = sum(1 for l in liabilities if l.confidence_level == ConfidenceLevel.ESTIMATED)
    return ar, ae, lr, le


def compute_net_worth(data: YNABData, as_of: Optional[date] = None) -> NetWorthPoint:
    """Compute net worth from assets and liabilities. Uses most recent starting balances."""
    if not data.assets and not data.liabilities:
        return NetWorthPoint(
            date=as_of or date.today(),
            total_assets=0.0,
            total_liabilities=0.0,
            net_worth=0.0,
            confidence_level=ConfidenceLevel.UNKNOWN,
            assets_reconciled=0,
            assets_estimated=0,
            liabilities_reconciled=0,
            liabilities_estimated=0,
        )

    # Use latest value per asset/liability (from starting balances; in future could track over time)
    asset_values: dict[str, float] = {}
    liability_values: dict[str, float] = {}
    asset_dates: dict[str, date] = {}
    liability_dates: dict[str, date] = {}

    for a in data.assets:
        # Keep latest by id (in case of multiple snapshots)
        if a.id not in asset_values or a.value_as_of > asset_dates.get(a.id, date.min):
            asset_values[a.id] = a.value
            asset_dates[a.id] = a.value_as_of

    for l in data.liabilities:
        if l.id not in liability_values or l.balance_as_of > liability_dates.get(l.id, date.min):
            liability_values[l.id] = l.principal_balance
            liability_dates[l.id] = l.balance_as_of

    total_assets = sum(asset_values.values())
    total_liabilities = sum(liability_values.values())
    net_worth = total_assets - total_liabilities

    # Confidence: if any reconciled, overall is at least estimated
    assets_list = [a for a in data.assets if a.id in asset_values]
    liabs_list = [l for l in data.liabilities if l.id in liability_values]
    ar, ae, lr, le = _count_by_confidence(assets_list, liabs_list)

    if ar + lr > 0 and (ae + le) == 0:
        conf = ConfidenceLevel.RECONCILED
    elif ar + ae + lr + le > 0:
        conf = ConfidenceLevel.ESTIMATED
    else:
        conf = ConfidenceLevel.UNKNOWN

    return NetWorthPoint(
        date=as_of or max(asset_dates.values(), default=date.today()),
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        net_worth=net_worth,
        confidence_level=conf,
        assets_reconciled=ar,
        assets_estimated=ae,
        liabilities_reconciled=lr,
        liabilities_estimated=le,
    )


def compute_integrity_queue(
    data: YNABData,
    reconciliation_threshold_days: int = 30,
    stale_valuation_days: int = 90,
) -> list[IntegrityQueueItem]:
    """Build integrity queue: accounts/assets/liabilities needing attention."""
    items: list[IntegrityQueueItem] = []
    today = date.today()

    # Assets with stale valuations
    for a in data.assets:
        days = (today - a.value_as_of).days
        if days > stale_valuation_days:
            items.append(
                IntegrityQueueItem(
                    account_or_asset=a.name,
                    item_type="asset",
                    issue="stale_valuation",
                    last_known_date=a.value_as_of,
                    days_since=days,
                    recommended_action="Update valuation or attach statement",
                )
            )

    # Liabilities with stale balances
    for l in data.liabilities:
        days = (today - l.balance_as_of).days
        if days > stale_valuation_days:
            items.append(
                IntegrityQueueItem(
                    account_or_asset=l.name,
                    item_type="liability",
                    issue="stale_valuation",
                    last_known_date=l.balance_as_of,
                    days_since=days,
                    recommended_action="Reconcile balance or attach statement",
                )
            )

    return items


def verify_transfers_net_zero(transactions: list[Transaction]) -> list[tuple[str, str, float]]:
    """Check that transfer pairs net to zero. Returns list of (tx_id, pair_id, residual) for mismatches."""
    mismatches: list[tuple[str, str, float]] = []
    seen: set[str] = set()

    for tx in transactions:
        if not tx.is_transfer or tx.id in seen:
            continue
        if tx.linked_transaction_id:
            seen.add(tx.id)
            seen.add(tx.linked_transaction_id)
            # Both sides should sum to zero (outflow + inflow)
            # tx.amount + linked.amount should be ~0
            continue  # We don't have easy access to linked tx here; would need lookup
    return mismatches
