# UI Contracts: Watchlist & My Holdings Tabs

## Signal Filter Tab Contract

The segmented control within each cap tier renders exactly three options in fixed order.

| Property | Value |
|----------|-------|
| Component | `st.segmented_control` |
| Options | `["Buy", "Watchlist", "My Holdings"]` |
| Default | `"Buy"` |
| Key format | `signal_{market}_{slug}` (unchanged) |
| Label | collapsed (unchanged) |

**Removed options**: `"All"`, `"SELL"`, `"HOLD"` — must not appear.

---

## Tab Behaviour Contracts

### Buy Tab

| Property | Contract |
|----------|----------|
| Data source | `tier_buy_rows` from `st.session_state` if available; falls back to `tier_rows` filtered to `signal_type == "BUY"` |
| Empty state | `st.caption("No BUY signals found for this tier.")` (existing behaviour, unchanged) |
| Renderer | `render_stock_list(data, market, filter_signal="BUY", key_prefix=tier_label)` |

### Watchlist Tab

| Property | Contract |
|----------|----------|
| Data source | `read_watchlist(market)` → set of symbols; filter `tier_rows` where `row["symbol"] in watchlist_symbols` |
| Empty state | `st.caption("No stocks in your watchlist yet.")` |
| Renderer | `render_stock_list(filtered_rows, market, filter_signal="ALL", key_prefix=tier_label)` |

### My Holdings Tab

| Property | Contract |
|----------|----------|
| Data source | `read_holdings(market)` → set of symbols; filter `tier_rows` where `row["symbol"] in holdings_symbols` |
| Empty state | `st.caption("No holdings added yet.")` |
| Renderer | `render_stock_list(filtered_rows, market, filter_signal="ALL", key_prefix=tier_label)` |

---

## Stock Detail Panel Contract (Add/Remove Actions)

The detail panel (`marketpulse/ui/stock_detail.py`) exposes two action rows when a stock is selected.

### Watchlist Action

| State | Button label | Action on click |
|-------|-------------|-----------------|
| Not in watchlist | `"+ Add to Watchlist"` | `add_to_watchlist(symbol, market)` then `st.rerun()` |
| In watchlist | `"✓ Remove from Watchlist"` | `remove_from_watchlist(symbol, market)` then `st.rerun()` |

### Holdings Action

| State | Button label | Action on click |
|-------|-------------|-----------------|
| Not in holdings | `"+ Add to Holdings"` | `add_to_holdings(symbol, market)` then `st.rerun()` |
| In holdings | `"✓ Remove from Holdings"` | `remove_from_holdings(symbol, market)` then `st.rerun()` |

**Membership check**: Performed by calling `read_watchlist(market)` / `read_holdings(market)` at render time, checking if `symbol` is in the returned list.

**Button type**: `secondary` to match existing refresh button style.

---

## Storage Function Contracts

### add_to_watchlist / add_to_holdings

```
Input:  symbol: str, market: Literal["IN", "US"], db_path: Path | None = None
Effect: Upsert (symbol, market, added_at=now_utc_iso) into watchlist/holdings table
Output: None
Error:  None raised — idempotent on duplicate
```

### remove_from_watchlist / remove_from_holdings

```
Input:  symbol: str, market: Literal["IN", "US"], db_path: Path | None = None
Effect: DELETE FROM table WHERE symbol=? AND market=?
Output: None
Error:  None raised — no-op if not found
```

### read_watchlist / read_holdings

```
Input:  market: Literal["IN", "US"], db_path: Path | None = None
Output: list[str]  — list of symbol strings for the given market
Error:  Returns [] if DB does not exist
```
