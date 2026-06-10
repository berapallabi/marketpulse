# Implementation Plan: Explore Live Search — Any Stock

**Branch**: `009-explore-live-search` | **Date**: 2026-06-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/009-explore-live-search/spec.md`

## Summary

Extend the Explore tab so users can search any stock from the full NSE/NYSE+NASDAQ universe, not just the ~50/~100 currently tracked. Search covers two complementary modes: (a) curated name+symbol match against Nifty 500 (India) and S&P 500 (US) hardcoded symbol/name dictionaries, and (b) direct ticker fallback for arbitrary symbols not in that list. Non-cached selections trigger an on-demand price + OHLCV fetch from existing data providers (nsepython/yfinance), displayed with a loading indicator. Cached stocks continue to use DB data without a redundant fetch.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Streamlit (UI), nsepython + nsetools (India data), yfinance (US data), pandas (data transforms), SQLite `sqlite3` (local cache)

**Storage**: SQLite at `~/.marketpulse/cache.db` — no schema changes required for this feature

**Testing**: pytest (TDD — tests written before implementation per Constitution Principle III)

**Target Platform**: Local only; `streamlit run app.py` at `localhost:8501`

**Project Type**: Desktop app (Streamlit dashboard)

**Performance Goals**: Non-cached detail fetch completes within 5 seconds under normal network (spec SC-002). Search results display instantly (universe dict lookup is in-memory).

**Constraints**: No new external APIs — use nsepython and yfinance already in requirements.txt. No new Python dependencies. No schema migration needed. Symbol universe is hardcoded (Nifty 500 / S&P 500 change at most twice a year; acceptable for a personal tool).

**Scale/Scope**: Nifty 500 (500 India symbols) + S&P 500 (505 US symbols) search universe per market.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Accuracy | PASS | On-demand fetch uses verified providers (nsepython/yfinance). Load errors surface as visible error message, never silently hidden. |
| II. User Safety | PASS | No new signal generation — non-cached stocks show price + chart only. Existing risk disclosure on add-to-watchlist/holdings is unaffected. |
| III. Test-First | PASS | Tests written before implementation (TDD mandatory). New `test_live_search.py` precedes all new code. |
| IV. Simplicity (YAGNI) | PASS | Hardcoded universe dict — no DB table, no network call, no cron refresh. On-demand fetch reuses existing `fetch_quotes` + `fetch_ohlcv_history`. No new abstractions. |
| V. Dual-Market Parity | PASS | Both India (Nifty 500) and US (S&P 500) delivered in the same feature. `get_universe("IN")` and `get_universe("US")` both implemented and tested. |

## Project Structure

### Documentation (this feature)

```text
specs/009-explore-live-search/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── contracts/
│   └── search-contracts.md   # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (new/changed files)

```text
marketpulse/
├── data/
│   └── universe.py          # NEW: Nifty 500 + S&P 500 {symbol: company_name} dicts
├── storage/
│   └── cache.py             # CHANGE: add search_stocks_live()
└── ui/
    ├── dashboard.py         # CHANGE: _render_explore_tab uses live search + on-demand fetch
    └── stock_detail.py      # CHANGE: add optional live_quote param to render_stock_detail

tests/
└── test_live_search.py      # NEW: all Feature 009 tests (TDD)
```

## Phase 0: Research

See [research.md](./research.md) for full findings. Key decisions:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| India universe source | Hardcoded Nifty 500 `{symbol: company_name}` dict in `universe.py` | nsepython has no Nifty 500 index endpoint; scraping NSE at runtime is fragile; hardcoded dict is zero-latency, zero-network, acceptable for personal tool (index changes ~2x/year) |
| US universe source | Hardcoded S&P 500 `{symbol: company_name}` dict in `universe.py` | Wikipedia scrape is an external call that can break; hardcoded is reliable; S&P 500 changes ~10-20 times/year |
| India on-demand fetch | `india.fetch_quotes([symbol])` (existing) | Already uses `nse_eq(symbol)`; returns company name, price, OHLCV fields |
| US on-demand fetch | `us.fetch_quotes([symbol])` (existing) | Already uses `yf.Ticker(symbol).info`; returns company name, price, etc. |
| India OHLCV fetch | `india.fetch_ohlcv_history(symbol)` (existing) | Already uses `yf.Ticker(f"{symbol}.NS")` |
| US OHLCV fetch | `us.fetch_ohlcv_history(symbol)` (existing) | Already uses `yf.Ticker(symbol)` |
| Arbitrary ticker fallback | UI-layer fallback: if `search_stocks_live` returns 0 results and query ≥ 2 chars, show "Try direct lookup for [QUERY]" button | Keeps `search_stocks_live` pure (no side-effects); direct lookup is an explicit user action |
| Price display for non-cached | Pass `live_quote: StockQuote | None` optional param to `render_stock_detail` | Clean interface extension; all existing callers pass nothing (default None) |
| Session-state caching | Key `live_snapshot_{market}_{symbol}` stores `{quote, ohlcv, error}` dict | Prevents redundant re-fetch on Streamlit reruns; cleared on tab switch |

## Phase 1: Design & Contracts

### Data Model

No new DB schema. The search universe is an in-memory Python dict — no SQLite table needed.

**Extended search result shape** (returned by `search_stocks_live`):

Each result dict carries the same keys as existing `search_stocks` output, plus one new marker:

| Key | Type | Cached stock | Non-cached stock |
|-----|------|--------------|-----------------|
| `symbol` | str | ✓ | ✓ |
| `market` | str | ✓ | ✓ |
| `company_name` | str | ✓ | ✓ (from universe dict) |
| `signal_type` | str or None | str or None | None |
| `confidence_score` | int or None | int or None | None |
| `technical_score` | float or None | float or None | None |
| `sentiment_score` | float or None | float or None | None |
| `contributing_factors` | str or None | str or None | None |
| `generated_at` | str or None | str or None | None |
| `cap_tier` | str or None | str or None | None |
| `current_price` | float or None | float or None | None |
| `last_updated` | str or None | str or None | None |

**Note**: The `_is_cached` flag is NOT stored in the dict. Instead, callers infer it from whether `current_price` is None AND `signal_type` is None — consistent with how existing cached-but-no-signal rows already work. This avoids polluting the shared dict shape.

Alternatively, non-cached rows can be identified by checking `cache.read_quotes(symbol, market)` in the UI. But the simplest approach: `search_stocks_live` returns a plain result list; `_render_explore_tab` checks `row.get("current_price") is None and row.get("signal_type") is None` to decide if on-demand fetch is needed.

Actually, to be unambiguous, `search_stocks_live` will add `"_live": True` to rows sourced from the universe dict only (not from DB). This sentinel is used only in the UI layer; no tests should depend on it for business logic.

### New Functions

#### `marketpulse/data/universe.py`

```python
NIFTY_500_UNIVERSE: dict[str, str]  # symbol → company_name (500 entries)
SP500_UNIVERSE: dict[str, str]       # symbol → company_name (~505 entries)

def get_universe(market: str) -> dict[str, str]:
    """Return the symbol→company_name universe dict for the given market ('IN' or 'US')."""
```

#### `marketpulse/storage/cache.py` (new function)

```python
def search_stocks_live(query: str, market: str, db_path: Path | None = None) -> list[dict]:
    """
    Search both cached DB stocks and the expanded symbol universe.
    
    Returns combined, deduplicated results. DB results appear first.
    Non-cached universe results carry "_live": True.
    Returns [] if len(query) < 2.
    """
```

#### `marketpulse/ui/stock_detail.py` (signature change)

```python
def render_stock_detail(
    symbol: str,
    market: str,
    technical,
    news_items: list,
    ohlcv,
    key: str,
    live_quote=None,   # NEW optional: StockQuote for on-demand fetched price
) -> None:
```

When `live_quote` is not None, the detail panel header shows `live_quote.current_price` and `live_quote.company_name` instead of cached values.

### UI Flow Changes (`_render_explore_tab`)

```
User types query (≥2 chars)
    ↓
search_stocks_live(query, market) → results (mixed cached + live)
    ↓
render_stock_list(results, ...)   [same component, no change needed]
    ↓
User selects a stock
    ↓
Is it a "_live" row (not in cache)?
  NO  → read_technical + read_news + ohlcv from session_state → render_stock_detail (existing path)
  YES → check session_state["live_snapshot_{market}_{symbol}"]
          NOT FOUND → st.spinner("Loading…") → fetch_quotes([symbol]) + fetch_ohlcv_history(symbol)
                        → store in session_state → render_stock_detail(live_quote=quote, ohlcv=df)
          FOUND      → render_stock_detail(live_quote=cached_quote, ohlcv=cached_df)
          ERROR      → st.error("Could not load data for {symbol}. Try again later.")
    ↓
(Fallback) If search returns 0 results AND query looks like a ticker (2–7 uppercase alphanumeric chars):
  Show: st.button(f"Try direct lookup for '{query.upper()}'")
  On click → same on-demand fetch flow as above
```

### Contracts

See [contracts/search-contracts.md](./contracts/search-contracts.md) for full interface contracts.

### Quickstart

See [quickstart.md](./quickstart.md) for manual test scenarios.
