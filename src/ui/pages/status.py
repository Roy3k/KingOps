"""Status page — household snapshot: focus areas, projects, open todos, data lineage."""

from datetime import date
from pathlib import Path

import streamlit as st

from src.data.household_store import (
    get_focus_areas,
    get_projects,
    get_todos,
    load_household_members,
)
from src.ui.components.object_card import object_card


def render(data=None) -> None:
    """Render Status overview — at-a-glance household and data state."""
    root = Path(__file__).resolve().parent.parent.parent.parent

    people = load_household_members(root)
    focus_areas = get_focus_areas(root)
    projects = get_projects(root)

    open_todos: list = []
    completed_todos: list = []
    for proj in projects:
        for todo in get_todos(root, proj.id):
            if todo.completed:
                completed_todos.append((proj, todo))
            else:
                open_todos.append((proj, todo))

    st.subheader("Status")
    st.caption(f"Snapshot · {date.today().strftime('%A, %b %d, %Y')}")

    # Top-level metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Household", len(people))
    m2.metric("Focus areas", len(focus_areas))
    m3.metric("Projects", len(projects))
    m4.metric("Open todos", len(open_todos))

    # Financial data lineage
    st.markdown("---")
    st.markdown("**Financial data**")
    if data is not None:
        f1, f2 = st.columns(2)
        f1.metric("Transactions", f"{len(data.transactions):,}")
        f2.metric("Accounts", len(data.accounts))
        st.caption("Source: YNAB Plan & Register CSV")
    else:
        st.caption("No financial dataset loaded for this view. Open Assets, Capital, Coverage, or Timeline to load YNAB data.")

    # Open todos
    st.markdown("---")
    st.markdown("**Open todos**")
    if not open_todos:
        st.caption("No open todos. Add tasks under Projects.")
    else:
        people_map = {p.id: p.name for p in people}
        for proj, todo in open_todos:
            assignee = people_map.get(todo.assignee_id, "—") if todo.assignee_id else "—"
            object_card(
                title=todo.title,
                subtitle=f"{proj.name} · Assigned to {assignee}",
                expandable=False,
            )

    # Recently completed
    if completed_todos:
        st.markdown("---")
        st.markdown(f"**Recently completed** ({len(completed_todos)})")
        for proj, todo in completed_todos[-5:]:
            st.caption(f"✓ {todo.title} — {proj.name}")
