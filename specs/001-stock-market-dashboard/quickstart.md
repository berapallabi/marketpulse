# Quickstart: MarketPulse Investment Dashboard

## Prerequisites

- Python 3.11 or higher
- Internet connection (for data fetch)
- ~200MB disk space (Python packages + SQLite cache)

## Setup

```bash
# 1. Clone the repo
git clone <repo-url>
cd stock-market

# 2. Create and activate a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The dashboard opens automatically in your browser at `http://localhost:8501`.

## First Run

On first open, the cache is empty. Click **🔄 Refresh Data** in the sidebar to fetch live data for both markets. This takes up to 60 seconds.

Subsequent opens load from the local SQLite cache (`~/.marketpulse/cache.db`) and render in under 5 seconds. Refresh again whenever you want fresh signals.

## Stopping the App

Press `Ctrl+C` in the terminal. The SQLite cache persists and is available on the next run.

## Running Tests

```bash
pytest tests/ -v
```

All tests run offline using recorded fixtures — no live API calls required.

## Resetting the Cache

```bash
rm ~/.marketpulse/cache.db
```

The database is recreated automatically on the next refresh.
