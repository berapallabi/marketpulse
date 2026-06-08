# Data Model: Market Cap Tier Tabs

## Changed Entities

### StockQuote (marketpulse/data/types.py)

Adds one field. All other fields unchanged.

| Field | Type | Description |
|-------|------|-------------|
| symbol | str | |
| market | str | |
| company_name | str | |
| current_price | float | |
| open_price | float \| None | |
| high_price | float \| None | |
| low_price | float \| None | |
| volume | int \| None | |
| currency | str | |
| fetched_at | str | |
| **market_cap** | **float \| None** | **Absolute value in local currency (INR or USD). None if unavailable.** |

### Signal (marketpulse/analysis/signals.py)

Adds one field. All other fields unchanged.

| Field | Type | Description |
|-------|------|-------------|
| symbol | str | |
| market | str | |
| signal_type | str | |
| confidence_score | int | |
| technical_score | float | |
| sentiment_score | float | |
| contributing_factors | list[str] | |
| generated_at | str | |
| **cap_tier** | **str** | **One of: "Large Cap", "Mid Cap", "Small Cap" (India); "Mega Cap", "Large Cap", "Mid Cap", "Small Cap" (US); "Unknown" when market_cap is None.** |

## New Entity

### MarketCapTier (marketpulse/analysis/cap_tiers.py — config constants, not a DB table)

| Field | Type | Description |
|-------|------|-------------|
| label | str | Display name: "Large Cap", "Mid Cap", etc. |
| lower_bound | float | Minimum market cap (inclusive), absolute local currency |
| upper_bound | float \| None | Maximum market cap (exclusive). None = no upper limit. |

**India tiers** (INR, absolute rupees):

| Label | lower_bound | upper_bound |
|-------|-------------|-------------|
| Large Cap | 2×10¹¹ | None |
| Mid Cap | 5×10¹⁰ | 2×10¹¹ |
| Small Cap | 0 | 5×10¹⁰ |

**US tiers** (USD, absolute dollars):

| Label | lower_bound | upper_bound |
|-------|-------------|-------------|
| Mega Cap | 2×10¹¹ | None |
| Large Cap | 1×10¹⁰ | 2×10¹¹ |
| Mid Cap | 2×10⁹ | 1×10¹⁰ |
| Small Cap | 0 | 2×10⁹ |

## SQLite Schema Changes

### signals table

One additive column:

```sql
ALTER TABLE signals ADD COLUMN cap_tier TEXT DEFAULT 'Unknown';
```

Applied via `init_db()` migration (try/except OperationalError pattern — see research.md).

### All other tables: unchanged
