"""Allocation Flow Bar — horizontal flow, muted tonal segments, variance glow."""

from __future__ import annotations

from typing import Sequence

import streamlit as st

from src.ui.theme import theme


def allocation_flow_bar(
    segments: Sequence[tuple[str, float]],
    *,
    total: float | None = None,
    title: str | None = None,
) -> None:
    """
    Render horizontal flow bar — Sankey-like but restrained.

    segments: [(label, value), ...]
    Each segment uses muted tonal differences. Variance as subtle glow.
    """
    t = theme
    if not segments:
        return
    computed_total = sum(s[1] for s in segments)
    total_val = total or computed_total
    if total_val <= 0:
        return

    if title:
        st.markdown(f"**{title}**")

    # Build HTML for horizontal stacked bar
    colors = [t.color_accent.moss_green, t.color_accent.driftwood_brown, "#7A858F", "#8B9E7A", "#5a8a6a"]
    parts = []
    left = 0
    for i, (label, value) in enumerate(segments):
        pct = (value / total_val) * 100
        color = colors[i % len(colors)]
        parts.append(
            f'<div style="'
            f'position:absolute; left:{left}%; width:{pct}%; height:24px; '
            f'background:{color}; opacity:0.7; border-radius:2px; '
            f'display:flex; align-items:center; justify-content:center; '
            f'font-size:0.75rem; color:white; font-family:{t.font_secondary.family};'
            f'">{label} ({value:,.0f})</div>'
        )
        left += pct

    st.markdown(
        f"""
        <div style="
            position:relative; height:28px; background:rgba(106,94,75,0.1);
            border-radius:{t.radius.sm}; overflow:hidden; margin: {t.spacing.sm} 0;
        ">
            {''.join(parts)}
        </div>
        """,
        unsafe_allow_html=True,
    )
