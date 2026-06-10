# Research: Watchlist & Holdings Refresh

**Branch**: `010-watchlist-refresh` | **Phase**: 0

## Existing Refresh Patterns

### Decision: Mirror `_refresh_tier_buy` but scope to a symbol set
**Rationale**: `_refresh_tier_buy` in `dashboard.py` already implements the full pipeline — fetch quotes → OHLCV → technical indicators → sentiment → signal → cache write → session state update. The only difference for watchlist/holdings is the input symbol set: instead of all 50/100 market symbols, we use only the symbols from `read_watchlist` or `read_holdings` filtered by the selected tier.

**Alternatives considered**:
- Re-use `_refresh_tier_buy` with a symbol filter argument — rejected; function has hard-coded session state keys tightly coupled to the BUY tab rendering flow.
- Full market refresh (existing `_refresh_market`) — rejected per FR-004 (scope isolation); too slow and refetches unrelated stocks.

---

## State Management Keys

### Decision: Follow the two-rerun pattern used by the BUY tab
**Rationale**: Streamlit re-executes the full script on every interaction. The BUY tab uses a `fetching_{market}_{slug}` flag stored in session state: the first click sets the flag and reruns, the second pass (with flag=True) shows a disabled "Fetching…" button, calls the refresh function, clears the flag, and reruns again. This pattern prevents double-submission and gives visible loading feedback without blocking the UI thread.

**New session state keys introduced**:
- `fetching_{market}_watchlist_{tier_slug}` — refresh-in-progress flag for watchlist
- `fetching_{market}_my_holdings_{tier_slug}` — refresh-in-progress flag for holdings

**Keys cleared after refresh** (to reset stale selections):
- `selected_{market}` — selected stock (avoids stale detail panel)
- `_prev_rows_{market}_watchlist_*` — dataframe row tracking for watchlist
- `_prev_rows_{market}_my_holdings_*` — dataframe row tracking for holdings

---

## Symbol Set Resolution

### Decision: Read watchlist/holdings symbols, then intersect with tier from signal_rows
**Rationale**: `read_watchlist` and `read_holdings` return all symbols regardless of tier. To scope a refresh to the currently-viewed tier, intersect the symbol list with those signal rows that have `cap_tier == tier_label`. This also naturally handles the case where a stock added from Explore has a placeholder signal — its `cap_tier` was set via `write_live_stock_data`, so it is included when refreshing the correct tier.

**Edge case — new stock with wrong tier in placeholder**: After refresh, `classify_cap_tier` recomputes the tier from the live market cap. If the recomputed tier differs from the placeholder tier, the signal is updated with the correct tier. The stock will then appear in the correct tier tab on the next render.

---

## No Schema Changes Required

**Decision**: Reuse existing `signals`, `stocks`, `price_snapshots`, `technical_snapshots`, `sentiment_snapshots`, and `news_items` tables without modification.

**Rationale**: The refresh pipeline already writes to all these tables via `write_signals`, `write_technical`, `write_sentiment`, `write_news`, and `write_quotes`. The watchlist/holdings refresh reuses the identical write path — only the input symbol set differs.

---

## Data Providers

| Market | Quotes | OHLCV + market cap |
|--------|--------|--------------------|
| India (IN) | `nsepython.nse_eq` via `fetch_quotes` | `yfinance` via `fetch_ohlcv_history` (returns `(df, market_cap)`) |
| US | `yfinance` via `fetch_quotes` (returns `StockQuote` with `market_cap` field) | `yfinance` via `fetch_ohlcv_history` (returns `(df, None)`) |

Both providers are already used identically in `_refresh_tier_buy` — no new provider work required.

---

## Test Strategy

**Decision**: Unit tests using a real SQLite in-memory/temp-file DB, mocked data providers
**Rationale**: Constitution Principle III (Test-First). Existing test suite in `tests/` uses `pytest` with temp SQLite paths. No mock is needed for the DB — real schema with test data is cleaner and more reliable.

**Test scope**:
1. `_refresh_section` writes updated signals only for the targeted symbols
2. Symbols in other sections/tiers are not modified
3. Empty watchlist/holdings results in a no-op (no crash, no DB writes)
4. Unavailable stocks are skipped; remaining stocks still get updated signals
5. Placeholder HOLD/0 signals from Explore are upgraded to real analysis
