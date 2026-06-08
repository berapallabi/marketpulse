# MarketPulse

A local investment dashboard for Indian (Nifty 50) and US (S&P 100) markets. Combines technical indicators and news sentiment to generate BUY / HOLD / SELL signals, grouped by cap tier.

> **Informational only — not financial advice. All signals are generated algorithmically.**

## Features

- **Signal tabs** — Buy, Watchlist, My Holdings as the top-level navigation
- **Cap tier breakdown** — Large / Mid / Small Cap (India) and Mega / Large / Mid / Small Cap (US)
- **Technical signals** — RSI, moving averages, and other indicators scored into a confidence rating
- **Sentiment analysis** — News headlines scored with VADER and blended into the final signal
- **Watchlist & Holdings** — Persistent per-market lists backed by SQLite; add/remove from the stock detail panel
- **Stock detail panel** — Price, signal breakdown, OHLCV chart, and recent news for any selected stock
- **Per-tier refresh** — Fetch fresh quotes and recompute signals for a single cap tier without a full reload

## Setup

**Prerequisites**: Python 3.11+

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`.

## Deploying to Streamlit Cloud

1. Push this repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **New app**.
3. Select the repository, set the branch to `main`, and set the main file path to `app.py`.
4. Click **Deploy**.

No secrets or environment variables are required — all data is fetched from public sources.

> **Note**: Streamlit Cloud's filesystem is ephemeral. The SQLite cache (`~/.marketpulse/cache.db`) resets on each restart or redeployment. Refresh data after the app starts.

## Running Tests

```bash
PYTHONPATH=. .venv/bin/pytest tests/
```

## Project Structure

```
app.py                      # Streamlit entry point
marketpulse/
  config.py                 # Symbols, thresholds, feed URLs
  data/                     # Quote and OHLCV fetchers (India via nsepython, US via yfinance)
  analysis/                 # Indicators, signals, cap tier classification, market summary
  storage/                  # SQLite cache (quotes, signals, technicals, watchlist, holdings)
  ui/                       # Dashboard layout, stock list, stock detail, theme
specs/                      # Feature specs and implementation plans
tests/                      # pytest test suite
```

## Data Sources

| Market | Quotes & OHLCV | News |
|--------|---------------|------|
| India  | nsepython / nsetools | Economic Times, Moneycontrol RSS |
| US     | yfinance | Yahoo Finance, Reuters RSS |

## Storage

All data is persisted to `~/.marketpulse/cache.db` (SQLite). The database is created automatically on first run.
