# Implementation Plan: Swap Tab Hierarchy

**Branch**: `008-swap-tab-hierarchy` | **Date**: 2026-06-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/007-swap-tab-hierarchy/spec.md`

## Summary

Invert the two-level tab hierarchy within each market section. Buy/Watchlist/My Holdings moves from a compact `st.segmented_control` (inner) to a bold `st.tabs()` (outer). Cap tiers move from `st.tabs()` (outer) to a compact `st.segmented_control` (inner). The design swap is automatic — switching components achieves the visual change. The main implementation work is restructuring `_render_market_tab` in `dashboard.py` and renaming all session-state and widget keys to incorporate the signal slug.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Streamlit (UI), `st.tabs()`, `st.segmented_control()`

**Storage**: No changes — SQLite schema and cache functions untouched

**Testing**: pytest — `tests/` directory

**Target Platform**: Local only, `localhost:8501`

**Project Type**: Streamlit dashboard app

**Performance Goals**: Unchanged — standard local-app responsiveness

**Constraints**: No new Python dependencies. No DB schema changes.

**Scale/Scope**: UI-only refactor; affects `dashboard.py` and `stock_detail.py` (key scoping)

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Accuracy | PASS | No data pipeline changes; display only |
| II. Risk Transparency | PASS | No signal or recommendation surface changes |
| III. Test-First | REQUIRED | Tests for new tab structure written before restructuring |
| IV. YAGNI | PASS | Pure UI inversion — no new features added |
| V. Dual-Market Parity | PASS | Both IN and US markets receive the same structural change |

**Gate result**: PASS. Test-first (Principle III) drives task ordering.

## Project Structure

### Documentation (this feature)

```text
specs/007-swap-tab-hierarchy/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # N/A — no data model changes
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── ui-contracts.md  # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
marketpulse/
└── ui/
    ├── dashboard.py     # PRIMARY CHANGE: restructure _render_market_tab
    └── stock_detail.py  # KEY SCOPING: key arg receives signal_slug prefix

tests/
└── test_tab_hierarchy.py  # NEW: tab structure and key uniqueness tests
```

**Structure Decision**: Single-file UI refactor. No new modules needed.

## Key Structural Change

### Before (`_render_market_tab`)

```
st.tabs(tier_labels)                     ← outer, bold tab style
  └─ for each tier_tab:
       st.segmented_control(             ← inner, compact style
           ["Buy", "Watchlist", "My Holdings"])
       render content based on signal_choice
```

### After (`_render_market_tab`)

```
st.tabs(["Buy", "Watchlist", "My Holdings"])  ← outer, bold tab style (automatic)
  └─ for each signal_tab (buy / watchlist / holdings):
       st.segmented_control(tier_labels)       ← inner, compact style (automatic)
       render content based on which signal_tab is active
```

## Session-State Key Mapping

| Purpose | Old key | New key |
|---------|---------|---------|
| Tier segmented control | `signal_{market}_{tier_slug}` | `tier_{market}_{signal_slug}` |
| Fetching flag | `fetching_{market}_{tier_slug}` | `fetching_{market}_{signal_slug}_{tier_slug}` |
| Refresh button | `btn_tier_buy_{market}_{tier_slug}` | `btn_tier_buy_{market}_{signal_slug}_{tier_slug}` |
| Cached BUY rows | `tier_buy_{market}_{tier_slug}` | `tier_buy_{market}_{signal_slug}_{tier_slug}` |
| Stock table key prefix | `tier_label` | `f"{signal_slug}_{tier_label}"` |
| Detail panel buttons | `wl/hd_{sym}_{market}_{tier_slug}` | `wl/hd_{sym}_{market}_{signal_slug}_{tier_slug}` |

`signal_slug` values: `buy`, `watchlist`, `my_holdings`

## Implementation Phases

### Phase A: Tests (test-first)

Write `tests/test_tab_hierarchy.py` with failing tests:
- Outer tab source code contains `st.tabs(["Buy", "Watchlist", "My Holdings"])` (not tier labels)
- Inner tier control source code uses `st.segmented_control` with tier labels
- Old outer tier `st.tabs(tier_labels)` call is absent from `_render_market_tab`
- All existing tests still pass (regression gate)

### Phase B: Restructure `_render_market_tab` in `dashboard.py`

1. Replace `st.tabs(tier_labels)` with `st.tabs(["Buy", "Watchlist", "My Holdings"])`
2. Inside each signal tab (`with buy_tab:`, `with watchlist_tab:`, `with holdings_tab:`):
   - Add `st.segmented_control(tier_labels, ...)` keyed as `tier_{market}_{signal_slug}`
   - Derive `tier_label` from the segmented control's value (default to first tier if None)
   - Derive `slug` (tier slug) from `tier_label`
   - Update all widget keys to include `signal_slug`
   - Replace the `if signal_choice == "Buy" / "Watchlist" / "My Holdings"` branching with direct logic per tab context
3. Update `_refresh_market` session-state cleanup to clear the new key format for `tier_buy_*` and `fetching_*`

### Phase C: Update `stock_detail.py` key scoping

The `render_stock_detail` call in `dashboard.py` passes `key=slug` (tier slug) to scope the add/remove button keys. After the swap, the same tier slug appears in three signal tabs simultaneously, causing duplicate key errors. Fix: pass `key=f"{signal_slug}_{slug}"`.

### Phase D: Run tests

`pytest tests/` — all tests including the new `test_tab_hierarchy.py` must pass.

## Complexity Tracking

No constitution violations. No complexity tracking required.
