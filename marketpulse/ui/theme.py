"""Central design token and CSS module. Single source of truth for all visual constants."""

PALETTE = {
    "PRIMARY":       "#ffffff",
    "INTERACTIVE":   "#3b82f6",
    "BUY":           "#4ade80",
    "SELL":          "#f87171",
    "HOLD":          "#fbbf24",
    "NEUTRAL_LIGHT": "#1a1a1a",
    "NEUTRAL_MID":   "#2d2d2d",
    "NEUTRAL_DARK":  "#f5f5f5",
}

SIGNAL_BADGE_STYLE = {
    "BUY":  "#4ade80",
    "SELL": "#f87171",
    "HOLD": "#fbbf24",
}


def signal_cell_style(signal_type: str) -> str:
    """Return a Pandas Styler-compatible CSS string for a signal cell."""
    fg = SIGNAL_BADGE_STYLE.get(signal_type)
    if not fg:
        return ""
    return f"color: {fg}; font-weight: bold"


def get_global_css() -> str:
    """Return the full CSS string for injection into the Streamlit page."""
    p = PALETTE
    return f"""
/* ── Hide full-width tab divider ── */
.stTabs [data-baseweb="tab-border"] {{
    display: none;
}}

/* ── Level 1: Market tabs (India / US) ── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 6px;
    background-color: {p['NEUTRAL_LIGHT']};
    padding: 6px 6px 0 6px;
    border-radius: 8px 8px 0 0;
    width: fit-content;
}}
.stTabs [data-baseweb="tab"] {{
    padding: 10px 24px;
    border-radius: 6px 6px 0 0;
    font-size: 14px;
    font-weight: 500;
    color: {p['NEUTRAL_DARK']};
    background-color: {p['NEUTRAL_MID']};
}}
.stTabs [data-baseweb="tab"][aria-selected="true"] {{
    background-color: {p['NEUTRAL_LIGHT']};
    color: {p['PRIMARY']};
    font-weight: 700;
    border-bottom: 3px solid {p['NEUTRAL_DARK']};
}}

/* ── Level 2: Tier tabs (Large / Mid / Small Cap) ── */
.stTabs .stTabs [data-baseweb="tab-list"] {{
    gap: 2px;
    background-color: {p['NEUTRAL_LIGHT']};
    padding: 4px 4px 0 4px;
    border-radius: 6px 6px 0 0;
    width: fit-content;
    margin-top: 12px;
}}
.stTabs .stTabs [data-baseweb="tab"] {{
    padding: 7px 18px;
    border-radius: 4px 4px 0 0;
    font-size: 13px;
    font-weight: 500;
    color: {p['NEUTRAL_DARK']};
    background-color: {p['NEUTRAL_MID']};
}}
.stTabs .stTabs [data-baseweb="tab"][aria-selected="true"] {{
    background-color: {p['NEUTRAL_LIGHT']};
    color: {p['PRIMARY']};
    font-weight: 600;
    border-bottom: 2px solid {p['NEUTRAL_DARK']};
}}

/* ── Level 3: Signal tabs (All / BUY / SELL / HOLD) ── */
.stTabs .stTabs .stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    background-color: transparent;
    border-bottom: 1px solid {p['NEUTRAL_MID']};
    padding: 0;
    border-radius: 0;
    width: fit-content;
    margin-top: 8px;
}}
.stTabs .stTabs .stTabs [data-baseweb="tab"] {{
    padding: 5px 16px;
    border-radius: 0;
    font-size: 12px;
    font-weight: 400;
    color: {p['NEUTRAL_DARK']};
    background-color: transparent;
    opacity: 0.65;
}}
.stTabs .stTabs .stTabs [data-baseweb="tab"][aria-selected="true"] {{
    background-color: transparent;
    color: {p['PRIMARY']};
    font-weight: 600;
    border-bottom: 2px solid {p['PRIMARY']};
    opacity: 1;
}}

/* ── Page layout ── */
.block-container {{
    padding-top: 1rem;
}}

/* ── Typography scale ── */
h1 {{
    font-size: 1.75rem;
    font-weight: 700;
    color: {p['PRIMARY']};
}}
h2, h3 {{
    font-size: 1.1rem;
    font-weight: 600;
    color: {p['PRIMARY']};
}}
.stCaption, .stCaption p {{
    font-size: 0.75rem;
    color: {p['NEUTRAL_DARK']};
    opacity: 0.65;
}}

/* ── Buttons ── */
.stButton > button {{
    border-radius: 6px;
    font-weight: 500;
    padding: 6px 18px;
}}
"""


def inject_global_css() -> None:
    """Inject the global stylesheet into the current Streamlit page."""
    import streamlit as st
    st.markdown(f"<style>{get_global_css()}</style>", unsafe_allow_html=True)
