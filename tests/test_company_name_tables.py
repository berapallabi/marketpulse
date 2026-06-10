"""Tests for Feature 011: Company Name in Stock Tables."""
import sqlite3
from datetime import datetime, timezone

import pytest

from marketpulse.storage.cache import init_db, read_signals, write_signals
from marketpulse.analysis.signals import Signal


def _now():
    return datetime.now(timezone.utc).isoformat()


def _seed_stock(db_path, symbol, market, company_name):
    currency = "INR" if market == "IN" else "USD"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO stocks (symbol, market, company_name, currency) VALUES (?, ?, ?, ?)",
            (symbol, market, company_name, currency),
        )
        conn.commit()
    finally:
        conn.close()


def _seed_signal(db_path, symbol, market, cap_tier="Large Cap"):
    sig = Signal(
        symbol=symbol, market=market, signal_type="BUY",
        confidence_score=70, technical_score=65.0, sentiment_score=60.0,
        contributing_factors=[], generated_at=_now(), cap_tier=cap_tier,
    )
    write_signals([sig], db_path)


@pytest.fixture()
def db(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    return db_path


class TestReadSignalsIncludesCompanyName:
    def test_company_name_returned_when_stock_exists(self, db):
        _seed_stock(db, "TCS", "IN", "Tata Consultancy Services")
        _seed_signal(db, "TCS", "IN")

        rows = read_signals("IN", db)
        assert len(rows) == 1
        assert rows[0]["company_name"] == "Tata Consultancy Services"

    def test_company_name_falls_back_to_symbol_when_not_in_stocks_or_universe(self, db):
        # Signal with no stocks row and symbol not in universe → symbol used as fallback
        conn = sqlite3.connect(db)
        try:
            conn.execute(
                "INSERT OR IGNORE INTO stocks (symbol, market, company_name, currency) VALUES (?, ?, ?, ?)",
                ("ORPHAN", "IN", "Orphan Corp", "INR"),
            )
            conn.execute(
                "INSERT INTO signals (symbol, market, signal_type, confidence_score, "
                "technical_score, sentiment_score, generated_at, cap_tier) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("ORPHAN", "IN", "HOLD", 0, 0.0, 0.0, _now(), "Unknown"),
            )
            conn.commit()
        finally:
            conn.close()

        # Remove from stocks to simulate orphan signal (ORPHAN is not in the Nifty universe)
        conn = sqlite3.connect(db)
        try:
            conn.execute("DELETE FROM stocks WHERE symbol = 'ORPHAN'")
            conn.commit()
        finally:
            conn.close()

        rows = read_signals("IN", db)
        assert len(rows) == 1
        # Not in stocks table and not in universe → falls back to the symbol itself
        assert rows[0]["company_name"] == "ORPHAN"

    def test_multiple_stocks_each_get_correct_name(self, db):
        for sym, name in [("TCS", "Tata Consultancy Services"), ("INFY", "Infosys Limited")]:
            _seed_stock(db, sym, "IN", name)
            _seed_signal(db, sym, "IN")

        rows = {r["symbol"]: r for r in read_signals("IN", db)}
        assert rows["TCS"]["company_name"] == "Tata Consultancy Services"
        assert rows["INFY"]["company_name"] == "Infosys Limited"

    def test_us_market_company_name_returned(self, db):
        _seed_stock(db, "AAPL", "US", "Apple Inc.")
        _seed_signal(db, "AAPL", "US")

        rows = read_signals("US", db)
        assert len(rows) == 1
        assert rows[0]["company_name"] == "Apple Inc."


class TestBuildDfCompanyNameFallback:
    def test_fallback_to_symbol_when_company_name_missing(self):
        from marketpulse.ui.stock_list import _build_df
        rows = [{"symbol": "XYZ", "signal_type": "BUY", "confidence_score": 70,
                 "company_name": None, "current_price": 100.0, "market": "IN"}]
        df = _build_df(rows)
        assert df.iloc[0]["Company"] == "XYZ"

    def test_fallback_to_symbol_when_company_name_empty_string(self):
        from marketpulse.ui.stock_list import _build_df
        rows = [{"symbol": "XYZ", "signal_type": "BUY", "confidence_score": 70,
                 "company_name": "", "current_price": 100.0, "market": "IN"}]
        df = _build_df(rows)
        assert df.iloc[0]["Company"] == "XYZ"

    def test_company_name_shown_when_present(self):
        from marketpulse.ui.stock_list import _build_df
        rows = [{"symbol": "TCS", "signal_type": "BUY", "confidence_score": 75,
                 "company_name": "Tata Consultancy Services", "current_price": 3800.0, "market": "IN"}]
        df = _build_df(rows)
        assert df.iloc[0]["Company"] == "Tata Consultancy Services"
