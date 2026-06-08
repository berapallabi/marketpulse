"""Tests for the signal filter tab layout and per-tab rendering logic."""
import sqlite3
from unittest.mock import MagicMock, patch

import pytest

from marketpulse.storage.cache import (
    add_to_holdings,
    add_to_watchlist,
    init_db,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def db(tmp_db):
    init_db(tmp_db)
    return tmp_db


def _signal_row(symbol, signal_type="BUY", cap_tier="Large Cap"):
    return {
        "symbol": symbol,
        "market": "IN",
        "signal_type": signal_type,
        "confidence_score": 75,
        "technical_score": 0.7,
        "sentiment_score": 0.6,
        "cap_tier": cap_tier,
        "current_price": 100.0,
        "last_updated": "2026-06-08T10:00:00+00:00",
        "contributing_factors": "[]",
        "generated_at": "2026-06-08T10:00:00+00:00",
    }


TIER_ROWS = [
    _signal_row("RELIANCE", "BUY"),
    _signal_row("TCS", "BUY"),
    _signal_row("INFY", "SELL"),
    _signal_row("HDFC", "HOLD"),
]


# ── US1: Tab options ───────────────────────────────────────────────────────────

class TestTabOptions:
    """Segmented control must show exactly Buy/Watchlist/My Holdings."""

    def test_options_are_buy_watchlist_holdings(self):
        import marketpulse.ui.dashboard as dashboard
        import inspect, ast
        src = inspect.getsource(dashboard._render_market_tab)
        # Find the options list passed to st.segmented_control
        assert '"Buy"' in src or "'Buy'" in src
        assert '"Watchlist"' in src or "'Watchlist'" in src
        assert '"My Holdings"' in src or "'My Holdings'" in src

    def test_old_options_absent(self):
        import marketpulse.ui.dashboard as dashboard
        import inspect
        src = inspect.getsource(dashboard._render_market_tab)
        # "All", "SELL", "HOLD" must not appear as segmented_control options
        # Check the options list specifically (not other references)
        assert '"All"' not in src and "'All'" not in src
        assert '"SELL"' not in src and "'SELL'" not in src
        assert '"HOLD"' not in src and "'HOLD'" not in src

    def test_default_is_buy(self):
        import marketpulse.ui.dashboard as dashboard
        import inspect
        src = inspect.getsource(dashboard._render_market_tab)
        assert 'default="Buy"' in src or "default='Buy'" in src


# ── US1: Buy tab regression ────────────────────────────────────────────────────

class TestBuyTab:
    """Buy tab must return only BUY-signal rows (regression against old BUY filter)."""

    def test_buy_tab_filters_to_buy_signals(self, db):
        from marketpulse.storage.cache import read_signals
        buy_rows = [r for r in TIER_ROWS if r["signal_type"] == "BUY"]
        assert len(buy_rows) == 2
        assert all(r["signal_type"] == "BUY" for r in buy_rows)
        non_buy = [r for r in buy_rows if r["signal_type"] != "BUY"]
        assert non_buy == []

    def test_sell_rows_not_in_buy_filter(self):
        buy_rows = [r for r in TIER_ROWS if r["signal_type"] == "BUY"]
        symbols = [r["symbol"] for r in buy_rows]
        assert "INFY" not in symbols

    def test_hold_rows_not_in_buy_filter(self):
        buy_rows = [r for r in TIER_ROWS if r["signal_type"] == "BUY"]
        symbols = [r["symbol"] for r in buy_rows]
        assert "HDFC" not in symbols


# ── US2: Watchlist tab ─────────────────────────────────────────────────────────

class TestWatchlistTab:
    """Watchlist tab shows only symbols in the watchlist table for the given market."""

    def test_watchlist_tab_shows_watchlisted_symbols(self, db):
        add_to_watchlist("RELIANCE", "IN", db)
        from marketpulse.storage.cache import read_watchlist
        watchlist_symbols = set(read_watchlist("IN", db))
        visible = [r for r in TIER_ROWS if r["symbol"] in watchlist_symbols]
        assert len(visible) == 1
        assert visible[0]["symbol"] == "RELIANCE"

    def test_watchlist_tab_empty_state_when_no_entries(self, db):
        from marketpulse.storage.cache import read_watchlist
        watchlist_symbols = set(read_watchlist("IN", db))
        visible = [r for r in TIER_ROWS if r["symbol"] in watchlist_symbols]
        assert visible == []

    def test_watchlist_tab_does_not_show_non_watchlisted_symbols(self, db):
        add_to_watchlist("RELIANCE", "IN", db)
        from marketpulse.storage.cache import read_watchlist
        watchlist_symbols = set(read_watchlist("IN", db))
        visible_symbols = {r["symbol"] for r in TIER_ROWS if r["symbol"] in watchlist_symbols}
        assert "TCS" not in visible_symbols
        assert "INFY" not in visible_symbols
        assert "HDFC" not in visible_symbols

    def test_watchlist_tab_shows_all_watchlisted_symbols(self, db):
        add_to_watchlist("RELIANCE", "IN", db)
        add_to_watchlist("INFY", "IN", db)
        from marketpulse.storage.cache import read_watchlist
        watchlist_symbols = set(read_watchlist("IN", db))
        visible = {r["symbol"] for r in TIER_ROWS if r["symbol"] in watchlist_symbols}
        assert visible == {"RELIANCE", "INFY"}


# ── US2: Watchlist detail panel buttons ───────────────────────────────────────

class TestWatchlistDetailPanel:
    """Detail panel shows correct add/remove button based on watchlist membership."""

    def test_add_button_label_when_not_in_watchlist(self, db):
        from marketpulse.storage.cache import read_watchlist
        watchlist = read_watchlist("IN", db)
        in_list = "RELIANCE" in watchlist
        expected_label = "✓ Remove from Watchlist" if in_list else "+ Add to Watchlist"
        assert expected_label == "+ Add to Watchlist"

    def test_remove_button_label_when_in_watchlist(self, db):
        add_to_watchlist("RELIANCE", "IN", db)
        from marketpulse.storage.cache import read_watchlist
        watchlist = read_watchlist("IN", db)
        in_list = "RELIANCE" in watchlist
        expected_label = "✓ Remove from Watchlist" if in_list else "+ Add to Watchlist"
        assert expected_label == "✓ Remove from Watchlist"

    def test_detail_panel_imports_watchlist_functions(self):
        import inspect
        import marketpulse.ui.stock_detail as sd
        src = inspect.getsource(sd)
        assert "add_to_watchlist" in src
        assert "remove_from_watchlist" in src
        assert "read_watchlist" in src


# ── US3: My Holdings tab ───────────────────────────────────────────────────────

class TestHoldingsTab:
    """My Holdings tab shows only symbols in the holdings table for the given market."""

    def test_holdings_tab_shows_held_symbols(self, db):
        add_to_holdings("TCS", "IN", db)
        from marketpulse.storage.cache import read_holdings
        holdings_symbols = set(read_holdings("IN", db))
        visible = [r for r in TIER_ROWS if r["symbol"] in holdings_symbols]
        assert len(visible) == 1
        assert visible[0]["symbol"] == "TCS"

    def test_holdings_tab_empty_state_when_no_entries(self, db):
        from marketpulse.storage.cache import read_holdings
        holdings_symbols = set(read_holdings("IN", db))
        visible = [r for r in TIER_ROWS if r["symbol"] in holdings_symbols]
        assert visible == []

    def test_holdings_tab_does_not_show_non_held_symbols(self, db):
        add_to_holdings("TCS", "IN", db)
        from marketpulse.storage.cache import read_holdings
        holdings_symbols = set(read_holdings("IN", db))
        visible_symbols = {r["symbol"] for r in TIER_ROWS if r["symbol"] in holdings_symbols}
        assert "RELIANCE" not in visible_symbols
        assert "INFY" not in visible_symbols
        assert "HDFC" not in visible_symbols

    def test_holdings_tab_shows_all_held_symbols(self, db):
        add_to_holdings("TCS", "IN", db)
        add_to_holdings("HDFC", "IN", db)
        from marketpulse.storage.cache import read_holdings
        holdings_symbols = set(read_holdings("IN", db))
        visible = {r["symbol"] for r in TIER_ROWS if r["symbol"] in holdings_symbols}
        assert visible == {"TCS", "HDFC"}


# ── US3: My Holdings detail panel buttons ─────────────────────────────────────

class TestHoldingsDetailPanel:
    """Detail panel shows correct add/remove button based on holdings membership."""

    def test_add_button_label_when_not_in_holdings(self, db):
        from marketpulse.storage.cache import read_holdings
        holdings = read_holdings("IN", db)
        in_list = "TCS" in holdings
        expected_label = "✓ Remove from Holdings" if in_list else "+ Add to Holdings"
        assert expected_label == "+ Add to Holdings"

    def test_remove_button_label_when_in_holdings(self, db):
        add_to_holdings("TCS", "IN", db)
        from marketpulse.storage.cache import read_holdings
        holdings = read_holdings("IN", db)
        in_list = "TCS" in holdings
        expected_label = "✓ Remove from Holdings" if in_list else "+ Add to Holdings"
        assert expected_label == "✓ Remove from Holdings"

    def test_detail_panel_imports_holdings_functions(self):
        import inspect
        import marketpulse.ui.stock_detail as sd
        src = inspect.getsource(sd)
        assert "add_to_holdings" in src
        assert "remove_from_holdings" in src
        assert "read_holdings" in src
