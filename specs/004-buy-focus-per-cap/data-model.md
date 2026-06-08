# Data Model: Per-Tier BUY Refresh

## No New Database Entities

This feature introduces no new SQLite tables or columns. All per-tier BUY results are held in Streamlit session state and never persisted to disk.

---

## Session State Entries (New)

### `tier_buy_{market}_{tier_slug}`

Holds the top-20 BUY signals for a specific (market, tier) pair, populated on demand when the user clicks that tier's BUY Refresh button.

| Key | Type | Example | Description |
|-----|------|---------|-------------|
| market | str | `"IN"` | Market code |
| tier_slug | str | `"large_cap"` | Snake-case tier label (derived from tier_label.replace(" ", "_").lower()) |
| value | list[dict] | see below | Up to 20 signal dicts in read_signals() format |

**Value format** — each dict in the list matches the `cache.read_signals()` output format so existing rendering code (`render_stock_list`) requires no changes:

| Field | Type | Description |
|-------|------|-------------|
| symbol | str | Stock ticker |
| market | str | `"IN"` or `"US"` |
| signal_type | str | Always `"BUY"` (filtered) |
| confidence_score | int | 0–100, sorted descending |
| technical_score | float | From `compute_indicators` |
| sentiment_score | float | From `score_articles_for_stock` |
| contributing_factors | str | JSON-serialised list |
| generated_at | str | ISO 8601 UTC timestamp of this refresh |
| cap_tier | str | Tier label (e.g. `"Large Cap"`) |
| current_price | float \| None | From `fetch_quotes` |
| last_updated | str \| None | ISO 8601 from quote fetch |

---

## Existing Session State Keys Modified

| Key | Change |
|-----|--------|
| `_prev_rows_{market}_{slug}{filter}` | Now also cleared for tier-slug-prefixed BUY keys when a tier BUY refresh runs, so stale row selections don't persist across refreshes. |

---

## Existing DB Schema: Unchanged

The `signals` table is not written to by the per-tier BUY Refresh. SELL/HOLD signals in the DB remain as left by the last global refresh.
