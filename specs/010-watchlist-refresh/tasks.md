# Tasks: Watchlist & Holdings Refresh

**Input**: Design documents from `/specs/010-watchlist-refresh/`

**Branch**: `010-watchlist-refresh`

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files or independent code blocks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Verify Prerequisites)

**Purpose**: Confirm that all functions and modules the implementation depends on already exist and are in their expected shape. No new modules are created in this phase.

- [x] T001 Confirm `cache.read_watchlist(market)`, `cache.read_holdings(market)`, `cache.read_signals(market)`, `cache.write_signals(...)`, `cache.write_technical(...)`, `cache.write_sentiment(...)`, `cache.write_news(...)`, `cache.write_quotes(...)` exist in `marketpulse/storage/cache.py`
- [x] T002 Confirm `_refresh_tier_buy`, `_rows_last_at`, and `_news_items_from_sentiment` are defined in `marketpulse/ui/dashboard.py` — these are the reference patterns for the new function

**Checkpoint**: All referenced helpers confirmed present — implementation can begin

---

## Phase 2: Foundational (Blocking Prerequisite)

**Purpose**: Add the `_refresh_section` core function that all three user stories depend on. No UI changes here.

**⚠️ CRITICAL**: No user story UI work can begin until this phase is complete.

- [x] T003 Add `_refresh_section(market: str, section: str, tier_label: str) -> None` to `marketpulse/ui/dashboard.py` directly after `_refresh_tier_buy` (before `_rows_last_at`). The function must:
  - Read symbols from `cache.read_watchlist(market)` or `cache.read_holdings(market)` based on `section`
  - Read `cache.read_signals(market)` to resolve which symbols belong to `tier_label`
  - Build `tier_symbols` list as intersection: symbols in section AND in the correct tier
  - Return early (no-op) if `tier_symbols` is empty
  - Call `fetch_quotes(tier_symbols)` → `cache.write_quotes(quotes)` (raise `DataProviderError` → `st.error`, return)
  - Fetch articles via `fetch_market_articles(market)` (best-effort; empty list on failure)
  - For each quote: call `fetch_ohlcv_history` → `compute_indicators` → `score_articles_for_stock` → `generate_signal`; assign `signal.cap_tier = classify_cap_tier(market_cap, market)` where `market_cap = mc if market == "IN" else quote.market_cap`; call `cache.write_technical`, `cache.write_sentiment`, `cache.write_news`, append to `signals` list; skip silently on any exception
  - Call `cache.write_signals(signals)` if signals list is non-empty
  - Clear `st.session_state["selected_{market}"]` and any keys matching `_prev_rows_{market}_{section}_{tier_slug}*`

**Checkpoint**: `_refresh_section` exists and is callable — user story phases can now proceed

---

## Phase 3: User Story 1 — Refresh Watchlist Analysis (Priority: P1) 🎯 MVP

**Goal**: Add a working "Refresh" button to the Watchlist tab (per tier) that calls `_refresh_section` for watchlist symbols in that tier, shows a loading indicator while running, and re-renders with fresh signal data on completion.

**Independent Test**: Add a stock to watchlist, note its current signal, click Refresh in the matching tier tab, and verify that signal type and confidence score update (and are non-zero if market data is available).

### Implementation for User Story 1

- [x] T004 [US1] Update the Watchlist tab block in `marketpulse/ui/dashboard.py` (lines ~336–369): wrap the existing `tier_label = st.segmented_control(...)` inside a new `seg_col, btn_col = st.columns([5, 4], vertical_alignment="center")` nested under `filter_col, _ = st.columns([3, 2], gap="large")`. Add the refresh button in `btn_col` following the two-rerun pattern:
  - Compute: `slug`, `fetching_key = f"fetching_{market}_{signal_slug}_{slug}"`, `fetching = st.session_state.get(fetching_key, False)`, `watchlist_rows` (existing logic)
  - If `watchlist_rows` is non-empty and `fetching` is True: render disabled `"⏳  Refreshing…"` button, call `_refresh_section(market, "watchlist", tier_label)`, set `st.session_state[fetching_key] = False`, call `st.rerun()`
  - If `watchlist_rows` is non-empty and `fetching` is False: compute `last_at = _rows_last_at(watchlist_rows)`, render `f"🔄  Refresh  ·  last at {last_at}"` or `"🔄  Refresh"` button; on click: set `st.session_state[fetching_key] = True`, call `st.rerun()`
  - If `watchlist_rows` is empty: no button rendered (existing `st.caption("No stocks in your watchlist yet.")` behaviour unchanged)

### Tests for User Story 1

- [x] T005 [P] [US1] Write `test_refresh_section_updates_watchlist_symbols` in `tests/test_watchlist_refresh.py`: seed temp DB with one watchlist symbol in Large Cap tier with placeholder signal (HOLD, score=0); mock `fetch_quotes`, `fetch_ohlcv_history`, `compute_indicators`, `score_articles_for_stock`, `generate_signal`; call `_refresh_section("IN", "watchlist", "Large Cap", db_path=tmp_path)`; assert `cache.read_signals("IN")` returns a signal for that symbol with `signal_type != "HOLD"` or `confidence_score > 0`
- [x] T006 [P] [US1] Write `test_refresh_section_no_op_when_empty` in `tests/test_watchlist_refresh.py`: call `_refresh_section("IN", "watchlist", "Large Cap")` with empty watchlist; assert no signals written, no exception raised
- [x] T007 [P] [US1] Write `test_refresh_section_skips_unavailable` in `tests/test_watchlist_refresh.py`: seed two watchlist symbols; mock `fetch_ohlcv_history` to return `(None, None)` for the first, valid data for the second; call `_refresh_section`; assert only the second symbol has an updated signal
- [x] T008 [P] [US1] Write `test_refresh_section_upgrades_placeholder_signal` in `tests/test_watchlist_refresh.py`: seed a watchlist symbol with a placeholder HOLD/0 signal (as `write_live_stock_data` would insert); call `_refresh_section`; assert the resulting signal has `confidence_score > 0` (real analysis, not placeholder)

**Checkpoint**: Watchlist refresh button is fully functional and all US1 tests pass

---

## Phase 4: User Story 2 — Refresh Holdings Analysis (Priority: P2)

**Goal**: Add a "Refresh" button to the My Holdings tab (per tier) with identical behaviour to the Watchlist tab refresh, scoped to holdings symbols.

**Independent Test**: Add a stock to holdings, click Refresh in its tier tab, verify the signal and confidence score update independently of the watchlist.

### Implementation for User Story 2

- [x] T009 [US2] Update the My Holdings tab block in `marketpulse/ui/dashboard.py` (lines ~371–404): apply the identical layout and button pattern as T004, using `signal_slug = "my_holdings"`, `holdings_rows` instead of `watchlist_rows`, and `section = "my_holdings"` in the `_refresh_section` call. Caption for empty state remains `"No holdings added yet."`

### Tests for User Story 2

- [x] T010 [P] [US2] Write `test_refresh_section_updates_holdings_symbols` in `tests/test_watchlist_refresh.py`: same structure as T005 but using `cache.write_holdings` to seed holdings and calling `_refresh_section("IN", "my_holdings", "Large Cap")`; assert signal updated for the holdings symbol

**Checkpoint**: Holdings refresh button functional; US2 tests pass

---

## Phase 5: User Story 3 — Scoped Refresh per Tier (Priority: P3)

**Goal**: Confirm that refreshing one (market, section, tier) triple does not modify signals for symbols in any other section or tier. This story is validated entirely through tests — the scope isolation is inherent in `_refresh_section` by design (T003).

**Independent Test**: Seed watchlist symbols in Large Cap and Mid Cap tiers; refresh Large Cap only; verify Mid Cap signals are unchanged.

### Tests for User Story 3

- [x] T011 [US3] Write `test_refresh_section_scope_isolation` in `tests/test_watchlist_refresh.py`: seed DB with Large Cap and Mid Cap watchlist symbols AND a holdings symbol in Large Cap; call `_refresh_section("IN", "watchlist", "Large Cap")`; assert Large Cap watchlist symbol signal is updated, Mid Cap watchlist symbol signal is unchanged, and Large Cap holdings symbol signal is unchanged
- [x] T012 [P] [US3] Write `test_refresh_section_only_targeted_tier` in `tests/test_watchlist_refresh.py`: seed watchlist with one Large Cap and one Mid Cap symbol (both as placeholder HOLD/0); call `_refresh_section("IN", "watchlist", "Mid Cap")`; assert only the Mid Cap symbol's signal is updated

**Checkpoint**: All three user stories independently functional; scope isolation verified

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T013 Run `PYTHONPATH=. .venv/bin/pytest tests/test_watchlist_refresh.py -v` and confirm all tests pass
- [ ] T014 [P] Manual smoke test: start the app with `PYTHONPATH=. .venv/bin/streamlit run marketpulse/app.py`, add a stock from the Explore tab to watchlist, navigate to Watchlist tab, select the correct tier, click Refresh, and verify the detail panel shows a non-zero confidence score
- [ ] T015 [P] Manual smoke test: verify that clicking Refresh in the Watchlist Large Cap tier does not alter signals visible in the My Holdings tab or in the Watchlist Mid Cap tier

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user story phases
- **US1 (Phase 3)**: Depends on Phase 2 completion
- **US2 (Phase 4)**: Depends on Phase 2 completion — can start in parallel with US1
- **US3 (Phase 5)**: Depends on Phase 2 completion — tests can be written in parallel with US1/US2
- **Polish (Phase 6)**: Depends on all desired user story phases complete

### User Story Dependencies

- **US1 (P1)**: No dependency on US2 or US3 — independently testable
- **US2 (P2)**: No dependency on US1 or US3 — independently testable
- **US3 (P3)**: The `_refresh_section` scoping logic (T003) already satisfies US3; tests verify it

### Within Each Phase

- T004 (US1 UI) must come before T005–T008 (US1 tests) only for integration testing; unit tests for `_refresh_section` can be written as soon as T003 is done
- T009 (US2 UI) can proceed in parallel with T005–T008 since it modifies a different code block in `dashboard.py`
- All test tasks marked [P] within a phase can be written simultaneously

---

## Parallel Example: Writing All Tests After Phase 2

```text
After T003 is complete, launch in parallel:
  T005: test_refresh_section_updates_watchlist_symbols
  T006: test_refresh_section_no_op_when_empty
  T007: test_refresh_section_skips_unavailable
  T008: test_refresh_section_upgrades_placeholder_signal
  T010: test_refresh_section_updates_holdings_symbols
  T011: test_refresh_section_scope_isolation
  T012: test_refresh_section_only_targeted_tier
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Verify prerequisites (T001–T002)
2. Complete Phase 2: Add `_refresh_section` (T003)
3. Complete Phase 3: Watchlist tab refresh button + tests (T004–T008)
4. **STOP and VALIDATE**: Run tests + manual smoke test for Watchlist refresh
5. Merge or demo the MVP — Holdings and scope tests can follow

### Incremental Delivery

1. Phase 1–2 → `_refresh_section` available
2. Phase 3 → Watchlist refresh works + tested (MVP)
3. Phase 4 → Holdings refresh works + tested
4. Phase 5 → Scope isolation verified
5. Phase 6 → All tests green, smoke tests pass

---

## Notes

- All source changes are in **one file**: `marketpulse/ui/dashboard.py`
- All tests go in **one file**: `tests/test_watchlist_refresh.py`
- `_refresh_section` must accept an optional `db_path` argument (forwarded to cache calls) to allow tests to use a temp SQLite path without patching globals
- `signal_slug` for holdings is `"my_holdings"` — matches existing session state key convention in the dashboard
- The `[P]` label on test tasks (T005–T008, T010–T012) reflects that they touch the same test file but write independent test functions — they can be authored simultaneously by different developers or parallel agents
