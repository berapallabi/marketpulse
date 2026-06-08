# Research: Swap Tab Hierarchy

## Summary

No external research needed. All decisions are grounded in direct code inspection of `dashboard.py` and `theme.py`.

---

## Decision 1: Component Swap Is Automatic

**Decision**: Switching Buy/Watchlist/My Holdings from `st.segmented_control()` to `st.tabs()`, and cap tiers from `st.tabs()` to `st.segmented_control()`, automatically achieves the design swap requested. No manual CSS changes are required for the component styles themselves.

**Rationale**: Streamlit applies its component styling per-widget type. The existing CSS in `theme.py` targets `.stTabs [data-baseweb="tab-list"]` which applies to all `st.tabs()` instances. When Buy/Watchlist/Holdings becomes a `st.tabs()`, it inherits the bold tab styling. When cap tiers become `st.segmented_control()`, they inherit the compact pill styling automatically.

**Alternatives considered**:
- Manual CSS overrides to keep old components but restyle them: rejected — fragile against Streamlit version updates and harder to maintain.

---

## Decision 2: Signal Choice Is Implicit in Tab Context

**Decision**: After the swap, the "signal choice" (Buy / Watchlist / My Holdings) is no longer read from a widget's session state key. Instead, the code for each signal tab lives inside a `with buy_tab:` / `with watchlist_tab:` / `with holdings_tab:` block, making the choice implicit and the per-tab conditional (`if signal_choice == "Buy"`) unnecessary.

**Rationale**: `st.tabs()` renders each tab's content inside a `with tab:` context manager. The signal is determined by which context the code runs in — no need to store or read it from session state. This simplifies the branching logic.

---

## Decision 3: Key Namespacing Requires Signal Slug

**Decision**: All Streamlit widget keys and session-state keys that currently use `{market}_{tier_slug}` must be extended to `{market}_{signal_slug}_{tier_slug}` (or `{market}_{signal_slug}` for tier-level state). This avoids duplicate-key errors when the same tier appears under multiple signal tabs.

**Why this is required**: After the swap, Large Cap appears as an inner tier under Buy, Watchlist, AND My Holdings — all within the same Streamlit render cycle. If the table, buttons, and session-state keys all use only the tier slug, three copies of the same widget key appear per render cycle and Streamlit raises `StreamlitDuplicateElementKey`.

**Affected keys**:
- `signal_{market}_{slug}` → removed (no longer a widget; signal is a tab)
- Tier segmented control: new key `tier_{market}_{signal_slug}`
- `fetching_{market}_{slug}` → `fetching_{market}_{signal_slug}_{slug}`
- `btn_tier_buy_{market}_{slug}` → `btn_tier_buy_{market}_{signal_slug}_{slug}`
- `tier_buy_{market}_{slug}` → `tier_buy_{market}_{signal_slug}_{slug}`
- `_prev_rows_{market}_{slug}_{filter}` → namespaced via `key_prefix` passed to `render_stock_list`
- `render_stock_detail` `key` arg → `f"{signal_slug}_{slug}"` to keep add/remove button keys unique

---

## Decision 4: Detail Panel Stays Shared Per Market

**Decision**: `selected_{market}` session state remains a single value per market, shared across all signal tabs and all tiers. Clicking a stock in any tab sets the same key; the detail panel renders in whichever tab the user is currently viewing.

**Rationale**: The detail panel is displayed inside the active tier block, next to the table. Because Streamlit re-renders the whole page on each interaction, the detail panel naturally appears within the currently active outer tab. No change needed.

---

## Decision 5: Refresh Scope Stays Per-Tier

**Decision**: The refresh button remains inside each tier's content area (inside the segmented-control-selected tier). It still triggers `_refresh_tier_buy(market, tier_label)` — no change to the refresh function itself.

**Rationale**: Refreshing per-tier keeps the fetch scope narrow. The outer signal tab context doesn't affect what data needs refreshing — only the market and tier do.

---

## Decision 6: CSS — Nested Tab Selector Stays Valid

**Decision**: The existing `.stTabs .stTabs [data-testid="baseButton-secondary"] p` CSS rule (small font for the refresh button) remains correct after the swap. After the swap, the refresh button lives inside the Buy/Watchlist/Holdings tab (`.stTabs`) which is inside the India/US market tab (`.stTabs`), so the double-nested selector still matches.

**Rationale**: The nesting depth is unchanged — the button is still two tab levels deep. No CSS changes required.
