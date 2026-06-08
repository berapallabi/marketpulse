# Tasks: Swap Tab Hierarchy

**Input**: Design documents from `specs/007-swap-tab-hierarchy/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, contracts/ui-contracts.md ✓, quickstart.md ✓

**TDD**: Required by Constitution Principle III — write tests first, verify they fail, then implement.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new dependencies or project structure changes — this is a pure UI refactor.

*(No setup tasks needed — skip to foundational)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Read current implementation so test and implementation tasks are grounded in actual code.

**⚠️ CRITICAL**: Must complete before Phase 3 — implementation tasks reference exact key names from current code.

- [x] T001 Read current `_render_market_tab` in `marketpulse/ui/dashboard.py` to identify: all session-state key formats (`signal_`, `fetching_`, `btn_tier_buy_`, `tier_buy_`), tier loop structure, and `render_stock_detail` key argument

**Checkpoint**: Current structure understood — Phase 3 can begin

---

## Phase 3: User Story 1 — Navigate by Intent First, Then by Tier (Priority: P1) 🎯 MVP

**Goal**: Invert the two-level tab hierarchy — `st.tabs(["Buy","Watchlist","My Holdings"])` becomes outer, `st.segmented_control(tier_labels)` becomes inner. Update all widget/session-state keys to include `signal_slug` to prevent duplicate key errors.

**Note**: US2 (Visual Design Swapped) is automatically achieved by this structural change — switching components from `st.tabs()` ↔ `st.segmented_control()` inherits the correct Streamlit visual styles. No additional implementation is needed for US2.

**Independent Test**: Open the app, select any market. Outer row shows **Buy | Watchlist | My Holdings** in the bold tab style. Selecting Buy reveals a compact segmented tier row beneath.

### Tests for User Story 1 ⚠️ Write FIRST — must FAIL before implementation

- [x] T002 [US1] Write failing test: assert `_render_market_tab` source calls `st.tabs(["Buy", "Watchlist", "My Holdings"])` as outer tab in `tests/test_tab_hierarchy.py`
- [x] T003 [US1] Write failing test: assert `_render_market_tab` source does NOT contain old outer `st.tabs(tier_labels)` pattern in `tests/test_tab_hierarchy.py`
- [x] T004 [US1] Write failing test: assert inner tier row uses `st.segmented_control` (not `st.tabs`) in `tests/test_tab_hierarchy.py`
- [x] T005 [US1] Write failing test: assert all widget keys in `_render_market_tab` include `signal_slug` so the same tier slug under different signal tabs produces unique keys in `tests/test_tab_hierarchy.py`

### Implementation for User Story 1

- [x] T006 [US1] Replace outer `st.tabs(tier_labels)` with `st.tabs(["Buy", "Watchlist", "My Holdings"])` in `_render_market_tab` in `marketpulse/ui/dashboard.py` and add `with buy_tab:`, `with watchlist_tab:`, `with holdings_tab:` context blocks
- [x] T007 [US1] Implement Buy tab body in `marketpulse/ui/dashboard.py`: inside `with buy_tab:`, set `signal_slug="buy"`, add `st.segmented_control(tier_labels, key=f"tier_{market}_buy")`, derive `tier_label` (default to first if None), derive `slug`, update all keys: `fetching_{market}_buy_{slug}`, `btn_tier_buy_{market}_buy_{slug}`, `tier_buy_{market}_buy_{slug}`, `key_prefix=f"buy_{tier_label}"`
- [x] T008 [US1] Implement Watchlist tab body in `marketpulse/ui/dashboard.py`: inside `with watchlist_tab:`, `signal_slug="watchlist"`, add `st.segmented_control(tier_labels, key=f"tier_{market}_watchlist")`, derive tier, filter `tier_rows` by `read_watchlist(market)`, render list or empty caption
- [x] T009 [US1] Implement My Holdings tab body in `marketpulse/ui/dashboard.py`: inside `with holdings_tab:`, `signal_slug="my_holdings"`, add `st.segmented_control(tier_labels, key=f"tier_{market}_my_holdings")`, derive tier, filter `tier_rows` by `read_holdings(market)`, render list or empty caption
- [x] T010 [US1] Update `render_stock_detail` call in `marketpulse/ui/dashboard.py` to pass `key=f"{signal_slug}_{slug}"` instead of `key=slug`, preventing duplicate add/remove button keys when the same stock appears across signal tabs
- [x] T011 [US1] Update `_refresh_market` session-state cleanup loop in `marketpulse/ui/dashboard.py` to delete keys matching new formats: `tier_buy_{market}_{signal_slug}_{tier_slug}` and `fetching_{market}_{signal_slug}_{tier_slug}` for all signal slugs and tier slugs

**Checkpoint**: US1 + US2 both done. App shows inverted hierarchy with correct visual styles.

---

## Phase 4: User Story 2 — Visual Design Swapped (Priority: P2)

**Goal**: Verify the outer row uses the bold tab style (previously applied to cap tiers) and the inner row uses the compact segmented-control style (previously applied to Buy/Watchlist/Holdings). No new code needed — the component switch in Phase 3 achieves this automatically.

**Independent Test**: Open the app. The outer Buy/Watchlist/My Holdings row is visually dominant (bold, large tabs). The inner cap tier row is visually subordinate (compact, pill-style).

### Tests for User Story 2 ⚠️ Write FIRST — must FAIL before implementation

> **Note**: T002 (outer is `st.tabs()`) and T004 (inner is `st.segmented_control()`) from Phase 3 already cover the component-type checks required by US2. Add verification-level tests below only if US2 needs additional assertions beyond Phase 3 tests.

- [x] T012 [US2] Write test: assert no CSS override is applied to signal tabs (visual style comes from component choice, not manual override) — inspect `marketpulse/ui/theme.py` source for absence of signal-specific tab overrides in `tests/test_tab_hierarchy.py`

### Implementation for User Story 2

*(No code changes needed — automatically achieved by Phase 3's component swap. `st.tabs()` inherits bold styling; `st.segmented_control()` inherits compact styling.)*

**Checkpoint**: All user stories complete.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Regression testing and manual validation

- [x] T013 Run full test suite and confirm all tests pass: `PYTHONPATH=/Users/pallabi/personal/stock-market .venv/bin/pytest tests/ -v`
- [x] T014 [P] Verify app UI manually per `specs/007-swap-tab-hierarchy/quickstart.md`: outer bold tabs, inner compact tiers, all existing features (refresh, detail panel, add/remove watchlist/holdings) working

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 2)**: Must complete before Phase 3 — T001 informs all key name references
- **Phase 3 (US1)**: Tests (T002–T005) must FAIL before implementing T006–T011
- **Phase 4 (US2)**: Can start after T006 exists (test T012 reads theme.py, not dashboard.py) — but logically follows Phase 3
- **Polish (Phase 5)**: Requires all implementation tasks (T006–T011) complete

### Within Phase 3

```
T001 → T002, T003, T004, T005 (write tests first, verify failure)
     → T006 (outer tab restructure)
     → T007 (Buy tab — depends on T006)
     → T008 (Watchlist tab — depends on T006)
     → T009 (My Holdings tab — depends on T006)
     → T010 (render_stock_detail key — depends on T006)
     → T011 (refresh cleanup — depends on T006)
```

T007, T008, T009 can run in parallel once T006 is done (each is a separate `with` block).

T010 and T011 can run in parallel with T007/T008/T009 if editing different line ranges.

---

## Parallel Execution

```bash
# After T006 (outer tab restructure), run simultaneously:
Task T007: Implement Buy tab body
Task T008: Implement Watchlist tab body
Task T009: Implement My Holdings tab body
Task T010: Fix render_stock_detail key
Task T011: Fix _refresh_market cleanup
```

---

## Implementation Strategy

### MVP (US1 Only)

1. T001: Read current code
2. T002–T005: Write failing tests
3. T006: Replace outer tabs
4. T007–T009: Implement each signal tab
5. T010–T011: Fix keys
6. T013: Run tests — must all pass
7. **VALIDATE**: US1 + US2 both delivered (visual design is automatic)

### Key Naming Reference (from contracts/ui-contracts.md)

| Widget | New key format |
|--------|---------------|
| Tier segmented control | `tier_{market}_{signal_slug}` |
| Fetching flag | `fetching_{market}_{signal_slug}_{tier_slug}` |
| Refresh button | `btn_tier_buy_{market}_{signal_slug}_{tier_slug}` |
| Cached BUY rows | `tier_buy_{market}_{signal_slug}_{tier_slug}` |
| Stock table key_prefix | `f"{signal_slug}_{tier_label}"` |
| Detail panel buttons | passed via `key=f"{signal_slug}_{slug}"` |

`signal_slug` values: Buy→`buy`, Watchlist→`watchlist`, My Holdings→`my_holdings`

---

## Notes

- [P] tasks = different files or independent line ranges, no unresolved dependencies
- TDD is mandatory (Constitution Principle III): tests T002–T005 MUST fail before T006–T011
- US2 is achieved automatically by US1's component swap — no separate implementation
- `render_stock_detail(symbol, market, key)` — the `key` param must include `signal_slug` to prevent `StreamlitDuplicateElementKey` when the same stock appears in multiple signal tabs
- No DB schema changes, no new modules, no new Python dependencies
