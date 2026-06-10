# Developer Quickstart: Watchlist & Holdings Refresh

## What's being built

A `_refresh_section(market, section, tier_label)` function in `dashboard.py` that runs full analysis for a scoped symbol list (watchlist OR holdings for a single cap-tier), plus refresh buttons wired into the Watchlist and My Holdings tab UIs.

## Files to change

| File | Change |
|------|--------|
| `marketpulse/ui/dashboard.py` | Add `_refresh_section`; update watchlist + holdings tab layouts |
| `tests/test_watchlist_refresh.py` | New test file |

## Running the app locally

```bash
PYTHONPATH=. .venv/bin/streamlit run marketpulse/app.py
```

## Running tests

```bash
PYTHONPATH=. .venv/bin/pytest tests/test_watchlist_refresh.py -v
```

## Key reference points in `dashboard.py`

| What | Where |
|------|-------|
| Existing refresh pattern to mirror | `_refresh_tier_buy()` at line ~130 |
| `_rows_last_at` helper (for last-refresh timestamp) | line ~237 |
| `_news_items_from_sentiment` helper | line ~563 |
| Watchlist tab rendering | line ~336 |
| Holdings tab rendering | line ~371 |

## Gotchas

- `fetch_ohlcv_history` returns `(df, market_cap)` — capture both; use `mc if market == "IN" else quote.market_cap` for market cap (US market cap comes from the quote object, not OHLCV).
- `generate_signal` does not set `cap_tier` — you must assign `signal.cap_tier = classify_cap_tier(market_cap, market)` after generating the signal.
- The watchlist/holdings tabs do NOT use a session-state result cache (unlike the BUY tab's `tier_buy_…` key). After refresh, a plain `st.rerun()` is enough — `cache.read_signals(market)` at the top of `_render_market_tab` returns the fresh data.
- Session state key separator is `_`: `fetching_IN_watchlist_large_cap` not `fetching_IN_watchlist_Large Cap`.
- `signal_slug` for holdings is `"my_holdings"` (matching the existing key pattern), not `"holdings"`.

## Test pattern

Use a real temp SQLite DB (via `tmp_path` fixture), insert test signals/watchlist/holdings rows, mock `fetch_quotes`/`fetch_ohlcv_history`/`compute_indicators`/`generate_signal`/`score_articles_for_stock`, call `_refresh_section`, then assert the signals table state.

```python
# Minimal mock shape
from unittest.mock import MagicMock, patch

mock_quote = MagicMock()
mock_quote.symbol = "TCS"
mock_quote.company_name = "Tata Consultancy Services"
mock_quote.market_cap = 15_000_000_000_000  # ₹15L Cr

mock_signal = MagicMock()
mock_signal.symbol = "TCS"
mock_signal.market = "IN"
mock_signal.signal_type = "BUY"
mock_signal.confidence_score = 72.5
mock_signal.technical_score = 68.0
mock_signal.sentiment_score = 60.0
mock_signal.contributing_factors = []
mock_signal.cap_tier = None  # assigned by _refresh_section after classify_cap_tier
```
