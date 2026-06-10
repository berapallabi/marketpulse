# Quickstart: Explore Tab

## Happy Path — Find and Track a Stock

1. Start the app: `streamlit run app.py`
2. Select the India or US market tab at the top.
3. Click the **Explore** tab (rightmost of the four tabs).
4. Type `"REL"` in the search box.
5. Verify a result row for `RELIANCE` appears in the left column with its signal type and price.
6. Click the `RELIANCE` row.
7. Verify the right column shows the detail panel (price, signal, chart if available, news).
8. Click **+ Add to Watchlist** in the detail panel.
9. Verify the button label changes to **✓ Remove from Watchlist**.
10. Switch to the **Watchlist** tab and verify `RELIANCE` appears there.

## Empty Cache Path

1. Start the app fresh (no prior data loaded).
2. Open the **Explore** tab.
3. Type any query.
4. Verify the message "No results found" or "No stock data available yet" appears — no error.

## Minimum Query Length

1. Open the **Explore** tab.
2. Type a single character (e.g. `"T"`).
3. Verify no results are shown and a hint prompts for at least 2 characters.

## Cross-Tab Selection Independence

1. Select a stock in the **Buy** tab (e.g. `TCS`).
2. Switch to the **Explore** tab.
3. Verify the Explore detail panel does not pre-select `TCS`.
4. Search and select `INFY` in Explore.
5. Switch back to the **Buy** tab.
6. Verify the Buy tab still shows `TCS` selected, not `INFY`.

## US Market

Repeat the happy path on the **US** market tab to confirm parity:
- Search `"APPL"` → matches `AAPL` (Apple)
- Add to Holdings
- Verify in My Holdings tab
