# Research: Company Name in Stock Tables

**Branch**: `011-company-name-tables` | **Phase**: 0

## Root Cause

### Decision: Fix `read_signals` to JOIN the `stocks` table
**Rationale**: `_build_df` in `stock_list.py` already has a "Company" column and reads `r.get("company_name")`, but `read_signals` only joins `signals` with `price_snapshots`. It never touches the `stocks` table, so `company_name` is always absent from the returned dicts and the column is always blank.

The fix is a one-line change to the SQL query in `read_signals`:

```sql
-- Before
SELECT s.*, p.current_price, p.last_updated
FROM signals s
LEFT JOIN price_snapshots p ON s.symbol = p.symbol AND s.market = p.market
WHERE s.market = ?

-- After
SELECT s.*, p.current_price, p.last_updated, st.company_name
FROM signals s
LEFT JOIN price_snapshots p ON s.symbol = p.symbol AND s.market = p.market
LEFT JOIN stocks st ON s.symbol = st.symbol AND s.market = st.market
WHERE s.market = ?
```

**Alternatives considered**:
- Fetch company name separately per-symbol — rejected; extra N queries and unnecessary complexity
- Store company_name in the signals table — rejected; redundant denormalisation

---

## Explore Tab (US2)

### Decision: No change required for Explore search results
**Rationale**: `search_stocks_live` in `cache.py` (lines ~325–403) already returns rows with `company_name` populated from the universe index. The Explore results table already shows company names correctly. US2 is therefore a verify-only task.

---

## Fallback for Missing Company Names

### Decision: Use ticker symbol as fallback in `_build_df`
**Rationale**: `_build_df` currently uses `r.get("company_name") or ""`. The spec requires the ticker as fallback instead of blank. Change to `r.get("company_name") or r["symbol"]`.

---

## No Schema Changes

No tables are added or altered. The fix is read-path only.

---

## Test Strategy

Two targeted tests:
1. Assert `read_signals` returns rows with non-empty `company_name` for stocks that exist in the `stocks` table
2. Assert `_build_df` uses ticker as fallback when `company_name` is absent from a row
