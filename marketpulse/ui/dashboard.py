"""Main dashboard layout — wires all user stories together."""
from datetime import datetime, timezone

import streamlit as st

from marketpulse import config
from marketpulse.storage import cache


def _is_market_closed(market: str) -> bool:
    now_utc = datetime.now(timezone.utc)
    hour_utc = now_utc.hour + now_utc.minute / 60

    if market == "IN":
        # NSE: 09:15–15:30 IST = 03:45–10:00 UTC
        return not (3.75 <= hour_utc <= 10.0)
    else:
        # NYSE: 09:30–16:00 ET = 14:30–21:00 UTC (approximate; ignores DST)
        return not (14.5 <= hour_utc <= 21.0)


_TAB_CSS = """
<style>
/* Tab strip background */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background-color: #f0f2f6;
    padding: 6px 6px 0 6px;
    border-radius: 8px 8px 0 0;
}
/* Inactive tab */
.stTabs [data-baseweb="tab"] {
    padding: 10px 24px;
    border-radius: 6px 6px 0 0;
    font-size: 14px;
    font-weight: 500;
    color: #555;
    background-color: #e2e5ea;
}
/* Active tab */
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background-color: #ffffff;
    color: #0f1117;
    font-weight: 700;
    border-bottom: 3px solid #ff4b4b;
}
</style>
"""


def render_dashboard() -> None:
    st.set_page_config(page_title="MarketPulse", page_icon="📈", layout="wide")
    st.markdown(_TAB_CSS, unsafe_allow_html=True)
    st.title("📈 MarketPulse Investment Dashboard")
    st.caption("⚠️ Informational only — not financial advice. Signals are generated algorithmically.")

    cache.init_db()

    with st.sidebar:
        st.header("Controls")
        refresh_clicked = st.button("🔄 Refresh Data", use_container_width=True)
        if cache.check_staleness("IN") or cache.check_staleness("US"):
            st.caption("Data may be stale (> 1 hour old).")

    tab_in, tab_us = st.tabs(["🇮🇳 India (Nifty 50)", "🇺🇸 US (S&P 100)"])

    if refresh_clicked:
        with tab_in:
            _refresh_market("IN")
        with tab_us:
            _refresh_market("US")
        st.rerun()

    with tab_in:
        _render_market_tab("IN")

    with tab_us:
        _render_market_tab("US")


def _refresh_market(market: str) -> None:
    from marketpulse.analysis.indicators import compute_indicators
    from marketpulse.analysis.market_summary import compute_market_summary
    from marketpulse.analysis.signals import generate_signal
    from marketpulse.data.sentiment import fetch_market_articles, score_articles_for_stock
    from marketpulse.data.types import DataProviderError

    if market == "IN":
        from marketpulse.data.india import fetch_ohlcv_history, fetch_quotes
        symbols = config.NIFTY_50_SYMBOLS
    else:
        from marketpulse.data.us import fetch_ohlcv_history, fetch_quotes
        symbols = config.SP100_SYMBOLS

    unavailable = 0
    signals = []
    sentiments = []
    ohlcv_cache: dict = st.session_state.get(f"ohlcv_{market}", {})

    with st.spinner(f"Fetching {'India' if market == 'IN' else 'US'} market data…"):
        try:
            quotes = fetch_quotes(symbols)
        except DataProviderError as e:
            st.session_state[f"error_{market}"] = str(e)
            st.session_state[f"unavailable_{market}"] = len(symbols)
            return

    st.session_state.pop(f"error_{market}", None)
    cache.write_quotes(quotes)

    articles = []
    try:
        articles = fetch_market_articles(market)
    except Exception:
        pass

    with st.spinner("Computing signals…"):
        for quote in quotes:
            ohlcv = fetch_ohlcv_history(quote.symbol)
            if ohlcv is None:
                unavailable += 1
                continue

            technical = compute_indicators(quote.symbol, market, ohlcv)
            if technical is None:
                unavailable += 1
                continue

            sentiment = score_articles_for_stock(articles, quote.symbol, quote.company_name)
            sentiment.market = market

            signal = generate_signal(technical, sentiment)

            cache.write_technical(technical)
            cache.write_sentiment(sentiment)
            cache.write_news(quote.symbol, market, _news_items_from_sentiment(sentiment))

            ohlcv_cache[quote.symbol] = ohlcv
            signals.append(signal)
            sentiments.append(sentiment)

    if signals:
        cache.write_signals(signals)

    from marketpulse.analysis.market_summary import compute_market_summary
    market_summary = compute_market_summary(market, signals, sentiments)
    cache.write_market_summary(market_summary)

    st.session_state[f"ohlcv_{market}"] = ohlcv_cache
    st.session_state[f"unavailable_{market}"] = unavailable

    # Clear selection state so the drill-down resets after a refresh
    st.session_state.pop(f"selected_{market}", None)
    for _f in ["all", "buy", "sell", "hold"]:
        st.session_state.pop(f"_prev_rows_{market}_{_f}", None)


def _render_market_tab(market: str) -> None:
    from marketpulse.ui.sentiment_gauge import render_sentiment_gauge
    from marketpulse.ui.stock_detail import render_stock_detail
    from marketpulse.ui.stock_list import render_stock_list

    error = st.session_state.get(f"error_{market}")
    if error:
        st.error(f"⚠️ Data unavailable — {error}")

    if _is_market_closed(market):
        st.info("🔴 Market Closed — showing last-close data")

    summary = cache.read_market_summary(market)
    render_sentiment_gauge(summary, "🇮🇳 Market Sentiment" if market == "IN" else "🇺🇸 Market Sentiment")

    signal_rows = cache.read_signals(market)

    tab_all, tab_buy, tab_sell, tab_hold = st.tabs(["All", "BUY", "SELL", "HOLD"])
    with tab_all:
        sym = render_stock_list(signal_rows, market, filter_signal="ALL")
        if sym:
            st.session_state[f"selected_{market}"] = sym
    with tab_buy:
        sym = render_stock_list(signal_rows, market, filter_signal="BUY")
        if sym:
            st.session_state[f"selected_{market}"] = sym
    with tab_sell:
        sym = render_stock_list(signal_rows, market, filter_signal="SELL")
        if sym:
            st.session_state[f"selected_{market}"] = sym
    with tab_hold:
        sym = render_stock_list(signal_rows, market, filter_signal="HOLD")
        if sym:
            st.session_state[f"selected_{market}"] = sym

    # Drill-down — persists across sub-tab switches; cleared on refresh
    selected_symbol = st.session_state.get(f"selected_{market}")
    if selected_symbol:
        technical = cache.read_technical(selected_symbol, market)
        news_items = cache.read_news(selected_symbol, market)
        ohlcv = st.session_state.get(f"ohlcv_{market}", {}).get(selected_symbol)
        render_stock_detail(selected_symbol, market, technical, news_items, ohlcv)


def _news_items_from_sentiment(sentiment) -> list:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    vader = SentimentIntensityAnalyzer()
    now = datetime.now(timezone.utc).isoformat()

    class _NewsItem:
        pass

    items = []
    for article in (sentiment.matched_articles or []):
        compound = vader.polarity_scores(article.headline + " " + article.summary)["compound"]
        if compound >= 0.05:
            label = "Positive"
        elif compound <= -0.05:
            label = "Negative"
        else:
            label = "Neutral"

        item = _NewsItem()
        item.headline = article.headline
        item.source = article.source
        item.published_at = article.published_at
        item.sentiment_label = label
        item.fetched_at = now
        items.append(item)

    return items
