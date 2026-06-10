# Tasks: Explore Tab — Stock Search

**Input**: Design documents from `specs/008-explore-tab/`

**Prerequisites**: plan.md ✓, spec.md ✓, contracts/ui-contracts.md ✓, quickstart.md ✓

**TDD**: Constitution Principle III mandates test-first. Tests are written before implementation and verified to fail first.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup

**Purpose**: Read existing code to establish the baseline before any changes.

- [ ] T001 Read `_render_market_tab` in `marketpulse/ui/dashboard.py` to confirm current `st.tabs` call and session-state key patterns
- [ ] T002 Read `cache.py` (lines 1–170) to confirm `_upsert`, `read_signals`, and `stocks` table schema before adding `search_stocks`

---

## Phase 2: Foundational — `search_stocks` cache function

**Purpose**: The search backend is a prerequisite for both US1 and US2. Must be complete before either user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

> **TDD — write the failing tests first, confirm they fail, then implement.**

- [ ] T003 Write failing tests for `search_stocks` in `tests/test_explore_tab.py`: symbol match, company name match, case-insensitive, no match, query < 2 chars, missing DB — confirm all fail before T004
- [ ] T004 Implement `search_stocks(query: str, market: str, db_path: Path | None = None) -> list[dict]` in `marketpulse/storage/cache.py` following the contract in `specs/008-explore-tab/contracts/ui-contracts.md` — LEFT JOIN `stocks` + `signals` + `price_snapshots`, LIKE filter on symbol and company_name, returns `[]` for query < 2 chars or missing DB
- [ ] T005 Run `PYTHONPATH=. .venv/bin/pytest tests/test_explore_tab.py -k search` and confirm all `search_stocks` tests pass

**Checkpoint**: `search_stocks` is implemented and tested. User story implementation can begin.

---

## Phase 3: User Story 1 — Search and View Stock Details (Priority: P1) 🎯 MVP

**Goal**: User can type a query in the Explore tab, see matching stocks, select one, and view its full detail panel.

**Independent Test**: Open the Explore tab, type "REL", see RELIANCE in results, click it, confirm the detail panel appears on the right.

> **TDD — write the failing structural tests first, confirm they fail, then implement.**

- [ ] T006 [US1] Write failing tests for Explore tab structure in `tests/test_explore_tab.py`: `"Explore"` present in `st.tabs` call in `_render_market_tab` source; `_render_explore_tab` function exists in `dashboard` module — confirm they fail before T007
- [ ] T007 [US1] Add `_render_explore_tab(market: str)` to `marketpulse/ui/dashboard.py`: `st.text_input` keyed as `explore_query_{market}`; if query < 2 chars show hint; else call `cache.search_stocks(query, market)` and render with two-column layout — left col uses `render_stock_list(rows, market, filter_signal="ALL", key_prefix=f"explore_{market}")`, right col uses `render_stock_detail(..., key=f"explore_{market}")` or caption; selection stored in `st.session_state[f"selected_explore_{market}"]`
- [ ] T008 [US1] Extend `st.tabs` call in `_render_market_tab` in `marketpulse/ui/dashboard.py`: change `buy_tab, watchlist_tab, holdings_tab = st.tabs(["Buy", "Watchlist", "My Holdings"])` to `buy_tab, watchlist_tab, holdings_tab, explore_tab = st.tabs(["Buy", "Watchlist", "My Holdings", "Explore"])` and add `with explore_tab: _render_explore_tab(market)`
- [ ] T009 [US1] Run `PYTHONPATH=. .venv/bin/pytest tests/test_explore_tab.py` and confirm all US1 tests pass

**Checkpoint**: Explore tab is live. Search, results list, and detail panel all work. Existing tabs unaffected.

---

## Phase 4: User Story 2 — Add to Watchlist / Holdings from Explore (Priority: P2)

**Goal**: From the Explore detail panel, user can add/remove the selected stock to watchlist or holdings; changes persist and are visible in the respective tabs.

**Independent Test**: Find a stock in Explore, click "Add to Watchlist", switch to Watchlist tab, confirm the stock appears.

> **TDD — write the failing key-uniqueness test first, then verify.**

- [ ] T010 [US2] Write failing test in `tests/test_explore_tab.py`: `_render_explore_tab` source contains `key=f"explore_{market}"` (or equivalent) passed to `render_stock_detail` to prevent duplicate widget key errors when the same stock is open across multiple tabs — confirm it fails before T011
- [ ] T011 [US2] Verify `_render_explore_tab` in `marketpulse/ui/dashboard.py` passes `key=f"explore_{market}"` to `render_stock_detail` — the add/remove watchlist and holdings buttons in `render_stock_detail` call `_render_list_actions(symbol, market, key)` which already uses the key to scope button widget IDs; no new add/remove logic needed
- [ ] T012 [US2] Run `PYTHONPATH=. .venv/bin/pytest tests/test_explore_tab.py` and confirm all US2 tests pass

**Checkpoint**: Add/remove watchlist and holdings works from Explore. Changes visible instantly on tab switch.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T013 Run full test suite `PYTHONPATH=. .venv/bin/pytest tests/ -q` and confirm all tests (including pre-existing 126) pass with no regressions
- [ ] T014 [P] Validate empty-cache edge case: confirm Explore tab shows a clear empty state (not an error) when `stocks` table is empty
- [ ] T015 [P] Validate cross-tab selection independence per `quickstart.md`: select a stock in Buy tab, switch to Explore, confirm no pre-selection; select in Explore, switch back to Buy, confirm Buy selection unchanged

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 reads — blocks all user story work
- **US1 (Phase 3)**: Depends on Phase 2 (`search_stocks` must exist)
- **US2 (Phase 4)**: Depends on Phase 3 (`_render_explore_tab` must exist and call `render_stock_detail`)
- **Polish (Phase 5)**: Depends on Phases 3 and 4

### Within Each Phase

- Tests MUST be written first and confirmed failing before implementation
- T003 → T004 → T005 (sequential — search function)
- T006 → T007 → T008 → T009 (sequential — tab structure)
- T010 → T011 → T012 (sequential — key uniqueness)

### Parallel Opportunities

- T001 and T002 (Phase 1) can run in parallel — different files
- T014 and T015 (Phase 5) can run in parallel — independent validations

---

## Implementation Strategy

### MVP (US1 only — Phases 1–3)

1. Phase 1: Read baseline code
2. Phase 2: Implement and test `search_stocks`
3. Phase 3: Add `_render_explore_tab` and extend `st.tabs`
4. **STOP and VALIDATE**: Run quickstart happy path manually
5. US1 is fully functional — ship or demo

### Full Delivery (US1 + US2 — Phases 1–4)

US2 requires minimal additional work (key uniqueness only — add/remove logic already exists in `render_stock_detail`). Complete Phase 4 immediately after Phase 3.

---

## Notes

- `render_stock_list` and `render_stock_detail` are reused directly — no new UI components
- The `stocks` table (populated by `write_quotes`) is the search source, not `signals`, so stocks with no signal data are still discoverable
- `selected_explore_{market}` is intentionally separate from `selected_{market}` to prevent cross-tab selection bleed
- All widget keys in `_render_explore_tab` must use `explore_{market}` prefix to avoid `StreamlitDuplicateElementKey` errors
