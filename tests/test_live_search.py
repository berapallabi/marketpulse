"""Tests for Feature 009: Explore Live Search.

TDD — all tests in this file are written before their corresponding
implementation tasks (Constitution Principle III).
"""
import inspect
import re

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2: Universe module
# ─────────────────────────────────────────────────────────────────────────────

class TestUniverseModule:
    def test_get_universe_in_returns_non_empty_dict(self):
        from marketpulse.data.universe import get_universe
        result = get_universe("IN")
        assert isinstance(result, dict)
        assert len(result) >= 400

    def test_get_universe_us_returns_non_empty_dict(self):
        from marketpulse.data.universe import get_universe
        result = get_universe("US")
        assert isinstance(result, dict)
        assert len(result) >= 400

    def test_get_universe_in_symbols_are_uppercase(self):
        from marketpulse.data.universe import get_universe
        for symbol in get_universe("IN"):
            assert symbol == symbol.upper(), f"Symbol not uppercase: {symbol}"

    def test_get_universe_us_symbols_are_uppercase(self):
        from marketpulse.data.universe import get_universe
        for symbol in get_universe("US"):
            assert symbol == symbol.upper(), f"Symbol not uppercase: {symbol}"

    def test_get_universe_values_are_non_empty_strings(self):
        from marketpulse.data.universe import get_universe
        for market in ("IN", "US"):
            for sym, name in get_universe(market).items():
                assert isinstance(name, str) and len(name) > 0, f"Bad company name for {sym}"

    def test_get_universe_unknown_market_raises(self):
        from marketpulse.data.universe import get_universe
        with pytest.raises((ValueError, KeyError)):
            get_universe("XX")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 (US1): search_stocks_live
# ─────────────────────────────────────────────────────────────────────────────

class TestSearchStocksLive:
    def test_returns_universe_results_not_in_db(self, tmp_path):
        """A symbol in the universe but not in DB should appear in results."""
        from marketpulse.storage.cache import init_db, search_stocks_live
        db = tmp_path / "test.db"
        init_db(db)
        # BAJAJAUT is a Nifty 500 stock not in the Nifty 50 tracked set
        results = search_stocks_live("BAJAJAUT", "IN", db)
        symbols = [r["symbol"] for r in results]
        assert "BAJAJAUT" in symbols

    def test_deduplicates_symbol_in_both_db_and_universe(self, tmp_path):
        """A symbol in both DB and universe must appear only once."""
        from marketpulse.storage.cache import init_db, search_stocks_live, write_quotes
        from marketpulse.data.types import StockQuote
        from datetime import datetime, timezone
        db = tmp_path / "test.db"
        init_db(db)
        # Write a stock that is also in the Nifty 500 universe
        q = StockQuote(
            symbol="RELIANCE", market="IN", company_name="Reliance Industries Ltd",
            current_price=2500.0, open_price=None, high_price=None, low_price=None,
            volume=None, currency="INR", fetched_at=datetime.now(timezone.utc).isoformat(),
        )
        write_quotes([q], db)
        results = search_stocks_live("RELIANCE", "IN", db)
        symbols = [r["symbol"] for r in results]
        assert symbols.count("RELIANCE") == 1

    def test_is_market_scoped_in(self, tmp_path):
        """India search must not return US symbols."""
        from marketpulse.storage.cache import init_db, search_stocks_live
        db = tmp_path / "test.db"
        init_db(db)
        results = search_stocks_live("Apple", "IN", db)
        markets = {r["market"] for r in results}
        assert "US" not in markets

    def test_is_market_scoped_us(self, tmp_path):
        """US search must not return India symbols."""
        from marketpulse.storage.cache import init_db, search_stocks_live
        db = tmp_path / "test.db"
        init_db(db)
        results = search_stocks_live("Reliance", "US", db)
        markets = {r["market"] for r in results}
        assert "IN" not in markets

    def test_short_query_returns_empty(self, tmp_path):
        from marketpulse.storage.cache import init_db, search_stocks_live
        db = tmp_path / "test.db"
        init_db(db)
        assert search_stocks_live("A", "IN", db) == []
        assert search_stocks_live("", "IN", db) == []

    def test_universe_only_rows_have_live_flag(self, tmp_path):
        """Rows sourced only from the universe dict must carry _live=True."""
        from marketpulse.storage.cache import init_db, search_stocks_live
        db = tmp_path / "test.db"
        init_db(db)
        results = search_stocks_live("BAJAJAUT", "IN", db)
        live_rows = [r for r in results if r.get("symbol") == "BAJAJAUT"]
        assert live_rows, "BAJAJAUT should be in results"
        assert live_rows[0]["_live"] is True

    def test_db_rows_have_live_false(self, tmp_path):
        """Rows sourced from the DB must have _live=False."""
        from marketpulse.storage.cache import init_db, search_stocks_live, write_quotes
        from marketpulse.data.types import StockQuote
        from datetime import datetime, timezone
        db = tmp_path / "test.db"
        init_db(db)
        q = StockQuote(
            symbol="RELIANCE", market="IN", company_name="Reliance Industries Ltd",
            current_price=2500.0, open_price=None, high_price=None, low_price=None,
            volume=None, currency="INR", fetched_at=datetime.now(timezone.utc).isoformat(),
        )
        write_quotes([q], db)
        results = search_stocks_live("RELIANCE", "IN", db)
        rel_rows = [r for r in results if r["symbol"] == "RELIANCE"]
        assert rel_rows
        assert rel_rows[0]["_live"] is False

    def test_case_insensitive_match(self, tmp_path):
        from marketpulse.storage.cache import init_db, search_stocks_live
        db = tmp_path / "test.db"
        init_db(db)
        results_lower = search_stocks_live("bajajaut", "IN", db)
        results_upper = search_stocks_live("BAJAJAUT", "IN", db)
        syms_lower = [r["symbol"] for r in results_lower]
        syms_upper = [r["symbol"] for r in results_upper]
        assert "BAJAJAUT" in syms_lower
        assert "BAJAJAUT" in syms_upper

    def test_missing_db_returns_universe_results(self, tmp_path):
        """When DB does not exist, universe results are still returned."""
        from marketpulse.storage.cache import search_stocks_live
        db = tmp_path / "nonexistent.db"
        results = search_stocks_live("BAJAJAUT", "IN", db)
        symbols = [r["symbol"] for r in results]
        assert "BAJAJAUT" in symbols

    def test_db_results_appear_before_universe_results(self, tmp_path):
        """DB rows should come first in the result list."""
        from marketpulse.storage.cache import init_db, search_stocks_live, write_quotes
        from marketpulse.data.types import StockQuote
        from datetime import datetime, timezone
        db = tmp_path / "test.db"
        init_db(db)
        q = StockQuote(
            symbol="RELIANCE", market="IN", company_name="Reliance Industries Ltd",
            current_price=2500.0, open_price=None, high_price=None, low_price=None,
            volume=None, currency="INR", fetched_at=datetime.now(timezone.utc).isoformat(),
        )
        write_quotes([q], db)
        # Search for something that will match both DB (RELIANCE) and universe rows
        results = search_stocks_live("REL", "IN", db)
        if len(results) > 1:
            # First row should be from DB (RELIANCE)
            first_db = next((r for r in results if r["_live"] is False), None)
            first_live = next((r for r in results if r["_live"] is True), None)
            if first_db and first_live:
                assert results.index(first_db) < results.index(first_live)

    def test_us_universe_symbol_found(self, tmp_path):
        """A S&P 500 stock not in S&P 100 should be findable by name."""
        from marketpulse.storage.cache import init_db, search_stocks_live
        db = tmp_path / "test.db"
        init_db(db)
        results = search_stocks_live("Palantir", "US", db)
        symbols = [r["symbol"] for r in results]
        assert "PLTR" in symbols


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 (US1): _render_explore_tab uses search_stocks_live
# ─────────────────────────────────────────────────────────────────────────────

class TestExploreTabUsesLiveSearch:
    def test_render_explore_tab_calls_search_stocks_live(self):
        """_render_explore_tab must call search_stocks_live, not search_stocks."""
        import marketpulse.ui.dashboard as dashboard
        src = inspect.getsource(dashboard._render_explore_tab)
        assert "search_stocks_live" in src

    def test_render_explore_tab_does_not_call_plain_search_stocks(self):
        """search_stocks (old) should no longer be called directly in _render_explore_tab."""
        import marketpulse.ui.dashboard as dashboard
        src = inspect.getsource(dashboard._render_explore_tab)
        # Must not call cache.search_stocks( (but search_stocks_live is fine)
        assert "cache.search_stocks(" not in src


# ─────────────────────────────────────────────────────────────────────────────
# Phase 4 (US2): on-demand fetch behaviour
# ─────────────────────────────────────────────────────────────────────────────

class TestRenderStockDetailSignature:
    def test_render_stock_detail_accepts_live_quote_param(self):
        from marketpulse.ui.stock_detail import render_stock_detail
        sig = inspect.signature(render_stock_detail)
        assert "live_quote" in sig.parameters

    def test_live_quote_param_defaults_to_none(self):
        from marketpulse.ui.stock_detail import render_stock_detail
        sig = inspect.signature(render_stock_detail)
        assert sig.parameters["live_quote"].default is None


class TestExploreTabOnDemandFetch:
    def test_render_explore_tab_contains_spinner(self):
        import marketpulse.ui.dashboard as dashboard
        src = inspect.getsource(dashboard._render_explore_tab)
        assert "st.spinner" in src

    def test_render_explore_tab_caches_live_snapshot_in_session_state(self):
        import marketpulse.ui.dashboard as dashboard
        src = inspect.getsource(dashboard._render_explore_tab)
        assert "live_snapshot_" in src

    def test_render_explore_tab_shows_error_on_fetch_failure(self):
        import marketpulse.ui.dashboard as dashboard
        src = inspect.getsource(dashboard._render_explore_tab)
        assert "st.error" in src

    def test_render_explore_tab_auto_direct_lookup_uses_session_cache(self):
        """Direct lookup must be automatic (no button) and cached under direct_lookup_ key."""
        import marketpulse.ui.dashboard as dashboard
        src = inspect.getsource(dashboard._render_explore_tab)
        # Auto-lookup caches result so it doesn't re-fetch on every rerun
        assert "direct_lookup_" in src
        # No manual button — lookup is automatic
        assert "Try direct lookup" not in src
