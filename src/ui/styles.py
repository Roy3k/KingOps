"""
KingOps Design System — CSS generation from theme tokens.

Pacific Northwest × Japanese Tea Garden.
"""

from src.ui.theme import generate_css_vars, theme


def get_full_styles() -> str:
    """Return complete CSS for the app."""
    t = theme
    return f"""
    {generate_css_vars()}

    /* Google Fonts: Lora (serif), DM Sans (sans), Material Icons (Streamlit sidebar/expander) */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=Lora:ital,wght@0,400;0,500;0,600;1,400&display=swap');
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0');

    /* Base app background — cream linen gradient */
    .stApp {{
        background: linear-gradient(180deg, var(--color-cream-linen) 0%, var(--color-mist) 100%) !important;
    }}

    /* Typography: serif for headings, sans for body */
    h1, h2, h3, h4, h5, h6 {{
        font-family: var(--font-primary) !important;
        color: var(--color-slate) !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em;
    }}

    p, span, div, label {{
        font-family: var(--font-secondary) !important;
        color: var(--color-slate) !important;
    }}

    /* Streamlit icons: restore icon font (Material Symbols) — our span rule was overriding it */
    [data-testid="stIconMaterial"] {{
        font-family: 'Material Symbols Outlined', 'Material Icons' !important;
    }}

    /* Data tables: tabular figures, clean sans */
    .stDataFrame, .stTable, [data-testid="stDataFrame"] {{
        font-family: var(--font-secondary) !important;
        font-variant-numeric: tabular-nums;
        border-radius: var(--radius-md) !important;
        overflow: hidden;
        box-shadow: var(--shadow-card);
    }}

    /* Metrics / cards — soft leather, rounded, soft shadow */
    [data-testid="stMetric"], .stMetric {{
        background: rgba(200, 184, 158, 0.4) !important;
        padding: var(--space-md) !important;
        border-radius: var(--radius-md) !important;
        box-shadow: var(--shadow-card);
        border: 1px solid rgba(106, 94, 75, 0.1);
    }}

    /* Sidebar — foundation panel */
    div[data-testid="stSidebar"] {{
        background: rgba(243, 239, 230, 0.98) !important;
        border-right: 1px solid rgba(106, 94, 75, 0.12);
    }}

    /* Buttons — subdued, rounded */
    .stButton > button {{
        border-radius: var(--radius-md) !important;
        font-family: var(--font-secondary) !important;
        transition: all 200ms ease-out;
    }}

    .stButton > button:hover {{
        box-shadow: var(--shadow-hover);
    }}

    /* Expanders — calm disclosure, ensure text renders correctly */
    .streamlit-expanderHeader {{
        font-family: var(--font-primary) !important;
        border-radius: var(--radius-sm);
    }}
    /* Icon spans must keep icon font — do not inherit */
    .streamlit-expanderHeader [data-testid="stIconMaterial"] {{
        font-family: 'Material Symbols Outlined', 'Material Icons' !important;
    }}

    /* Inputs — avoid font/placeholder rendering issues */
    .stTextInput label, .stTextArea label {{
        font-family: var(--font-secondary) !important;
    }}
    .stTextInput input, .stTextArea textarea {{
        font-family: var(--font-secondary) !important;
        border-radius: var(--radius-sm);
    }}

    /* Avoid pure white, electric blues */
    .stSelectbox, .stTextInput, .stNumberInput {{
        border-radius: var(--radius-sm);
    }}

    /* Info / success / warning / error — memo alert scale */
    [data-testid="stAlert"] {{
        border-radius: var(--radius-md);
        border-left-width: 4px;
    }}
    """
