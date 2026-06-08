# UI Contracts: Swap Tab Hierarchy

## Outer Signal Tab Row

Replaces the current `st.segmented_control` signal filter. Now a `st.tabs()` component.

| Property | Value |
|----------|-------|
| Component | `st.tabs(["Buy", "Watchlist", "My Holdings"])` |
| Tab labels | `["Buy", "Watchlist", "My Holdings"]` (exact, in this order) |
| Default | First tab (Buy) — Streamlit default for `st.tabs()` |
| Nesting | Inside the India/US market tab |

---

## Inner Cap Tier Row

Replaces the current `st.tabs(tier_labels)` cap tier row. Now a `st.segmented_control` component.

| Property | Value |
|----------|-------|
| Component | `st.segmented_control` |
| Options | `INDIA_TIER_ORDER` or `US_TIER_ORDER` per market |
| Default | First tier in the market's order |
| Key format | `tier_{market}_{signal_slug}` |
| Label | collapsed |
| Nesting | Inside the Buy / Watchlist / My Holdings tab |

---

## Widget Key Contracts (updated)

| Widget | Old key | New key |
|--------|---------|---------|
| Tier segmented control | `signal_{market}_{tier_slug}` | `tier_{market}_{signal_slug}` |
| Fetching flag | `fetching_{market}_{tier_slug}` | `fetching_{market}_{signal_slug}_{tier_slug}` |
| Refresh button | `btn_tier_buy_{market}_{tier_slug}` | `btn_tier_buy_{market}_{signal_slug}_{tier_slug}` |
| Tier BUY rows (session) | `tier_buy_{market}_{tier_slug}` | `tier_buy_{market}_{signal_slug}_{tier_slug}` |
| Stock table / prev-rows | uses `key_prefix=tier_label` | uses `key_prefix=f"{signal_slug}_{tier_label}"` |
| Detail panel buttons | `wl_{symbol}_{market}_{tier_slug}` | `wl_{symbol}_{market}_{signal_slug}_{tier_slug}` |

`signal_slug` is the lowercase-underscored outer tab label:
- Buy → `buy`
- Watchlist → `watchlist`
- My Holdings → `my_holdings`

---

## Tab Rendering Contract

### Buy Tab

```
with buy_tab:
    tier = st.segmented_control(tier_labels, key=f"tier_{market}_buy")
    tier_rows = [r for r in signal_rows if r["cap_tier"] == tier]
    # ... refresh button (keyed with "buy_{tier_slug}")
    # ... render BUY-filtered stock list
    # ... detail panel
```

### Watchlist Tab

```
with watchlist_tab:
    tier = st.segmented_control(tier_labels, key=f"tier_{market}_watchlist")
    tier_rows = [r for r in signal_rows if r["cap_tier"] == tier]
    watchlist_symbols = set(cache.read_watchlist(market))
    filtered = [r for r in tier_rows if r["symbol"] in watchlist_symbols]
    # ... render filtered list or empty-state caption
    # ... detail panel
```

### My Holdings Tab

```
with holdings_tab:
    tier = st.segmented_control(tier_labels, key=f"tier_{market}_my_holdings")
    tier_rows = [r for r in signal_rows if r["cap_tier"] == tier]
    holdings_symbols = set(cache.read_holdings(market))
    filtered = [r for r in tier_rows if r["symbol"] in holdings_symbols]
    # ... render filtered list or empty-state caption
    # ... detail panel
```

---

## CSS Contract

No new CSS rules required. The design swap is achieved purely by switching components:

- `st.tabs()` for Buy/Watchlist/My Holdings → inherits existing `.stTabs` bold tab styling
- `st.segmented_control()` for cap tiers → inherits Streamlit's built-in compact pill styling

The existing rule `.stTabs .stTabs [data-testid="baseButton-secondary"] p` continues to correctly target the refresh button (still two tab levels deep after the swap).
