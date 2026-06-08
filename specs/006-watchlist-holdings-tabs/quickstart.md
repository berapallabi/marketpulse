# Quickstart: Watchlist & My Holdings Tabs

## Running the App

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. No additional setup — the new `watchlist` and `holdings` tables are created automatically on first run via `init_db()`.

## Verifying the Feature

1. Open the dashboard and select any market (India or US).
2. Navigate to any cap tier — confirm the signal filter shows **Buy | Watchlist | My Holdings** (All/SELL/HOLD are gone).
3. Click a stock row to open the detail panel.
4. Click **"+ Add to Watchlist"** — switch to the Watchlist tab and confirm the stock appears.
5. Click **"+ Add to Holdings"** — switch to the My Holdings tab and confirm the stock appears.
6. Reload the page — confirm both stocks still appear (persistence check).
7. Click **"✓ Remove from Watchlist"** / **"✓ Remove from Holdings"** — confirm removal.

## Running Tests

```bash
pytest tests/
```

Tests for this feature live in:
- `tests/test_watchlist_holdings.py` — storage layer (add/remove/read, duplicates, cross-market isolation)
- `tests/test_dashboard_tabs.py` — UI layer (tab options, Buy tab regression, empty states)

## Database Location

The SQLite database is at the path configured in `marketpulse/config.py` (`DB_PATH`). The new tables are added non-destructively — existing data is unaffected.
