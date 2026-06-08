from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from marketpulse.config import STALE_HOURS

_SIGNAL_COLOURS = {
    "BUY": "#22c55e",
    "SELL": "#ef4444",
    "HOLD": "#f59e0b",
}


def render_stock_list(
    signal_rows: list[dict],
    market: str,
    filter_signal: str = "ALL",
    key_prefix: str = "",
) -> str | None:
    """Render filtered, colour-coded signal table. Returns selected symbol on new click, else None."""
    st.caption("⚠️ Informational only — not financial advice.")

    if not signal_rows:
        st.info("Click 🔄 Refresh to load data.")
        return None

    df = _build_df(signal_rows)
    filtered = df if filter_signal == "ALL" else df[df["Signal"] == filter_signal]

    if filtered.empty:
        st.caption("No stocks match the selected filter.")
        return None

    filtered = filtered.sort_values("Confidence", ascending=False).reset_index(drop=True)

    _slug = f"{key_prefix.replace(' ', '_').lower()}_" if key_prefix else ""
    table_key = f"table_{market}_{_slug}{filter_signal.lower()}"
    prev_key = f"_prev_rows_{market}_{_slug}{filter_signal.lower()}"

    styled = filtered.style.apply(_colour_signal_col, axis=1)
    event = st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=table_key,
    )

    unavailable = st.session_state.get(f"unavailable_{market}", 0)
    if unavailable > 0:
        st.caption(f"{unavailable} stocks unavailable")

    # Return symbol only when the row selection has changed (new click detected)
    current_rows = list(event.selection.rows) if event and event.selection else []
    if current_rows != st.session_state.get(prev_key, []):
        st.session_state[prev_key] = current_rows
        if current_rows and current_rows[0] < len(filtered):
            return filtered.iloc[current_rows[0]]["Symbol"]

    return None


def _build_df(rows: list[dict]) -> pd.DataFrame:
    records = []
    now = datetime.now(timezone.utc)
    for r in rows:
        stale = _is_stale(r.get("last_updated") or r.get("generated_at"), now)
        staleness_label = " ⚠️" if stale else ""
        records.append({
            "Symbol": r["symbol"],
            "Signal": r["signal_type"],
            "Confidence": int(r["confidence_score"]),
            "Price": _fmt_price(r.get("current_price"), r.get("market", "")),
            "Updated": _fmt_time(r.get("last_updated") or r.get("generated_at")) + staleness_label,
        })
    return pd.DataFrame(records)


def _colour_signal_col(row):
    colour = _SIGNAL_COLOURS.get(row.get("Signal", ""), "#ffffff")
    return [
        f"color: {colour}; font-weight: bold" if col == "Signal" else ""
        for col in row.index
    ]


def _is_stale(ts_str: str | None, now: datetime) -> bool:
    if not ts_str:
        return True
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return (now - ts).total_seconds() > STALE_HOURS * 3600
    except ValueError:
        return True


def _fmt_price(price: float | None, market: str) -> str:
    if price is None:
        return "—"
    symbol = "₹" if market == "IN" else "$"
    return f"{symbol}{price:,.2f}"


def _fmt_time(ts_str: str | None) -> str:
    if not ts_str:
        return "—"
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return ts.strftime("%H:%M UTC")
    except ValueError:
        return ts_str[:16]
