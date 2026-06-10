# Implementation Plan: Explore Tab

**Branch**: `009-explore-tab` | **Date**: 2026-06-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/008-explore-tab/spec.md`

## Summary

Add an "Explore" tab alongside Buy / Watchlist / My Holdings that lets users search the cached stock universe by name or symbol, view the full detail panel for any match, and add stocks to watchlist or holdings. No tier selector, no refresh button. Reads from the existing SQLite cache; no new data fetching.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Streamlit (UI), SQLite via stdlib `sqlite3`

**Storage**: Existing `~/.marketpulse/cache.db` — `stocks` table (symbol, company_name, market) is the search source; `signals` and `price_snapshots` joined for signal/price data. No schema changes.

**Testing**: pytest — `tests/` directory, run via `.venv/bin/pytest`

**Target Platform**: Local only, `localhost:8501`

**Project Type**: Streamlit dashboard app

**Performance Goals**: Search results appear on each keystroke — SQLite LIKE query over ~100-150 rows is effectively instant locally.

**Constraints**: No new Python dependencies. No DB schema changes. No data fetching from Explore tab. Minimum 2-character query before results show.

**Scale/Scope**: UI addition to one function (`_render_market_tab`) + one new cache function. Affects `dashboard.py` and `cache.py` only.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Accuracy | PASS | Reads from cache only; missing data shown as "N/A", never fabricated |
| II. Risk Transparency | PASS | Detail panel already carries the informational-only disclaimer |
| III. Test-First | REQUIRED | Tests for search logic and tab structure written before implementation |
| IV. YAGNI | PASS | No new abstractions; reuses `render_stock_list` and `render_stock_detail` directly |
| V. Dual-Market Parity | PASS | `search_stocks` and `_render_explore_tab` are market-parameterised; IN and US covered equally |

**Gate result**: PASS. Test-first (Principle III) drives task ordering.

## Project Structure

### Documentation (this feature)

```text
specs/008-explore-tab/
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
├── storage/
│   └── cache.py         # ADD: search_stocks(query, market, db_path) → list[dict]
└── ui/
    └── dashboard.py     # ADD: _render_explore_tab(market); extend st.tabs call

tests/
└── test_explore_tab.py  # NEW: search logic + tab structure tests
```

**Structure Decision**: Single-file additions. No new modules needed; search is a cache read, explore rendering is a dashboard function matching existing patterns.

## Phase 0: Research

### Decision: Search Implementation

**Decision**: SQLite `LIKE` query on the `stocks` table, LEFT JOINed with `signals` and `price_snapshots`.

**Rationale**: The `stocks` table is populated by `write_quotes` on every tier refresh and contains `symbol`, `company_name`, and `market` — exactly the search fields. A LEFT JOIN to `signals` and `price_snapshots` produces result rows in the same shape as `read_signals`, enabling direct reuse of `render_stock_list`. Pattern: `WHERE UPPER(symbol) LIKE UPPER(?) OR UPPER(company_name) LIKE UPPER(?)` with `%query%` wrapping.

**Alternatives considered**:
- In-memory filter on `read_signals` results: rejected because stocks with no signals yet (never refreshed in any tier) would be invisible.
- Full-text search extension: rejected as overkill for 50-100 rows; `LIKE` is sufficient and requires no new dependency.

### Decision: Result Row Shape

**Decision**: Search results use the same dict shape as `read_signals` rows (`symbol`, `market`, `company_name`, `signal_type`, `confidence_score`, `current_price`, `last_updated`, etc.), with `None` for any fields not yet populated for a given stock.

**Rationale**: `render_stock_list` and `render_stock_detail` both accept this shape. No adapter layer needed.

**Alternatives considered**: A separate `SearchResult` dataclass — rejected (YAGNI; dict shape is sufficient and consistent with the rest of the UI layer).

### Decision: Session State Keys

**Decision**: `explore_query_{market}` for the search input value and `selected_explore_{market}` for the selected symbol. These are distinct from `selected_{market}` used by the other tabs to avoid cross-tab selection bleed.

**Rationale**: If the user selects RELIANCE in Explore and then opens the Buy tab, the Buy tab should not pre-select RELIANCE. Independent selection state per tab context.

## Phase 1: Design & Contracts

### data-model.md

No new entities. The Explore tab reads two existing entities:

- **Stock** (`stocks` table): `symbol`, `company_name`, `market`, `currency`. Populated by `write_quotes`. This is the search source.
- **Signal** (`signals` table): `signal_type`, `confidence_score`, `technical_score`, `sentiment_score`, `cap_tier`, `generated_at`. LEFT JOINed — may be absent for stocks not yet refreshed.
- **PriceSnapshot** (`price_snapshots` table): `current_price`, `last_updated`. LEFT JOINed — may be absent.

No schema changes. No new tables.

### contracts/ui-contracts.md

See [contracts/ui-contracts.md](contracts/ui-contracts.md).

### quickstart.md

See [quickstart.md](quickstart.md).

## Implementation Phases

### Phase A: Tests (test-first)

Write `tests/test_explore_tab.py` with failing tests covering:
- `search_stocks` returns results matching symbol prefix
- `search_stocks` returns results matching company name substring
- `search_stocks` is case-insensitive
- `search_stocks` returns empty list when no match
- `search_stocks` returns empty list when query is shorter than 2 characters
- `_render_market_tab` source contains `"Explore"` in the `st.tabs` call
- Existing tabs (Buy, Watchlist, My Holdings) still present in source

### Phase B: Add `search_stocks` to `cache.py`

New function:
```python
def search_stocks(query: str, market: str, db_path: Path | None = None) -> list[dict]:
```
- Returns `[]` if `len(query) < 2` or DB does not exist
- SQLite LEFT JOIN of `stocks`, `signals`, `price_snapshots`
- Case-insensitive `LIKE` on both `symbol` and `company_name`
- Returns rows as dicts with the same keys as `read_signals` rows plus `company_name`

### Phase C: Add `_render_explore_tab` to `dashboard.py`

New private function `_render_explore_tab(market: str)`:
- `st.text_input` for query, keyed as `explore_query_{market}`
- If query length < 2: show "Enter at least 2 characters to search"
- Else: call `cache.search_stocks(query, market)` and render results
- Two-column layout: left for result list (`render_stock_list` with `filter_signal="ALL"`), right for detail panel (`render_stock_detail`)
- Selection stored in `st.session_state[f"selected_explore_{market}"]`

### Phase D: Extend `st.tabs` in `_render_market_tab`

Change:
```python
buy_tab, watchlist_tab, holdings_tab = st.tabs(["Buy", "Watchlist", "My Holdings"])
```
to:
```python
buy_tab, watchlist_tab, holdings_tab, explore_tab = st.tabs(["Buy", "Watchlist", "My Holdings", "Explore"])
```
Add `with explore_tab: _render_explore_tab(market)`.

### Phase E: Run tests

`pytest tests/` — all tests including `test_explore_tab.py` must pass.

## Complexity Tracking

No constitution violations. No complexity tracking required.
