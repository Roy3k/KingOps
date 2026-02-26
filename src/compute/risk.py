"""Framework 3 — Risk & Insurance Coverage Map."""

import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from src.schema.models import Person, Policy


@dataclass
class CoverageMapItem:
    """People ↔ Risks ↔ Policies ↔ Limits."""

    person_id: Optional[str]
    person_name: Optional[str]
    risk_type: str
    policy_id: Optional[str]
    policy_type: Optional[str]
    carrier: Optional[str]
    limits: Optional[dict]
    renewal_date: Optional[date]
    status: str  # covered | unknown | gap


@dataclass
class RenewalEvent:
    """Upcoming renewal event."""

    policy_id: str
    policy_type: str
    renewal_date: date
    carrier: Optional[str]
    premium: Optional[float]
    days_until: int


def get_coverage_map(
    policies: list[Policy],
    people: list[Person],
) -> list[CoverageMapItem]:
    """Build coverage map: People ↔ Risks ↔ Policies ↔ Limits."""
    items: list[CoverageMapItem] = []
    if not policies:
        for p in people:
            items.append(
                CoverageMapItem(
                    person_id=p.id,
                    person_name=p.name,
                    risk_type="general",
                    policy_id=None,
                    policy_type=None,
                    carrier=None,
                    limits=None,
                    renewal_date=None,
                    status="unknown",
                )
            )
        return items

    for pol in policies:
        if pol.covered_people:
            for pid in pol.covered_people:
                p = next((x for x in people if x.id == pid), None)
                items.append(
                    CoverageMapItem(
                        person_id=pid,
                        person_name=p.name if p else pid,
                        risk_type=pol.policy_type,
                        policy_id=pol.id,
                        policy_type=pol.policy_type,
                        carrier=pol.carrier,
                        limits=pol.limits,
                        renewal_date=pol.renewal_date,
                        status="covered",
                    )
                )
        else:
            items.append(
                CoverageMapItem(
                    person_id=None,
                    person_name=None,
                    risk_type=pol.policy_type,
                    policy_id=pol.id,
                    policy_type=pol.policy_type,
                    carrier=pol.carrier,
                    limits=pol.limits,
                    renewal_date=pol.renewal_date,
                    status="covered",
                )
            )
    return items


def get_renewal_calendar(
    policies: list[Policy],
    lookahead_days: int = 365,
) -> list[RenewalEvent]:
    """Renewal calendar for policies with renewal dates."""
    today = date.today()
    events: list[RenewalEvent] = []
    for pol in policies:
        if not pol.renewal_date:
            continue
        days = (pol.renewal_date - today).days
        if 0 <= days <= lookahead_days:
            events.append(
                RenewalEvent(
                    policy_id=pol.id,
                    policy_type=pol.policy_type,
                    renewal_date=pol.renewal_date,
                    carrier=pol.carrier,
                    premium=pol.premium,
                    days_until=days,
                )
            )
    return sorted(events, key=lambda e: e.renewal_date)


def _parse_date(val: str) -> Optional[date]:
    """Parse date from string (YYYY-MM-DD or MM/DD/YYYY)."""
    if not val or str(val).strip() == "":
        return None
    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def load_policies_from_vault(vault_path: Path) -> list[Policy]:
    """Load policies from Vault/policies.csv. CSV columns: policy_type, carrier, policy_number, premium, renewal_date, covered_people."""
    import csv

    policies: list[Policy] = []
    csv_path = vault_path / "policies.csv"
    if not csv_path.exists():
        return []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            try:
                ptype = str(row.get("policy_type", "")).strip() or "unknown"
                carrier = str(row.get("carrier", "")).strip() or None
                pnum = str(row.get("policy_number", "")).strip() or None
                premium_val = row.get("premium", "")
                premium = None
                if premium_val:
                    s = re.sub(r"[^0-9.-]", "", str(premium_val).replace("$", "").replace(",", ""))
                    try:
                        premium = float(s) if s else None
                    except ValueError:
                        pass
                renewal = _parse_date(str(row.get("renewal_date", "")))
                covered = str(row.get("covered_people", "")).strip()
                covered_people = [x.strip() for x in covered.split(",") if x.strip()] if covered else []
                pid = f"pol_{i}_{ptype}"
                policies.append(
                    Policy(
                        id=pid,
                        policy_type=ptype,
                        carrier=carrier,
                        policy_number=pnum,
                        premium=premium,
                        renewal_date=renewal,
                        covered_people=covered_people,
                        status="active",
                    )
                )
            except Exception:
                continue
    return policies
