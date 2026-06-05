# Data Model: MarketPulse Investment Dashboard

**Branch**: `001-stock-market-dashboard` | **Date**: 2026-06-05

## SQLite Schema

Database file: `~/.marketpulse/cache.db`

---

### Table: `stocks`

Canonical list of tracked stocks. Populated from hardcoded config on first run; updated on each refresh.

```sql
CREATE TABLE IF NOT EXISTS stocks (
    symbol       TEXT NOT NULL,
    market       TEXT NOT NULL CHECK (market IN ('IN', 'US')),
    company_name TEXT NOT NULL,
    sector       TEXT,
    currency     TEXT NOT NULL CHECK (currency IN ('INR', 'USD')),
    PRIMARY KEY (symbol, market)
);
```

**Notes**:
- `symbol` uses NSE format for India (e.g., `RELIANCE`) and standard ticker for US (e.g., `AAPL`)
- `sector` sourced from nsepython/yfinance metadata; nullable if unavailable

---

### Table: `price_snapshots`

Latest price data per stock. One row per stock; overwritten on each refresh.

```sql
CREATE TABLE IF NOT EXISTS price_snapshots (
    symbol        TEXT NOT NULL,
    market        TEXT NOT NULL,
    current_price REAL NOT NULL,
    open_price    REAL,
    high_price    REAL,
    low_price     REAL,
    volume        INTEGER,
    last_updated  TEXT NOT NULL,   -- ISO 8601 UTC
    PRIMARY KEY (symbol, market),
    FOREIGN KEY (symbol, market) REFERENCES stocks (symbol, market)
);
```

---

### Table: `technical_snapshots`

Latest computed technical indicator values per stock. One row per stock; overwritten on each refresh.

```sql
CREATE TABLE IF NOT EXISTS technical_snapshots (
    symbol          TEXT NOT NULL,
    market          TEXT NOT NULL,
    rsi_14          REAL,
    macd_val        REAL,
    macd_signal     REAL,
    bb_upper        REAL,
    bb_middle       REAL,
    bb_lower        REAL,
    sma_50          REAL,
    sma_200         REAL,
    rsi_score       REAL,          -- -1, 0, or +1
    macd_score      REAL,          -- -1 or +1
    bb_score        REAL,          -- -1, 0, or +1
    sma_score       REAL,          -- -1 or +1
    technical_score REAL,          -- 0 to 100, normalised
    computed_at     TEXT NOT NULL,
    PRIMARY KEY (symbol, market),
    FOREIGN KEY (symbol, market) REFERENCES stocks (symbol, market)
);
```

---

### Table: `sentiment_snapshots`

Latest sentiment score per stock derived from RSS news. One row per stock; overwritten on each refresh.

```sql
CREATE TABLE IF NOT EXISTS sentiment_snapshots (
    symbol          TEXT NOT NULL,
    market          TEXT NOT NULL,
    sentiment_score REAL NOT NULL,   -- 0 to 100, normalised
    article_count   INTEGER NOT NULL,
    is_sufficient   INTEGER NOT NULL CHECK (is_sufficient IN (0, 1)),  -- 0 if < 2 articles matched
    computed_at     TEXT NOT NULL,
    PRIMARY KEY (symbol, market),
    FOREIGN KEY (symbol, market) REFERENCES stocks (symbol, market)
);
```

---

### Table: `signals`

Final computed buy/sell/hold signal per stock. One row per stock; overwritten on each refresh.

```sql
CREATE TABLE IF NOT EXISTS signals (
    symbol               TEXT NOT NULL,
    market               TEXT NOT NULL,
    signal_type          TEXT NOT NULL CHECK (signal_type IN ('BUY', 'SELL', 'HOLD')),
    confidence_score     INTEGER NOT NULL,   -- 0 to 100
    technical_score      REAL NOT NULL,
    sentiment_score      REAL NOT NULL,
    contributing_factors TEXT,               -- JSON array of strings, e.g. '["RSI:BUY","MACD:SELL"]'
    generated_at         TEXT NOT NULL,
    PRIMARY KEY (symbol, market),
    FOREIGN KEY (symbol, market) REFERENCES stocks (symbol, market)
);
```

---

### Table: `news_items`

Recent news articles matched to a stock. Replaced per-stock on each refresh.

```sql
CREATE TABLE IF NOT EXISTS news_items (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol         TEXT NOT NULL,
    market         TEXT NOT NULL,
    headline       TEXT NOT NULL,
    source         TEXT NOT NULL,
    published_at   TEXT,            -- ISO 8601, nullable if feed omits date
    sentiment_label TEXT NOT NULL CHECK (sentiment_label IN ('Positive', 'Neutral', 'Negative')),
    fetched_at     TEXT NOT NULL,
    FOREIGN KEY (symbol, market) REFERENCES stocks (symbol, market)
);
```

**Index**:
```sql
CREATE INDEX IF NOT EXISTS idx_news_symbol_market ON news_items (symbol, market);
```

---

### Table: `market_summaries`

Aggregate market-level sentiment. One row per market; overwritten on each refresh.

```sql
CREATE TABLE IF NOT EXISTS market_summaries (
    market            TEXT NOT NULL PRIMARY KEY CHECK (market IN ('IN', 'US')),
    overall_sentiment TEXT NOT NULL CHECK (overall_sentiment IN ('Bullish', 'Neutral', 'Bearish')),
    sentiment_score   REAL NOT NULL,   -- 0 to 100, average of all stock sentiment scores
    buy_count         INTEGER NOT NULL,
    sell_count        INTEGER NOT NULL,
    hold_count        INTEGER NOT NULL,
    last_updated      TEXT NOT NULL
);
```

---

## Entity Relationships

```
stocks (1) ──< price_snapshots (1)       one-to-one, overwritten per refresh
stocks (1) ──< technical_snapshots (1)   one-to-one, overwritten per refresh
stocks (1) ──< sentiment_snapshots (1)   one-to-one, overwritten per refresh
stocks (1) ──< signals (1)               one-to-one, overwritten per refresh
stocks (1) ──< news_items (N)            one-to-many, replaced per refresh
market_summaries — standalone, one row per market (IN/US)
```

---

## Validation Rules

| Field | Rule |
|-------|------|
| `signal_type` | Must be exactly one of BUY, SELL, HOLD |
| `confidence_score` | Integer in [0, 100] |
| `technical_score` | Float in [0.0, 100.0] |
| `sentiment_score` | Float in [0.0, 100.0] |
| `market` | Exactly 'IN' or 'US' |
| `currency` | 'INR' for IN market, 'USD' for US market |
| `is_sufficient` | 0 when article_count < 2; 1 otherwise |
| `last_updated` / `computed_at` / `generated_at` | ISO 8601 UTC string |

---

## State Transitions

**Refresh cycle** (triggered by user clicking Refresh):

```
[App opens]
    │
    ▼
Read market_summaries.last_updated
    │
    ├─ > 1 hour ago ──► Display staleness warning; serve cached data
    │
    └─ User clicks Refresh
           │
           ▼
    Fetch price data (nsepython / yfinance)
           │
           ▼
    Fetch 200-day OHLCV history → compute technical indicators → compute scores
           │
           ▼
    Fetch RSS feeds → filter by stock → VADER score → compute sentiment score
           │
           ▼
    Compute final signal (70/30) for each stock
           │
           ▼
    DELETE existing rows → INSERT new rows (all tables, per market)
           │
           ▼
    Compute and write market_summaries
           │
           ▼
    Re-render dashboard with fresh data
```
