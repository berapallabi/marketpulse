from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean

import pandas as pd
import ta


@dataclass
class TechnicalSnapshot:
    symbol: str
    market: str
    rsi_14: float | None
    macd_val: float | None
    macd_signal: float | None
    bb_upper: float | None
    bb_middle: float | None
    bb_lower: float | None
    sma_50: float | None
    sma_200: float | None
    rsi_score: float
    macd_score: float
    bb_score: float
    sma_score: float
    technical_score: float
    computed_at: str


def compute_indicators(symbol: str, market: str, ohlcv: pd.DataFrame) -> TechnicalSnapshot | None:
    """Compute technical indicators from OHLCV DataFrame. Returns None if < 50 rows."""
    if ohlcv is None or len(ohlcv) < 50:
        return None

    close = ohlcv["Close"].astype(float)
    high = ohlcv["High"].astype(float)
    low = ohlcv["Low"].astype(float)

    # RSI (14)
    try:
        rsi_series = ta.momentum.RSIIndicator(close, window=14).rsi()
        rsi_val = _last(rsi_series)
    except Exception:
        rsi_val = None
    rsi_score = _rsi_score(rsi_val)

    # MACD (12/26/9)
    try:
        macd_indicator = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9)
        macd_val = _last(macd_indicator.macd())
        macd_signal = _last(macd_indicator.macd_signal())
        if macd_val is not None and macd_signal is not None:
            macd_score = 1.0 if macd_val > macd_signal else -1.0
        else:
            macd_score = 1.0
    except Exception:
        macd_val = macd_signal = None
        macd_score = 1.0

    # Bollinger Bands (20, 2σ)
    try:
        bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        bb_upper = _last(bb.bollinger_hband())
        bb_middle = _last(bb.bollinger_mavg())
        bb_lower = _last(bb.bollinger_lband())
        last_close = _last(close)
        if last_close is not None and bb_upper is not None and bb_lower is not None:
            if last_close < bb_lower:
                bb_score = 1.0
            elif last_close > bb_upper:
                bb_score = -1.0
            else:
                bb_score = 0.0
        else:
            bb_score = 0.0
    except Exception:
        bb_upper = bb_middle = bb_lower = None
        bb_score = 0.0

    # SMA 50 / 200
    try:
        sma_50 = _last(ta.trend.SMAIndicator(close, window=50).sma_indicator())
        sma_200 = _last(ta.trend.SMAIndicator(close, window=200).sma_indicator())
        if sma_50 is not None and sma_200 is not None:
            sma_score = 1.0 if sma_50 > sma_200 else -1.0
        else:
            sma_score = 0.0
    except Exception:
        sma_50 = sma_200 = None
        sma_score = 0.0

    # Aggregate score from available indicators
    available = [
        (rsi_score, rsi_val),
        (macd_score, macd_val),
        (bb_score, bb_upper),
        (sma_score, sma_50),
    ]
    available_scores = [score for score, val in available if val is not None]

    if not available_scores:
        return None

    raw = mean(available_scores)
    technical_score = (raw + 1) / 2 * 100

    return TechnicalSnapshot(
        symbol=symbol,
        market=market,
        rsi_14=rsi_val,
        macd_val=macd_val,
        macd_signal=macd_signal,
        bb_upper=bb_upper,
        bb_middle=bb_middle,
        bb_lower=bb_lower,
        sma_50=sma_50,
        sma_200=sma_200,
        rsi_score=rsi_score,
        macd_score=macd_score,
        bb_score=bb_score,
        sma_score=sma_score,
        technical_score=technical_score,
        computed_at=datetime.now(timezone.utc).isoformat(),
    )


def _last(series) -> float | None:
    try:
        val = series.dropna().iloc[-1]
        return float(val) if pd.notna(val) else None
    except (IndexError, AttributeError, TypeError):
        return None


def _rsi_score(rsi: float | None) -> float:
    if rsi is None:
        return 0.0
    if rsi < 30:
        return 1.0
    if rsi > 70:
        return -1.0
    return 0.0
