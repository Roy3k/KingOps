"""
KingOps — Intelligent Household Financial Dashboard

Pacific Northwest × Japanese Tea Garden design.
"""

from pathlib import Path

import streamlit as st
import yaml

from src.ingest.ynab import discover_vault_datasets, load_ynab_data
from src.ui.layout import NAV_ITEMS, PAGE_MAP
from src.ui.pages import allocation, behavioral, household, net_worth, people, projects, risk

# Page config
st.set_page_config(
    page_title="KingOps",
    page_icon="🌲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Design system: Pacific Northwest × Japanese Tea Garden
from src.ui.styles import get_full_styles

st.markdown(f"<style>{get_full_styles()}</style>", unsafe_allow_html=True)


@st.cache_data
def load_data(plan_path_str: str | None, register_path_str: str | None):
    """Load YNAB data with caching. Path strings used for cache key."""
    root = Path(__file__).parent
    config = {}
    config_path = root / "config.yaml"
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    plan_override = Path(plan_path_str) if plan_path_str else None
    reg_override = Path(register_path_str) if register_path_str else None
    try:
        return load_ynab_data(root, config, plan_path_override=plan_override, register_path_override=reg_override)
    except FileNotFoundError as e:
        raise e
    except Exception as e:
        raise e


def main():
    root = Path(__file__).parent
    st.sidebar.title("🌲 KingOps")
    st.sidebar.caption("Household Financial Dashboard")

    # Phase 4.2: Vault file selector
    vault_pairs = discover_vault_datasets(root)
    plan_override_str: str | None = None
    register_override_str: str | None = None
    if vault_pairs:
        options = ["Config (default)"] + [f"{p[0].name}" for p in vault_pairs]
        idx = st.sidebar.selectbox(
            "Data source",
            range(len(options)),
            format_func=lambda i: options[i],
            key="data_source",
        )
        if idx > 0:
            plan_override_str = str(vault_pairs[idx - 1][0])
            register_override_str = str(vault_pairs[idx - 1][1])

    # Object-oriented navigation (Section 4.2)
    st.sidebar.markdown("---")
    st.sidebar.caption("Navigate")
    nav_labels = [label for label, _ in NAV_ITEMS]
    nav_keys = [key for _, key in NAV_ITEMS]
    nav_idx = st.sidebar.radio(
        "Nav",
        range(len(nav_labels)),
        format_func=lambda i: nav_labels[i],
        label_visibility="collapsed",
        key="nav_radio",
    )
    page_key = nav_keys[nav_idx]

    # Pages that need YNAB data
    financial_pages = {"net_worth", "allocation", "risk", "behavioral"}
    needs_ynab = PAGE_MAP.get(page_key) in financial_pages

    data = None
    if needs_ynab:
        with st.spinner("Loading data..."):
            try:
                data = load_data(plan_override_str, register_override_str)
            except FileNotFoundError as e:
                st.error(f"**Data not found:** {e}")
                st.info(
                    "**Data request checklist:**\n"
                    "- Ensure Plan CSV and Register CSV paths in config.yaml are correct\n"
                    "- Or place *Plan*.csv and *Register*.csv in the Vault/ folder\n"
                    "- Use the Data source selector (sidebar) if multiple files exist in Vault"
                )
                return
            except Exception as e:
                st.error(f"**Load error:** {e}")
                st.caption("Check config.yaml paths and CSV format. Plan needs: Month, Category Group, Category, Assigned, Activity, Available. Register needs: Account, Date, Payee, Outflow, Inflow, Category Group/Category.")
                return
        st.sidebar.caption(f"Loaded: {len(data.transactions)} txns, {len(data.accounts)} accounts")
    else:
        st.sidebar.caption("Household & projects")

    # Three-panel layout: center (focus) + right (context)
    center_col, right_col = st.columns([3, 1])

    def render_context_panel():
        if data:
            st.caption("**Data lineage**")
            st.write(f"Transactions: {len(data.transactions):,}")
            st.write(f"Accounts: {len(data.accounts)}")
            st.caption("**Provenance**")
            st.write("YNAB Plan & Register CSV")
        else:
            st.caption("**Household**")
            st.write("Focus areas, projects, todos")
            st.write("Stored in data/household.json")

    with center_col:
        mapped = PAGE_MAP.get(page_key)
        if mapped == "net_worth":
            net_worth.render(data)
        elif mapped == "allocation":
            allocation.render(data)
        elif mapped == "risk":
            risk.render(data)
        elif mapped == "behavioral":
            behavioral.render(data)
        elif mapped == "household":
            household.render(data)
        elif mapped == "people":
            people.render(data)
        elif mapped == "projects":
            projects.render(data)
        else:
            st.subheader(nav_labels[nav_idx])
            if page_key == "obligations":
                st.caption("Debts, loans, and recurring obligations. Connect YNAB liability accounts or add manually.")
            elif page_key == "documents":
                st.caption("Important documents and file references. Coming soon.")
            else:
                st.caption("This view is not yet implemented.")

    with right_col:
        render_context_panel()


if __name__ == "__main__":
    main()
