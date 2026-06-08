import streamlit as st


_COLOURS = {
    "Bullish": "normal",
    "Neutral": "off",
    "Bearish": "inverse",
}

_ICONS = {
    "Bullish": "📈",
    "Bearish": "📉",
    "Neutral": "➡️",
}


def render_sentiment_gauge(summary: dict | None, label: str) -> None:
    """Render a market sentiment metric widget."""
    if summary is None:
        st.metric(label=label, value="No data", delta="Click Refresh")
        return

    if summary.get("insufficient_data") or (
        isinstance(summary, object) and getattr(summary, "insufficient_data", False)
    ):
        overall = "Insufficient data"
    else:
        overall = summary.get("overall_sentiment") if isinstance(summary, dict) else summary.overall_sentiment

    score = summary.get("sentiment_score") if isinstance(summary, dict) else summary.sentiment_score
    buy = summary.get("buy_count", 0) if isinstance(summary, dict) else summary.buy_count
    sell = summary.get("sell_count", 0) if isinstance(summary, dict) else summary.sell_count
    hold = summary.get("hold_count", 0) if isinstance(summary, dict) else summary.hold_count

    icon = _ICONS.get(overall, "➡️")
    delta_label = f"BUY {buy} | SELL {sell} | HOLD {hold}"

    st.metric(
        label=label,
        value=f"{icon} {overall}",
        delta=f"Score: {score:.1f}  ·  {delta_label}",
    )
