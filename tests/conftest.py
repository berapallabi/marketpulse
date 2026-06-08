import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from marketpulse.data.types import DataProviderError, StockQuote


@pytest.fixture
def sample_ohlcv_df():
    """200-row OHLCV DataFrame with a realistic upward trend."""
    rng = np.random.default_rng(42)
    n = 200
    dates = pd.date_range(end="2024-12-31", periods=n, freq="B")
    close = 100 + np.cumsum(rng.normal(0, 1, n))
    close = np.maximum(close, 10)
    high = close * (1 + rng.uniform(0, 0.02, n))
    low = close * (1 - rng.uniform(0, 0.02, n))
    open_ = close * (1 + rng.normal(0, 0.01, n))
    volume = rng.integers(100_000, 1_000_000, n)
    return pd.DataFrame({
        "Date": dates,
        "Open": open_,
        "High": high,
        "Low": low,
        "Close": close,
        "Volume": volume,
    })


@pytest.fixture
def sample_news_articles():
    from marketpulse.data.sentiment import NewsArticle
    now = datetime.now(timezone.utc).isoformat()
    return [
        NewsArticle(headline="RELIANCE posts strong Q3 earnings beat", summary="Revenue up 15%", source="ET Markets", published_at=now, fetched_at=now),
        NewsArticle(headline="RELIANCE shares surge on positive outlook", summary="Analysts bullish on Reliance", source="Moneycontrol", published_at=now, fetched_at=now),
        NewsArticle(headline="INFY guidance disappoints investors", summary="Infosys cuts revenue forecast", source="ET Markets", published_at=now, fetched_at=now),
        NewsArticle(headline="Market opens flat amid global uncertainty", summary="Mixed signals from Fed", source="ET Markets", published_at=now, fetched_at=now),
        NewsArticle(headline="TCS wins large banking contract", summary="Deal worth $500M over 5 years", source="Moneycontrol", published_at=now, fetched_at=now),
    ]


@pytest.fixture
def tmp_db(tmp_path):
    """Temporary SQLite DB path for isolated test runs."""
    return tmp_path / "test_cache.db"


@pytest.fixture
def mock_india_quotes():
    now = datetime.now(timezone.utc).isoformat()
    return [
        StockQuote("RELIANCE", "IN", "Reliance Industries", 2450.0, 2440.0, 2460.0, 2430.0, 5_000_000, "INR", now),
        StockQuote("TCS", "IN", "Tata Consultancy Services", 3800.0, 3790.0, 3820.0, 3780.0, 2_000_000, "INR", now),
        StockQuote("INFY", "IN", "Infosys", 1500.0, 1495.0, 1510.0, 1490.0, 3_000_000, "INR", now),
    ]


@pytest.fixture
def mock_us_quotes():
    now = datetime.now(timezone.utc).isoformat()
    return [
        StockQuote("AAPL", "US", "Apple Inc", 185.0, 183.0, 186.0, 182.0, 50_000_000, "USD", now),
        StockQuote("MSFT", "US", "Microsoft Corporation", 420.0, 418.0, 422.0, 417.0, 20_000_000, "USD", now),
        StockQuote("NVDA", "US", "NVIDIA Corporation", 870.0, 860.0, 880.0, 855.0, 30_000_000, "USD", now),
    ]
