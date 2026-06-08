"""Tests for marketpulse/data/india.py — write first, confirm FAIL, then implement."""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from marketpulse.data.types import DataProviderError, StockQuote


def test_fetch_quotes_returns_stock_quote_list(mock_india_quotes):
    with patch("marketpulse.data.india.nse_eq") as mock_nse:
        mock_nse.return_value = {
            "companyName": "Reliance Industries",
            "lastPrice": 2450.0,
            "open": 2440.0,
            "dayHigh": 2460.0,
            "dayLow": 2430.0,
            "totalTradedVolume": 5_000_000,
        }
        from marketpulse.data.india import fetch_quotes
        quotes = fetch_quotes(["RELIANCE"])
    assert len(quotes) == 1
    q = quotes[0]
    assert isinstance(q, StockQuote)
    assert q.symbol == "RELIANCE"
    assert q.market == "IN"
    assert q.currency == "INR"
    assert q.current_price == 2450.0


def test_fetch_quotes_raises_on_total_failure():
    with patch("marketpulse.data.india.nse_eq", side_effect=Exception("Connection failed")):
        from marketpulse.data.india import fetch_quotes
        # All symbols fail → DataProviderError
        with pytest.raises(DataProviderError):
            fetch_quotes(["RELIANCE", "TCS", "INFY"])


def test_fetch_quotes_returns_partial_list_on_single_failure():
    call_count = 0

    def side_effect(symbol):
        nonlocal call_count
        call_count += 1
        if symbol == "TCS":
            raise Exception("Symbol not found")
        return {
            "companyName": f"{symbol} Corp",
            "lastPrice": 1000.0,
            "open": 990.0,
            "dayHigh": 1010.0,
            "dayLow": 980.0,
            "totalTradedVolume": 1_000_000,
        }

    with patch("marketpulse.data.india.nse_eq", side_effect=side_effect):
        from marketpulse.data.india import fetch_quotes
        quotes = fetch_quotes(["RELIANCE", "TCS", "INFY"])
    assert len(quotes) == 2
    symbols = {q.symbol for q in quotes}
    assert "TCS" not in symbols


def test_fetch_ohlcv_returns_dataframe():
    mock_df = pd.DataFrame({
        "Date": pd.date_range(end="2024-12-31", periods=200, freq="B"),
        "Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0, "Volume": 1_000_000,
    })
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = mock_df
    mock_ticker.info = {"marketCap": 5e11}
    with patch("marketpulse.data.india.yf.Ticker", return_value=mock_ticker):
        from marketpulse.data.india import fetch_ohlcv_history
        df, market_cap = fetch_ohlcv_history("RELIANCE")
    assert df is not None
    assert set(df.columns) >= {"Date", "Open", "High", "Low", "Close", "Volume"}
    assert len(df) == 200
    assert market_cap == 5e11


def test_fetch_ohlcv_returns_none_when_fewer_than_50_rows():
    mock_df = pd.DataFrame({
        "Date": pd.date_range(end="2024-12-31", periods=30, freq="B"),
        "Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0, "Volume": 1_000_000,
    })
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = mock_df
    mock_ticker.info = {"marketCap": None}
    with patch("marketpulse.data.india.yf.Ticker", return_value=mock_ticker):
        from marketpulse.data.india import fetch_ohlcv_history
        df, market_cap = fetch_ohlcv_history("RELIANCE")
    assert df is None
