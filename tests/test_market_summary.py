"""Tests for marketpulse/analysis/market_summary.py — write first, confirm FAIL, then implement."""
from dataclasses import dataclass

import pytest

from marketpulse.analysis.market_summary import compute_market_summary


@dataclass
class _Signal:
    symbol: str
    market: str
    signal_type: str
    confidence_score: int
    technical_score: float
    sentiment_score: float
    contributing_factors: list
    generated_at: str = "2024-01-01T00:00:00+00:00"


@dataclass
class _Sentiment:
    symbol: str
    market: str
    sentiment_score: float
    article_count: int
    is_sufficient: bool
    matched_articles: list = None

    def __post_init__(self):
        if self.matched_articles is None:
            self.matched_articles = []


def _make_sentiments(n: int, score: float, sufficient: bool = True):
    return [_Sentiment(f"S{i}", "IN", score, 5 if sufficient else 1, sufficient) for i in range(n)]


def _make_signals(buys: int, sells: int, holds: int):
    sigs = []
    for i in range(buys):
        sigs.append(_Signal(f"B{i}", "IN", "BUY", 70, 70.0, 65.0, []))
    for i in range(sells):
        sigs.append(_Signal(f"SE{i}", "IN", "SELL", 30, 30.0, 35.0, []))
    for i in range(holds):
        sigs.append(_Signal(f"H{i}", "IN", "HOLD", 50, 50.0, 50.0, []))
    return sigs


def test_bullish_when_avg_sentiment_ge_60():
    signals = _make_signals(5, 2, 3)
    sentiments = _make_sentiments(10, 70.0)
    summary = compute_market_summary("IN", signals, sentiments)
    assert summary.overall_sentiment == "Bullish"


def test_bearish_when_avg_sentiment_le_40():
    signals = _make_signals(1, 7, 2)
    sentiments = _make_sentiments(10, 30.0)
    summary = compute_market_summary("IN", signals, sentiments)
    assert summary.overall_sentiment == "Bearish"


def test_neutral_when_avg_sentiment_between_40_60():
    signals = _make_signals(3, 3, 4)
    sentiments = _make_sentiments(10, 50.0)
    summary = compute_market_summary("IN", signals, sentiments)
    assert summary.overall_sentiment == "Neutral"


def test_buy_sell_hold_counts_match_input():
    signals = _make_signals(4, 3, 3)
    sentiments = _make_sentiments(10, 50.0)
    summary = compute_market_summary("IN", signals, sentiments)
    assert summary.buy_count == 4
    assert summary.sell_count == 3
    assert summary.hold_count == 3


def test_insufficient_data_when_fewer_than_5_stocks_sufficient():
    signals = _make_signals(2, 1, 1)
    sentiments = _make_sentiments(4, 70.0, sufficient=True)  # only 4 sufficient
    summary = compute_market_summary("IN", signals, sentiments)
    assert summary.overall_sentiment == "Neutral"
    assert summary.insufficient_data is True


def test_not_insufficient_when_5_or_more_sufficient():
    signals = _make_signals(3, 1, 1)
    sentiments = _make_sentiments(5, 70.0, sufficient=True)
    summary = compute_market_summary("IN", signals, sentiments)
    assert summary.insufficient_data is False
