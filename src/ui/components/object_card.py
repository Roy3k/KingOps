"""Object Card — foundation unit for people, assets, policies, documents."""

from __future__ import annotations

from typing import Any, Callable

import streamlit as st

from src.ui.theme import theme


def object_card(
    title: str,
    subtitle: str | None = None,
    content: Any = None,
    *,
    explain: str | None = None,
    expandable: bool = True,
    render: Callable[[], None] | None = None,
) -> None:
    """
    Render an Object Card — soft leather background, rounded, no heavy borders.

    Supports layered disclosure via expandable section and optional explainability.
    Pass content (st.write-able) or render (callable that draws Streamlit widgets).
    """
    t = theme
    with st.container():
        st.markdown(
            f"""
            <div style="
                background: rgba(200, 184, 158, 0.35);
                padding: {t.spacing.md};
                border-radius: {t.radius.md};
                box-shadow: {t.shadow.card};
                border: 1px solid rgba(106, 94, 75, 0.08);
                margin-bottom: {t.spacing.md};
            ">
                <div style="font-family: {t.font_primary.family}; font-weight: 500; color: {t.color_base.slate_charcoal}; font-size: 1.05rem;">
                    {title}
                </div>
                {f'<div style="font-family: {t.font_secondary.family}; color: {t.color_base.river_stone}; font-size: 0.85rem; margin-top: 4px;">{subtitle}</div>' if subtitle else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )
        if render:
            render()
        elif content is not None:
            st.write(content)
        if explain and expandable:
            with st.expander("Why this matters", expanded=False):
                st.caption(explain)
        elif explain and not expandable:
            st.caption(explain)
