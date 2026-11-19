"""Obligations view — debts and recurring fixed costs."""

import pandas as pd
import streamlit as st

from src.compute.obligations import get_debts, get_recurring_obligations
from src.ingest.ynab import YNABData
from src.ui.components.disclosure_drawer import disclosure_drawer

MONTHS = 6


def render(data: YNABData) -> None:
    """Render debts (balance, rate, payment activity) and fixed monthly costs."""
    debts = get_debts(data, MONTHS)
    recurring = get_recurring_obligations(data, MONTHS)

    st.subheader("Obligations")
    st.caption(f"Balances as of {data.as_of:%b %d, %Y} · activity over the last {MONTHS} months")

    total_debt = sum(d.balance for d in debts)
    est_interest = sum(d.est_monthly_interest or 0 for d in debts)
    fixed_monthly = recurring["Average"].sum() if not recurring.empty else 0.0
    k1, k2, k3 = st.columns(3)
    k1.metric("Total debt", f"${total_debt:,.0f}")
    k2.metric("Est. interest / month", f"${est_interest:,.0f}", help="Balance × APR ÷ 12, APR read from the account name")
    k3.metric("Fixed costs / month", f"${fixed_monthly:,.0f}", help=f"{MONTHS}-month average of the categories below")

    st.markdown("**Debts**")
    if debts:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Debt": d.name,
                        "Type": d.liability_type.replace("_", " "),
                        "Balance": d.balance,
                        "APR": d.rate * 100 if d.rate is not None else None,
                        "Est. interest / mo": d.est_monthly_interest,
                        "Paid / mo": d.avg_monthly_paid,
                        "Added / mo": d.avg_monthly_added,
                        f"{MONTHS}-mo change": d.balance_change,
                    }
                    for d in debts
                ]
            ),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Balance": st.column_config.NumberColumn(format="$%.0f"),
                "APR": st.column_config.NumberColumn(format="%.0f%%"),
                "Est. interest / mo": st.column_config.NumberColumn(format="$%.0f"),
                "Paid / mo": st.column_config.NumberColumn(format="$%.0f"),
                "Added / mo": st.column_config.NumberColumn(format="$%.0f", help="Charges, draws, interest and fees"),
                f"{MONTHS}-mo change": st.column_config.NumberColumn(format="$%.0f", help="Positive = owed more than at the start"),
            },
        )
    else:
        st.success("No liabilities found.")

    st.markdown("**Recurring fixed costs**")
    if recurring.empty:
        st.caption("No fixed-cost categories matched.")
    else:
        money_cols = [c for c in recurring.columns if c not in ("Bucket", "Category")]
        st.dataframe(
            recurring,
            use_container_width=True,
            hide_index=True,
            column_config={c: st.column_config.NumberColumn(format="$%.0f") for c in money_cols},
        )

    disclosure_drawer(
        "Obligations methodology",
        [
            {"Balances": "Register running balance per account as of the export date"},
            {"APR": "Read from the account name (e.g. '*19% Disney 3701')"},
            {"Paid / Added": "Inflows to / outflows from the debt account, averaged per month"},
            {"Fixed costs": "Plan activity for housing, debt interest, taxes, auto, utilities and tuition categories"},
        ],
    )
