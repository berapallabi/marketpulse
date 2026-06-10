"""Tests for the Explore tab: search_stocks cache function and tab structure."""
import inspect

import pytest

from marketpulse.storage.cache import init_db, write_quotes


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def db(tmp_db):
    init_db(tmp_db)
    return tmp_db


@pytest.fixture
def populated_db(db, mock_india_quotes, mock_us_quotes):
    write_quotes(mock_india_quotes, db)
    write_quotes(mock_us_quotes, db)
    return db


# ── Phase 2: search_stocks ────────────────────────────────────────────────────

class TestSearchStocks:
    def test_match_by_symbol_prefix(self, populated_db):
        from marketpulse.storage.cache import search_stocks
        results = search_stocks("REL", "IN", populated_db)
        symbols = [r["symbol"] for r in results]
        assert "RELIANCE" in symbols

    def test_match_by_company_name_substring(self, populated_db):
        from marketpulse.storage.cache import search_stocks
        results = search_stocks("Tata", "IN", populated_db)
        symbols = [r["symbol"] for r in results]
        assert "TCS" in symbols

    def test_case_insensitive_symbol(self, populated_db):
        from marketpulse.storage.cache import search_stocks
        results = search_stocks("reliance", "IN", populated_db)
        symbols = [r["symbol"] for r in results]
        assert "RELIANCE" in symbols

    def test_case_insensitive_company_name(self, populated_db):
        from marketpulse.storage.cache import search_stocks
        results = search_stocks("tata consultancy", "IN", populated_db)
        symbols = [r["symbol"] for r in results]
        assert "TCS" in symbols

    def test_no_match_returns_empty(self, populated_db):
        from marketpulse.storage.cache import search_stocks
        results = search_stocks("ZZZZZ", "IN", populated_db)
        assert results == []

    def test_query_shorter_than_2_chars_returns_empty(self, populated_db):
        from marketpulse.storage.cache import search_stocks
        assert search_stocks("T", "IN", populated_db) == []
        assert search_stocks("", "IN", populated_db) == []

    def test_market_scoped_us(self, populated_db):
        from marketpulse.storage.cache import search_stocks
        results = search_stocks("Apple", "US", populated_db)
        symbols = [r["symbol"] for r in results]
        assert "AAPL" in symbols
        assert "RELIANCE" not in symbols

    def test_market_scoped_in(self, populated_db):
        from marketpulse.storage.cache import search_stocks
        results = search_stocks("Apple", "IN", populated_db)
        assert results == []

    def test_missing_db_returns_empty(self, tmp_path):
        from marketpulse.storage.cache import search_stocks
        results = search_stocks("REL", "IN", tmp_path / "nonexistent.db")
        assert results == []

    def test_result_contains_company_name(self, populated_db):
        from marketpulse.storage.cache import search_stocks
        results = search_stocks("REL", "IN", populated_db)
        assert any(r.get("company_name") for r in results)

    def test_result_without_signal_has_none_signal_type(self, populated_db):
        from marketpulse.storage.cache import search_stocks
        results = search_stocks("REL", "IN", populated_db)
        # No signals written — signal_type should be None
        assert all(r.get("signal_type") is None for r in results)


# ── Phase 3: Explore tab structure ────────────────────────────────────────────

class TestExploreTabStructure:
    def test_explore_in_st_tabs_call(self):
        import marketpulse.ui.dashboard as dashboard
        src = inspect.getsource(dashboard._render_market_tab)
        assert '"Explore"' in src or "'Explore'" in src

    def test_all_four_tabs_present(self):
        import marketpulse.ui.dashboard as dashboard
        src = inspect.getsource(dashboard._render_market_tab)
        assert '"Buy"' in src
        assert '"Watchlist"' in src
        assert '"My Holdings"' in src
        assert '"Explore"' in src

    def test_render_explore_tab_function_exists(self):
        import marketpulse.ui.dashboard as dashboard
        assert hasattr(dashboard, "_render_explore_tab")

    def test_render_explore_tab_accepts_market(self):
        import marketpulse.ui.dashboard as dashboard
        sig = inspect.signature(dashboard._render_explore_tab)
        assert "market" in sig.parameters


# ── Phase 4: Explore detail panel key uniqueness ──────────────────────────────

class TestExploreDetailKey:
    def test_render_stock_detail_called_with_explore_key(self):
        import marketpulse.ui.dashboard as dashboard
        src = inspect.getsource(dashboard._render_explore_tab)
        assert "explore_" in src
