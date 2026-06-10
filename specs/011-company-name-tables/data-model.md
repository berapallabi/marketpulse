# Data Model: Company Name in Stock Tables

## No Schema Changes

This feature makes no changes to the SQLite schema. All entities already exist.

## StockRow (read-path aggregate, not persisted)

The dict returned by `read_signals` after this fix:

| Field | Source table | Notes |
|-------|-------------|-------|
| `symbol` | `signals` | Primary identifier |
| `market` | `signals` | `"IN"` / `"US"` |
| `signal_type` | `signals` | `"BUY"` / `"SELL"` / `"HOLD"` |
| `confidence_score` | `signals` | 0–100 |
| `cap_tier` | `signals` | e.g. `"Large Cap"` |
| `current_price` | `price_snapshots` | May be NULL (LEFT JOIN) |
| `last_updated` | `price_snapshots` | May be NULL (LEFT JOIN) |
| `company_name` | **`stocks`** | **New** — May be NULL if stock not in stocks table (LEFT JOIN) |

## Fallback Rule

In `_build_df` (`stock_list.py`), if `company_name` is NULL/missing, the ticker `symbol` is shown instead of a blank cell.
