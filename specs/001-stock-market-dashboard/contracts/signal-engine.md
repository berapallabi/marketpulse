# Contract: Signal Engine

**Module paths**: `marketpulse/analysis/indicators.py`, `marketpulse/analysis/signals.py`, `marketpulse/analysis/market_summary.py`

---

## Technical Indicators (`analysis/indicators.py`)

### `compute_indicators(symbol: str, market: str, ohlcv: pd.DataFrame) -> TechnicalSnapshot | None`

Computes all required technical indicators from OHLCV history.

**Input**: Symbol, market, DataFrame with columns `[Date, Open, High, Low, Close, Volume]` (min 50 rows; 200 preferred).

**Output**:

```python
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
    rsi_score: float        # -1, 0, or +1
    macd_score: float       # -1 or +1
    bb_score: float         # -1, 0, or +1
    sma_score: float        # -1 or +1
    technical_score: float  # 0.0 to 100.0
    computed_at: str        # ISO 8601 UTC
```

Returns `None` if DataFrame has fewer than 50 rows.

**Partial indicator handling**: When only a subset of indicators is computable (e.g., SMA200 unavailable due to fewer than 200 rows), `technical_score` is computed from the available scores only. Missing indicators appear in `contributing_factors` as `"<INDICATOR>:UNAVAILABLE"`.

**All-indicators-unavailable**: If all four indicator scores remain `None` after computation, `compute_indicators` returns `None`. The caller marks the stock as having insufficient data, excludes it from the signal table, and increments the unavailable count.

**Scoring rules**:

| Indicator | +1 (BUY) | -1 (SELL) | 0 (Neutral) |
|-----------|----------|-----------|-------------|
| RSI | < 30 | > 70 | 30–70 |
| MACD | macd_val > macd_signal | macd_val < macd_signal | — |
| Bollinger | close < bb_lower | close > bb_upper | between bands |
| SMA cross | sma_50 > sma_200 | sma_50 < sma_200 | — |

**Aggregation**:
```python
raw = mean([rsi_score, macd_score, bb_score, sma_score])
technical_score = (raw + 1) / 2 * 100
```

---

## Signal Generator (`analysis/signals.py`)

### `generate_signal(technical: TechnicalSnapshot, sentiment: SentimentResult) -> Signal`

Combines technical and sentiment scores using 70/30 weighting and classifies the signal.

**Input**: Populated `TechnicalSnapshot` and `SentimentResult` for the same stock.

**Output**:

```python
@dataclass
class Signal:
    symbol: str
    market: str
    signal_type: str          # "BUY", "SELL", or "HOLD"
    confidence_score: int     # 0 to 100 (rounded final_score)
    technical_score: float    # passthrough from TechnicalSnapshot
    sentiment_score: float    # passthrough from SentimentResult
    contributing_factors: list[str]  # e.g. ["RSI:BUY", "MACD:SELL", "BB:HOLD", "SMA:BUY"]
    generated_at: str         # ISO 8601 UTC
```

**Classification**:
```python
final_score = 0.7 * technical.technical_score + 0.3 * sentiment.sentiment_score

signal_type = (
    "BUY"  if final_score >= 60 else
    "SELL" if final_score <= 40 else
    "HOLD"
)
confidence_score = round(final_score)
```

**Contributing factors format**: `"<INDICATOR>:<SIGNAL>"` for each sub-score ≠ 0, e.g. `["RSI:BUY", "MACD:SELL", "BB:HOLD", "SMA:BUY", "SENTIMENT:NEUTRAL"]`.

---

## Market Summary (`analysis/market_summary.py`)

### `compute_market_summary(market: str, signals: list[Signal], sentiments: list[SentimentResult]) -> MarketSummary`

Aggregates stock-level signals and sentiment into a single market-level summary.

**Output**:

```python
@dataclass
class MarketSummary:
    market: str              # "IN" or "US"
    overall_sentiment: str   # "Bullish", "Neutral", or "Bearish"
    sentiment_score: float   # mean of all stock sentiment_scores
    buy_count: int
    sell_count: int
    hold_count: int
    last_updated: str        # ISO 8601 UTC
```

**Classification**:
```python
avg_sentiment = mean([s.sentiment_score for s in sentiments])
overall_sentiment = (
    "Bullish" if avg_sentiment >= 60 else
    "Bearish" if avg_sentiment <= 40 else
    "Neutral"
)
```

**Minimum data requirement**: If fewer than 5 stocks have valid sentiment data, `overall_sentiment = "Neutral"` and the UI displays "Insufficient data".
