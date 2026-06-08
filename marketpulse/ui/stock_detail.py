import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from marketpulse.storage.cache import (
    add_to_holdings,
    add_to_watchlist,
    read_holdings,
    read_watchlist,
    remove_from_holdings,
    remove_from_watchlist,
)
from marketpulse.ui.theme import PALETTE


def render_stock_detail(
    symbol: str,
    market: str,
    technical: dict | None,
    news_items: list[dict],
    ohlcv_df: pd.DataFrame | None = None,
    key: str = "",
) -> None:
    """Render drill-down detail panel for a selected stock."""
    st.markdown(f"#### 📊 {symbol}")
    _render_list_actions(symbol, market, key)
    if ohlcv_df is not None and not ohlcv_df.empty:
        _render_price_chart(symbol, ohlcv_df, key=key)
    else:
        st.info("No price chart available.")

    if technical:
        _render_indicators(technical)
    else:
        st.info("No technical indicator data available.")

    _render_news(news_items)


def _render_list_actions(symbol: str, market: str, key: str = "") -> None:
    in_watchlist = symbol in read_watchlist(market)
    in_holdings = symbol in read_holdings(market)
    col_w, col_h = st.columns(2)
    with col_w:
        if in_watchlist:
            if st.button("✓ Remove from Watchlist", key=f"wl_{symbol}_{market}_{key}", use_container_width=True, type="secondary"):
                remove_from_watchlist(symbol, market)
                st.rerun()
        else:
            if st.button("+ Add to Watchlist", key=f"wl_{symbol}_{market}_{key}", use_container_width=True, type="secondary"):
                add_to_watchlist(symbol, market)
                st.rerun()
    with col_h:
        if in_holdings:
            if st.button("✓ Remove from Holdings", key=f"hd_{symbol}_{market}_{key}", use_container_width=True, type="secondary"):
                remove_from_holdings(symbol, market)
                st.rerun()
        else:
            if st.button("+ Add to Holdings", key=f"hd_{symbol}_{market}_{key}", use_container_width=True, type="secondary"):
                add_to_holdings(symbol, market)
                st.rerun()


def _render_price_chart(symbol: str, ohlcv_df: pd.DataFrame, key: str = "") -> None:
    df = ohlcv_df.tail(90).copy()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=df["Close"],
        mode="lines",
        name="Close",
        line=dict(color=PALETTE["INTERACTIVE"], width=2),
    ))
    fig.update_layout(
        title=f"{symbol} — 90-Day Close Price",
        xaxis_title="Date",
        yaxis_title="Price",
        height=300,
        margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig, use_container_width=True, key=f"price_{symbol}_{key}")


def _render_indicators(technical: dict) -> None:
    st.subheader("Technical Indicators")
    col1, col2 = st.columns(2)

    rsi = technical.get("rsi_14")
    with col1:
        if rsi is not None:
            label = "Overbought" if rsi > 70 else ("Oversold" if rsi < 30 else "Neutral")
            st.metric("RSI (14)", f"{rsi:.1f}", delta=label)
        else:
            st.metric("RSI (14)", "N/A")

        macd_val = technical.get("macd_val")
        macd_sig = technical.get("macd_signal")
        if macd_val is not None and macd_sig is not None:
            st.metric("MACD", f"{macd_val:.3f}", delta=f"Signal: {macd_sig:.3f}")
        else:
            st.metric("MACD", "N/A")

    with col2:
        bb_upper = technical.get("bb_upper")
        bb_lower = technical.get("bb_lower")
        if bb_upper is not None and bb_lower is not None:
            st.metric("Bollinger Bands", f"{bb_lower:.2f} – {bb_upper:.2f}")
        else:
            st.metric("Bollinger Bands", "N/A")

        sma50 = technical.get("sma_50")
        sma200 = technical.get("sma_200")
        if sma50 is not None and sma200 is not None:
            cross = "Golden Cross" if sma50 > sma200 else "Death Cross"
            st.metric("SMA 50 / 200", f"{sma50:.2f} / {sma200:.2f}", delta=f"{cross} Cross")
        else:
            st.metric("SMA 50 / 200", "N/A")

    factors_raw = technical.get("contributing_factors") or "[]"
    if isinstance(factors_raw, str):
        try:
            factors = json.loads(factors_raw)
        except json.JSONDecodeError:
            factors = []
    else:
        factors = factors_raw
    if factors:
        st.caption(f"Contributing factors: {', '.join(factors)}")


def _render_news(news_items: list[dict]) -> None:
    st.subheader("Recent News")
    if not news_items:
        st.info("No recent news found for this stock.")
        return

    _BADGE = {"Positive": "🟢", "Negative": "🔴", "Neutral": "⚪"}

    for item in news_items[:10]:
        badge = _BADGE.get(item.get("sentiment_label", "Neutral"), "⚪")
        published = item.get("published_at") or "Date unknown"
        if published and published != "Date unknown":
            try:
                from datetime import datetime, timezone
                ts = datetime.fromisoformat(published.replace("Z", "+00:00"))
                published = ts.strftime("%d %b %Y %H:%M UTC")
            except ValueError:
                pass
        st.markdown(
            f"{badge} **{item.get('headline', '')}**  \n"
            f"*{item.get('source', '')} · {published}*"
        )
