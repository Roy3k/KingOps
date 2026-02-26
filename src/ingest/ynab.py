"""YNAB CSV ingestion pipeline."""

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from src.schema.models import (
    Account,
    Asset,
    Budget,
    ConfidenceLevel,
    IngestionAudit,
    Liability,
    Transaction,
)


def _parse_dollar(val: str) -> float:
    """Parse YNAB dollar string ($1,234.56 or -$1,234.56) to float."""
    if pd.isna(val) or val == "" or val == "$0.00":
        return 0.0
    s = str(val).replace("$", "").replace(",", "").strip()
    return float(s) if s else 0.0


def _parse_date(val: str) -> Optional[datetime]:
    """Parse MM/DD/YYYY to date."""
    if pd.isna(val) or val == "":
        return None
    try:
        dt = datetime.strptime(str(val).strip(), "%m/%d/%Y")
        return dt
    except ValueError:
        return None


def _infer_account_type(name: str) -> str:
    """Infer account type from name patterns."""
    name_lower = name.lower()
    if "checking" in name_lower or "savings" in name_lower:
        return "checking" if "checking" in name_lower else "savings"
    if "401" in name or "401k" in name_lower or "ira" in name_lower:
        return "investment"
    if "college" in name_lower or "529" in name:
        return "investment"
    if "stocks" in name_lower:
        return "investment"
    if "house" in name_lower and "mortgage" not in name_lower:
        return "asset"
    if "mortgage" in name_lower or "heloc" in name_lower:
        return "loan"
    if any(x in name_lower for x in ["%", "prime", "apple card", "disney", "freedom", "capital one", "citi", "amex"]):
        return "credit"
    if name_lower in ["paypal", "venmo", "cash", "axos"]:
        return "checking"
    return "other"


def _infer_asset_type(name: str, account_type: str) -> str:
    """Map to Asset.asset_type: home | vehicle | brokerage | 401k | ira | 529 | other."""
    name_lower = name.lower()
    if "house" in name_lower and "mortgage" not in name_lower:
        return "home"
    if "401" in name or "401k" in name_lower:
        return "401k"
    if "ira" in name_lower:
        return "ira"
    if "college" in name_lower or "529" in name:
        return "529"
    if "stocks" in name_lower or account_type == "investment":
        return "brokerage"
    return "other"


def _infer_liability_type(name: str, account_type: str) -> str:
    """Map to Liability.liability_type."""
    name_lower = name.lower()
    if "mortgage" in name_lower:
        return "mortgage"
    if "heloc" in name_lower:
        return "heloc"
    if account_type == "credit":
        return "credit_card"
    return "other"


def _account_id(name: str) -> str:
    """Generate stable account id from name."""
    return re.sub(r"[^a-z0-9]", "_", name.lower().strip())


def load_plan_csv(path: Path) -> tuple[list[Budget], IngestionAudit]:
    """Load YNAB Plan CSV."""
    df = pd.read_csv(path)
    audits: list[str] = []
    budgets: list[Budget] = []

    for idx, row in df.iterrows():
        try:
            month = str(row.get("Month", "")).strip()
            cat_group = str(row.get("Category Group", "")).strip()
            category = str(row.get("Category", "")).strip()
            assigned = _parse_dollar(str(row.get("Assigned", 0)))
            activity = _parse_dollar(str(row.get("Activity", 0)))
            available = _parse_dollar(str(row.get("Available", 0)))

            bid = f"b_{month}_{cat_group}_{category}".replace(" ", "_").replace("/", "_")
            budgets.append(
                Budget(
                    id=bid,
                    period=month,
                    category_group=cat_group,
                    category=category,
                    assigned=assigned,
                    activity=activity,
                    available=available,
                    source_file_id=path.name,
                )
            )
        except Exception as e:
            audits.append(f"Row {idx}: {e}")

    checksum = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    audit = IngestionAudit(
        source_file_id=f"{path.name}_{checksum}",
        filename=path.name,
        upload_timestamp=datetime.now().isoformat(),
        row_count=len(df),
        parse_errors=audits,
        checksum_hash=checksum,
    )
    return budgets, audit


def load_register_csv(path: Path) -> tuple[list[Account], list[Transaction], list[Asset], list[Liability], IngestionAudit]:
    """Load YNAB Register CSV, extract accounts, transactions, assets, liabilities."""
    df = pd.read_csv(path)
    audits: list[str] = []
    accounts_map: dict[str, Account] = {}
    transactions: list[Transaction] = []
    assets: list[Asset] = []
    liabilities: list[Liability] = []

    # First pass: collect unique accounts
    for acc_name in df["Account"].dropna().unique():
        acc_name = str(acc_name).strip()
        if not acc_name:
            continue
        aid = _account_id(acc_name)
        if aid not in accounts_map:
            accounts_map[aid] = Account(
                id=aid,
                name=acc_name,
                account_type=_infer_account_type(acc_name),
                institution=None,
                status="active",
            )

    for idx, row in df.iterrows():
        try:
            acc_name = str(row.get("Account", "")).strip()
            date_val = _parse_date(str(row.get("Date", "")))
            payee = str(row.get("Payee", "")).strip()
            cat_combo = str(row.get("Category Group/Category", ""))
            cat_group = str(row.get("Category Group", ""))
            category = str(row.get("Category", ""))
            memo = str(row.get("Memo", "")).strip() if pd.notna(row.get("Memo")) else ""
            outflow = _parse_dollar(str(row.get("Outflow", 0)))
            inflow = _parse_dollar(str(row.get("Inflow", 0)))
            cleared = str(row.get("Cleared", "")).strip() if pd.notna(row.get("Cleared")) else None

            if not date_val or not acc_name:
                continue

            acc_id = _account_id(acc_name)

            # Starting balance -> Asset or Liability
            if payee == "Starting Balance":
                amt = inflow - outflow
                acc_type = accounts_map[acc_id].account_type if acc_id in accounts_map else "other"
                if amt > 0:
                    assets.append(
                        Asset(
                            id=f"asset_{acc_id}",
                            asset_type=_infer_asset_type(acc_name, acc_type),
                            name=acc_name,
                            value=amt,
                            value_as_of=date_val.date(),
                            valuation_method="mark_to_market",
                            confidence_level=ConfidenceLevel.RECONCILED,
                            source_file_id=path.name,
                        )
                    )
                else:
                    liabilities.append(
                        Liability(
                            id=f"liab_{acc_id}",
                            liability_type=_infer_liability_type(acc_name, acc_type),
                            name=acc_name,
                            principal_balance=abs(amt),
                            balance_as_of=date_val.date(),
                            linked_account_id=acc_id,
                            confidence_level=ConfidenceLevel.RECONCILED,
                            source_file_id=path.name,
                        )
                    )
                continue

            # Regular transaction
            amount = inflow - outflow
            direction = "in" if amount >= 0 else "out"
            is_transfer = payee.startswith("Transfer :")
            conf = ConfidenceLevel.RECONCILED if cleared == "Reconciled" else (ConfidenceLevel.ESTIMATED if cleared == "Cleared" else ConfidenceLevel.ESTIMATED)

            tid = f"tx_{idx}_{acc_id}_{date_val.strftime('%Y%m%d')}"
            tx = Transaction(
                id=tid,
                account_id=acc_id,
                date_posted=date_val.date(),
                date_effective=date_val.date(),
                amount=amount,
                direction=direction,
                payee_raw=payee,
                category_raw=cat_combo if cat_combo else None,
                category_group=cat_group if cat_group else None,
                category_normalized=category if category else None,
                memo=memo if memo else None,
                is_transfer=is_transfer,
                confidence_level=conf,
                source_file_id=path.name,
                source_row_index=int(idx),
                cleared=cleared,
            )
            transactions.append(tx)

        except Exception as e:
            audits.append(f"Row {idx}: {e}")

    # Link transfer pairs
    transfer_txs = [(i, t) for i, t in enumerate(transactions) if t.is_transfer]
    for i, tx in transfer_txs:
        # Payee format: "Transfer : AccountName"
        if "Transfer :" in tx.payee_raw:
            other_acc = tx.payee_raw.replace("Transfer :", "").strip()
            other_id = _account_id(other_acc)
            amt = abs(tx.amount)
            date_str = tx.date_posted.isoformat()
            # Find matching transfer (opposite direction, same date, same amount)
            for j, ot in enumerate(transactions):
                if j == i:
                    continue
                if ot.is_transfer and ot.account_id == other_id and ot.date_posted == tx.date_posted and abs(abs(ot.amount) - amt) < 0.01:
                    transactions[i].linked_transaction_id = ot.id
                    transactions[j].linked_transaction_id = tx.id
                    break

    checksum = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    audit = IngestionAudit(
        source_file_id=f"{path.name}_{checksum}",
        filename=path.name,
        upload_timestamp=datetime.now().isoformat(),
        row_count=len(df),
        parse_errors=audits,
        checksum_hash=checksum,
    )
    return list(accounts_map.values()), transactions, assets, liabilities, audit


class YNABData:
    """Container for loaded YNAB data."""

    def __init__(
        self,
        accounts: list[Account],
        transactions: list[Transaction],
        budgets: list[Budget],
        assets: list[Asset],
        liabilities: list[Liability],
        plan_audit: IngestionAudit,
        register_audit: IngestionAudit,
    ):
        self.accounts = accounts
        self.transactions = transactions
        self.budgets = budgets
        self.assets = assets
        self.liabilities = liabilities
        self.plan_audit = plan_audit
        self.register_audit = register_audit


def discover_vault_datasets(project_root: Path, vault_folder: str = "Vault") -> list[tuple[Path, Path]]:
    """Discover Plan+Register CSV pairs in Vault. Returns [(plan_path, register_path), ...]."""
    vault = project_root / vault_folder
    if not vault.exists():
        return []
    plan_files = sorted(vault.glob("*Plan*.csv"))
    reg_files = list(vault.glob("*Register*.csv"))
    pairs: list[tuple[Path, Path]] = []
    for pf in plan_files:
        # YNAB: "2025 Budget as of 2026-02-26 09-33 - Plan.csv" / " - Register.csv"
        base = pf.stem.replace(" - Plan", "").replace("- Plan", "").strip()
        match = None
        for rf in reg_files:
            rf_base = rf.stem.replace(" - Register", "").replace("- Register", "").strip()
            if base == rf_base:
                match = rf
                break
        if match:
            pairs.append((pf, match))
        elif len(reg_files) == 1:
            pairs.append((pf, reg_files[0]))
    return pairs


def load_ynab_data(
    project_root: Path,
    config: Optional[dict] = None,
    plan_path_override: Optional[Path] = None,
    register_path_override: Optional[Path] = None,
) -> YNABData:
    """Load Plan and Register CSVs from config, Vault, or explicit overrides."""
    if config is None:
        config = {}
    data = config.get("data", {})
    plan_path = plan_path_override or (project_root / data.get("plan_csv", "2025 Budget as of 2026-02-26 09-33 - Plan.csv"))
    register_path = register_path_override or (project_root / data.get("register_csv", "2025 Budget as of 2026-02-26 09-33 - Register.csv"))

    # Also check Vault if paths don't exist
    vault = project_root / data.get("vault_folder", "Vault")
    if not plan_path.exists() and vault.exists():
        plan_candidates = list(vault.glob("*Plan*.csv"))
        if plan_candidates:
            plan_path = plan_candidates[0]
    if not register_path.exists() and vault.exists():
        reg_candidates = list(vault.glob("*Register*.csv"))
        if reg_candidates:
            register_path = reg_candidates[0]

    if not plan_path.exists():
        raise FileNotFoundError(f"Plan CSV not found: {plan_path}")
    if not register_path.exists():
        raise FileNotFoundError(f"Register CSV not found: {register_path}")

    budgets, plan_audit = load_plan_csv(plan_path)
    accounts, transactions, assets, liabilities, register_audit = load_register_csv(register_path)

    return YNABData(
        accounts=accounts,
        transactions=transactions,
        budgets=budgets,
        assets=assets,
        liabilities=liabilities,
        plan_audit=plan_audit,
        register_audit=register_audit,
    )
