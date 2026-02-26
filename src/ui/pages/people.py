"""People page — household members from config."""

from pathlib import Path

import streamlit as st

from src.data.household_store import load_household_members
from src.ui.components.object_card import object_card
from src.ui.theme import theme


def render(data=None) -> None:
    """Render People view — 4 household members."""
    root = Path(__file__).resolve().parent.parent.parent.parent
    people = load_household_members(root)
    t = theme

    st.subheader("Household Members")
    st.caption("People from config.yaml — used for project assignments and todos.")

    if not people:
        st.info("No household members in config.yaml. Add a `household.members` section.")
        return

    for p in people:
        role_label = "Adult" if p.role == "adult" else "Dependent"
        dob_str = p.dob.strftime("%b %d, %Y") if p.dob else "—"
        object_card(
            title=p.name,
            subtitle=f"{role_label} · DOB: {dob_str}",
            content=None,
            expandable=False,
        )
