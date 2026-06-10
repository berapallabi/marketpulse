import pandas as pd
import streamlit as st

from marketpulse.ui.theme import signal_cell_style


def render_stock_list(
    signal_rows: list[dict],
    market: str,
    filter_signal: str = "ALL",
    key_prefix: str = "",
) -> str | None:
    """Render filtered, colour-coded signal table. Returns selected symbol on new click, else None."""
    if not signal_rows:
        st.caption("No data loaded yet. Click 🔄 Refresh BUY to fetch signals.")
        return None

    df = _build_df(signal_rows)
    filtered = df if filter_signal == "ALL" else df[df["Signal"] == filter_signal]

    if filtered.empty:
        st.info(f"No {filter_signal} signals in this tier.")
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
    for r in rows:
        records.append({
            "Signal": r["signal_type"] or "—",
            "Confidence": int(r["confidence_score"]) if r.get("confidence_score") is not None else 0,
            "Symbol": r["symbol"],
            "Company": r.get("company_name") or r["symbol"],
            "Price": _fmt_price(r.get("current_price"), r.get("market", "")),
        })
    return pd.DataFrame(records)


def _colour_signal_col(row):
    return [
        signal_cell_style(row.get("Signal", "")) if col == "Signal" else ""
        for col in row.index
    ]


def _fmt_price(price: float | None, market: str) -> str:
    if price is None:
        return "—"
    symbol = "₹" if market == "IN" else "$"
    return f"{symbol}{price:,.2f}"
