"""Projects page — project cards with per-project todo system."""

from pathlib import Path

import streamlit as st

from src.data.household_store import (
    add_project,
    add_todo,
    delete_project,
    delete_todo,
    get_focus_areas,
    get_projects,
    get_todos,
    load_household_members,
    toggle_todo,
    update_todo_assignee,
)
from src.ui.theme import theme


def _project_card(root: Path, project, people: list, focus_areas: list) -> None:
    """Render a single project card with its todo list."""
    t = theme
    fa_name = next((fa.name for fa in focus_areas if fa.id == project.focus_area_id), None)
    subtitle = f"Focus: {fa_name}" if fa_name else "No focus area"

    st.markdown(
        f"""
        <div style="
            background: rgba(200, 184, 158, 0.4);
            padding: {t.spacing.md};
            border-radius: {t.radius.md};
            box-shadow: {t.shadow.card};
            border: 1px solid rgba(106, 94, 75, 0.1);
            margin-bottom: {t.spacing.lg};
        ">
            <div style="font-family: {t.font_primary.family}; font-weight: 500; color: {t.color_base.slate_charcoal}; font-size: 1.1rem;">
                {project.name}
            </div>
            <div style="font-family: {t.font_secondary.family}; color: {t.color_base.river_stone}; font-size: 0.85rem; margin-top: 4px;">
                {subtitle}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    todos = get_todos(root, project.id)
    people_map = {p.id: p.name for p in people}

    # Add todo form
    todo_col1, todo_col2, todo_col3 = st.columns([3, 1, 1])
    with todo_col1:
        new_todo = st.text_input(
            "New todo",
            key=f"new_todo_{project.id}",
            placeholder="Enter task description",
            label_visibility="visible",
        )
    with todo_col2:
        assignee_options = ["— Unassigned"] + [p.name for p in people]
        assignee_idx = st.selectbox(
            "Assign to",
            range(len(assignee_options)),
            format_func=lambda i: assignee_options[i],
            key=f"assignee_{project.id}",
        )
        assignee_id = None if assignee_idx == 0 else people[assignee_idx - 1].id
    with todo_col3:
        add_clicked = st.button("Add", key=f"add_todo_{project.id}")

    if add_clicked and new_todo.strip():
        add_todo(root, project.id, new_todo.strip(), assignee_id)
        st.rerun()

    # Todo list
    if not todos:
        st.caption("No todos yet. Add one above.")
    else:
        for todo in todos:
            assignee_name = people_map.get(todo.assignee_id, "—") if todo.assignee_id else "—"
            text_col, toggle_col, del_col = st.columns([4, 1, 1])
            with text_col:
                done_str = "✓" if todo.completed else "○"
                style = "line-through; color: var(--color-river-stone)" if todo.completed else "none; color: var(--color-slate)"
                st.markdown(
                    f"<span style='text-decoration: {style}; font-family: var(--font-secondary);'>"
                    f"{done_str} **{todo.title}** <small style='color: var(--color-river-stone)'>({assignee_name})</small>"
                    f"</span>",
                    unsafe_allow_html=True,
                )
            with toggle_col:
                if st.button("✓" if not todo.completed else "↺", key=f"toggle_{todo.id}", help="Toggle complete"):
                    toggle_todo(root, todo.id)
                    st.rerun()
            with del_col:
                if st.button("🗑", key=f"del_todo_{todo.id}", help="Delete"):
                    delete_todo(root, todo.id)
                    st.rerun()

    # Delete project
    if st.button("Delete project", key=f"del_proj_{project.id}"):
        delete_project(root, project.id)
        st.rerun()


def render(data=None) -> None:
    """Render Projects view — project cards with todos."""
    root = Path(__file__).resolve().parent.parent.parent.parent
    people = load_household_members(root)
    focus_areas = get_focus_areas(root)
    projects = get_projects(root)
    t = theme

    st.subheader("Projects")
    st.caption("Project cards with their own todo lists. Assign tasks to household members.")

    # Add project form
    with st.expander("Create project", expanded=len(projects) == 0):
        proj_name = st.text_input(
            "Project name",
            placeholder="Kitchen remodel, Vacation planning, etc.",
            label_visibility="visible",
            key="new_proj_name",
        )
        fa_options = ["— No focus area"] + [fa.name for fa in focus_areas]
        fa_idx = st.selectbox(
            "Focus area",
            range(len(fa_options)),
            format_func=lambda i: fa_options[i],
            key="new_proj_fa",
        )
        focus_area_id = None if fa_idx == 0 else focus_areas[fa_idx - 1].id
        if st.button("Create project") and proj_name.strip():
            add_project(root, proj_name.strip(), focus_area_id)
            st.rerun()

    # Project cards
    if not projects:
        st.info("No projects yet. Create one above.")
    else:
        for proj in projects:
            _project_card(root, proj, people, focus_areas)
