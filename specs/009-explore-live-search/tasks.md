# Tasks: Explore Live Search — Any Stock

**Input**: Design documents from `/specs/009-explore-live-search/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, contracts/search-contracts.md ✓, quickstart.md ✓

**Tests**: TDD is **mandatory** (Constitution Principle III). Test tasks appear before their corresponding implementation tasks. Tests MUST fail before implementation begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: Which user story this task belongs to ([US1] or [US2])
- Exact file paths are included in all task descriptions

---

## Phase 1: Setup

**Purpose**: Create empty module stub so test imports work before implementation.

- [x] T001 Create `marketpulse/data/__init__.py` if absent, then create `marketpulse/data/universe.py` with empty `NIFTY_500_UNIVERSE: dict = {}`, `SP500_UNIVERSE: dict = {}`, and a stub `get_universe` that raises `NotImplementedError`

---

## Phase 2: Foundational — Symbol Universe Module

**Purpose**: Deliver `NIFTY_500_UNIVERSE`, `SP500_UNIVERSE`, and `get_universe()` — required by both user stories. MUST be complete before any user-story work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

**Goal**: `get_universe("IN")` returns a non-empty `{symbol: company_name}` dict for Nifty 500; `get_universe("US")` for S&P 500; unknown market raises `ValueError`.

**Independent Test**: `python -c "from marketpulse.data.universe import get_universe; assert len(get_universe('IN')) >= 400; assert len(get_universe('US')) >= 400; print('PASS')"` — both pass.

- [x] T002 Write failing tests for `get_universe()` in `tests/test_live_search.py`: returns non-empty dict for `"IN"`, returns non-empty dict for `"US"`, all symbol keys are uppercase strings, all values are non-empty strings, unknown market raises `ValueError`
- [x] T003 Populate `NIFTY_500_UNIVERSE` dict (symbol → company name, ≥ 400 Nifty 500 entries) in `marketpulse/data/universe.py`
- [x] T004 Populate `SP500_UNIVERSE` dict (symbol → company name, ≥ 400 S&P 500 entries) in `marketpulse/data/universe.py`
- [x] T005 Implement `get_universe(market: str) -> dict[str, str]` dispatch function, confirm T002 tests pass: `pytest tests/test_live_search.py -k "Universe"` in `marketpulse/data/universe.py`

**Checkpoint**: `pytest tests/test_live_search.py -k "Universe"` — all green. Foundation ready.

---

## Phase 3: User Story 1 — Search Expanded Universe (Priority: P1) 🎯 MVP

**Goal**: User can search any Nifty 500 / S&P 500 stock by name or symbol in the Explore tab — not just the ~50/~100 currently tracked. Results are a single unified list (cached + universe-only).

**Independent Test**: App running → India Explore tab → type `"Bajaj Auto"` → `BAJAJAUT` appears in results. US Explore tab → type `"Palantir"` → `PLTR` appears. Short query `"B"` shows no results.

### Tests (write FIRST — must fail before implementation)

- [x] T006 [US1] Write failing tests for `search_stocks_live()` in `tests/test_live_search.py`: returns universe-only results not in DB, deduplicates symbols that exist in both DB and universe, is market-scoped (`"IN"` returns no US symbols), returns `[]` for query shorter than 2 chars, universe-only rows have `_live=True`, DB rows have `_live=False`, matching is case-insensitive, missing DB path returns universe results

- [x] T007 [US1] Write failing test asserting `_render_explore_tab` calls `search_stocks_live` (not `search_stocks`) via source inspection in `tests/test_live_search.py`

### Implementation

- [x] T008 [US1] Implement `search_stocks_live(query, market, db_path)` in `marketpulse/storage/cache.py`: query existing `search_stocks()` for DB results, search `get_universe(market)` dict for additional matches, deduplicate (DB wins), tag DB rows `_live=False` and universe-only rows `_live=True`, return combined list

- [x] T009 [US1] Update `_render_explore_tab` in `marketpulse/ui/dashboard.py` to call `cache.search_stocks_live(query, market)` instead of `cache.search_stocks(query, market)`, confirm T007 source-inspection test passes

**Checkpoint**: `pytest tests/test_live_search.py -k "US1 or search_stocks_live or explore_uses_live"` — all green. Manually verify Bajaj Auto / Palantir searchable.

---

## Phase 4: User Story 2 — Live Price and Detail for Non-Cached Stocks (Priority: P2)

**Goal**: Selecting a non-cached stock from search results triggers an on-demand price + OHLCV fetch (spinner shown), result cached in session state to avoid re-fetch. Failed fetches show a clear error — no crash. Watchlist/holdings add works for any found stock. A direct ticker lookup button appears when search returns 0 results.

**Independent Test**: App running → India Explore → search `"Bajaj Auto"` → select `BAJAJAUT` → spinner → current price and chart visible within 5s. Disconnect internet → repeat → `st.error` shown, no crash.

### Tests (write FIRST — must fail before implementation)

- [x] T010 [US2] Write failing tests for US2 behaviour in `tests/test_live_search.py`:
  - `render_stock_detail` signature accepts `live_quote` keyword arg (inspect.signature test)
  - `_render_explore_tab` source contains `st.spinner` (source inspection test)
  - `_render_explore_tab` source contains session-state key pattern `live_snapshot_` (source inspection test)
  - `_render_explore_tab` source contains `st.error` for fetch failure (source inspection test)
  - `_render_explore_tab` source contains direct lookup button text `"Try direct lookup"` (source inspection test)

### Implementation

- [x] T011 [P] [US2] Add optional `live_quote=None` parameter to `render_stock_detail` in `marketpulse/ui/stock_detail.py`; when `live_quote` is not None, display `live_quote.current_price` as current price and `live_quote.company_name` as display name; all existing callers unchanged (default None)

- [x] T012 [US2] Update `_render_explore_tab` in `marketpulse/ui/dashboard.py`:
  - For `_live=True` rows on selection: check `st.session_state[f"live_snapshot_{market}_{symbol}"]`
  - If absent: show `st.spinner("Loading…")`, call `fetch_quotes([symbol])` + `fetch_ohlcv_history(symbol)` from the market-appropriate data module, store result in session state
  - Pass fetched `StockQuote` as `live_quote=` to `render_stock_detail`
  - On `DataProviderError` or empty result: store error in session state, show `st.error(…)`
  - If `fetch_ohlcv_history` returns `None`: show `st.caption("Price history unavailable.")` — no crash

- [x] T013 [US2] Add direct ticker lookup fallback to `_render_explore_tab` in `marketpulse/ui/dashboard.py`: when `search_stocks_live` returns `[]` and query matches `^[A-Za-z0-9.\-]{2,12}$`, render `st.button(f"Try direct lookup for '{query.upper()}'")`; on click trigger the same on-demand fetch flow as T012

**Checkpoint**: `pytest tests/test_live_search.py -k "US2 or live_quote or spinner or live_snapshot or direct_lookup"` — all green. Manually select non-cached stock → spinner → price shown.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Confirm no regressions and validate all acceptance scenarios end-to-end.

- [x] T014 Run full test suite `pytest tests/` — confirm all existing tests still pass alongside new tests
- [ ] T015 Manual validation of all 7 quickstart scenarios from `specs/009-explore-live-search/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — **BLOCKS both user stories**
- **Phase 3 (US1)**: Depends on Phase 2 completion
- **Phase 4 (US2)**: Depends on Phase 3 completion (US2 builds on the extended search results)
- **Phase 5 (Polish)**: Depends on all phases complete

### Within Each Phase (TDD order)

- Tests (T006, T007, T010) MUST be written and MUST FAIL before their implementation tasks
- T003 and T004 (universe dicts) can be worked simultaneously (different variables, same file)
- T011 (render_stock_detail signature) is marked [P] — it has no dependency on T012 or T013

### Parallel Opportunities

Within Phase 2: T003 and T004 (different dict constants, same file) can be done together  
Within Phase 4: T011 (stock_detail.py change) can be done in parallel with T010 (test writing)

---

## Parallel Example: Phase 2

```
# These two data-entry tasks can proceed simultaneously:
Task T003: "Populate NIFTY_500_UNIVERSE in marketpulse/data/universe.py"
Task T004: "Populate SP500_UNIVERSE in marketpulse/data/universe.py"
# Then T005 combines them and tests pass
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002–T005)
3. Complete Phase 3: User Story 1 (T006–T009)
4. **STOP and VALIDATE**: Explore tab now searches Nifty 500 / S&P 500 universe
5. Ship US1, defer US2 to next cycle if needed

### Full Delivery (Both Stories)

1. Complete Phases 1–3 (US1 MVP)
2. Add Phase 4 (US2 on-demand fetch)
3. Polish and validate (Phase 5)

---

## Notes

- [P] = different files or logically independent — safe to run concurrently
- [US1]/[US2] maps each task to its user story for traceability
- All tests in `tests/test_live_search.py` (new file for this feature)
- Universe dicts are large (500+ entries each) — T003/T004 are data-entry tasks
- Constitution Principle III: tests MUST be written before implementation and MUST be red before going green
- Commit after each phase checkpoint
