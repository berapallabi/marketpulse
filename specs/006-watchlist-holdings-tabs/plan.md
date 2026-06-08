# Implementation Plan: Watchlist & My Holdings Tabs

**Branch**: `007-watchlist-holdings-tabs` | **Date**: 2026-06-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/006-watchlist-holdings-tabs/spec.md`

## Summary

Replace the four-option signal filter (All/BUY/SELL/HOLD) with a three-tab layout (Buy/Watchlist/My Holdings) within each market cap tier. Add two new SQLite tables (`watchlist`, `holdings`) with add/remove/read storage functions. Expose add/remove actions in the stock detail panel. The Buy tab retains existing BUY signal behaviour exactly; Watchlist and My Holdings filter the existing tier rows by symbols stored in the respective table.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Streamlit (UI), pandas (data), SQLite `sqlite3` (storage)

**Storage**: SQLite at `DB_PATH` (configured in `marketpulse/config.py`). Two new tables: `watchlist`, `holdings`.

**Testing**: pytest — `tests/` directory

**Target Platform**: Local only, `localhost:8501`

**Project Type**: Streamlit dashboard app

**Performance Goals**: Standard local-app responsiveness — tab switch renders within one rerun cycle

**Constraints**: No new Python dependencies. Tables added non-destructively (`CREATE TABLE IF NOT EXISTS`).

**Scale/Scope**: Single-user local app, two markets (IN/US), up to ~150 stocks per market

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Accuracy | PASS | Watchlist/Holdings display live signal data from existing pipeline — no fabricated values |
| II. Risk Transparency | PASS | No new signal or recommendation surface; existing risk context unchanged |
| III. Test-First | REQUIRED | Tests for storage functions and tab behaviour must be written before implementation |
| IV. YAGNI | PASS | Exactly the requested scope — no extra fields, no sorting/filtering on watchlist, no quantity tracking |
| V. Dual-Market Parity | PASS | Both IN and US markets receive the same three tabs; storage is per-market |

**Gate result**: PASS — no violations. Test-first principle (III) is non-negotiable and drives task ordering.

## Project Structure

### Documentation (this feature)

```text
specs/006-watchlist-holdings-tabs/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── ui-contracts.md  # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
marketpulse/
├── storage/
│   └── cache.py         # ADD: watchlist + holdings tables in init_db(); 6 new functions
├── ui/
│   ├── dashboard.py     # MODIFY: segmented_control options + 2 new tab branches
│   └── stock_detail.py  # MODIFY: add/remove buttons for watchlist and holdings

tests/
├── test_watchlist_holdings.py   # NEW: storage layer tests
└── test_dashboard_tabs.py       # NEW: UI tab contract tests
```

**Structure Decision**: Single-project layout. All changes are confined to `marketpulse/storage/cache.py`, `marketpulse/ui/dashboard.py`, and `marketpulse/ui/stock_detail.py`. Two new test files cover the two layers.

## Implementation Phases

### Phase A: Storage Layer (test-first)

1. Write failing tests in `tests/test_watchlist_holdings.py`:
   - `add_to_watchlist` inserts a row
   - `read_watchlist` returns only symbols for the given market
   - Duplicate add does not create a second row
   - `remove_from_watchlist` deletes the row
   - `remove_from_watchlist` on missing symbol is a no-op
   - Same suite mirrored for `holdings`
   - Cross-market isolation: IN watchlist does not appear in US watchlist

2. Add `watchlist` and `holdings` tables to `init_db()` in `cache.py`.

3. Implement `add_to_watchlist`, `remove_from_watchlist`, `read_watchlist`, `add_to_holdings`, `remove_from_holdings`, `read_holdings` in `cache.py`.

4. Run tests — all must pass.

### Phase B: UI — Detail Panel Actions (test-first)

1. Write failing tests in `tests/test_dashboard_tabs.py` covering:
   - Detail panel renders "Add to Watchlist" when symbol not in watchlist
   - Detail panel renders "Remove from Watchlist" when symbol is in watchlist
   - Same for Holdings

2. Update `stock_detail.py` to import storage functions and render add/remove buttons.

3. Run tests — all must pass.

### Phase C: UI — Signal Filter Tabs (test-first)

1. Extend `tests/test_dashboard_tabs.py`:
   - Segmented control options are exactly `["Buy", "Watchlist", "My Holdings"]`
   - "All", "SELL", "HOLD" options are absent
   - Buy tab shows BUY-signal rows only (regression against existing behaviour)
   - Watchlist tab shows only symbols present in the watchlist table
   - My Holdings tab shows only symbols present in the holdings table
   - Empty-state caption appears when watchlist/holdings is empty

2. Update `dashboard.py`:
   - Change `options=["All", "BUY", "SELL", "HOLD"]` to `["Buy", "Watchlist", "My Holdings"]`
   - Change `default="All"` to `default="Buy"`
   - Replace the three conditional branches (All/SELL/HOLD) with Watchlist and My Holdings branches

3. Run full test suite — no regressions.

## Complexity Tracking

No constitution violations. No complexity tracking required.
