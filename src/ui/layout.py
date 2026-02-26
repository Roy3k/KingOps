"""
KingOps Layout — three-panel structure.

Left Panel (sidebar) → Foundation
Center Pane → Living Room (current focus)
Right Pane → Firelight Detail (context, actions, linked data)
"""

from __future__ import annotations

from typing import Any, Callable

import streamlit as st

from src.ui.theme import theme

# Object-oriented navigation (Section 4.2)
NAV_ITEMS = [
    ("Household", "household"),
    ("People", "people"),
    ("Projects", "projects"),
    ("Assets", "assets"),
    ("Obligations", "obligations"),
    ("Coverage", "coverage"),
    ("Capital", "capital"),
    ("Timeline", "timeline"),
    ("Documents", "documents"),
]

# Map nav keys to existing page modules
PAGE_MAP = {
    "assets": "net_worth",
    "capital": "allocation",
    "coverage": "risk",
    "timeline": "behavioral",
    "household": "household",
    "people": "people",
    "projects": "projects",
    "obligations": None,
    "documents": None,
}


def render_sidebar_nav() -> str:
    """Render quiet, architectural nav. Returns selected nav key."""
    st.sidebar.markdown("---")
    st.sidebar.caption("Navigate")
    labels = [label for label, _ in NAV_ITEMS]
    keys = [key for _, key in NAV_ITEMS]
    idx = st.sidebar.radio(
        "Nav",
        range(len(labels)),
        format_func=lambda i: labels[i],
        label_visibility="collapsed",
        key="nav_radio",
    )
    return keys[idx]


def render_three_panel(
    center_content: Callable[[], None],
    right_content: Callable[[], None] | None = None,
    *,
    center_cols: int = 3,
    right_cols: int = 1,
) -> None:
    """
    Render center (living room) + right (firelight detail) panels.

    Panels use rounded edges, soft shadows, generous spacing.
    """
    t = theme
    total = center_cols + right_cols
    center, right = st.columns([center_cols, right_cols])

    with center:
        center_content()

    with right:
        if right_content:
            st.markdown(
                f"""
                <div style="
                    background: rgba(200, 184, 158, 0.25);
                    padding: {t.spacing.md};
                    border-radius: {t.radius.md};
                    box-shadow: {t.shadow.card};
                    border: 1px solid rgba(106, 94, 75, 0.06);
                    min-height: 200px;
                ">
                    <div style="font-family: {t.font_primary.family}; font-size: 0.9rem; color: {t.color_base.slate_charcoal}; margin-bottom: {t.spacing.sm};">
                        Context
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            right_content()
