"""Assumption Disclosure Drawer — layered disclosure for scenario assumptions."""

from __future__ import annotations

from typing import Any, Sequence

import streamlit as st

from src.ui.theme import theme


def disclosure_drawer(
    title: str = "Assumptions & methodology",
    items: Sequence[dict[str, Any]] | None = None,
    *,
    default_expanded: bool = False,
) -> None:
    """
    Render expandable drawer for assumptions, audit logs, scenario inputs.

    Calm disclosure — no sudden modal intrusions.
    """
    with st.expander(title, expanded=default_expanded):
        if items:
            for item in items:
                if isinstance(item, dict):
                    for k, v in item.items():
                        st.write(f"**{k}:** {v}")
                else:
                    st.write(item)
        else:
            st.caption("No assumptions documented.")
