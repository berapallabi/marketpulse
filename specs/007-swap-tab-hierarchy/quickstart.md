# Quickstart: Swap Tab Hierarchy

## Running the App

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. No DB or dependency changes — this is a pure UI restructuring.

## Verifying the Feature

1. Open the dashboard and select any market (India or US).
2. Confirm the **outer** tab row shows: **Buy | Watchlist | My Holdings** — using the bold tab style (not the compact pill style).
3. Confirm the **inner** row shows cap tiers (e.g., Large Cap | Mid Cap | Small Cap) in the **compact segmented-control style** (not bold tabs).
4. Click each outer tab — verify cap tier tabs appear inside each.
5. Switch cap tiers within Buy — verify the stock list updates.
6. Switch to Watchlist, add a stock via the detail panel — verify it appears in the Watchlist tab under the correct tier.
7. Reload the page — verify outer tab defaults to Buy, inner defaults to the first tier.
8. Verify the Refresh button still works inside each tier.

## Running Tests

```bash
pytest tests/
```

All 115 existing tests must pass. New tests for the tab hierarchy are in:
- `tests/test_tab_hierarchy.py`
