"""Behavioral Surfaces view — subdued metrics, calm disclosure."""

import streamlit as st
import plotly.express as px
import pandas as pd

from src.compute.behavioral import (
    get_category_volatility,
    get_fragmentation_metrics,
    get_subscription_inventory,
    get_uncategorized_queue,
)
from src.ingest.ynab import YNABData
from src.ui.components.alert_card import AlertSeverity, alert_card
from src.ui.theme import theme


def render(data: YNABData) -> None:
    """Render Behavioral Surfaces view."""
    t = theme

    if not data.transactions:
        alert_card(
            "No transaction data. Import Register CSV with Account, Date, Payee, Outflow, Inflow, Category.",
            severity=AlertSeverity.WARNING,
        )
        return

    st.subheader("Subscription Inventory")
    subs = get_subscription_inventory(data)
    if subs:
        df = pd.DataFrame(
            [
                {
                    "Name": s.name,
                    "Category": s.category,
                    "Last Amount": f"${s.last_amount:,.2f}",
                    "Last Date": s.last_date,
                    "Renewal": s.renewal_note or "—",
                }
                for s in subs
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.caption("No subscriptions detected.")

    st.subheader("Fragmentation Metrics")
    frag = get_fragmentation_metrics(data)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Accounts used (monthly)", frag.accounts_used_monthly)
    with col2:
        st.metric("Uncategorized count", frag.uncategorized_count)
    with col3:
        st.metric("Uncategorized rate", f"{frag.uncategorized_rate:.1%}")

    st.subheader("Category Volatility")
    vol = get_category_volatility(data, months=6)
    if vol:
        df_vol = pd.DataFrame(vol)
        df_vol = df_vol.T
        fig = px.imshow(
            df_vol,
            labels=dict(x="Month", y="Category", color="Spend"),
            aspect="auto",
            color_continuous_scale=["#F3EFE6", "#556B57", "#2F4A3E"],
        )
        fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family=t.font_secondary.family),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("No volatility data.")

    st.subheader("Uncategorized Queue")
    uq = get_uncategorized_queue(data)
    if not uq:
        st.success("No uncategorized transactions.")
    else:
        st.caption(f"{len(uq)} transactions need categorization.")
        for txn in uq[:15]:
            st.write(f"- {txn.date_posted} | {txn.payee_raw} | ${abs(txn.amount):,.2f} | {txn.account_id}")
