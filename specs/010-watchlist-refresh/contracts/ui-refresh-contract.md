# UI Contract: Watchlist & Holdings Refresh Button

## Overview

Each tier tab within the Watchlist and My Holdings sections must expose a refresh button that follows the same behavioural contract as the existing BUY tab refresh button.

---

## Refresh Button States

### State 1 — Idle (has stocks in section + tier)

| Property | Value |
|----------|-------|
| Visible | Yes |
| Enabled | Yes |
| Label | `🔄  Refresh  ·  last at HH:MM AM/PM IST` (if previously refreshed) OR `🔄  Refresh` |
| Tooltip | — |
| Action on click | Set `fetching_{market}_{section}_{tier_slug} = True`, call `st.rerun()` |

### State 2 — In Progress (fetching flag is True)

| Property | Value |
|----------|-------|
| Visible | Yes |
| Enabled | No (disabled) |
| Label | `⏳  Refreshing…` |
| Tooltip | — |
| Action | Call `_refresh_section(market, section, tier_label)`, then set flag = False, call `st.rerun()` |

### State 3 — Section empty (no stocks in this tier)

| Property | Value |
|----------|-------|
| Visible | No (button not rendered) |
| Enabled | N/A |
| Label | N/A |

---

## Session State Keys

| Key pattern | Type | Lifecycle |
|-------------|------|-----------|
| `fetching_{market}_{section}_{tier_slug}` | `bool` | Set True on click; set False after `_refresh_section` returns |

Where:
- `{market}` = `"IN"` or `"US"`
- `{section}` = `"watchlist"` or `"my_holdings"`
- `{tier_slug}` = tier_label with spaces replaced by `_`, lowercased (e.g., `"large_cap"`)

---

## Layout

```text
filter_col (3/5 width), _ (2/5 width)
  └── seg_col (5/9), btn_col (4/9)  [vertical_alignment="center"]
        ├── segmented_control (tier selector)
        └── refresh button (full width, secondary type)

list_col (3/5), detail_col (2/5)
  ├── render_stock_list(...)
  └── render_stock_detail(...)
```

---

## Post-Refresh Side Effects

After `_refresh_section` completes:
1. `st.session_state["selected_{market}"]` is cleared (avoids stale detail panel)
2. `st.session_state` keys matching `_prev_rows_{market}_{section}_{tier_slug}*` are cleared
3. `st.rerun()` is called — next render reads fresh data from `cache.read_signals(market)`

---

## Error Handling

If `fetch_quotes` raises `DataProviderError`, `st.error(...)` is displayed and the function returns without modifying any cache data.

If an individual stock's OHLCV or indicator computation fails, the stock is silently skipped and the remaining stocks proceed normally.
