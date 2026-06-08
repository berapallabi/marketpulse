"""Tests for marketpulse/analysis/signals.py — write first, confirm FAIL, then implement."""
from dataclasses import dataclass

import pytest

from marketpulse.analysis.signals import generate_signal


@dataclass
class _Tech:
    symbol: str
    market: str
    rsi_14: float | None = 50.0
    macd_val: float | None = 0.0
    macd_signal: float | None = 0.0
    bb_upper: float | None = 110.0
    bb_middle: float | None = 100.0
    bb_lower: float | None = 90.0
    sma_50: float | None = 100.0
    sma_200: float | None = 100.0
    rsi_score: float = 0.0
    macd_score: float = 1.0
    bb_score: float = 0.0
    sma_score: float = 1.0
    technical_score: float = 75.0
    computed_at: str = "2024-01-01T00:00:00+00:00"


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


def test_buy_when_final_score_ge_60():
    tech = _Tech("AAPL", "US", technical_score=80.0)
    sent = _Sentiment("AAPL", "US", sentiment_score=70.0, article_count=5, is_sufficient=True)
    # final = 0.7*80 + 0.3*70 = 56+21 = 77
    signal = generate_signal(tech, sent)
    assert signal.signal_type == "BUY"
    assert signal.confidence_score == 77


def test_sell_when_final_score_le_40():
    tech = _Tech("AAPL", "US", technical_score=30.0)
    sent = _Sentiment("AAPL", "US", sentiment_score=20.0, article_count=5, is_sufficient=True)
    # final = 0.7*30 + 0.3*20 = 21+6 = 27
    signal = generate_signal(tech, sent)
    assert signal.signal_type == "SELL"
    assert signal.confidence_score == 27


def test_hold_when_final_score_between_40_and_60():
    tech = _Tech("AAPL", "US", technical_score=55.0)
    sent = _Sentiment("AAPL", "US", sentiment_score=45.0, article_count=5, is_sufficient=True)
    # final = 0.7*55 + 0.3*45 = 38.5+13.5 = 52
    signal = generate_signal(tech, sent)
    assert signal.signal_type == "HOLD"
    assert signal.confidence_score == 52


def test_confidence_score_equals_round_final_score():
    tech = _Tech("AAPL", "US", technical_score=63.4)
    sent = _Sentiment("AAPL", "US", sentiment_score=63.4, article_count=3, is_sufficient=True)
    # final = 63.4 exactly → round = 63
    signal = generate_signal(tech, sent)
    assert signal.confidence_score == round(0.7 * 63.4 + 0.3 * 63.4)


def test_sentiment_defaults_to_50_when_not_sufficient():
    tech = _Tech("AAPL", "US", technical_score=70.0)
    sent = _Sentiment("AAPL", "US", sentiment_score=20.0, article_count=1, is_sufficient=False)
    # is_sufficient=False → sentiment treated as 50 → final = 0.7*70 + 0.3*50 = 49+15 = 64
    signal = generate_signal(tech, sent)
    assert signal.confidence_score == 64
    assert signal.signal_type == "BUY"


def test_conflicting_indicators_produce_hold_near_50():
    # RSI BUY (+1), MACD SELL (-1), BB neutral (0), SMA neutral (0)
    # raw = mean([1,-1,0,0]) = 0 → technical_score = 50
    tech = _Tech("AAPL", "US",
                 rsi_score=1.0, macd_score=-1.0, bb_score=0.0, sma_score=0.0,
                 technical_score=50.0)
    sent = _Sentiment("AAPL", "US", sentiment_score=50.0, article_count=3, is_sufficient=True)
    signal = generate_signal(tech, sent)
    assert signal.signal_type == "HOLD"
    assert 40 < signal.confidence_score < 60


def test_contributing_factors_are_set(sample_ohlcv_df):
    tech = _Tech("AAPL", "US", technical_score=75.0)
    sent = _Sentiment("AAPL", "US", sentiment_score=65.0, article_count=3, is_sufficient=True)
    signal = generate_signal(tech, sent)
    assert isinstance(signal.contributing_factors, list)
    assert len(signal.contributing_factors) > 0


def test_signal_has_generated_at():
    tech = _Tech("AAPL", "US", technical_score=75.0)
    sent = _Sentiment("AAPL", "US", sentiment_score=65.0, article_count=3, is_sufficient=True)
    signal = generate_signal(tech, sent)
    assert signal.generated_at is not None
    assert "T" in signal.generated_at
