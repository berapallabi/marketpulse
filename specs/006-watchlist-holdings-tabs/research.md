# Research: Watchlist & My Holdings Tabs

## Summary

No external research or clarification was required. All decisions are grounded in the existing codebase patterns. This document records the design decisions reached by direct code inspection.

---

## Decision 1: Storage for Watchlist and My Holdings

**Decision**: Two new SQLite tables (`watchlist`, `holdings`) added via `init_db()` in `marketpulse/storage/cache.py`.

**Rationale**: The app already uses SQLite via `cache.py` for all persistent state (signals, snapshots, summaries). Adding tables there is the zero-dependency path that matches the existing `_upsert` / `read_*` / `write_*` pattern. No new library, no migration tool, no schema versioning overhead.

**Alternatives considered**:
- Session state only (`st.session_state`): rejected — does not survive page reloads (FR-008).
- Separate JSON file: rejected — introduces a second persistence mechanism with no benefit.
- New database file: rejected — splits state unnecessarily.

---

## Decision 2: Scope of Watchlist/Holdings — Per-Market

**Decision**: Both tables use `(symbol, market)` as the composite primary key, making each list market-scoped (India ≠ US).

**Rationale**: Symbols can overlap between markets (e.g., INFY.NS vs INFY on NYSE). Per-market scoping avoids false matches and is consistent with how all other tables in the schema work — every table keys on `(symbol, market)`.

**Alternatives considered**:
- Global list: rejected — symbol collision risk, inconsistent with existing data model.

---

## Decision 3: Signal Filter Tab Replacement

**Decision**: Replace `st.segmented_control` options `["All", "BUY", "SELL", "HOLD"]` with `["Buy", "Watchlist", "My Holdings"]` at `marketpulse/ui/dashboard.py:255–261`.

**Rationale**: The segmented control is already the right component for this three-way choice. Only the options list and the downstream conditional branches change — the component, its key, and its styling are untouched (FR-012).

**Alternatives considered**:
- Switch to `st.tabs`: rejected — `st.tabs` cannot be nested inside an existing `st.tabs` context without layout issues; `st.segmented_control` is already working and fits the three-option case.

---

## Decision 4: Add/Remove Entry Point

**Decision**: Add/remove buttons live in the stock detail panel (`marketpulse/ui/stock_detail.py`). No row-level buttons in the stock list table.

**Rationale**: The detail panel is already the place where users take actions on a specific stock (it shows full signal context). Row-level buttons would require changes to `stock_list.py` and introduce layout complexity. The detail panel is always visible when a stock is selected, so discoverability is not a concern.

**Alternatives considered**:
- Row-level inline buttons: deferred — higher implementation complexity, more disruptive to the existing table layout.

---

## Decision 5: Display of Watchlist/Holdings Rows

**Decision**: Watchlist and My Holdings tabs read the full signals list for the market, then filter to symbols found in the respective SQLite table. The same `render_stock_list` function is reused — no new display component.

**Rationale**: Signal data (price, confidence, technical score) is already in the `signals` table joined with `price_snapshots`. Filtering the existing row list by watchlist/holdings symbols costs nothing and reuses all existing display logic (columns, colours, click handler).

**Alternatives considered**:
- Separate data fetch for watchlist/holdings: rejected — unnecessary, signals are already loaded for the tier.
