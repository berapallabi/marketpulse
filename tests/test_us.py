"""Tests for marketpulse/data/us.py — write first, confirm FAIL, then implement."""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from marketpulse.data.types import DataProviderError, StockQuote


def test_fetch_quotes_returns_us_stock_quotes(mock_us_quotes):
    mock_info = {
        "longName": "Apple Inc",
        "regularMarketPrice": 185.0,
        "regularMarketOpen": 183.0,
        "dayHigh": 186.0,
        "dayLow": 182.0,
        "regularMarketVolume": 50_000_000,
        "marketCap": 3e12,
    }
    mock_ticker = MagicMock()
    mock_ticker.info = mock_info
    mock_ticker.fast_info = MagicMock(last_price=185.0)

    with patch("marketpulse.data.us.yf.Ticker", return_value=mock_ticker):
        from marketpulse.data.us import fetch_quotes
        quotes = fetch_quotes(["AAPL"])

    assert len(quotes) == 1
    q = quotes[0]
    assert isinstance(q, StockQuote)
    assert q.market == "US"
    assert q.currency == "USD"
    assert q.market_cap == 3e12


def test_fetch_quotes_raises_on_total_failure():
    with patch("marketpulse.data.us.yf.Ticker", side_effect=Exception("Network error")):
        from marketpulse.data.us import fetch_quotes
        with pytest.raises(DataProviderError):
            fetch_quotes(["AAPL", "MSFT", "NVDA"])


def test_fetch_quotes_returns_partial_list_on_single_failure():
    call_count = 0

    class _FakeTicker:
        def __init__(self, symbol):
            self.symbol = symbol
            if symbol == "MSFT":
                raise Exception("Symbol error")
            self.info = {
                "longName": f"{symbol} Corp",
                "regularMarketPrice": 100.0,
                "regularMarketOpen": 99.0,
                "dayHigh": 101.0,
                "dayLow": 98.0,
                "regularMarketVolume": 1_000_000,
            }

    with patch("marketpulse.data.us.yf.Ticker", side_effect=_FakeTicker):
        from marketpulse.data.us import fetch_quotes
        quotes = fetch_quotes(["AAPL", "MSFT", "NVDA"])

    assert len(quotes) == 2
    assert all(q.symbol != "MSFT" for q in quotes)


def test_fetch_ohlcv_returns_dataframe():
    mock_df = pd.DataFrame({
        "Date": pd.date_range(end="2024-12-31", periods=200, freq="B"),
        "Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0, "Volume": 1_000_000,
    })
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = mock_df
    with patch("marketpulse.data.us.yf.Ticker", return_value=mock_ticker):
        from marketpulse.data.us import fetch_ohlcv_history
        df, market_cap = fetch_ohlcv_history("AAPL")
    assert df is not None
    assert len(df) == 200
    assert market_cap is None  # US market_cap comes from fetch_quotes, not here


def test_fetch_ohlcv_returns_none_when_fewer_than_50_rows():
    mock_df = pd.DataFrame({
        "Date": pd.date_range(end="2024-12-31", periods=30, freq="B"),
        "Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0, "Volume": 1_000_000,
    })
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = mock_df
    with patch("marketpulse.data.us.yf.Ticker", return_value=mock_ticker):
        from marketpulse.data.us import fetch_ohlcv_history
        df, market_cap = fetch_ohlcv_history("AAPL")
    assert df is None
