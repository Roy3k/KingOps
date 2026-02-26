"""Cash Flow Allocation view — horizontal flow bars, budget vs actual, restrained."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from src.compute.cash_flow import (
    get_allocation_sankey_data,
    get_monthly_allocation,
    get_uncategorized_inbox,
    get_variance_drivers,
)
from src.ingest.ynab import YNABData
from src.ui.components.allocation_flow_bar import allocation_flow_bar
from src.ui.components.disclosure_drawer import disclosure_drawer
from src.ui.theme import theme


def render(data: YNABData) -> None:
    """Render Cash Flow Allocation view — Section 5.2 memo."""
    allocation = get_monthly_allocation(data)
    periods = sorted(set(a.period for a in allocation), reverse=True)
    selected_period = st.selectbox("Period", periods, index=0) if periods else None

    if selected_period:
        alloc_period = [a for a in allocation if a.period == selected_period]
        df = pd.DataFrame(
            [
                {
                    "Category Group": a.category_group,
                    "Category": a.category,
                    "Planned": a.planned,
                    "Actual": a.actual,
                    "Variance": a.variance,
                }
                for a in alloc_period
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Allocation Flow")
    sankey = get_allocation_sankey_data(data, selected_period)
    t = theme

    if sankey.get("income", 0) > 0:
        # Horizontal flow bar — muted tonal segments (Section 5.2)
        segments = [
            ("Needs", sankey.get("needs", 0)),
            ("Wants", sankey.get("wants", 0)),
            ("Debt", sankey.get("debt", 0)),
            ("Savings", sankey.get("savings", 0)),
        ]
        allocation_flow_bar(segments, total=sankey.get("income"), title="Income → Allocation")

        # Restrained Sankey (Section 5.2)
        fig = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="rgba(42, 42, 42, 0.08)", width=0.5),
                        label=["Income", "Needs", "Wants", "Debt", "Savings"],
                        color=[
                            t.color_accent.moss_green,
                            t.color_accent.moss_green,
                            t.color_accent.driftwood_brown,
                            "#7A858F",
                            "#556B57",
                        ],
                    ),
                    link=dict(
                        source=[0, 0, 0, 0],
                        target=[1, 2, 3, 4],
                        value=[
                            sankey.get("needs", 0),
                            sankey.get("wants", 0),
                            sankey.get("debt", 0),
                            sankey.get("savings", 0),
                        ],
                    ),
                )
            ]
        )
        fig.update_layout(
            title="Income → Needs → Wants → Debt → Savings",
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family=t.font_secondary.family),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Income data not available. Add inflow transactions to see allocation.")

    # Variance drivers — calm expandable, variance as number not loud color (Section 5.2)
    st.subheader("Variance Drivers")
    drivers = get_variance_drivers(data, allocation, top_n=10)
    if drivers:
        for d in drivers:
            st.write(f"**{d.merchant_or_category}** ({d.period}): ${d.variance:,.2f}")
    else:
        st.caption("No significant variance drivers.")

    st.subheader("Uncategorized Inbox")
    inbox = get_uncategorized_inbox(data)
    if not inbox:
        st.success("No uncategorized transactions.")
    else:
        st.caption(f"{len(inbox)} transactions need categorization.")
        for item in inbox[:20]:
            st.write(f"- {item.date} | {item.payee} | ${item.amount:,.2f} | {item.account}")

    disclosure_drawer(
        "Allocation methodology",
        [
            {"Rollup": "Core/True → needs, Subs/QoL → wants, LT/Projects → savings"},
            {"Source": "YNAB Plan Activity"},
        ],
    )
