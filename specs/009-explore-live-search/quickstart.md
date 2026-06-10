# Quickstart: Explore Live Search — Any Stock

**Feature**: 009-explore-live-search  
**Date**: 2026-06-10

## Manual Test Scenarios

### Scenario 1 — Search a Nifty 500 stock not in the tracked Nifty 50

1. `streamlit run app.py` → open India tab → click **Explore**
2. Type `Bajaj Auto` in the search box
3. **Expected**: `BAJAJAUT` appears in results with company name "Bajaj Auto Ltd"
4. Click `BAJAJAUT`
5. **Expected**: Loading spinner appears briefly, then detail panel shows current price and chart

### Scenario 2 — Search a S&P 500 stock not in the tracked S&P 100

1. Switch to US tab → click **Explore**
2. Type `Palantir` in the search box
3. **Expected**: `PLTR` appears in results with company name "Palantir Technologies Inc."
4. Click `PLTR`
5. **Expected**: Loading spinner, then current price and chart

### Scenario 3 — Cached stock still uses cached data (no redundant fetch)

1. India tab → Explore → type `RELIANCE`
2. **Expected**: RELIANCE appears with its cached signal type (BUY/HOLD/SELL) and cached price
3. Click RELIANCE
4. **Expected**: Detail shows instantly (no spinner) with technical data and news

### Scenario 4 — Direct ticker lookup for arbitrary stock

1. India tab → Explore → type `HDFCAMC` (valid NSE stock, not in Nifty 500)
2. **Expected**: 0 search results + button `Try direct lookup for 'HDFCAMC'`
3. Click the button
4. **Expected**: Current price and chart displayed for HDFCAMC

### Scenario 5 — Error handling when fetch fails

1. Disconnect from internet
2. India tab → Explore → search `Bajaj Auto` → click `BAJAJAUT`
3. **Expected**: `st.error("Could not load data for BAJAJAUT. Check your connection and try again.")`
4. No crash, no blank panel

### Scenario 6 — Add non-cached stock to watchlist

1. Complete Scenario 1 (BAJAJAUT detail panel open)
2. Click `+ Add to Watchlist`
3. Switch to Watchlist tab
4. **Expected**: BAJAJAUT appears in watchlist

### Scenario 7 — Short query rejected

1. India tab → Explore → type `B` (1 character)
2. **Expected**: "Enter at least 2 characters to search." message, no results list
