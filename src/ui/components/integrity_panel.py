"""Integrity Panel — stacked cards for attribution, what changed, audit."""

from __future__ import annotations

from typing import Any, Callable, Sequence

import streamlit as st

from src.ui.theme import theme


def _to_dict(item: Any) -> dict[str, Any]:
    """Convert dataclass or object to dict."""
    if isinstance(item, dict):
        return item
    if hasattr(item, "__dict__"):
        return {k: v for k, v in vars(item).items() if not k.startswith("_")}
    return {"value": str(item)}


def integrity_panel(
    items: Sequence[dict[str, Any] | Any],
    *,
    title: str = "Integrity Queue",
    empty_message: str = "No items requiring attention.",
    expander_label_fn: Callable[[dict], str] | None = None,
) -> None:
    """
    Render stacked cards — calm expandable rows for integrity queue items.

    Each item: account_or_asset, issue, item_type, last_known_date, days_since, recommended_action.
    Accepts dicts or dataclass instances.
    """
    st.subheader(title)
    if not items:
        st.success(empty_message)
        return

    for item in items:
        d = _to_dict(item)
        label = str(d.get("account_or_asset", "")) + " — " + str(d.get("issue", ""))
        if expander_label_fn:
            label = expander_label_fn(d)
        with st.expander(label, expanded=False):
            for key, val in d.items():
                if key not in ("account_or_asset", "issue"):
                    st.write(f"**{key.replace('_', ' ').title()}:** {val}")
