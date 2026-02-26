"""Household data store — focus areas, projects, todos. Persisted as JSON."""

from __future__ import annotations

import json
import uuid
from datetime import date
from pathlib import Path
from typing import Optional

import yaml

from src.schema.models import FocusArea, Person, Project, Todo


def _parse_dob(val) -> Optional[date]:
    """Parse dob from config (string or None) to date."""
    if val is None:
        return None
    if isinstance(val, date):
        return val
    try:
        return date.fromisoformat(str(val).strip())
    except (ValueError, TypeError):
        return None


def load_household_members(root: Path) -> list[Person]:
    """Load household members from config.yaml."""
    config_path = root / "config.yaml"
    if not config_path.exists():
        return []
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    members = cfg.get("household", {}).get("members", [])
    return [
        Person(
            id=m.get("id", ""),
            name=m.get("name", ""),
            role=m.get("role", "adult"),
            dob=_parse_dob(m.get("dob")),
        )
        for m in members
    ]


def _store_path(root: Path) -> Path:
    """Path to household JSON store."""
    return root / "data" / "household.json"


def _ensure_data_dir(root: Path) -> None:
    (root / "data").mkdir(exist_ok=True)


def _default_store() -> dict:
    return {
        "focus_areas": [],
        "projects": [],
        "todos": [],
    }


def load_store(root: Path) -> dict:
    """Load household store from JSON. Returns default if missing."""
    path = _store_path(root)
    if not path.exists():
        return _default_store()
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return _default_store()


def save_store(root: Path, store: dict) -> None:
    """Persist household store to JSON."""
    _ensure_data_dir(root)
    path = _store_path(root)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)


def get_focus_areas(root: Path) -> list[FocusArea]:
    """Load focus areas from store."""
    store = load_store(root)
    return [FocusArea(**fa) for fa in store.get("focus_areas", [])]


def add_focus_area(root: Path, name: str, description: Optional[str] = None) -> FocusArea:
    """Add a focus area and persist."""
    store = load_store(root)
    fa = FocusArea(
        id=f"fa_{uuid.uuid4().hex[:8]}",
        name=name,
        description=description,
    )
    store.setdefault("focus_areas", []).append(fa.model_dump())
    save_store(root, store)
    return fa


def delete_focus_area(root: Path, fa_id: str) -> None:
    """Remove focus area and unlink projects."""
    store = load_store(root)
    store["focus_areas"] = [fa for fa in store.get("focus_areas", []) if fa["id"] != fa_id]
    for p in store.get("projects", []):
        if p.get("focus_area_id") == fa_id:
            p["focus_area_id"] = None
    save_store(root, store)


def get_projects(root: Path, focus_area_id: Optional[str] = None) -> list[Project]:
    """Load projects, optionally filtered by focus area."""
    store = load_store(root)
    projects = [Project(**p) for p in store.get("projects", [])]
    if focus_area_id:
        projects = [p for p in projects if p.focus_area_id == focus_area_id]
    return projects


def add_project(root: Path, name: str, focus_area_id: Optional[str] = None) -> Project:
    """Add a project and persist."""
    store = load_store(root)
    proj = Project(
        id=f"proj_{uuid.uuid4().hex[:8]}",
        name=name,
        focus_area_id=focus_area_id,
        created_at=date.today().isoformat(),
    )
    store.setdefault("projects", []).append(proj.model_dump())
    save_store(root, store)
    return proj


def delete_project(root: Path, project_id: str) -> None:
    """Remove project and its todos."""
    store = load_store(root)
    store["projects"] = [p for p in store.get("projects", []) if p["id"] != project_id]
    store["todos"] = [t for t in store.get("todos", []) if t["project_id"] != project_id]
    save_store(root, store)


def get_todos(root: Path, project_id: str) -> list[Todo]:
    """Load todos for a project."""
    store = load_store(root)
    return [Todo(**t) for t in store.get("todos", []) if t["project_id"] == project_id]


def add_todo(root: Path, project_id: str, title: str, assignee_id: Optional[str] = None) -> Todo:
    """Add a todo and persist."""
    store = load_store(root)
    todo = Todo(
        id=f"todo_{uuid.uuid4().hex[:8]}",
        project_id=project_id,
        title=title,
        assignee_id=assignee_id,
        created_at=date.today().isoformat(),
    )
    store.setdefault("todos", []).append(todo.model_dump())
    save_store(root, store)
    return todo


def toggle_todo(root: Path, todo_id: str) -> None:
    """Toggle todo completed state."""
    store = load_store(root)
    for t in store.get("todos", []):
        if t["id"] == todo_id:
            t["completed"] = not t.get("completed", False)
            break
    save_store(root, store)


def update_todo_assignee(root: Path, todo_id: str, assignee_id: Optional[str]) -> None:
    """Update todo assignee."""
    store = load_store(root)
    for t in store.get("todos", []):
        if t["id"] == todo_id:
            t["assignee_id"] = assignee_id
            break
    save_store(root, store)


def delete_todo(root: Path, todo_id: str) -> None:
    """Remove a todo."""
    store = load_store(root)
    store["todos"] = [t for t in store.get("todos", []) if t["id"] != todo_id]
    save_store(root, store)
