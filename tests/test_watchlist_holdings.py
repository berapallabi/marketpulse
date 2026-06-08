import pytest

from marketpulse.storage.cache import (
    add_to_holdings,
    add_to_watchlist,
    init_db,
    read_holdings,
    read_watchlist,
    remove_from_holdings,
    remove_from_watchlist,
)


@pytest.fixture(autouse=True)
def db(tmp_db):
    init_db(tmp_db)
    return tmp_db


# ── Watchlist ─────────────────────────────────────────────────────────────────

class TestWatchlist:
    def test_add_and_read(self, db):
        add_to_watchlist("RELIANCE", "IN", db)
        assert "RELIANCE" in read_watchlist("IN", db)

    def test_read_returns_empty_when_none_added(self, db):
        assert read_watchlist("IN", db) == []

    def test_duplicate_add_no_extra_row(self, db):
        add_to_watchlist("RELIANCE", "IN", db)
        add_to_watchlist("RELIANCE", "IN", db)
        assert read_watchlist("IN", db).count("RELIANCE") == 1

    def test_remove_deletes_entry(self, db):
        add_to_watchlist("RELIANCE", "IN", db)
        remove_from_watchlist("RELIANCE", "IN", db)
        assert "RELIANCE" not in read_watchlist("IN", db)

    def test_remove_noop_when_not_present(self, db):
        remove_from_watchlist("RELIANCE", "IN", db)  # must not raise
        assert read_watchlist("IN", db) == []

    def test_cross_market_isolation(self, db):
        add_to_watchlist("INFY", "IN", db)
        assert "INFY" not in read_watchlist("US", db)

    def test_multiple_symbols(self, db):
        add_to_watchlist("RELIANCE", "IN", db)
        add_to_watchlist("TCS", "IN", db)
        result = read_watchlist("IN", db)
        assert set(result) == {"RELIANCE", "TCS"}

    def test_us_market_independent(self, db):
        add_to_watchlist("AAPL", "US", db)
        add_to_watchlist("RELIANCE", "IN", db)
        assert read_watchlist("US", db) == ["AAPL"]
        assert read_watchlist("IN", db) == ["RELIANCE"]


# ── Holdings ──────────────────────────────────────────────────────────────────

class TestHoldings:
    def test_add_and_read(self, db):
        add_to_holdings("TCS", "IN", db)
        assert "TCS" in read_holdings("IN", db)

    def test_read_returns_empty_when_none_added(self, db):
        assert read_holdings("IN", db) == []

    def test_duplicate_add_no_extra_row(self, db):
        add_to_holdings("TCS", "IN", db)
        add_to_holdings("TCS", "IN", db)
        assert read_holdings("IN", db).count("TCS") == 1

    def test_remove_deletes_entry(self, db):
        add_to_holdings("TCS", "IN", db)
        remove_from_holdings("TCS", "IN", db)
        assert "TCS" not in read_holdings("IN", db)

    def test_remove_noop_when_not_present(self, db):
        remove_from_holdings("TCS", "IN", db)  # must not raise
        assert read_holdings("IN", db) == []

    def test_cross_market_isolation(self, db):
        add_to_holdings("TCS", "IN", db)
        assert "TCS" not in read_holdings("US", db)

    def test_multiple_symbols(self, db):
        add_to_holdings("TCS", "IN", db)
        add_to_holdings("INFY", "IN", db)
        result = read_holdings("IN", db)
        assert set(result) == {"TCS", "INFY"}

    def test_us_market_independent(self, db):
        add_to_holdings("MSFT", "US", db)
        add_to_holdings("TCS", "IN", db)
        assert read_holdings("US", db) == ["MSFT"]
        assert read_holdings("IN", db) == ["TCS"]


# ── Cross-list independence ───────────────────────────────────────────────────

class TestWatchlistHoldingsIndependence:
    def test_symbol_in_both_lists(self, db):
        add_to_watchlist("RELIANCE", "IN", db)
        add_to_holdings("RELIANCE", "IN", db)
        assert "RELIANCE" in read_watchlist("IN", db)
        assert "RELIANCE" in read_holdings("IN", db)

    def test_remove_from_watchlist_does_not_affect_holdings(self, db):
        add_to_watchlist("RELIANCE", "IN", db)
        add_to_holdings("RELIANCE", "IN", db)
        remove_from_watchlist("RELIANCE", "IN", db)
        assert "RELIANCE" not in read_watchlist("IN", db)
        assert "RELIANCE" in read_holdings("IN", db)
