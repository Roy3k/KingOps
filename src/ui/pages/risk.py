"""Risk & Coverage Map view — tea garden layout, stone path calendar."""

from pathlib import Path

import streamlit as st
import yaml

from src.compute.risk import get_coverage_map, get_renewal_calendar, load_policies_from_vault
from src.schema.models import Person, Policy
from src.ui.components.alert_card import AlertSeverity, alert_card
from src.ui.theme import theme


def load_household() -> list[Person]:
    """Load household from config."""
    root = Path(__file__).resolve().parent.parent.parent.parent
    config_path = root / "config.yaml"
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        members = cfg.get("household", {}).get("members", [])
        return [
            Person(
                id=m.get("id", ""),
                name=m.get("name", ""),
                role=m.get("role", "adult"),
                dob=m.get("dob"),
            )
            for m in members
        ]
    return []


def render(data=None) -> None:
    """Render Risk & Coverage Map view — Section 5.3 memo (tea garden map)."""
    root = Path(__file__).resolve().parent.parent.parent.parent
    people = load_household()
    policies = load_policies_from_vault(root / "Vault")
    t = theme

    st.subheader("Coverage Map")

    if not policies:
        alert_card(
            "No policy data. Add policies to Vault or use the form below. "
            "Upload policy CSV or add policy manually.",
            severity=AlertSeverity.WARNING,
        )
        with st.expander("Add policy manually"):
            st.text_input("Policy type", key="pol_type", placeholder="auto, home, umbrella, term_life")
            st.text_input("Carrier", key="pol_carrier", placeholder="Insurance company name")
            st.date_input("Renewal date", key="pol_renewal")
            st.number_input("Premium ($)", key="pol_premium", value=0.0)
            if st.button("Add policy"):
                st.info("Add a policies.csv file to the Vault folder to persist policies.")
    else:
        coverage = get_coverage_map(policies, people)

        # Tea garden: People | Risks | Policies (Section 5.3)
        col_people, col_risks, col_policies = st.columns(3)
        with col_people:
            st.caption("People")
            for p in people:
                st.markdown(f"• {p.name}")
            if not people:
                st.caption("—")

        with col_risks:
            st.caption("Risks")
            risk_types = sorted(set(c.risk_type for c in coverage))
            for r in risk_types:
                st.markdown(f"• {r}")

        with col_policies:
            st.caption("Policies")
            for c in coverage:
                person = c.person_name or "General"
                carrier = c.carrier or "Unknown"
                st.markdown(f"• **{person}** | {c.risk_type} | {carrier}")

    # Renewal timeline — stone path calendar (Section 5.3)
    st.subheader("Renewal Calendar")
    if policies:
        events = get_renewal_calendar(policies)
        if events:
            # Horizontal stone path — events spaced, approaching renewals subtly warm
            for e in events:
                warm = "color: #B46A3C;" if e.days_until < 60 else ""
                st.markdown(
                    f"<div style='padding: 0.5rem 0; border-bottom: 1px solid rgba(106,94,75,0.1); {warm}'>"
                    f"{e.renewal_date} | {e.policy_type} | {e.carrier or 'Unknown'} ({e.days_until} days)"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No policies with renewal dates in the next 12 months.")
    else:
        st.caption("No policies with renewal dates.")
