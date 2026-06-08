import streamlit as st

from marketpulse.ui.theme import PALETTE

_ICONS = {
    "Bullish": "📈",
    "Bearish": "📉",
    "Neutral": "➡️",
}


def render_sentiment_gauge(summary: dict | None, label: str) -> None:
    """Render market sentiment as a single-line styled bar."""
    if summary is None:
        _render_bar(label, "➡️", "No data", None, 0, 0, 0)
        return

    if summary.get("insufficient_data") if isinstance(summary, dict) else getattr(summary, "insufficient_data", False):
        overall = "Insufficient data"
    else:
        overall = summary.get("overall_sentiment") if isinstance(summary, dict) else summary.overall_sentiment

    score = summary.get("sentiment_score") if isinstance(summary, dict) else summary.sentiment_score
    buy   = summary.get("buy_count",  0)   if isinstance(summary, dict) else summary.buy_count
    sell  = summary.get("sell_count", 0)   if isinstance(summary, dict) else summary.sell_count
    hold  = summary.get("hold_count", 0)   if isinstance(summary, dict) else summary.hold_count

    _render_bar(label, _ICONS.get(overall, "➡️"), overall, score, buy, sell, hold)


def _render_bar(label: str, icon: str, overall: str, score, buy: int, sell: int, hold: int) -> None:
    score_part = f"&nbsp;&nbsp;·&nbsp;&nbsp;Score: <b>{score:.1f}</b>" if score is not None else ""
    html = f"""
    <div style="
        background-color: {PALETTE['NEUTRAL_LIGHT']};
        border: 1px solid {PALETTE['NEUTRAL_MID']};
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 0.85rem;
        color: {PALETTE['NEUTRAL_DARK']};
        display: flex;
        align-items: center;
        gap: 0;
        margin-bottom: 12px;
    ">
        <span style="font-weight:600; margin-right:8px;">{label}</span>
        <span style="margin-right:4px;">{icon}</span>
        <span style="font-weight:600;">{overall}</span>
        <span>{score_part}&nbsp;&nbsp;·&nbsp;&nbsp;
            <span style="color:{PALETTE['BUY']}; font-weight:600;">▲ {buy} BUY</span>
            &nbsp;
            <span style="color:{PALETTE['SELL']}; font-weight:600;">▼ {sell} SELL</span>
            &nbsp;
            <span style="color:{PALETTE['HOLD']}; font-weight:600;">● {hold} HOLD</span>
        </span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
