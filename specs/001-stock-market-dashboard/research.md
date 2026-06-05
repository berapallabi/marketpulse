# Research: MarketPulse Investment Dashboard

**Branch**: `001-stock-market-dashboard` | **Date**: 2026-06-05

## R-001: Stock Universe — Symbol Lists

**Decision**: Nifty 50 symbols hardcoded in `config.py` using NSE ticker format (e.g., `RELIANCE`, `TCS`). S&P 100 symbols hardcoded using standard US ticker format (e.g., `AAPL`, `MSFT`).

**Rationale**: Both lists are stable (rebalanced quarterly at most). Hardcoding avoids a bootstrap API call on startup, removes a dependency on an external index list provider, and aligns with Principle IV (Simplicity). Lists can be updated in config when index compositions change.

**Alternatives considered**:
- Fetch Nifty 50 list dynamically via nsepython — adds latency and a failure point on every startup.
- Fetch S&P 100 from Wikipedia HTML — fragile to HTML changes.

---

## R-002: Indian Market Data Provider

**Decision**: `nsepython` as primary provider for Indian stock data (price, PE, fundamentals). `nsetools` as fallback for basic quote data.

**Rationale**: `nsepython` wraps NSE India's public endpoints directly and returns structured data. It covers current price, day OHLC, 52-week high/low, and fundamental metrics. More reliable than yfinance `.NS` suffix lookups for Indian stocks.

**Alternatives considered**:
- `yfinance` with `.NS` suffix — inconsistent symbol support; known data gaps for smaller NSE stocks.
- `nsetools` alone — limited to real-time quotes; lacks historical OHLCV needed for technical indicators.

**Historical data for indicators**: `yfinance` with `.NS` suffix used exclusively for pulling 200-day price history needed by `pandas-ta`. If yfinance returns no data for a symbol, that stock is skipped and counted in the "unavailable" tally.

---

## R-003: US Market Data Provider

**Decision**: `yfinance` for all US stock data — real-time quotes, OHLCV history, and fundamentals.

**Rationale**: Reliable and well-maintained for NYSE/NASDAQ stocks. Covers all S&P 100 components without exception. Free with no authentication required.

**Alternatives considered**:
- Alpha Vantage free tier — exhausts 25 req/day limit immediately at S&P 100 scale.
- Finnhub free tier — 60 req/min adequate but adds API key management.

---

## R-004: Technical Indicator Computation

**Decision**: `pandas-ta` library computing RSI (14), MACD (12/26/9), Bollinger Bands (20, 2σ), SMA50, SMA200 on 200-day daily OHLCV history.

**Rationale**: pandas-ta integrates directly with pandas DataFrames, covers all required indicators, and runs entirely locally with no network calls.

**Minimum history requirement**: 200 trading days (~10 months). Stocks with fewer than 200 days of history are flagged as "Insufficient data" and excluded from signal generation.

---

## R-005: Technical Signal Scoring Algorithm

**Decision**: Per-indicator scores in the range [-1, +1], averaged and normalised to [0, 100].

| Indicator | BUY (+1) | SELL (-1) | Neutral (0) |
|-----------|----------|-----------|-------------|
| RSI (14) | RSI < 30 | RSI > 70 | 30 ≤ RSI ≤ 70 |
| MACD | MACD line > Signal line | MACD line < Signal line | — |
| Bollinger Bands | Close < Lower Band | Close > Upper Band | Between bands |
| SMA Cross | SMA50 > SMA200 | SMA50 < SMA200 | — |

**Aggregation**:
```
technical_raw   = mean([rsi_score, macd_score, bb_score, sma_score])   # range: -1 to +1
technical_score = (technical_raw + 1) / 2 * 100                        # range: 0 to 100
```

**Alternatives considered**:
- Weighted per-indicator scoring (e.g., RSI weighted higher) — unnecessary complexity for v1; equal weighting is transparent and testable.
- ML-based scoring — explicitly out of scope per spec.

---

## R-006: Sentiment Scoring Algorithm

**Decision**: VADER compound score per stock, derived from broad financial RSS feeds filtered by stock symbol or company name. Normalised to [0, 100].

**RSS feed sources**:
| Market | Feed | URL pattern |
|--------|------|-------------|
| India | Economic Times Markets | `https://economictimes.indiatimes.com/markets/rss.cms` |
| India | Moneycontrol News | `https://www.moneycontrol.com/rss/latestnews.xml` |
| US | Yahoo Finance News | `https://finance.yahoo.com/news/rssindex` |
| US | Reuters Business | `https://feeds.reuters.com/reuters/businessNews` |

**Filtering**: An article is attributed to a stock if its title or description contains the stock's ticker symbol OR the company's short name (first two words). Case-insensitive match.

**Aggregation**:
```
articles        = [a for a in feed_articles if stock_matches(a, stock)]
compound_scores = [vader.polarity_scores(a.title + " " + a.summary)["compound"] for a in articles]
sentiment_raw   = mean(compound_scores) if len(compound_scores) >= 2 else None
sentiment_score = (sentiment_raw + 1) / 2 * 100 if sentiment_raw is not None else 50  # neutral default
```

If fewer than 2 articles match, sentiment defaults to neutral (50) and the stock row displays an "Insufficient news data" label.

---

## R-007: Final Signal Composition (70/30)

**Decision**: Weighted combination with fixed weights (70% technical, 30% sentiment).

```
final_score = 0.7 * technical_score + 0.3 * sentiment_score   # range: 0 to 100

signal_type:
  final_score >= 60  → BUY
  final_score <= 40  → SELL
  40 < score < 60    → HOLD

confidence_score = final_score  (rounded to nearest integer)
```

**Conflicting indicator handling**: If technical indicators disagree (e.g., RSI=BUY, MACD=SELL), `technical_raw` will be near 0 → `technical_score` near 50 → `final_score` near 50 → HOLD with low confidence. The conflicting indicator names are stored in `Signal.contributing_factors` for display in the drill-down view.

---

## R-008: SQLite Caching Strategy

**Decision**: Single SQLite database file at `~/.marketpulse/cache.db`. On each manual refresh, all rows for the refreshed market are deleted and rewritten (overwrite pattern). No history retained.

**Cache TTL check on load**: On app startup, read `last_updated` from the `market_summaries` table. If data is older than 1 hour, display a staleness warning but serve the cached data. Do not auto-fetch.

**Rationale**: Overwrite-on-refresh is the simplest schema that satisfies "latest only" (Clarification Q3). Storing cache outside the repo (in `~/.marketpulse/`) avoids accidental git commits of data files.

---

## R-009: Streamlit Layout Architecture

**Decision**: Single-page app with three logical zones:

1. **Header zone**: Market sentiment gauges (India | US) using `st.metric` + colour coding
2. **Market tab zone**: `st.tabs(["🇮🇳 India", "🇺🇸 US"])` — each tab contains:
   - Signal filter radio buttons (ALL / BUY / SELL / HOLD)
   - Sortable stock signal table via `st.dataframe` with colour-coded signal column
   - Market closed badge when applicable
3. **Detail zone**: `st.expander` per selected stock row — shows price chart (Plotly), indicator values, news headlines

**Refresh**: Single `st.button("🔄 Refresh Data")` in the sidebar triggers full data fetch for both markets.

**Risk disclaimer**: Rendered as `st.warning()` banner pinned below the header zone, visible on every page view.

---

## R-010: Testing Strategy

**Decision**: `pytest` with unit tests for all computation logic. Integration tests for data provider calls using recorded fixtures (no live API calls in CI).

**Test scope**:
- `test_indicators.py` — signal scoring algorithm with known OHLCV inputs
- `test_signals.py` — 70/30 weighting, edge cases (conflicting indicators, no sentiment data)
- `test_sentiment.py` — VADER scoring, article matching logic, neutral default
- `test_cache.py` — SQLite read/write/overwrite, staleness detection

**Excluded from tests**: Streamlit UI components (no headless testing framework required for a personal tool), live RSS feed fetching.
