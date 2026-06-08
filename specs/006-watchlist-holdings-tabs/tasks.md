# Tasks: Watchlist & My Holdings Tabs

**Input**: Design documents from `specs/006-watchlist-holdings-tabs/`

**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/ui-contracts.md ✅

**Tests**: Included — the project constitution (Principle III) mandates test-first development. Every test task must FAIL before the corresponding implementation task begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup

**Purpose**: Confirm no structural changes needed before implementation begins.

- [X] T001 Verify `sqlite3` (stdlib), `streamlit`, and `pandas` are already in `requirements.txt` — no new dependencies needed for this feature

**Checkpoint**: No new dependencies required — proceed to Foundational phase.

---

## Phase 2: Foundational — Storage Layer

**Purpose**: Two new SQLite tables and six storage functions that US2 and US3 both depend on. Must complete before any user story that touches watchlist or holdings data.

**⚠️ CRITICAL**: US2 and US3 cannot start until this phase is complete.

> **Write tests FIRST — verify they FAIL before implementing**

- [X] T002 Write failing tests for all watchlist and holdings storage functions (add/remove/read, duplicate prevention, cross-market isolation, no-op remove) in `tests/test_watchlist_holdings.py`
- [X] T003 Add `watchlist` and `holdings` tables (`CREATE TABLE IF NOT EXISTS`) to the `executescript` block in `init_db()` in `marketpulse/storage/cache.py`
- [X] T004 Implement `add_to_watchlist`, `remove_from_watchlist`, `read_watchlist` using the `_upsert` / `DELETE` / `SELECT` pattern in `marketpulse/storage/cache.py`
- [X] T005 Implement `add_to_holdings`, `remove_from_holdings`, `read_holdings` using the same pattern in `marketpulse/storage/cache.py`
- [X] T006 Run `pytest tests/test_watchlist_holdings.py` — all tests must be green before proceeding

**Checkpoint**: Storage layer complete and tested — US2 and US3 can now begin.

---

## Phase 3: User Story 1 — Tab Navigation (Priority: P1) 🎯 MVP

**Goal**: Replace the four-option filter (All/BUY/SELL/HOLD) with the three-tab layout (Buy/Watchlist/My Holdings). Buy tab retains exact existing BUY behaviour. Watchlist and My Holdings show empty states.

**Independent Test**: Open the app, navigate to any market and cap tier. The signal filter shows exactly three options: Buy, Watchlist, My Holdings. Selecting Buy shows the same stock list as the old BUY filter. All, SELL, and HOLD are gone.

> **Write tests FIRST — verify they FAIL before implementing**

- [X] T007 Write failing tests asserting the segmented control options are exactly `["Buy", "Watchlist", "My Holdings"]` (no All/SELL/HOLD), default is `"Buy"`, and the Buy tab returns BUY-signal rows in `tests/test_dashboard_tabs.py`
- [X] T008 [US1] Update `st.segmented_control` options from `["All", "BUY", "SELL", "HOLD"]` to `["Buy", "Watchlist", "My Holdings"]` and `default` from `"All"` to `"Buy"` in `marketpulse/ui/dashboard.py` (lines 255–261)
- [X] T009 [US1] Replace the `elif signal_choice == "SELL"` and `elif signal_choice == "HOLD"` branches with `elif signal_choice == "Watchlist"` and `elif signal_choice == "My Holdings"` stubs (showing `st.caption` empty-state messages) in `marketpulse/ui/dashboard.py` (lines 285–315); update the `"All"` branch condition to `"Buy"`
- [X] T010 [US1] Run `pytest tests/test_dashboard_tabs.py` — US1 tests must pass

**Checkpoint**: Three-tab layout is live. Buy tab works correctly. Watchlist and My Holdings show empty states.

---

## Phase 4: User Story 2 — Watchlist (Priority: P2)

**Goal**: Users can add stocks to a watchlist from the detail panel and see them in the Watchlist tab. Entries persist across page reloads.

**Independent Test**: Add one stock to the Watchlist, reload the page, switch to the Watchlist tab — stock appears. Remove it — it disappears.

> **Write tests FIRST — verify they FAIL before implementing**

- [X] T011 Extend `tests/test_dashboard_tabs.py` with failing tests for: Watchlist tab shows only symbols in the watchlist table, shows empty-state caption when watchlist is empty, and does not show symbols absent from the watchlist
- [X] T012 Extend `tests/test_dashboard_tabs.py` with failing tests for: detail panel renders "Add to Watchlist" when symbol not in watchlist, renders "Remove from Watchlist" when symbol is in watchlist
- [X] T013 [P] [US2] Implement the Watchlist branch in `marketpulse/ui/dashboard.py`: call `read_watchlist(market)`, filter `tier_rows` to matching symbols, call `render_stock_list` or show `st.caption("No stocks in your watchlist yet.")` if empty
- [X] T014 [P] [US2] Import `add_to_watchlist`, `remove_from_watchlist`, `read_watchlist` from `marketpulse.storage.cache` and add Watchlist add/remove button to the stock detail panel in `marketpulse/ui/stock_detail.py` — button label toggles based on membership; click calls the appropriate function then `st.rerun()`
- [X] T015 [US2] Run `pytest tests/test_watchlist_holdings.py tests/test_dashboard_tabs.py` — all US2 tests must pass

**Checkpoint**: Watchlist tab fully functional and independently testable. US1 still passes.

---

## Phase 5: User Story 3 — My Holdings (Priority: P3)

**Goal**: Users can add stocks to My Holdings from the detail panel and see them in the My Holdings tab. Entries persist across page reloads.

**Independent Test**: Add one stock to My Holdings, reload the page, switch to the My Holdings tab — stock appears. Remove it — it disappears.

> **Write tests FIRST — verify they FAIL before implementing**

- [X] T016 Extend `tests/test_dashboard_tabs.py` with failing tests for: My Holdings tab shows only symbols in the holdings table, shows empty-state caption when holdings is empty, does not show symbols absent from holdings
- [X] T017 Extend `tests/test_dashboard_tabs.py` with failing tests for: detail panel renders "Add to Holdings" when symbol not in holdings, renders "Remove from Holdings" when symbol is in holdings
- [X] T018 [P] [US3] Implement the My Holdings branch in `marketpulse/ui/dashboard.py`: call `read_holdings(market)`, filter `tier_rows` to matching symbols, call `render_stock_list` or show `st.caption("No holdings added yet.")` if empty
- [X] T019 [P] [US3] Import `add_to_holdings`, `remove_from_holdings`, `read_holdings` from `marketpulse.storage.cache` and add Holdings add/remove button to the stock detail panel in `marketpulse/ui/stock_detail.py` — button label toggles based on membership; click calls the appropriate function then `st.rerun()`
- [X] T020 [US3] Run `pytest tests/test_watchlist_holdings.py tests/test_dashboard_tabs.py` — all US3 tests must pass

**Checkpoint**: All three user stories are fully functional and independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Full regression verification and manual validation.

- [X] T021 [P] Run full test suite `pytest tests/` — confirm zero regressions across all existing tests (test_cache, test_signals, test_dashboard_buy, test_theme, etc.)
- [ ] T022 Follow `quickstart.md` validation steps manually: run `streamlit run app.py`, verify all three tabs on both India and US markets, add/remove stocks in Watchlist and My Holdings, reload to confirm persistence, confirm duplicate add has no effect

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **blocks US2 and US3**
- **US1 (Phase 3)**: Depends on Phase 1 only — can start in parallel with Phase 2
- **US2 (Phase 4)**: Depends on Phase 2 (storage) + Phase 3 (tab structure)
- **US3 (Phase 5)**: Depends on Phase 2 (storage) + Phase 3 (tab structure); can run in parallel with US2
- **Polish (Phase 6)**: Depends on all story phases complete

### User Story Dependencies

- **US1 (P1)**: Can start after Setup — independent of storage layer
- **US2 (P2)**: Depends on Foundational (T002–T006) and US1 (T007–T010)
- **US3 (P3)**: Depends on Foundational (T002–T006) and US1 (T007–T010); parallelisable with US2

### Within Each Phase

- Tests tasks MUST be written and confirmed FAILING before implementation tasks begin
- T004 and T005 are in the same file — execute sequentially
- T013 and T014 touch different files — can run in parallel [P]
- T018 and T019 touch different files — can run in parallel [P]

---

## Parallel Example: Phase 2 + Phase 3

```bash
# Phase 2 and Phase 3 can start simultaneously after Phase 1:
Task A: "Write storage layer tests + implement watchlist/holdings tables & functions" (T002–T006)
Task B: "Write tab-options tests + update segmented_control options" (T007–T010)
# Both complete → unblocks US2 and US3
```

## Parallel Example: US2 + US3

```bash
# After Phase 2 + Phase 3 complete, US2 and US3 can run in parallel:
Developer A (US2):
  T011 Write Watchlist tab tests
  T012 Write Watchlist detail panel tests
  T013 [P] Implement Watchlist branch in dashboard.py
  T014 [P] Implement Watchlist buttons in stock_detail.py

Developer B (US3):
  T016 Write My Holdings tab tests
  T017 Write My Holdings detail panel tests
  T018 [P] Implement My Holdings branch in dashboard.py
  T019 [P] Implement My Holdings buttons in stock_detail.py
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 3: US1 (T007–T010) — tab structure change with Buy working
3. **STOP and VALIDATE**: App shows three tabs, Buy works, Watchlist/My Holdings show empty states
4. No storage work needed for MVP

### Incremental Delivery

1. Phase 1 + Phase 3 → Three tabs live, Buy works (MVP)
2. Phase 2 → Storage layer ready (unblocks US2 + US3)
3. Phase 4 (US2) → Watchlist fully functional
4. Phase 5 (US3) → My Holdings fully functional
5. Phase 6 → Regression clean, manually verified

---

## Notes

- [P] tasks = different files, no shared dependencies between them
- [Story] label maps each task to its user story for traceability
- Constitution Principle III (Test-First) is non-negotiable: failing test before every implementation
- No new Python packages — `sqlite3` is stdlib, everything else already in `requirements.txt`
- `CREATE TABLE IF NOT EXISTS` in T003 makes the DB migration additive and safe for existing databases
- `st.rerun()` is the correct Streamlit pattern to refresh UI after a DB write
