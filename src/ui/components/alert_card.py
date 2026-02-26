"""Alert Card — subdued severity scale, no aggressive red badges."""

from __future__ import annotations

from enum import Enum
from typing import Callable

import streamlit as st

from src.ui.theme import theme


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


def alert_card(
    message: str,
    severity: AlertSeverity = AlertSeverity.INFO,
    *,
    evidence_link: str | None = None,
    resolve_label: str | None = None,
    on_resolve: Callable[[], None] | None = None,
) -> None:
    """
    Render an Alert Card — explanation first, evidence link, soft resolve button.

    Severity: info (green border), warning (brown edge), critical (ember tone).
    Never aggressive red.
    """
    t = theme
    colors = {
        AlertSeverity.INFO: t.color_alert.info,
        AlertSeverity.WARNING: t.color_alert.warning,
        AlertSeverity.CRITICAL: t.color_alert.critical,
    }
    border_color = colors[severity]

    html = f"""
    <div style="
        background: rgba(243, 239, 230, 0.9);
        border-left: 4px solid {border_color};
        padding: {t.spacing.md};
        border-radius: {t.radius.md};
        box-shadow: {t.shadow.card};
        margin-bottom: {t.spacing.md};
        font-family: {t.font_secondary.family};
        color: {t.color_base.slate_charcoal};
    ">
        {message}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if evidence_link:
            st.link_button("View evidence", evidence_link)
    with col3:
        if resolve_label and on_resolve:
            if st.button(resolve_label, key=f"alert_resolve_{id(on_resolve)}"):
                on_resolve()
        elif resolve_label:
            st.button(resolve_label, disabled=True, key=f"alert_resolve_{id(resolve_label)}")
