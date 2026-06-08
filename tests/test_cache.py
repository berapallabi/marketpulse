"""Tests for marketpulse/storage/cache.py — write first, confirm FAIL, then implement."""
import sqlite3
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

import pytest

from marketpulse.storage.cache import (
    check_staleness,
    init_db,
    read_market_summary,
    read_signals,
    write_market_summary,
    write_signals,
)


@dataclass
class _Signal:
    symbol: str
    market: str
    signal_type: str
    confidence_score: int
    technical_score: float
    sentiment_score: float
    contributing_factors: list
    generated_at: str
    cap_tier: str = "Unknown"


@dataclass
class _Summary:
    market: str
    overall_sentiment: str
    sentiment_score: float
    buy_count: int
    sell_count: int
    hold_count: int
    last_updated: str


def test_init_db_creates_all_tables(tmp_db):
    init_db(tmp_db)
    conn = sqlite3.connect(tmp_db)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()
    expected = {"stocks", "price_snapshots", "technical_snapshots", "sentiment_snapshots", "signals", "news_items", "market_summaries"}
    assert expected.issubset(tables)


def test_write_signals_inserts_rows(tmp_db):
    init_db(tmp_db)
    now = datetime.now(timezone.utc).isoformat()
    signals = [
        _Signal("AAPL", "US", "BUY", 72, 75.0, 65.0, ["RSI:BUY"], now),
        _Signal("MSFT", "US", "HOLD", 55, 50.0, 50.0, ["RSI:HOLD"], now),
    ]
    write_signals(signals, tmp_db)
    rows = read_signals("US", tmp_db)
    assert len(rows) == 2
    symbols = {r["symbol"] for r in rows}
    assert symbols == {"AAPL", "MSFT"}


def test_write_signals_overwrites_on_second_call(tmp_db):
    init_db(tmp_db)
    now = datetime.now(timezone.utc).isoformat()
    sig = _Signal("AAPL", "US", "BUY", 72, 75.0, 65.0, ["RSI:BUY"], now)
    write_signals([sig], tmp_db)
    sig2 = _Signal("AAPL", "US", "SELL", 35, 30.0, 40.0, ["RSI:SELL"], now)
    write_signals([sig2], tmp_db)
    rows = read_signals("US", tmp_db)
    assert len(rows) == 1
    assert rows[0]["signal_type"] == "SELL"
    assert rows[0]["confidence_score"] == 35


def test_check_staleness_true_when_old(tmp_db):
    init_db(tmp_db)
    old_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    summary = _Summary("IN", "Bullish", 65.0, 20, 10, 20, old_time)
    write_market_summary(summary, tmp_db)
    assert check_staleness("IN", tmp_db) is True


def test_check_staleness_false_when_fresh(tmp_db):
    init_db(tmp_db)
    now = datetime.now(timezone.utc).isoformat()
    summary = _Summary("IN", "Bullish", 65.0, 20, 10, 20, now)
    write_market_summary(summary, tmp_db)
    assert check_staleness("IN", tmp_db) is False


def test_check_staleness_true_when_absent(tmp_db):
    init_db(tmp_db)
    assert check_staleness("US", tmp_db) is True


def test_write_signals_persists_cap_tier(tmp_db):
    init_db(tmp_db)
    now = datetime.now(timezone.utc).isoformat()
    sig = _Signal("AAPL", "US", "BUY", 72, 75.0, 65.0, ["RSI:BUY"], now, cap_tier="Mega Cap")
    write_signals([sig], tmp_db)
    rows = read_signals("US", tmp_db)
    assert len(rows) == 1
    assert rows[0]["cap_tier"] == "Mega Cap"
