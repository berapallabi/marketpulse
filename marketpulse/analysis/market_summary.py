from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean


@dataclass
class MarketSummary:
    market: str
    overall_sentiment: str
    sentiment_score: float
    buy_count: int
    sell_count: int
    hold_count: int
    last_updated: str
    insufficient_data: bool = False


def compute_market_summary(market: str, signals: list, sentiments: list) -> MarketSummary:
    """Aggregate stock-level signals and sentiment into a market-level summary."""
    sufficient = [s for s in sentiments if s.is_sufficient]
    insufficient_data = len(sufficient) < 5

    if sentiments:
        avg_score = mean(s.sentiment_score for s in sentiments)
    else:
        avg_score = 50.0

    if insufficient_data:
        overall = "Neutral"
    elif avg_score >= 60:
        overall = "Bullish"
    elif avg_score <= 40:
        overall = "Bearish"
    else:
        overall = "Neutral"

    buy_count = sum(1 for s in signals if s.signal_type == "BUY")
    sell_count = sum(1 for s in signals if s.signal_type == "SELL")
    hold_count = sum(1 for s in signals if s.signal_type == "HOLD")

    return MarketSummary(
        market=market,
        overall_sentiment=overall,
        sentiment_score=round(avg_score, 1),
        buy_count=buy_count,
        sell_count=sell_count,
        hold_count=hold_count,
        last_updated=datetime.now(timezone.utc).isoformat(),
        insufficient_data=insufficient_data,
    )
