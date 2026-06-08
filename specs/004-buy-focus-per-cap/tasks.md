---
description: "Task list for Per-Tier BUY Refresh — Top 20 Buy Stocks"
---

# Tasks: Per-Tier BUY Refresh — Top 20 Buy Stocks

**Input**: Design documents from `specs/004-buy-focus-per-cap/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/tier-buy-refresh.md

**Tests**: Included per constitution Principle III (TDD mandatory).

---

## Phase 1: Setup

**Purpose**: Verify baseline is clean before any changes.

- [X] T001 Verify `PYTHONPATH=. .venv/bin/pytest tests/ -q` passes (60 tests green) before any changes

---

## Phase 2: Foundational

**Purpose**: No new data models or DB migrations — this phase is empty. All work is in the user story phase.

*(No foundational tasks — feature adds no new DB tables, no new modules, no new dependencies.)*

---

## Phase 3: User Story 1 — Per-Tier BUY Refresh (Priority: P1)

**Goal**: Each cap tier's BUY sub-tab has a Refresh button that fetches fresh signals for that tier's stocks, displays top 20 BUY results ranked by confidence, and leaves SELL/HOLD data unchanged.

**Independent Test**: Run the app, perform a global Refresh. Navigate to India → Large Cap → BUY tab. Click the `🔄 Refresh BUY` button. Verify a spinner appears, then up to 20 BUY stocks are displayed sorted by confidence. Navigate to India → Large Cap → SELL tab — data is unchanged. Navigate to US → Mega Cap → BUY tab, click its Refresh BUY button — only US Mega Cap data is updated.

### TDD: Write failing tests first

- [X] T002 [US1] Write `tests/test_dashboard_buy.py` with 7 tests for `_top_buy_signals()` per `contracts/tier-buy-refresh.md`: empty list → `[]`; all SELL signals → `[]`; all BUY fewer than limit → all sorted desc; mixed BUY/SELL/HOLD → only BUY sorted desc; >20 BUY signals → top 20 desc; exactly 20 BUY signals → all 20 desc; `limit=5` with 10 BUY signals → top 5 desc. Run and confirm ALL FAIL before T003.

### Implementation

- [X] T003 [US1] Add `_top_buy_signals(signals: list, limit: int = 20) -> list` pure function to `marketpulse/ui/dashboard.py`: filter to `signal_type == "BUY"`, sort by `confidence_score` descending, return first `limit` items. Make T002 pass. Import from tests via `from marketpulse.ui.dashboard import _top_buy_signals`.

- [X] T004 [US1] Add `_refresh_tier_buy(market: str, tier_label: str) -> None` function to `marketpulse/ui/dashboard.py`. Function body:
  1. Derive `slug = tier_label.replace(" ", "_").lower()`.
  2. Get tier symbols: `existing = cache.read_signals(market); tier_symbols = [r["symbol"] for r in existing if r.get("cap_tier") == tier_label]`. If empty, store `[]` in session state and return.
  3. Import data provider for the market (same `if market == "IN" / else` pattern as `_refresh_market`).
  4. Fetch quotes for `tier_symbols` only. On `DataProviderError`, store `[]` and show `st.error(...)`.
  5. Fetch news articles for the market via `fetch_market_articles(market)`.
  6. For each quote: call `fetch_ohlcv_history(quote.symbol)` → unpack `(ohlcv, mc)`; skip if `ohlcv is None`; call `compute_indicators`; call `score_articles_for_stock`; call `generate_signal`; set `signal.cap_tier = classify_cap_tier(mc if market == "IN" else quote.market_cap, market)`. Wrap in a `st.spinner("Fetching BUY signals for {tier_label}…")`.
  7. Call `_top_buy_signals(signals, limit=20)` → convert each Signal to a dict matching `cache.read_signals()` output format (symbol, market, signal_type, confidence_score, technical_score, sentiment_score, contributing_factors as JSON string, generated_at, cap_tier, current_price from quote, last_updated from quote.fetched_at).
  8. Store list in `st.session_state[f"tier_buy_{market}_{slug}"]`.
  9. Clear `st.session_state.pop(f"_prev_rows_{market}_{slug}_buy", None)` so stale row selection resets.

- [X] T005 [US1] Update `_render_market_tab()` in `marketpulse/ui/dashboard.py`: inside each tier tab's BUY sub-tab (`with tab_buy:`), replace the current single `render_stock_list` call with:
  1. A `st.button("🔄 Refresh BUY", key=f"btn_tier_buy_{market}_{slug}")` button at the top.
  2. On click: call `_refresh_tier_buy(market, tier_label)`.
  3. Read `tier_buy_rows = st.session_state.get(f"tier_buy_{market}_{slug}")`.
  4. If `tier_buy_rows is None`: use `tier_rows` (from DB, existing behaviour — no per-tier refresh yet). If `tier_buy_rows` is an empty list `[]`: show `st.caption("No BUY signals found for this tier. Click 🔄 Refresh BUY above.")` and `return`. Otherwise use `tier_buy_rows` as the data.
  5. Call `render_stock_list(data, market, filter_signal="BUY", key_prefix=tier_label)` with the resolved data. The `All`, `SELL`, and `HOLD` sub-tabs continue to use `tier_rows` from DB unchanged.

- [X] T006 [US1] Update `_refresh_market()` in `marketpulse/ui/dashboard.py`: after the existing `st.session_state.pop(f"selected_{market}", None)` block, also clear all per-tier BUY session state keys for this market: `for _key in [k for k in st.session_state if k.startswith(f"tier_buy_{market}_")]: st.session_state.pop(_key, None)`. This ensures the global Refresh resets per-tier BUY results so stale cached results don't persist across global refreshes.

---

## Phase 4: Polish & Validation

- [X] T007 Run `PYTHONPATH=. .venv/bin/pytest tests/ -q` — all tests must pass. Fix any failures.

- [X] T008 Manual smoke test: `streamlit run app.py`. Run a global Refresh. Navigate to India → Large Cap → BUY tab, click `🔄 Refresh BUY`. Verify: spinner shown; up to 20 BUY stocks appear sorted by confidence; SELL/HOLD tabs are unchanged; other tier BUY tabs (Mid Cap, Small Cap) are unchanged. Repeat for US → Mega Cap → BUY tab. Run global Refresh again and verify per-tier BUY results reset (the BUY tab falls back to last-global-refresh data).

---

## Dependencies & Execution Order

- **T001** (baseline): Start here
- **T002** (failing tests): Before T003
- **T003** (`_top_buy_signals`): After T002 — make tests pass
- **T004** (`_refresh_tier_buy`): After T003 (calls `_top_buy_signals`)
- **T005** (UI button): After T004 (calls `_refresh_tier_buy`)
- **T006** (clear on global refresh): After T005 — all dashboard.py touches done
- **T007**, **T008**: After T006

All tasks touch `dashboard.py` (T003–T006) — execute sequentially. T002 only creates a new test file — no file conflicts.

---

## Notes

- `_top_buy_signals` is importable from `marketpulse.ui.dashboard` for tests. Streamlit is not imported at module level in `dashboard.py` (it uses `import streamlit as st` inside functions in some cases) — verify that `_top_buy_signals` can be imported without triggering Streamlit initialisation. If there's an import issue, move `_top_buy_signals` to a separate `marketpulse/analysis/buy_ranking.py` module.
- The per-tier BUY Refresh fetches quotes for `tier_symbols` only. Since `fetch_quotes` currently takes a full symbol list, it will work correctly with a subset — no signature change needed.
- The `_refresh_tier_buy` function does not call `cache.write_signals` — this is intentional (research.md decision 1: session state only).
