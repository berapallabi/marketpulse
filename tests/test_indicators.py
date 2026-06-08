"""Tests for marketpulse/analysis/indicators.py — write first, confirm FAIL, then implement."""
import pandas as pd
import numpy as np
import pytest

from marketpulse.analysis.indicators import compute_indicators


def _make_ohlcv(n: int, close_val: float = 100.0) -> pd.DataFrame:
    """Return a minimal OHLCV DataFrame of length n with constant close."""
    dates = pd.date_range(end="2024-12-31", periods=n, freq="B")
    return pd.DataFrame({
        "Date": dates,
        "Open": close_val,
        "High": close_val * 1.01,
        "Low": close_val * 0.99,
        "Close": close_val,
        "Volume": 1_000_000,
    })


def test_returns_none_when_fewer_than_50_rows():
    df = _make_ohlcv(49)
    result = compute_indicators("TEST", "US", df)
    assert result is None


def test_returns_snapshot_with_200_rows(sample_ohlcv_df):
    result = compute_indicators("TEST", "US", sample_ohlcv_df)
    assert result is not None
    assert result.symbol == "TEST"
    assert result.market == "US"


def test_technical_score_in_range(sample_ohlcv_df):
    result = compute_indicators("TEST", "US", sample_ohlcv_df)
    assert result is not None
    assert 0.0 <= result.technical_score <= 100.0


def test_rsi_score_buy_when_oversold():
    """Force RSI < 30 by using monotonically declining prices."""
    n = 200
    dates = pd.date_range(end="2024-12-31", periods=n, freq="B")
    close = np.linspace(200, 1, n)  # steep decline → RSI will be very low
    df = pd.DataFrame({
        "Date": dates,
        "Open": close,
        "High": close * 1.001,
        "Low": close * 0.999,
        "Close": close,
        "Volume": 1_000_000,
    })
    result = compute_indicators("TEST", "US", df)
    assert result is not None
    assert result.rsi_score == 1.0


def test_rsi_score_sell_when_overbought():
    """Force RSI > 70 by using monotonically rising prices."""
    n = 200
    dates = pd.date_range(end="2024-12-31", periods=n, freq="B")
    close = np.linspace(1, 500, n)  # steep ascent → RSI will be very high
    df = pd.DataFrame({
        "Date": dates,
        "Open": close,
        "High": close * 1.001,
        "Low": close * 0.999,
        "Close": close,
        "Volume": 1_000_000,
    })
    result = compute_indicators("TEST", "US", df)
    assert result is not None
    assert result.rsi_score == -1.0


def test_indicator_scores_are_valid_values(sample_ohlcv_df):
    result = compute_indicators("TEST", "US", sample_ohlcv_df)
    assert result is not None
    assert result.rsi_score in (-1.0, 0.0, 1.0)
    assert result.macd_score in (-1.0, 1.0)
    assert result.bb_score in (-1.0, 0.0, 1.0)
    assert result.sma_score in (-1.0, 1.0)


def test_computed_at_is_set(sample_ohlcv_df):
    result = compute_indicators("TEST", "US", sample_ohlcv_df)
    assert result is not None
    assert result.computed_at is not None
    assert "T" in result.computed_at  # ISO 8601
