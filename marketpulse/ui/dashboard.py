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



def _top_buy_signals(signals: list, limit: int = 20) -> list:
    buys = [s for s in signals if s.signal_type == "BUY"]
    return sorted(buys, key=lambda s: s.confidence_score, reverse=True)[:limit]


def render_dashboard() -> None:
    from marketpulse.ui.theme import inject_global_css
    st.set_page_config(page_title="MarketPulse", page_icon="📈", layout="wide")
    inject_global_css()
    st.title("📈 MarketPulse Investment Dashboard")
    st.caption("⚠️ Informational only — not financial advice. Signals are generated algorithmically.")

    cache.init_db()

    in_dot  = "🔴" if _is_market_closed("IN") else "🟢"
    us_dot  = "🔴" if _is_market_closed("US") else "🟢"
    tab_in, tab_us = st.tabs([f"🇮🇳 India (Nifty 50) {in_dot}", f"🇺🇸 US (S&P 100) {us_dot}"])

    with tab_in:
        _render_market_tab("IN")

    with tab_us:
        _render_market_tab("US")


def _refresh_market(market: str) -> None:
    from marketpulse.analysis.cap_tiers import classify_cap_tier
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
            ohlcv, mc = fetch_ohlcv_history(quote.symbol)
            market_cap = mc if market == "IN" else quote.market_cap
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
            signal.cap_tier = classify_cap_tier(market_cap, market)

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
    for _key in [k for k in st.session_state if k.startswith(f"_prev_rows_{market}_")]:
        st.session_state.pop(_key, None)
    for _key in [k for k in st.session_state if k.startswith(f"tier_buy_{market}_")]:
        st.session_state.pop(_key, None)


def _refresh_tier_buy(market: str, tier_label: str) -> None:
    from marketpulse.analysis.cap_tiers import classify_cap_tier
    from marketpulse.analysis.indicators import compute_indicators
    from marketpulse.analysis.signals import generate_signal
    from marketpulse.data.sentiment import fetch_market_articles, score_articles_for_stock
    from marketpulse.data.types import DataProviderError

    if market == "IN":
        from marketpulse.data.india import fetch_ohlcv_history, fetch_quotes
        symbols = config.NIFTY_50_SYMBOLS
    else:
        from marketpulse.data.us import fetch_ohlcv_history, fetch_quotes
        symbols = config.SP100_SYMBOLS

    slug = tier_label.replace(" ", "_").lower()
    session_key = f"tier_buy_{market}_{slug}"

    signals = []
    try:
        quotes = fetch_quotes(symbols)
    except DataProviderError as e:
        st.session_state[session_key] = []
        st.error(f"⚠️ Could not fetch quotes: {e}")
        return

    articles = []
    try:
        articles = fetch_market_articles(market)
    except Exception:
        pass

    for quote in quotes:
        try:
            ohlcv, mc = fetch_ohlcv_history(quote.symbol)
            if ohlcv is None:
                continue
            market_cap = mc if market == "IN" else quote.market_cap
            if classify_cap_tier(market_cap, market) != tier_label:
                continue
            technical = compute_indicators(quote.symbol, market, ohlcv)
            if technical is None:
                continue
            sentiment = score_articles_for_stock(articles, quote.symbol, quote.company_name)
            sentiment.market = market
            signal = generate_signal(technical, sentiment)
            signal.cap_tier = tier_label
            signals.append(signal)
        except Exception:
            continue

    top = _top_buy_signals(signals, limit=20)
    now_iso = datetime.now(timezone.utc).isoformat()
    rows = [
        {
            "symbol": s.symbol,
            "market": s.market,
            "signal_type": s.signal_type,
            "confidence_score": s.confidence_score,
            "technical_score": s.technical_score,
            "sentiment_score": s.sentiment_score,
            "contributing_factors": s.contributing_factors,
            "generated_at": now_iso,
            "cap_tier": s.cap_tier,
            "current_price": next((q.current_price for q in quotes if q.symbol == s.symbol), None),
            "last_updated": now_iso,
        }
        for s in top
    ]
    st.session_state[session_key] = rows
    st.session_state.pop(f"_prev_rows_{market}_{slug}_buy", None)


def _rows_last_at(rows: list[dict]) -> str | None:
    """Return the most recent last_updated/generated_at from a list of signal rows, formatted as HH:MM UTC."""
    best: str | None = None
    for r in rows:
        ts_str = r.get("last_updated") or r.get("generated_at")
        if ts_str and (best is None or ts_str > best):
            best = ts_str
    if best is None:
        return None
    try:
        ts = datetime.fromisoformat(best.replace("Z", "+00:00"))
        return ts.strftime("%H:%M UTC")
    except (ValueError, AttributeError):
        return None


def _render_market_tab(market: str) -> None:
    from marketpulse.analysis.cap_tiers import INDIA_TIER_ORDER, US_TIER_ORDER
    from marketpulse.ui.sentiment_gauge import render_sentiment_gauge
    from marketpulse.ui.stock_detail import render_stock_detail
    from marketpulse.ui.stock_list import render_stock_list

    error = st.session_state.get(f"error_{market}")
    if error:
        st.error(f"⚠️ Data unavailable — {error}")

    summary = cache.read_market_summary(market)
    render_sentiment_gauge(summary, "🇮🇳 Market Sentiment" if market == "IN" else "🇺🇸 Market Sentiment")

    signal_rows = cache.read_signals(market)
    tier_labels = INDIA_TIER_ORDER if market == "IN" else US_TIER_ORDER

    tier_tabs = st.tabs(tier_labels)
    for tier_tab, tier_label in zip(tier_tabs, tier_labels):
        with tier_tab:
            tier_rows = [r for r in signal_rows if r.get("cap_tier") == tier_label]
            slug = tier_label.replace(" ", "_").lower()
            fetching_key = f"fetching_{market}_{slug}"
            fetching = st.session_state.get(fetching_key, False)

            # Signal filter + refresh confined to left 60% — right side left empty
            filter_col, _ = st.columns([3, 2], gap="large")
            with filter_col:
                seg_col, btn_col = st.columns([5, 4], vertical_alignment="center")
                with seg_col:
                    signal_choice = st.segmented_control(
                        "Signal",
                        options=["All", "BUY", "SELL", "HOLD"],
                        default="All",
                        label_visibility="collapsed",
                        key=f"signal_{market}_{slug}",
                    )
                with btn_col:
                    rows_for_ts = st.session_state.get(f"tier_buy_{market}_{slug}") or tier_rows
                    last_at = _rows_last_at(rows_for_ts)
                    if fetching:
                        st.button(
                            "⏳  Fetching latest details…",
                            key=f"btn_tier_buy_{market}_{slug}",
                            use_container_width=True,
                            type="secondary",
                            disabled=True,
                        )
                        _refresh_tier_buy(market, tier_label)
                        st.session_state[fetching_key] = False
                        st.rerun()
                    else:
                        label = f"🔄  Refresh now  ·  last at {last_at}" if last_at else "🔄  Refresh now"
                        if st.button(label, key=f"btn_tier_buy_{market}_{slug}", use_container_width=True, type="secondary"):
                            st.session_state[fetching_key] = True
                            st.rerun()

            # Table | detail — second row, aligns detail panel with the table
            list_col, detail_col = st.columns([3, 2], gap="large")
            with list_col:
                if signal_choice == "All" or signal_choice is None:
                    sym = render_stock_list(tier_rows, market, filter_signal="ALL", key_prefix=tier_label)
                    if sym:
                        st.session_state[f"selected_{market}"] = sym
                elif signal_choice == "BUY":
                    tier_buy_rows = st.session_state.get(f"tier_buy_{market}_{slug}")
                    if tier_buy_rows is None:
                        buy_data = tier_rows
                    elif len(tier_buy_rows) == 0:
                        st.caption("No BUY signals found for this tier.")
                        buy_data = None
                    else:
                        buy_data = tier_buy_rows
                    if buy_data is not None:
                        sym = render_stock_list(buy_data, market, filter_signal="BUY", key_prefix=tier_label)
                        if sym:
                            st.session_state[f"selected_{market}"] = sym
                elif signal_choice == "SELL":
                    sym = render_stock_list(tier_rows, market, filter_signal="SELL", key_prefix=tier_label)
                    if sym:
                        st.session_state[f"selected_{market}"] = sym
                elif signal_choice == "HOLD":
                    sym = render_stock_list(tier_rows, market, filter_signal="HOLD", key_prefix=tier_label)
                    if sym:
                        st.session_state[f"selected_{market}"] = sym

            with detail_col:
                selected_symbol = st.session_state.get(f"selected_{market}")
                if selected_symbol:
                    technical = cache.read_technical(selected_symbol, market)
                    news_items = cache.read_news(selected_symbol, market)
                    ohlcv = st.session_state.get(f"ohlcv_{market}", {}).get(selected_symbol)
                    render_stock_detail(selected_symbol, market, technical, news_items, ohlcv)
                else:
                    st.caption("← Select a stock from the list to view details")


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
