"""Household overview — focus areas, add focus area."""

from pathlib import Path

import streamlit as st

from src.data.household_store import (
    add_focus_area,
    delete_focus_area,
    get_focus_areas,
    get_projects,
    load_household_members,
)
from src.ui.components.object_card import object_card


def render(data=None) -> None:
    """Render Household overview with focus areas."""
    root = Path(__file__).resolve().parent.parent.parent.parent
    people = load_household_members(root)
    focus_areas = get_focus_areas(root)

    st.subheader("Household Overview")
    st.caption(f"{len(people)} members · {len(focus_areas)} focus areas")

    # Add focus area form
    with st.expander("Add focus area", expanded=len(focus_areas) == 0):
        fa_name = st.text_input(
            "Name",
            placeholder="Home, Health, Finances, Kids",
            label_visibility="visible",
            key="fa_name_input",
        )
        fa_desc = st.text_area(
            "Description (optional)",
            placeholder="Short description of this focus area",
            label_visibility="visible",
            key="fa_desc_input",
        )
        if st.button("Add focus area") and fa_name.strip():
            add_focus_area(root, fa_name.strip(), fa_desc.strip() or None)
            st.rerun()

    # Focus area cards
    st.subheader("Focus Areas")
    if not focus_areas:
        st.caption("No focus areas yet. Add one above to organize projects.")
    else:
        for fa in focus_areas:
            proj_list = get_projects(root, focus_area_id=fa.id)
            with st.container():
                col_title, col_del = st.columns([4, 1])
                with col_title:
                    subtitle = fa.description or f"{len(proj_list)} project(s)"
                    if len(proj_list) == 0:
                        subtitle += " — Create projects in the Projects section"
                    object_card(
                        title=fa.name,
                        subtitle=subtitle,
                        expandable=False,
                    )
                with col_del:
                    if st.button("🗑", key=f"del_fa_{fa.id}", help="Delete focus area"):
                        delete_focus_area(root, fa.id)
                        st.rerun()
