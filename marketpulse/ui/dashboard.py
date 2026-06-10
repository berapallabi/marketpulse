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
    session_key = f"tier_buy_{market}_buy_{slug}"

    signals = []
    sentiments = []
    try:
        quotes = fetch_quotes(symbols)
    except DataProviderError as e:
        st.session_state[session_key] = []
        st.error(f"⚠️ Could not fetch quotes: {e}")
        return

    cache.write_quotes(quotes)

    articles = []
    try:
        articles = fetch_market_articles(market)
    except Exception:
        pass

    ohlcv_cache: dict = st.session_state.setdefault(f"ohlcv_{market}", {})
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
            sentiments.append(sentiment)
            cache.write_technical(technical)
            cache.write_sentiment(sentiment)
            cache.write_news(quote.symbol, market, _news_items_from_sentiment(sentiment))
            ohlcv_cache[quote.symbol] = ohlcv
        except Exception:
            continue

    if signals:
        from statistics import mean
        from marketpulse.analysis.market_summary import MarketSummary
        cache.write_signals(signals)
        buy_count = sum(1 for s in signals if s.signal_type == "BUY")
        sell_count = sum(1 for s in signals if s.signal_type == "SELL")
        hold_count = sum(1 for s in signals if s.signal_type == "HOLD")
        total = len(signals)
        avg_score = round(mean(s.sentiment_score for s in sentiments), 1) if sentiments else 50.0
        net = (buy_count - sell_count) / total if total > 0 else 0
        if net > 0.10:
            overall = "Bullish"
        elif net < -0.10:
            overall = "Bearish"
        else:
            overall = "Neutral"
        cache.write_market_summary(MarketSummary(
            market=market,
            overall_sentiment=overall,
            sentiment_score=avg_score,
            buy_count=buy_count,
            sell_count=sell_count,
            hold_count=hold_count,
            last_updated=datetime.now(timezone.utc).isoformat(),
        ))

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
    st.session_state.pop(f"_prev_rows_{market}_buy_{slug}_buy", None)


def _refresh_section(market: str, section: str, tier_label: str, db_path=None) -> None:
    """Refresh full analysis for watchlist or holdings symbols in a single tier."""
    from pathlib import Path
    from marketpulse.analysis.cap_tiers import classify_cap_tier
    from marketpulse.analysis.indicators import compute_indicators
    from marketpulse.analysis.signals import generate_signal
    from marketpulse.data.sentiment import fetch_market_articles, score_articles_for_stock
    from marketpulse.data.types import DataProviderError

    if market == "IN":
        from marketpulse.data.india import fetch_ohlcv_history, fetch_quotes
    else:
        from marketpulse.data.us import fetch_ohlcv_history, fetch_quotes

    symbol_set = set(
        cache.read_watchlist(market, db_path) if section == "watchlist"
        else cache.read_holdings(market, db_path)
    )
    if not symbol_set:
        return

    signal_rows = cache.read_signals(market, db_path)
    tier_symbols = [
        r["symbol"] for r in signal_rows
        if r.get("cap_tier") == tier_label and r["symbol"] in symbol_set
    ]
    if not tier_symbols:
        return

    try:
        quotes = fetch_quotes(tier_symbols)
    except DataProviderError as e:
        st.error(f"⚠️ Could not fetch quotes: {e}")
        return

    cache.write_quotes(quotes, db_path)

    articles = []
    try:
        articles = fetch_market_articles(market)
    except Exception:
        pass

    ohlcv_cache: dict = st.session_state.setdefault(f"ohlcv_{market}", {})
    signals = []
    for quote in quotes:
        try:
            ohlcv, mc = fetch_ohlcv_history(quote.symbol)
            if ohlcv is None:
                continue
            market_cap = mc if market == "IN" else quote.market_cap
            technical = compute_indicators(quote.symbol, market, ohlcv)
            if technical is None:
                continue
            sentiment = score_articles_for_stock(articles, quote.symbol, quote.company_name)
            sentiment.market = market
            signal = generate_signal(technical, sentiment)
            signal.cap_tier = classify_cap_tier(market_cap, market)
            signals.append(signal)
            cache.write_technical(technical, db_path)
            cache.write_sentiment(sentiment, db_path)
            cache.write_news(quote.symbol, market, _news_items_from_sentiment(sentiment), db_path)
            ohlcv_cache[quote.symbol] = ohlcv
        except Exception:
            continue

    if signals:
        cache.write_signals(signals, db_path)

    slug = tier_label.replace(" ", "_").lower()
    st.session_state.pop(f"selected_{market}", None)
    for key in [k for k in st.session_state if k.startswith(f"_prev_rows_{market}_{section}_{slug}")]:
        st.session_state.pop(key, None)


def _recategorize_section(market: str, section: str, db_path=None) -> None:
    """Fetch and assign cap_tier for watchlist/holdings symbols that have none or Unknown.

    Calls write_live_stock_data for each uncategorized symbol so it appears in
    the correct tier tab without running a full analysis pipeline.
    """
    from marketpulse.analysis.cap_tiers import classify_cap_tier

    if market == "IN":
        from marketpulse.data.india import fetch_ohlcv_history, fetch_quotes
    else:
        from marketpulse.data.us import fetch_ohlcv_history, fetch_quotes

    symbol_set = set(
        cache.read_watchlist(market, db_path) if section == "watchlist"
        else cache.read_holdings(market, db_path)
    )
    if not symbol_set:
        return

    signal_rows = cache.read_signals(market, db_path)
    categorized = {
        r["symbol"] for r in signal_rows
        if r.get("cap_tier") not in (None, "Unknown", "")
    }
    uncategorized = [sym for sym in symbol_set if sym not in categorized]
    if not uncategorized:
        return

    try:
        quotes = fetch_quotes(uncategorized)
    except Exception:
        return

    quote_map = {q.symbol: q for q in quotes}
    for sym in uncategorized:
        quote = quote_map.get(sym)
        if not quote:
            continue
        try:
            ohlcv_df, mc = fetch_ohlcv_history(sym)
            market_cap = mc if market == "IN" else quote.market_cap
            cap_tier = classify_cap_tier(market_cap, market)
            cache.write_live_stock_data(quote, cap_tier, db_path=db_path)
        except Exception:
            continue


def _rows_last_at(rows: list[dict]) -> str | None:
    """Return the most recent last_updated/generated_at from a list of signal rows, formatted as HH:MM IST."""
    from datetime import timedelta
    IST = timezone(timedelta(hours=5, minutes=30))
    best: str | None = None
    for r in rows:
        ts_str = r.get("last_updated") or r.get("generated_at")
        if ts_str and (best is None or ts_str > best):
            best = ts_str
    if best is None:
        return None
    try:
        ts = datetime.fromisoformat(best.replace("Z", "+00:00")).astimezone(IST)
        return ts.strftime("%I:%M %p IST")
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

    buy_tab, watchlist_tab, holdings_tab, explore_tab = st.tabs(["Buy", "Watchlist", "My Holdings", "Explore"])

    with buy_tab:
        signal_slug = "buy"

        # Tier selector + refresh button side-by-side, confined to left 60%
        filter_col, _ = st.columns([3, 2], gap="large")
        with filter_col:
            seg_col, btn_col = st.columns([5, 4], vertical_alignment="center")
            with seg_col:
                tier_label = st.segmented_control(
                    "Tier",
                    options=tier_labels,
                    default=tier_labels[0],
                    label_visibility="collapsed",
                    key=f"tier_{market}_{signal_slug}",
                ) or tier_labels[0]
            slug = tier_label.replace(" ", "_").lower()
            tier_rows = [r for r in signal_rows if r.get("cap_tier") == tier_label]
            fetching_key = f"fetching_{market}_{signal_slug}_{slug}"
            fetching = st.session_state.get(fetching_key, False)
            with btn_col:
                rows_for_ts = st.session_state.get(f"tier_buy_{market}_{signal_slug}_{slug}") or tier_rows
                last_at = _rows_last_at(rows_for_ts)
                if fetching:
                    st.button(
                        "⏳  Fetching latest details…",
                        key=f"btn_tier_buy_{market}_{signal_slug}_{slug}",
                        use_container_width=True,
                        type="secondary",
                        disabled=True,
                    )
                    _refresh_tier_buy(market, tier_label)
                    st.session_state[fetching_key] = False
                    st.rerun()
                else:
                    label = f"🔄  Refresh now  ·  last at {last_at}" if last_at else "🔄  Refresh now"
                    if st.button(label, key=f"btn_tier_buy_{market}_{signal_slug}_{slug}", use_container_width=True, type="secondary"):
                        st.session_state[fetching_key] = True
                        st.rerun()

        list_col, detail_col = st.columns([3, 2], gap="large")
        with list_col:
            tier_buy_rows = st.session_state.get(f"tier_buy_{market}_{signal_slug}_{slug}")
            if tier_buy_rows is None:
                buy_data = tier_rows
            elif len(tier_buy_rows) == 0:
                st.caption("No BUY signals found for this tier.")
                buy_data = None
            else:
                buy_data = tier_buy_rows
            if buy_data is not None:
                sym = render_stock_list(buy_data, market, filter_signal="BUY", key_prefix=f"{signal_slug}_{tier_label}")
                if sym:
                    st.session_state[f"selected_{market}"] = sym
        with detail_col:
            selected_symbol = st.session_state.get(f"selected_{market}")
            if selected_symbol:
                technical = cache.read_technical(selected_symbol, market)
                news_items = cache.read_news(selected_symbol, market)
                ohlcv = st.session_state.get(f"ohlcv_{market}", {}).get(selected_symbol)
                render_stock_detail(selected_symbol, market, technical, news_items, ohlcv, key=f"{signal_slug}_{slug}")
            else:
                st.caption("← Select a stock from the list to view details")

    with watchlist_tab:
        signal_slug = "watchlist"

        filter_col, _ = st.columns([3, 2], gap="large")
        with filter_col:
            seg_col, btn_col = st.columns([5, 4], vertical_alignment="center")
            with seg_col:
                tier_label = st.segmented_control(
                    "Tier",
                    options=tier_labels + ["Unrecognised"],
                    default=tier_labels[0],
                    label_visibility="collapsed",
                    key=f"tier_{market}_{signal_slug}",
                ) or tier_labels[0]
        slug = tier_label.replace(" ", "_").lower()
        watchlist_symbols = set(cache.read_watchlist(market))

        if tier_label == "Unrecognised":
            categorized_symbols = {
                r["symbol"] for r in signal_rows if r.get("cap_tier") not in (None, "Unknown", "")
            }
            uncategorized_watchlist = watchlist_symbols - categorized_symbols
            recategorize_key = f"recategorizing_{market}_{signal_slug}"
            with filter_col:
                with btn_col:
                    if uncategorized_watchlist:
                        if st.session_state.get(recategorize_key, False):
                            st.button(
                                "⏳  Categorizing…",
                                key=f"btn_{market}_{signal_slug}_{slug}",
                                disabled=True,
                                use_container_width=True,
                                type="secondary",
                            )
                            _recategorize_section(market, "watchlist")
                            st.session_state[recategorize_key] = False
                            st.rerun()
                        else:
                            if st.button(
                                "🔄  Refresh to categorize",
                                key=f"btn_{market}_{signal_slug}_{slug}",
                                use_container_width=True,
                                type="secondary",
                            ):
                                st.session_state[recategorize_key] = True
                                st.rerun()
            list_col, detail_col = st.columns([3, 2], gap="large")
            with list_col:
                if uncategorized_watchlist:
                    from marketpulse.data.universe import get_universe as _get_universe
                    _universe = _get_universe(market)
                    signal_map = {r["symbol"]: r for r in signal_rows}
                    uncat_rows = [
                        signal_map[sym] if sym in signal_map else {
                            "symbol": sym, "market": market,
                            "company_name": _universe.get(sym, sym),
                            "signal_type": None, "confidence_score": None, "current_price": None,
                        }
                        for sym in sorted(uncategorized_watchlist)
                    ]
                    sym = render_stock_list(uncat_rows, market, filter_signal="ALL", key_prefix=f"{signal_slug}_{tier_label}")
                    if sym:
                        st.session_state[f"selected_{market}"] = sym
                else:
                    st.caption("No unrecognised stocks in your watchlist.")
            with detail_col:
                selected_symbol = st.session_state.get(f"selected_{market}")
                if selected_symbol:
                    technical = cache.read_technical(selected_symbol, market)
                    news_items = cache.read_news(selected_symbol, market)
                    ohlcv = st.session_state.get(f"ohlcv_{market}", {}).get(selected_symbol)
                    render_stock_detail(selected_symbol, market, technical, news_items, ohlcv, key=f"{signal_slug}_{slug}")
                else:
                    st.caption("← Select a stock from the list to view details")
        else:
            tier_rows = [r for r in signal_rows if r.get("cap_tier") == tier_label]
            watchlist_rows = [r for r in tier_rows if r.get("symbol") in watchlist_symbols]
            fetching_key = f"fetching_{market}_{signal_slug}_{slug}"
            fetching = st.session_state.get(fetching_key, False)
            with filter_col:
                with btn_col:
                    if watchlist_rows:
                        if fetching:
                            st.button(
                                "⏳  Refreshing…",
                                key=f"btn_{market}_{signal_slug}_{slug}",
                                use_container_width=True,
                                type="secondary",
                                disabled=True,
                            )
                            _refresh_section(market, "watchlist", tier_label)
                            st.session_state[fetching_key] = False
                            st.rerun()
                        else:
                            last_at = _rows_last_at(watchlist_rows)
                            label = f"🔄  Refresh  ·  last at {last_at}" if last_at else "🔄  Refresh"
                            if st.button(label, key=f"btn_{market}_{signal_slug}_{slug}", use_container_width=True, type="secondary"):
                                st.session_state[fetching_key] = True
                                st.rerun()

            list_col, detail_col = st.columns([3, 2], gap="large")
            with list_col:
                if watchlist_rows:
                    sym = render_stock_list(watchlist_rows, market, filter_signal="ALL", key_prefix=f"{signal_slug}_{tier_label}")
                    if sym:
                        st.session_state[f"selected_{market}"] = sym
                else:
                    st.caption("No stocks in your watchlist yet.")
            with detail_col:
                selected_symbol = st.session_state.get(f"selected_{market}")
                if selected_symbol:
                    technical = cache.read_technical(selected_symbol, market)
                    news_items = cache.read_news(selected_symbol, market)
                    ohlcv = st.session_state.get(f"ohlcv_{market}", {}).get(selected_symbol)
                    render_stock_detail(selected_symbol, market, technical, news_items, ohlcv, key=f"{signal_slug}_{slug}")
                else:
                    st.caption("← Select a stock from the list to view details")

    with holdings_tab:
        signal_slug = "my_holdings"

        filter_col, _ = st.columns([3, 2], gap="large")
        with filter_col:
            seg_col, btn_col = st.columns([5, 4], vertical_alignment="center")
            with seg_col:
                tier_label = st.segmented_control(
                    "Tier",
                    options=tier_labels + ["Unrecognised"],
                    default=tier_labels[0],
                    label_visibility="collapsed",
                    key=f"tier_{market}_{signal_slug}",
                ) or tier_labels[0]
        slug = tier_label.replace(" ", "_").lower()
        holdings_symbols = set(cache.read_holdings(market))

        if tier_label == "Unrecognised":
            categorized_symbols = {
                r["symbol"] for r in signal_rows if r.get("cap_tier") not in (None, "Unknown", "")
            }
            uncategorized_holdings = holdings_symbols - categorized_symbols
            recategorize_key = f"recategorizing_{market}_{signal_slug}"
            with filter_col:
                with btn_col:
                    if uncategorized_holdings:
                        if st.session_state.get(recategorize_key, False):
                            st.button(
                                "⏳  Categorizing…",
                                key=f"btn_{market}_{signal_slug}_{slug}",
                                disabled=True,
                                use_container_width=True,
                                type="secondary",
                            )
                            _recategorize_section(market, "my_holdings")
                            st.session_state[recategorize_key] = False
                            st.rerun()
                        else:
                            if st.button(
                                "🔄  Refresh to categorize",
                                key=f"btn_{market}_{signal_slug}_{slug}",
                                use_container_width=True,
                                type="secondary",
                            ):
                                st.session_state[recategorize_key] = True
                                st.rerun()
            list_col, detail_col = st.columns([3, 2], gap="large")
            with list_col:
                if uncategorized_holdings:
                    from marketpulse.data.universe import get_universe as _get_universe
                    _universe = _get_universe(market)
                    signal_map = {r["symbol"]: r for r in signal_rows}
                    uncat_rows = [
                        signal_map[sym] if sym in signal_map else {
                            "symbol": sym, "market": market,
                            "company_name": _universe.get(sym, sym),
                            "signal_type": None, "confidence_score": None, "current_price": None,
                        }
                        for sym in sorted(uncategorized_holdings)
                    ]
                    sym = render_stock_list(uncat_rows, market, filter_signal="ALL", key_prefix=f"{signal_slug}_{tier_label}")
                    if sym:
                        st.session_state[f"selected_{market}"] = sym
                else:
                    st.caption("No unrecognised stocks in your holdings.")
            with detail_col:
                selected_symbol = st.session_state.get(f"selected_{market}")
                if selected_symbol:
                    technical = cache.read_technical(selected_symbol, market)
                    news_items = cache.read_news(selected_symbol, market)
                    ohlcv = st.session_state.get(f"ohlcv_{market}", {}).get(selected_symbol)
                    render_stock_detail(selected_symbol, market, technical, news_items, ohlcv, key=f"{signal_slug}_{slug}")
                else:
                    st.caption("← Select a stock from the list to view details")
        else:
            tier_rows = [r for r in signal_rows if r.get("cap_tier") == tier_label]
            holdings_rows = [r for r in tier_rows if r.get("symbol") in holdings_symbols]
            fetching_key = f"fetching_{market}_{signal_slug}_{slug}"
            fetching = st.session_state.get(fetching_key, False)
            with filter_col:
                with btn_col:
                    if holdings_rows:
                        if fetching:
                            st.button(
                                "⏳  Refreshing…",
                                key=f"btn_{market}_{signal_slug}_{slug}",
                                use_container_width=True,
                                type="secondary",
                                disabled=True,
                            )
                            _refresh_section(market, "my_holdings", tier_label)
                            st.session_state[fetching_key] = False
                            st.rerun()
                        else:
                            last_at = _rows_last_at(holdings_rows)
                            label = f"🔄  Refresh  ·  last at {last_at}" if last_at else "🔄  Refresh"
                            if st.button(label, key=f"btn_{market}_{signal_slug}_{slug}", use_container_width=True, type="secondary"):
                                st.session_state[fetching_key] = True
                                st.rerun()

            list_col, detail_col = st.columns([3, 2], gap="large")
            with list_col:
                if holdings_rows:
                    sym = render_stock_list(holdings_rows, market, filter_signal="ALL", key_prefix=f"{signal_slug}_{tier_label}")
                    if sym:
                        st.session_state[f"selected_{market}"] = sym
                else:
                    st.caption("No holdings added yet.")
            with detail_col:
                selected_symbol = st.session_state.get(f"selected_{market}")
                if selected_symbol:
                    technical = cache.read_technical(selected_symbol, market)
                    news_items = cache.read_news(selected_symbol, market)
                    ohlcv = st.session_state.get(f"ohlcv_{market}", {}).get(selected_symbol)
                    render_stock_detail(selected_symbol, market, technical, news_items, ohlcv, key=f"{signal_slug}_{slug}")
                else:
                    st.caption("← Select a stock from the list to view details")

    with explore_tab:
        _render_explore_tab(market)


def _render_explore_tab(market: str) -> None:
    import re
    from marketpulse.data.types import DataProviderError
    from marketpulse.ui.stock_detail import render_stock_detail
    from marketpulse.ui.stock_list import render_stock_list

    query = st.text_input(
        "Search",
        placeholder="Search by name or symbol…",
        label_visibility="collapsed",
        key=f"explore_query_{market}",
    )

    if len(query) < 2:
        st.caption("Enter at least 2 characters to search.")
        # Clear stale selection when query is too short
        st.session_state.pop(f"selected_explore_{market}", None)
        return

    # Clear selection when query changes so stale detail panel doesn't linger
    prev_query_key = f"explore_prev_query_{market}"
    if st.session_state.get(prev_query_key) != query:
        st.session_state.pop(f"selected_explore_{market}", None)
        st.session_state[prev_query_key] = query

    results = cache.search_stocks_live(query, market)

    # Automatic direct-ticker lookup when curated search finds nothing
    if not results and re.match(r"^[A-Za-z0-9.\-]{2,12}$", query.strip()):
        ticker_upper = query.strip().upper()
        lookup_key = f"direct_lookup_{market}_{ticker_upper}"
        cached_lookup = st.session_state.get(lookup_key)

        if cached_lookup is None:
            st.caption(
                f"No results found in universe. Trying direct lookup for '{ticker_upper}'…"
            )
            with st.spinner(f"Looking up '{ticker_upper}'…"):
                if market == "IN":
                    from marketpulse.data.india import fetch_ohlcv_history, fetch_quotes
                else:
                    from marketpulse.data.us import fetch_ohlcv_history, fetch_quotes
                try:
                    quotes = fetch_quotes([ticker_upper])
                    if not quotes:
                        raise DataProviderError(f"No data found for '{ticker_upper}'")
                    live_quote = quotes[0]
                    ohlcv_df, mc = fetch_ohlcv_history(ticker_upper)
                    market_cap = mc if market == "IN" else live_quote.market_cap
                    from marketpulse.analysis.cap_tiers import classify_cap_tier
                    cap_tier = classify_cap_tier(market_cap, market)
                    cache.write_live_stock_data(live_quote, cap_tier)
                    # Pre-populate the snapshot so selection needs no re-fetch
                    st.session_state[f"live_snapshot_{market}_{ticker_upper}"] = {
                        "quote": live_quote, "ohlcv": ohlcv_df, "cap_tier": cap_tier, "error": None,
                    }
                    cached_lookup = {
                        "symbol": live_quote.symbol,
                        "market": market,
                        "company_name": live_quote.company_name,
                        "current_price": live_quote.current_price,
                        "signal_type": None,
                        "confidence_score": None,
                        "technical_score": None,
                        "sentiment_score": None,
                        "contributing_factors": None,
                        "generated_at": None,
                        "cap_tier": cap_tier,
                        "last_updated": None,
                        "_live": True,
                    }
                    st.session_state[lookup_key] = cached_lookup
                except Exception as exc:
                    error_entry = {"error": str(exc)}
                    st.session_state[lookup_key] = error_entry
                    cached_lookup = error_entry

        if not cached_lookup or cached_lookup.get("error"):
            st.caption(f"No results found for '{ticker_upper}'.")
            return

        results = [cached_lookup]

    list_col, detail_col = st.columns([3, 2], gap="large")

    with list_col:
        if not results:
            st.caption("No results found.")
        else:
            sym = render_stock_list(results, market, filter_signal="ALL", key_prefix=f"explore_{market}")
            if sym:
                st.session_state[f"selected_explore_{market}"] = sym

    with detail_col:
        selected = st.session_state.get(f"selected_explore_{market}")
        if not selected:
            st.caption("← Select a stock from the list to view details")
        else:
            result_row = next((r for r in results if r["symbol"] == selected), None)
            is_live = result_row.get("_live", False) if result_row else True
            # Force live fetch if cap_tier is unknown — ensures stock appears in Holdings/Watchlist tabs
            if not is_live and result_row and result_row.get("cap_tier") in (None, "Unknown", ""):
                is_live = True

            if not is_live:
                # Cached stock — use DB data immediately
                technical = cache.read_technical(selected, market)
                news_items = cache.read_news(selected, market)
                ohlcv = st.session_state.get(f"ohlcv_{market}", {}).get(selected)
                render_stock_detail(selected, market, technical, news_items, ohlcv, key=f"explore_{market}")
            else:
                snapshot_key = f"live_snapshot_{market}_{selected}"
                snapshot = st.session_state.get(snapshot_key)

                if snapshot is None:
                    with st.spinner(f"Loading data for {selected}…"):
                        if market == "IN":
                            from marketpulse.data.india import fetch_ohlcv_history, fetch_quotes
                        else:
                            from marketpulse.data.us import fetch_ohlcv_history, fetch_quotes
                        try:
                            quotes = fetch_quotes([selected])
                            if not quotes:
                                raise DataProviderError(f"No data returned for {selected}")
                            live_quote = quotes[0]
                            ohlcv_df, mc = fetch_ohlcv_history(selected)
                            market_cap = mc if market == "IN" else live_quote.market_cap
                            from marketpulse.analysis.cap_tiers import classify_cap_tier
                            cap_tier = classify_cap_tier(market_cap, market)
                            universe_name = result_row.get("company_name") if result_row else None
                            cache.write_live_stock_data(live_quote, cap_tier, company_name=universe_name)
                            snapshot = {"quote": live_quote, "ohlcv": ohlcv_df, "cap_tier": cap_tier, "error": None}
                        except Exception as exc:
                            snapshot = {"quote": None, "ohlcv": None, "cap_tier": None, "error": str(exc)}
                    st.session_state[snapshot_key] = snapshot

                if snapshot.get("error"):
                    st.error(
                        f"Could not load data for {selected}. "
                        "Check your connection and try again."
                    )
                else:
                    live_quote = snapshot.get("quote")
                    ohlcv_df = snapshot.get("ohlcv")
                    if ohlcv_df is None:
                        st.caption("Price history unavailable.")
                    render_stock_detail(
                        selected, market,
                        technical=None,
                        news_items=[],
                        ohlcv_df=ohlcv_df,
                        key=f"explore_{market}",
                        live_quote=live_quote,
                    )


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
