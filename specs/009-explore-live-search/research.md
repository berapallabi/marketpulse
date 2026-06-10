# Research: Explore Live Search — Any Stock

**Feature**: 009-explore-live-search  
**Date**: 2026-06-10

## Question 1: India universe — how to get Nifty 500 symbols + company names?

**Finding**: nsepython does not expose a Nifty 500 index endpoint. `nse_eq_symbols()` returns ALL NSE-listed equities (~2000+). The Nifty 500 constituent list is published by NSE on its website as a CSV, but scraping it at runtime adds a fragile network dependency.

**Decision**: Hardcode `NIFTY_500_UNIVERSE` as a `dict[str, str]` (symbol → company_name) in `marketpulse/data/universe.py`. Source: NSE public data (current as of 2026-06-10).

**Rationale**: Zero network latency for search. Nifty 500 changes ~2x per year; a hardcoded dict is acceptable for a personal tool. The dict can be refreshed in config updates when the index rebalances.

**Alternatives considered**:
- `nse_eq_symbols()` at startup: provides symbols only (no company names), ~2000 symbols, no filtering to Nifty 500
- NSE CSV scrape at runtime: fragile, adds network dependency, slow first load
- SQLite `symbol_universe` table populated at startup: over-engineered for a personal tool; adds schema migration

---

## Question 2: US universe — how to get S&P 500 symbols + company names?

**Finding**: yfinance has no built-in S&P 500 index function. The standard approach in the Python community is `pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]`, which returns a DataFrame with Symbol and Security columns.

**Decision**: Hardcode `SP500_UNIVERSE` as a `dict[str, str]` (symbol → company_name) in `marketpulse/data/universe.py`. Source: Wikipedia / S&P data (current as of 2026-06-10).

**Rationale**: Same as India — zero latency, no external call, S&P 500 changes ~10-20x per year (manageable for a personal tool). Wikipedia scrapes are fragile (page structure can change).

**Alternatives considered**:
- Wikipedia `pd.read_html()` at runtime: requires network, pandas HTML parsing, fragile to page changes
- Hardcoded symbols only (no company names): can't do name-based search ("Palantir" → PLTR)

---

## Question 3: On-demand price fetch for non-cached stocks

**Finding**: Both existing data providers already support single-symbol fetches:
- `india.fetch_quotes(["BAJAJAUT"])` → calls `nse_eq("BAJAJAUT")`, returns StockQuote with company_name, current_price, OHLCV fields
- `us.fetch_quotes(["PLTR"])` → calls `yf.Ticker("PLTR").info`, returns StockQuote
- `india.fetch_ohlcv_history("BAJAJAUT")` → `yf.Ticker("BAJAJAUT.NS").history(...)`
- `us.fetch_ohlcv_history("PLTR")` → `yf.Ticker("PLTR").history(...)`

**Decision**: Reuse existing `fetch_quotes` and `fetch_ohlcv_history` from `marketpulse/data/india.py` and `marketpulse/data/us.py` directly. No new data functions needed.

**Rationale**: Zero new code in the data layer. The existing functions already handle errors gracefully (return None on failure, raise DataProviderError only if ALL symbols fail).

---

## Question 4: Where to show the live-fetched current price in the detail panel?

**Finding**: `render_stock_detail` in `marketpulse/ui/stock_detail.py` currently takes `(symbol, market, technical, news_items, ohlcv, key)`. The price is displayed from either `technical` or `ohlcv` data. Non-cached stocks have no `technical` data and no pre-fetched `ohlcv`.

**Decision**: Add optional `live_quote=None` parameter to `render_stock_detail`. When provided, the detail header shows `live_quote.current_price` and `live_quote.company_name`. All existing callers are unaffected (default None).

**Rationale**: Clean interface extension with backward compatibility. Avoids session-state coupling between dashboard and stock_detail.

---

## Question 5: How to prevent redundant on-demand re-fetches on Streamlit reruns?

**Finding**: Streamlit reruns the entire script on any user interaction. Without caching, selecting a non-cached stock would trigger a new `fetch_quotes` + `fetch_ohlcv_history` on every keystroke or widget interaction.

**Decision**: Store the on-demand fetch result in session state under key `f"live_snapshot_{market}_{symbol}"` as a dict `{"quote": StockQuote | None, "ohlcv": DataFrame | None, "error": str | None}`. Check this key before fetching; only fetch if absent.

**Rationale**: Consistent with how existing OHLCV data is cached in session state (`st.session_state[f"ohlcv_{market}"]`). No new patterns introduced.

---

## Question 6: Arbitrary ticker lookup (FR-001 direct lookup requirement)

**Finding**: FR-001 requires: "if the user's query exactly matches a stock symbol not in the curated list, the app MUST attempt to fetch and display that ticker directly." This means a query like "HDFCAMC" (a valid NSE stock not in Nifty 500) should trigger a direct fetch attempt.

**Decision**: If `search_stocks_live` returns 0 results and the query is 2–12 characters with only alphanumeric + `-` + `.` characters (valid ticker format), show a `st.button(f"Try direct lookup for '{query.upper()}'")`. On click, attempt `fetch_quotes([query.upper()])` for the active market. On success, show detail. On failure, show error.

**Rationale**: Keeps the search function clean (no side-effects). Direct lookup is an explicit user action, not a silent fallback.
