"""Net Worth Evolution view — terrain-like, attribution, calm disclosure."""

import streamlit as st
import plotly.graph_objects as go

from src.compute.balance_sheet import compute_integrity_queue, compute_net_worth
from src.ingest.ynab import YNABData
from src.ui.components.alert_card import AlertSeverity, alert_card
from src.ui.components.disclosure_drawer import disclosure_drawer
from src.ui.components.integrity_panel import integrity_panel
from src.ui.theme import theme


def render(data: YNABData) -> None:
    """Render Net Worth Evolution view — Section 5.1 memo."""
    nw = compute_net_worth(data)
    queue = compute_integrity_queue(data)
    t = theme

    st.subheader("Net Worth Evolution")

    if nw.confidence_level.value == "Unknown":
        alert_card(
            "No asset or liability data. Add account starting balances or import from YNAB. "
            "Register CSV with Starting Balance rows, or manual asset/liability inventory.",
            severity=AlertSeverity.WARNING,
        )

    # Attribution summary in clean stacked cards (Section 5.1)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total Assets",
            f"${nw.total_assets:,.0f}",
            help=f"Reconciled: {nw.assets_reconciled}, Estimated: {nw.assets_estimated}",
        )
    with col2:
        st.metric(
            "Total Liabilities",
            f"${nw.total_liabilities:,.0f}",
            help=f"Reconciled: {nw.liabilities_reconciled}, Estimated: {nw.liabilities_estimated}",
        )
    with col3:
        st.metric(
            "Net Worth",
            f"${nw.net_worth:,.0f}",
            help=f"Confidence: {nw.confidence_level.value}",
        )

    st.caption(f"**Provenance:** YNAB starting balances | **Confidence:** {nw.confidence_level.value}")

    # Soft line/bar — muted forest green, no grid clutter, light guides (Section 5.1)
    if data.assets or data.liabilities:
        fig = go.Figure()
        assets_vals = [a.value for a in data.assets]
        liab_vals = [l.principal_balance for l in data.liabilities]
        labels = [a.name for a in data.assets] + [l.name for l in data.liabilities]
        values = assets_vals + [-v for v in liab_vals]
        colors = [t.color_accent.moss_green] * len(assets_vals) + [t.color_accent.driftwood_brown] * len(liab_vals)
        fig.add_trace(
            go.Bar(
                x=labels,
                y=values,
                marker_color=colors,
                marker_line_width=0,
                name="Balance",
            )
        )
        fig.update_layout(
            title="Assets & Liabilities Snapshot",
            yaxis_title="Amount ($)",
            showlegend=False,
            margin=dict(l=20, r=20, t=40, b=120),
            xaxis_tickangle=-45,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(232, 228, 220, 0.3)",
            font=dict(family=t.font_secondary.family),
            xaxis=dict(showgrid=False),
            yaxis=dict(
                gridcolor="rgba(106, 94, 75, 0.12)",
                zeroline=True,
                zerolinecolor="rgba(106, 94, 75, 0.2)",
            ),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Integrity Queue — calm expandable rows (Section 5.1)
    integrity_panel(
        queue,
        title="What changed? Integrity Queue",
        empty_message="No items requiring attention.",
    )

    disclosure_drawer(
        "Attribution & methodology",
        [
            {"Source": "YNAB Plan & Register CSV"},
            {"Confidence": nw.confidence_level.value},
            {"Assets reconciled": nw.assets_reconciled, "Assets estimated": nw.assets_estimated},
        ],
    )
