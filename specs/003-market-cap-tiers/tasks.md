---
description: "Task list for Market Cap Tier Tabs"
---

# Tasks: Market Cap Tier Tabs

**Input**: Design documents from `specs/003-market-cap-tiers/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cap-tiers.md

**Tests**: Included per constitution Principle III (TDD mandatory).

---

## Phase 1: Setup

**Purpose**: No new project scaffolding needed — feature builds on the existing codebase.

- [x] T001 Verify `PYTHONPATH=. .venv/bin/pytest tests/ -q` passes (45 tests green) before any changes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Data layer and classification logic must be in place before UI or refresh changes.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 Write `tests/test_cap_tiers.py` — 12 tests covering all scenarios in `contracts/cap-tiers.md`: India Large/Mid/Small thresholds (including exact boundary values), US Mega/Large/Mid/Small thresholds, `None` input → `"Unknown"`, invalid market → `ValueError`. Run and confirm ALL FAIL before T003.

- [x] T003 Create `marketpulse/analysis/cap_tiers.py` with: `INDIA_TIERS` list of `(label, lower, upper)` tuples; `US_TIERS` list; `INDIA_TIER_ORDER = ["Large Cap", "Mid Cap", "Small Cap"]`; `US_TIER_ORDER = ["Mega Cap", "Large Cap", "Mid Cap", "Small Cap"]`; `classify_cap_tier(market_cap: float | None, market: str) -> str` pure function. Thresholds per `data-model.md`. Make T002 pass.

- [x] T004 [P] Add `market_cap: float | None = None` field to `StockQuote` dataclass in `marketpulse/data/types.py`; add `cap_tier: str = "Unknown"` field to `Signal` dataclass in `marketpulse/analysis/signals.py`. Both use `= None`/`= "Unknown"` defaults so all existing tests continue to pass without modification.

- [x] T005 [P] Add `cap_tier` column migration to `marketpulse/storage/cache.py`: after the `CREATE TABLE IF NOT EXISTS signals` block in `init_db()`, add `try: conn.execute("ALTER TABLE signals ADD COLUMN cap_tier TEXT DEFAULT 'Unknown'") except sqlite3.OperationalError: pass`. Update `write_signals()` to include `"cap_tier": sig.cap_tier` in the upsert dict. `read_signals()` needs no change — `SELECT *` already returns all columns. Add a test in `tests/test_cache.py` that writes a Signal with a non-default cap_tier and asserts it round-trips through read_signals.

**Checkpoint**: `PYTHONPATH=. .venv/bin/pytest tests/ -q` must pass. T002 tests now green. cap_tier stored and retrieved from SQLite.

---

## Phase 3: User Story 1 — Browse Stocks by Market Cap Tier (Priority: P1)

**Goal**: Tier tabs visible inside each market tab; each tier shows its stocks with All/BUY/SELL/HOLD sub-filters; signals classified by cap tier at refresh time.

**Independent Test**: Open the dashboard, click Refresh. India tab shows Large Cap / Mid Cap / Small Cap tier tabs. US tab shows Mega Cap / Large Cap / Mid Cap / Small Cap tier tabs. Each tier's All sub-tab shows only stocks whose market cap falls within that tier's bounds. All/BUY/SELL/HOLD filtering works inside each tier. Drill-down still works.

### Data providers — market cap fetch

- [x] T006 [US1] Update `marketpulse/data/us.py` `fetch_quotes()`: in the StockQuote constructor call, add `market_cap=_float(info.get("marketCap"))`. This uses the `ticker.info` dict that is already fetched — zero additional API calls. Update `tests/test_us.py` mock to include `"marketCap"` in the mock `info` dict and assert `quote.market_cap` is set correctly.

- [x] T007 [US1] Update `marketpulse/data/india.py` `fetch_ohlcv_history()`: change return type from `pd.DataFrame | None` to `tuple[pd.DataFrame | None, float | None]`. Inside the try block, after `ticker = yf.Ticker(f"{symbol}.NS")`, add `market_cap = _float(ticker.info.get("marketCap"))` before the `ticker.history()` call (same ticker object, one extra `.info` call per symbol). Change all `return None` and `return df` lines to `return None, None` and `return df, market_cap`. Update `tests/test_india.py`: mock `ticker.info` to return `{"marketCap": 5e11}`, update expected return type in all `fetch_ohlcv_history` tests to assert a tuple.

- [x] T008 [US1] Update `marketpulse/data/us.py` `fetch_ohlcv_history()`: change return type to `tuple[pd.DataFrame | None, float | None]` returning `(df, None)` (market_cap for US already comes from `fetch_quotes`). Update `tests/test_us.py` fetch_ohlcv_history tests to expect a tuple.

### Refresh pipeline — cap tier assignment

- [x] T009 [US1] Update `marketpulse/ui/dashboard.py` `_refresh_market()`: change `ohlcv = fetch_ohlcv_history(quote.symbol)` to `ohlcv, mc = fetch_ohlcv_history(quote.symbol)`. After that line set `market_cap = mc if market == "IN" else quote.market_cap`. Change the `if ohlcv is None: unavailable += 1; continue` block to remain as-is (skip stock if no OHLCV). After `signal = generate_signal(technical, sentiment)`, add `signal.cap_tier = classify_cap_tier(market_cap, market)` (import `classify_cap_tier` from `marketpulse.analysis.cap_tiers` at top of function). Ensure `cap_tier` is included when `write_signals(signals)` is called — the Signal dataclass already carries it.

### UI — tier tab navigation

- [x] T010 [US1] Update `marketpulse/ui/dashboard.py` `_render_market_tab()`: import `INDIA_TIER_ORDER, US_TIER_ORDER` from `marketpulse.analysis.cap_tiers`. Replace the existing body with:
  1. Render error / market-closed / sentiment gauge as before.
  2. Fetch `signal_rows = cache.read_signals(market)`.
  3. Build tier tabs: `tier_labels = INDIA_TIER_ORDER if market == "IN" else US_TIER_ORDER`. Create `st.tabs(tier_labels)` and for each tier tab: filter `tier_rows = [r for r in signal_rows if r.get("cap_tier") == tier_label]`, then render the four signal sub-tabs (All/BUY/SELL/HOLD) exactly as in the current implementation (copy the `tab_all, tab_buy, tab_sell, tab_hold = st.tabs(...)` block, passing `tier_rows` instead of `signal_rows`).
  4. Preserve the `selected_symbol` session state pattern and drill-down rendering below all tier tabs.
  5. Each dataframe key must include the tier to avoid Streamlit key collisions: e.g., `f"table_{market}_{tier_label.replace(' ', '_').lower()}_{filter_signal.lower()}"`. Update `render_stock_list()` to accept a `key_prefix: str = ""` parameter used in the dataframe key, and pass `key_prefix=tier_label` from the dashboard.

---

## Phase 4: Polish & Validation

- [x] T011 Run `PYTHONPATH=. .venv/bin/pytest tests/ -q` — all tests must pass. Fix any failures.

- [x] T012 Manual smoke test: `streamlit run app.py`, click Refresh. Verify India tab shows three tier tabs; US tab shows four tier tabs. Verify each tier's All sub-tab is populated (most/all Nifty 50 stocks will appear under Large Cap; S&P 100 will have Mega Cap and Large Cap populated). Verify BUY/SELL/HOLD filtering works inside a tier. Verify row click opens drill-down.

---

## Dependencies & Execution Order

- **T001** (baseline verification): Start here
- **T002** (tests written, failing): Before T003
- **T003** (cap_tiers.py): After T002
- **T004, T005** [P]: After T003 (use the new module); can run in parallel with each other
- **T006, T007, T008** [P]: After T004 (need StockQuote.market_cap field); can run in parallel
- **T009**: After T006, T007, T008 (needs data providers to return market_cap)
- **T010**: After T009 (needs cap_tier on signals in DB and classify_cap_tier imported)
- **T011, T012**: After T010

---

## Notes

- All tasks touch different files except T009 and T010 (both touch dashboard.py — do sequentially)
- `render_stock_list` key_prefix change in T010 is a minor signature addition; existing call sites in dashboard.py are the only callers
- India refresh will make one extra yfinance `.info` call per symbol (for market cap). With 50 symbols and CRITICAL-level yfinance logging, this is silent and acceptable for a personal app.
