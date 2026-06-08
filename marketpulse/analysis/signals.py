from dataclasses import dataclass
from datetime import datetime, timezone

from marketpulse.config import BUY_THRESHOLD, SELL_THRESHOLD


@dataclass
class Signal:
    symbol: str
    market: str
    signal_type: str
    confidence_score: int
    technical_score: float
    sentiment_score: float
    contributing_factors: list[str]
    generated_at: str
    cap_tier: str = "Unknown"


def generate_signal(technical, sentiment) -> Signal:
    """Combine technical (70%) and sentiment (30%) scores into a BUY/SELL/HOLD signal."""
    effective_sentiment = sentiment.sentiment_score if sentiment.is_sufficient else 50.0

    final_score = 0.7 * technical.technical_score + 0.3 * effective_sentiment

    if final_score >= BUY_THRESHOLD:
        signal_type = "BUY"
    elif final_score <= SELL_THRESHOLD:
        signal_type = "SELL"
    else:
        signal_type = "HOLD"

    contributing_factors = _build_factors(technical, sentiment)

    return Signal(
        symbol=technical.symbol,
        market=technical.market,
        signal_type=signal_type,
        confidence_score=round(final_score),
        technical_score=technical.technical_score,
        sentiment_score=effective_sentiment,
        contributing_factors=contributing_factors,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def _build_factors(technical, sentiment) -> list[str]:
    factors = []

    indicator_map = [
        ("RSI", technical.rsi_score),
        ("MACD", technical.macd_score),
        ("BB", technical.bb_score),
        ("SMA", technical.sma_score),
    ]
    for name, score in indicator_map:
        if score == 1.0:
            factors.append(f"{name}:BUY")
        elif score == -1.0:
            factors.append(f"{name}:SELL")
        else:
            factors.append(f"{name}:HOLD")

    if sentiment.is_sufficient:
        if sentiment.sentiment_score >= BUY_THRESHOLD:
            factors.append("SENTIMENT:BUY")
        elif sentiment.sentiment_score <= SELL_THRESHOLD:
            factors.append("SENTIMENT:SELL")
        else:
            factors.append("SENTIMENT:HOLD")
    else:
        factors.append("SENTIMENT:NEUTRAL")

    return factors
