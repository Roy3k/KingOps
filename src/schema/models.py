"""Data models for KingOps household financial dashboard."""

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """Provenance/confidence for metrics per PRD anti-hallucination guardrails."""

    RECONCILED = "Reconciled"
    ESTIMATED = "Estimated"
    UNKNOWN = "Unknown"


class Person(BaseModel):
    """Household member."""

    id: str
    name: str
    role: str  # adult | dependent
    dob: Optional[date] = None
    employment: Optional[str] = None


class Account(BaseModel):
    """Financial account container."""

    id: str
    name: str
    account_type: str  # checking | savings | credit | loan | investment | other
    institution: Optional[str] = None
    tax_treatment: Optional[str] = None  # taxable | traditional | roth | etc.
    status: str = "active"
    last_reconciled_at: Optional[date] = None


class Transaction(BaseModel):
    """Register-normalized transaction."""

    id: str
    account_id: str
    date_posted: date
    date_effective: Optional[date] = None
    amount: float  # positive = inflow, negative = outflow
    direction: str  # in | out
    payee_raw: str
    payee_normalized: Optional[str] = None
    category_raw: Optional[str] = None
    category_normalized: Optional[str] = None
    category_group: Optional[str] = None
    memo: Optional[str] = None
    is_transfer: bool = False
    linked_transaction_id: Optional[str] = None
    confidence_score: Optional[float] = None
    confidence_level: ConfidenceLevel = ConfidenceLevel.RECONCILED
    source_file_id: Optional[str] = None
    source_row_index: Optional[int] = None
    cleared: Optional[str] = None  # Uncleared | Cleared | Reconciled


class Budget(BaseModel):
    """Budget plan entry."""

    id: str
    period: str  # e.g. "Jan 2025"
    category_group: str
    category: str
    assigned: float
    activity: float
    available: float
    source_file_id: Optional[str] = None


class Asset(BaseModel):
    """Asset with valuation."""

    id: str
    asset_type: str  # home | vehicle | brokerage | 401k | ira | 529 | other
    name: str
    value: float
    value_as_of: date
    valuation_method: str = "mark_to_market"  # mark_to_market | appraisal_based | user_estimate | amortized_cost
    cost_basis: Optional[float] = None
    linked_account_id: Optional[str] = None
    confidence_level: ConfidenceLevel = ConfidenceLevel.RECONCILED
    source_file_id: Optional[str] = None


class Liability(BaseModel):
    """Liability/obligation."""

    id: str
    liability_type: str  # mortgage | heloc | credit_card | auto_loan | student_loan | other
    name: str
    principal_balance: float
    balance_as_of: date
    rate: Optional[float] = None
    payment: Optional[float] = None
    linked_account_id: Optional[str] = None
    confidence_level: ConfidenceLevel = ConfidenceLevel.RECONCILED
    source_file_id: Optional[str] = None


class Policy(BaseModel):
    """Insurance policy."""

    id: str
    policy_type: str  # auto | home | umbrella | term_life | disability | etc.
    carrier: Optional[str] = None
    policy_number: Optional[str] = None
    premium: Optional[float] = None
    renewal_date: Optional[date] = None
    limits: Optional[dict] = None
    deductibles: Optional[dict] = None
    covered_people: list[str] = Field(default_factory=list)
    covered_assets: list[str] = Field(default_factory=list)
    status: str = "active"


class IngestionAudit(BaseModel):
    """Audit trail for data ingestion."""

    source_file_id: str
    filename: str
    upload_timestamp: str
    row_count: int
    parse_errors: list[str] = Field(default_factory=list)
    checksum_hash: Optional[str] = None


# -----------------------------------------------------------------------------
# Household / Projects / Todos
# -----------------------------------------------------------------------------


class FocusArea(BaseModel):
    """Household focus area — e.g. Home, Health, Finances, Kids."""

    id: str
    name: str
    description: Optional[str] = None
    color: Optional[str] = None  # Hex or theme token for card accent


class Project(BaseModel):
    """Project card — belongs to a focus area, has its own todo list."""

    id: str
    name: str
    focus_area_id: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[str] = None  # ISO date string


class Todo(BaseModel):
    """Todo item — belongs to a project, assignable to a person."""

    id: str
    project_id: str
    title: str
    assignee_id: Optional[str] = None  # person id from household
    due_date: Optional[str] = None  # ISO date
    completed: bool = False
    created_at: Optional[str] = None
