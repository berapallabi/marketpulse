"""Tests for Feature 010: Watchlist & Holdings Refresh.

Covers _refresh_section() — the core function that runs full analysis
for watchlist or holdings symbols scoped to a single tier.
"""
import sqlite3
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import numpy as np
import pytest

from marketpulse.storage.cache import (
    add_to_holdings,
    add_to_watchlist,
    init_db,
    read_signals,
    write_signals,
)
from marketpulse.analysis.signals import Signal


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_signal(symbol, market, signal_type, confidence, cap_tier):
    now = datetime.now(timezone.utc).isoformat()
    return Signal(
        symbol=symbol,
        market=market,
        signal_type=signal_type,
        confidence_score=confidence,
        technical_score=float(confidence),
        sentiment_score=50.0,
        contributing_factors=[],
        generated_at=now,
        cap_tier=cap_tier,
    )


def _seed_stock(db_path, symbol, market="IN"):
    conn = sqlite3.connect(db_path)
    try:
        currency = "INR" if market == "IN" else "USD"
        conn.execute(
            "INSERT OR IGNORE INTO stocks (symbol, market, company_name, currency) VALUES (?, ?, ?, ?)",
            (symbol, market, f"{symbol} Corp", currency),
        )
        conn.commit()
    finally:
        conn.close()


def _make_ohlcv():
    rng = np.random.default_rng(42)
    n = 200
    dates = pd.date_range(end="2024-12-31", periods=n, freq="B")
    close = 100 + np.cumsum(rng.normal(0, 1, n))
    close = np.maximum(close, 10)
    return pd.DataFrame({
        "Date": dates,
        "Open": close * 0.99,
        "High": close * 1.01,
        "Low": close * 0.98,
        "Close": close,
        "Volume": rng.integers(100_000, 1_000_000, n),
    })


def _mock_quote(symbol, market="IN", market_cap=500_000_000_000):
    now = datetime.now(timezone.utc).isoformat()
    q = MagicMock()
    q.symbol = symbol
    q.market = market
    q.company_name = f"{symbol} Corp"
    q.market_cap = market_cap
    q.currency = "INR" if market == "IN" else "USD"
    q.current_price = 1000.0
    q.open_price = 990.0
    q.high_price = 1010.0
    q.low_price = 985.0
    q.volume = 1_000_000
    q.fetched_at = now
    return q


def _mock_technical(symbol, market="IN"):
    now = datetime.now(timezone.utc).isoformat()
    t = MagicMock()
    t.symbol = symbol
    t.market = market
    t.technical_score = 68.0
    t.rsi_14 = 55.0
    t.macd_val = 1.2
    t.macd_signal = 0.8
    t.bb_upper = 110.0
    t.bb_middle = 100.0
    t.bb_lower = 90.0
    t.sma_50 = 98.0
    t.sma_200 = 95.0
    t.rsi_score = 60.0
    t.macd_score = 65.0
    t.bb_score = 55.0
    t.sma_score = 70.0
    t.computed_at = now
    return t


def _mock_sentiment(symbol, market="IN"):
    s = MagicMock()
    s.symbol = symbol
    s.market = market
    s.sentiment_score = 60.0
    s.is_sufficient = True
    s.article_count = 0
    s.matched_articles = []
    return s


def _real_signal(symbol, market="IN", cap_tier="Large Cap"):
    return _make_signal(symbol, market, "BUY", 72, cap_tier)


@pytest.fixture()
def db(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    return db_path


# ─────────────────────────────────────────────────────────────────────────────
# US1: Refresh Watchlist Analysis
# ─────────────────────────────────────────────────────────────────────────────

class TestRefreshSectionUpdatesWatchlistSymbols:
    """T005 — _refresh_section writes updated signals for watchlist symbols in the tier."""

    def test_signal_updated_after_refresh(self, db):
        _seed_stock(db, "TCS")
        write_signals([_make_signal("TCS", "IN", "HOLD", 0, "Large Cap")], db)
        add_to_watchlist("TCS", "IN", db)

        mock_quote = _mock_quote("TCS")
        mock_technical = _mock_technical("TCS")
        mock_sentiment = _mock_sentiment("TCS")
        result_signal = _real_signal("TCS")

        with (
            patch("marketpulse.data.india.fetch_quotes", return_value=[mock_quote]),
            patch("marketpulse.data.india.fetch_ohlcv_history", return_value=(_make_ohlcv(), 500_000_000_000)),
            patch("marketpulse.analysis.indicators.compute_indicators", return_value=mock_technical),
            patch("marketpulse.data.sentiment.fetch_market_articles", return_value=[]),
            patch("marketpulse.data.sentiment.score_articles_for_stock", return_value=mock_sentiment),
            patch("marketpulse.analysis.signals.generate_signal", return_value=result_signal),
            patch("streamlit.session_state", {}),
            patch("streamlit.error"),
        ):
            from marketpulse.ui.dashboard import _refresh_section
            _refresh_section("IN", "watchlist", "Large Cap", db_path=db)

        rows = read_signals("IN", db)
        tcs_row = next((r for r in rows if r["symbol"] == "TCS"), None)
        assert tcs_row is not None
        assert tcs_row["signal_type"] == "BUY"
        assert tcs_row["confidence_score"] == 72


class TestRefreshSectionNoOpWhenEmpty:
    """T006 — _refresh_section is a no-op when section is empty."""

    def test_no_crash_empty_watchlist(self, db):
        with (
            patch("streamlit.session_state", {}),
            patch("streamlit.error"),
        ):
            from marketpulse.ui.dashboard import _refresh_section
            _refresh_section("IN", "watchlist", "Large Cap", db_path=db)
        assert read_signals("IN", db) == []

    def test_no_signals_written_when_watchlist_empty(self, db):
        _seed_stock(db, "TCS")
        write_signals([_make_signal("TCS", "IN", "HOLD", 0, "Large Cap")], db)

        with (
            patch("streamlit.session_state", {}),
            patch("streamlit.error"),
        ):
            from marketpulse.ui.dashboard import _refresh_section
            _refresh_section("IN", "watchlist", "Large Cap", db_path=db)

        rows = read_signals("IN", db)
        tcs_row = next((r for r in rows if r["symbol"] == "TCS"), None)
        assert tcs_row["signal_type"] == "HOLD"
        assert tcs_row["confidence_score"] == 0


class TestRefreshSectionSkipsUnavailable:
    """T007 — unavailable stock is skipped; remaining stocks are still updated."""

    def test_second_stock_updated_when_first_unavailable(self, db):
        for sym in ("TCS", "INFY"):
            _seed_stock(db, sym)
            write_signals([_make_signal(sym, "IN", "HOLD", 0, "Large Cap")], db)
            add_to_watchlist(sym, "IN", db)

        mock_quote_tcs = _mock_quote("TCS")
        mock_quote_infy = _mock_quote("INFY")
        mock_technical_infy = _mock_technical("INFY")
        mock_sentiment_infy = _mock_sentiment("INFY")
        result_signal_infy = _real_signal("INFY")

        ohlcv = _make_ohlcv()

        def _ohlcv_side_effect(symbol):
            if symbol == "TCS":
                return (None, None)
            return (ohlcv, 500_000_000_000)

        with (
            patch("marketpulse.data.india.fetch_quotes", return_value=[mock_quote_tcs, mock_quote_infy]),
            patch("marketpulse.data.india.fetch_ohlcv_history", side_effect=_ohlcv_side_effect),
            patch("marketpulse.analysis.indicators.compute_indicators", return_value=mock_technical_infy),
            patch("marketpulse.data.sentiment.fetch_market_articles", return_value=[]),
            patch("marketpulse.data.sentiment.score_articles_for_stock", return_value=mock_sentiment_infy),
            patch("marketpulse.analysis.signals.generate_signal", return_value=result_signal_infy),
            patch("streamlit.session_state", {}),
            patch("streamlit.error"),
        ):
            from marketpulse.ui.dashboard import _refresh_section
            _refresh_section("IN", "watchlist", "Large Cap", db_path=db)

        rows = {r["symbol"]: r for r in read_signals("IN", db)}
        assert rows["TCS"]["confidence_score"] == 0
        assert rows["INFY"]["confidence_score"] == 72


class TestRefreshSectionUpgradesPlaceholderSignal:
    """T008 — placeholder HOLD/0 from Explore is upgraded to real analysis."""

    def test_placeholder_replaced_with_real_signal(self, db):
        _seed_stock(db, "HDFCBANK")
        write_signals([_make_signal("HDFCBANK", "IN", "HOLD", 0, "Large Cap")], db)
        add_to_watchlist("HDFCBANK", "IN", db)

        real_sig = _real_signal("HDFCBANK")
        mock_quote = _mock_quote("HDFCBANK")
        mock_technical = _mock_technical("HDFCBANK")
        mock_sentiment = _mock_sentiment("HDFCBANK")

        with (
            patch("marketpulse.data.india.fetch_quotes", return_value=[mock_quote]),
            patch("marketpulse.data.india.fetch_ohlcv_history", return_value=(_make_ohlcv(), 700_000_000_000)),
            patch("marketpulse.analysis.indicators.compute_indicators", return_value=mock_technical),
            patch("marketpulse.data.sentiment.fetch_market_articles", return_value=[]),
            patch("marketpulse.data.sentiment.score_articles_for_stock", return_value=mock_sentiment),
            patch("marketpulse.analysis.signals.generate_signal", return_value=real_sig),
            patch("streamlit.session_state", {}),
            patch("streamlit.error"),
        ):
            from marketpulse.ui.dashboard import _refresh_section
            _refresh_section("IN", "watchlist", "Large Cap", db_path=db)

        rows = {r["symbol"]: r for r in read_signals("IN", db)}
        assert rows["HDFCBANK"]["signal_type"] == "BUY"
        assert rows["HDFCBANK"]["confidence_score"] > 0


# ─────────────────────────────────────────────────────────────────────────────
# US2: Refresh Holdings Analysis
# ─────────────────────────────────────────────────────────────────────────────

class TestRefreshSectionUpdatesHoldingsSymbols:
    """T010 — _refresh_section works for holdings section."""

    def test_holdings_signal_updated(self, db):
        _seed_stock(db, "RELIANCE")
        write_signals([_make_signal("RELIANCE", "IN", "HOLD", 0, "Large Cap")], db)
        add_to_holdings("RELIANCE", "IN", db)

        real_sig = _real_signal("RELIANCE")
        mock_quote = _mock_quote("RELIANCE")
        mock_technical = _mock_technical("RELIANCE")
        mock_sentiment = _mock_sentiment("RELIANCE")

        with (
            patch("marketpulse.data.india.fetch_quotes", return_value=[mock_quote]),
            patch("marketpulse.data.india.fetch_ohlcv_history", return_value=(_make_ohlcv(), 500_000_000_000)),
            patch("marketpulse.analysis.indicators.compute_indicators", return_value=mock_technical),
            patch("marketpulse.data.sentiment.fetch_market_articles", return_value=[]),
            patch("marketpulse.data.sentiment.score_articles_for_stock", return_value=mock_sentiment),
            patch("marketpulse.analysis.signals.generate_signal", return_value=real_sig),
            patch("streamlit.session_state", {}),
            patch("streamlit.error"),
        ):
            from marketpulse.ui.dashboard import _refresh_section
            _refresh_section("IN", "my_holdings", "Large Cap", db_path=db)

        rows = {r["symbol"]: r for r in read_signals("IN", db)}
        assert rows["RELIANCE"]["signal_type"] == "BUY"
        assert rows["RELIANCE"]["confidence_score"] == 72


# ─────────────────────────────────────────────────────────────────────────────
# US3: Scoped Refresh per Tier
# ─────────────────────────────────────────────────────────────────────────────

class TestRefreshSectionScopeIsolation:
    """T011 — refreshing one (section, tier) does not affect other sections or tiers."""

    def test_other_section_unchanged(self, db):
        """Refreshing watchlist Large Cap does not change holdings Large Cap signal."""
        _seed_stock(db, "TCS")
        _seed_stock(db, "RELIANCE")
        write_signals([
            _make_signal("TCS", "IN", "HOLD", 0, "Large Cap"),
            _make_signal("RELIANCE", "IN", "HOLD", 0, "Large Cap"),
        ], db)
        add_to_watchlist("TCS", "IN", db)
        add_to_holdings("RELIANCE", "IN", db)

        tcs_sig = _real_signal("TCS")
        mock_quote = _mock_quote("TCS")
        mock_technical = _mock_technical("TCS")
        mock_sentiment = _mock_sentiment("TCS")

        with (
            patch("marketpulse.data.india.fetch_quotes", return_value=[mock_quote]),
            patch("marketpulse.data.india.fetch_ohlcv_history", return_value=(_make_ohlcv(), 500_000_000_000)),
            patch("marketpulse.analysis.indicators.compute_indicators", return_value=mock_technical),
            patch("marketpulse.data.sentiment.fetch_market_articles", return_value=[]),
            patch("marketpulse.data.sentiment.score_articles_for_stock", return_value=mock_sentiment),
            patch("marketpulse.analysis.signals.generate_signal", return_value=tcs_sig),
            patch("streamlit.session_state", {}),
            patch("streamlit.error"),
        ):
            from marketpulse.ui.dashboard import _refresh_section
            _refresh_section("IN", "watchlist", "Large Cap", db_path=db)

        rows = {r["symbol"]: r for r in read_signals("IN", db)}
        assert rows["TCS"]["confidence_score"] == 72
        assert rows["RELIANCE"]["confidence_score"] == 0

    def test_other_tier_unchanged(self, db):
        """T012 — refreshing Mid Cap watchlist leaves Large Cap watchlist signal unchanged."""
        _seed_stock(db, "TCS")
        _seed_stock(db, "VOLTAS")
        write_signals([
            _make_signal("TCS", "IN", "HOLD", 0, "Large Cap"),
            _make_signal("VOLTAS", "IN", "HOLD", 0, "Mid Cap"),
        ], db)
        add_to_watchlist("TCS", "IN", db)
        add_to_watchlist("VOLTAS", "IN", db)

        voltas_sig = _real_signal("VOLTAS", cap_tier="Mid Cap")
        mock_quote = _mock_quote("VOLTAS")
        mock_technical = _mock_technical("VOLTAS")
        mock_sentiment = _mock_sentiment("VOLTAS")

        with (
            patch("marketpulse.data.india.fetch_quotes", return_value=[mock_quote]),
            patch("marketpulse.data.india.fetch_ohlcv_history", return_value=(_make_ohlcv(), 20_000_000_000)),
            patch("marketpulse.analysis.indicators.compute_indicators", return_value=mock_technical),
            patch("marketpulse.data.sentiment.fetch_market_articles", return_value=[]),
            patch("marketpulse.data.sentiment.score_articles_for_stock", return_value=mock_sentiment),
            patch("marketpulse.analysis.signals.generate_signal", return_value=voltas_sig),
            patch("streamlit.session_state", {}),
            patch("streamlit.error"),
        ):
            from marketpulse.ui.dashboard import _refresh_section
            _refresh_section("IN", "watchlist", "Mid Cap", db_path=db)

        rows = {r["symbol"]: r for r in read_signals("IN", db)}
        assert rows["VOLTAS"]["confidence_score"] == 72
        assert rows["TCS"]["confidence_score"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# Recategorize Section — fixes holdings/watchlist stocks with Unknown cap_tier
# ─────────────────────────────────────────────────────────────────────────────

class TestRecategorizeSectionAssignsCapTier:
    """_recategorize_section sets cap_tier for holdings with Unknown tier."""

    def test_unknown_holdings_get_cap_tier(self, db):
        _seed_stock(db, "TCS")
        # Placeholder signal with Unknown cap_tier (as written by write_live_stock_data when mc=None)
        write_signals([_make_signal("TCS", "IN", "HOLD", 0, "Unknown")], db)
        add_to_holdings("TCS", "IN", db)

        mock_quote = _mock_quote("TCS", market_cap=500_000_000_000)

        with (
            patch("marketpulse.data.india.fetch_quotes", return_value=[mock_quote]),
            patch("marketpulse.data.india.fetch_ohlcv_history", return_value=(_make_ohlcv(), 500_000_000_000)),
            patch("streamlit.session_state", {}),
            patch("streamlit.error"),
        ):
            from marketpulse.ui.dashboard import _recategorize_section
            _recategorize_section("IN", "my_holdings", db_path=db)

        rows = read_signals("IN", db)
        tcs_row = next(r for r in rows if r["symbol"] == "TCS")
        assert tcs_row["cap_tier"] not in (None, "Unknown", "")

    def test_no_signal_holdings_get_signal_with_cap_tier(self, db):
        _seed_stock(db, "INFY")
        add_to_holdings("INFY", "IN", db)
        # No signal entry at all

        mock_quote = _mock_quote("INFY", market_cap=200_000_000_000)

        with (
            patch("marketpulse.data.india.fetch_quotes", return_value=[mock_quote]),
            patch("marketpulse.data.india.fetch_ohlcv_history", return_value=(_make_ohlcv(), 200_000_000_000)),
            patch("streamlit.session_state", {}),
            patch("streamlit.error"),
        ):
            from marketpulse.ui.dashboard import _recategorize_section
            _recategorize_section("IN", "my_holdings", db_path=db)

        rows = read_signals("IN", db)
        infy_row = next((r for r in rows if r["symbol"] == "INFY"), None)
        assert infy_row is not None
        assert infy_row["cap_tier"] not in (None, "Unknown", "")

    def test_already_categorized_signal_not_overwritten(self, db):
        _seed_stock(db, "RELIANCE")
        write_signals([_make_signal("RELIANCE", "IN", "BUY", 80, "Large Cap")], db)
        add_to_holdings("RELIANCE", "IN", db)

        with (
            patch("marketpulse.data.india.fetch_quotes", return_value=[]),
            patch("streamlit.session_state", {}),
            patch("streamlit.error"),
        ):
            from marketpulse.ui.dashboard import _recategorize_section
            _recategorize_section("IN", "my_holdings", db_path=db)

        rows = read_signals("IN", db)
        rel_row = next(r for r in rows if r["symbol"] == "RELIANCE")
        # Already categorized — should not be touched
        assert rel_row["signal_type"] == "BUY"
        assert rel_row["confidence_score"] == 80

    def test_no_op_when_section_empty(self, db):
        with (
            patch("streamlit.session_state", {}),
            patch("streamlit.error"),
        ):
            from marketpulse.ui.dashboard import _recategorize_section
            _recategorize_section("IN", "my_holdings", db_path=db)
        assert read_signals("IN", db) == []
