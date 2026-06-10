# Data Model: Watchlist & Holdings Refresh

## No Schema Changes

This feature makes no changes to the SQLite schema. All entities already exist.

## Entities

### RefreshScope (logical, not persisted)

The input that defines a single refresh run.

| Field | Type | Description |
|-------|------|-------------|
| `market` | `str` | `"IN"` or `"US"` |
| `section` | `str` | `"watchlist"` or `"my_holdings"` |
| `tier_label` | `str` | e.g. `"Large Cap"`, `"Mid Cap"` |

Derived at runtime from: `(market, signal_slug, tier_label)` — not stored.

---

### Signal (existing — `signals` table)

The primary output written by each refresh run.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `symbol` | TEXT | No | Stock ticker |
| `market` | TEXT | No | `"IN"` / `"US"` |
| `signal_type` | TEXT | No | `"BUY"` / `"SELL"` / `"HOLD"` |
| `confidence_score` | REAL | No | 0–100 |
| `technical_score` | REAL | No | 0–100 |
| `sentiment_score` | REAL | No | 0–100 |
| `contributing_factors` | TEXT | Yes | JSON list |
| `generated_at` | TEXT | No | ISO-8601 UTC |
| `cap_tier` | TEXT | Yes | `"Large Cap"` / `"Mid Cap"` / etc. |

**Placeholder signals** (inserted by `write_live_stock_data` when a stock is added from Explore) have `signal_type='HOLD'`, `confidence_score=0`, `technical_score=0`, `sentiment_score=0.0`. After a section refresh, these are replaced with real values via `write_signals` (which upserts on `(symbol, market)`).

---

### TechnicalSnapshot (existing — `technical_snapshots` table)

Written per-symbol during refresh. Stores RSI-14, MACD value/signal, Bollinger Bands, SMA-50, SMA-200, and other indicators.

---

### SentimentSnapshot (existing — `sentiment_snapshots` table)

Written per-symbol during refresh. Stores sentiment score and contributing article summaries.

---

### NewsItem (existing — `news_items` table)

Written per-symbol during refresh. Stores article headlines and URLs used for sentiment scoring.

---

### PriceSnapshot (existing — `price_snapshots` table)

Updated per-symbol via `write_quotes` at the start of each refresh.

---

## State Transitions

### Placeholder → Real Signal (FR-009)

```
Explore detail view
  └─ write_live_stock_data()
       └─ INSERT OR IGNORE INTO signals (signal_type='HOLD', confidence_score=0, cap_tier=computed)
            ↓
Section Refresh (watchlist or holdings, correct tier)
  └─ _refresh_section()
       └─ write_signals() — upsert on (symbol, market)
            ↓
         signal_type=real, confidence_score>0, cap_tier=recomputed
```

### Refresh In-Progress State (session_state)

```
User clicks Refresh
  └─ st.session_state["fetching_{market}_{section}_{tier_slug}"] = True
       └─ st.rerun()
            ↓
Next render pass (fetching=True)
  └─ disabled button shown
  └─ _refresh_section(market, section, tier_label) called
  └─ st.session_state["fetching_{market}_{section}_{tier_slug}"] = False
  └─ st.rerun()
            ↓
Next render pass (fetching=False)
  └─ cache.read_signals(market) returns fresh data
  └─ Normal tab render with updated rows
```
