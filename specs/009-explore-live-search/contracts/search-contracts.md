# Interface Contracts: Explore Live Search

**Feature**: 009-explore-live-search  
**Date**: 2026-06-10

---

## Contract 1: `get_universe(market)` — `marketpulse/data/universe.py`

**Purpose**: Return the hardcoded symbol→company_name universe dict for the given market.

**Signature**:
```python
def get_universe(market: str) -> dict[str, str]
```

**Inputs**:
| Parameter | Type | Constraint |
|-----------|------|-----------|
| `market` | `str` | Must be `"IN"` or `"US"` |

**Output**: `dict[str, str]` — keys are uppercase ticker symbols, values are company names.

**Invariants**:
- `get_universe("IN")` returns exactly the Nifty 500 symbol/name dict
- `get_universe("US")` returns exactly the S&P 500 symbol/name dict
- All symbol keys are uppercase
- Unknown market raises `ValueError`
- Return value is never None and never empty

---

## Contract 2: `search_stocks_live(query, market, db_path)` — `marketpulse/storage/cache.py`

**Purpose**: Unified search across both cached DB stocks and the extended symbol universe.

**Signature**:
```python
def search_stocks_live(query: str, market: str, db_path: Path | None = None) -> list[dict]
```

**Inputs**:
| Parameter | Type | Constraint |
|-----------|------|-----------|
| `query` | `str` | Any string; returns `[]` if `len(query) < 2` |
| `market` | `str` | `"IN"` or `"US"` |
| `db_path` | `Path or None` | Defaults to `DB_PATH`; if path doesn't exist, universe-only results are returned |

**Output**: `list[dict]`, each dict has these keys:

| Key | Type | Cached DB row | Universe-only row |
|-----|------|--------------|------------------|
| `symbol` | `str` | ✓ | ✓ |
| `market` | `str` | ✓ | ✓ |
| `company_name` | `str or None` | ✓ | ✓ (from universe dict) |
| `signal_type` | `str or None` | `"BUY"/"SELL"/"HOLD"` or None | None |
| `confidence_score` | `int or None` | int or None | None |
| `technical_score` | `float or None` | float or None | None |
| `sentiment_score` | `float or None` | float or None | None |
| `contributing_factors` | `str or None` | str or None | None |
| `generated_at` | `str or None` | str or None | None |
| `cap_tier` | `str or None` | str or None | None |
| `current_price` | `float or None` | float or None | None |
| `last_updated` | `str or None` | str or None | None |
| `_live` | `bool` | False (or absent) | True |

**Invariants**:
- `len(query) < 2` → returns `[]`
- Results are market-scoped: all returned rows have `row["market"] == market`
- No duplicates: a symbol that appears in both the DB and the universe dict appears only once (DB version wins)
- DB results appear before universe-only results
- Matching is case-insensitive substring match on both `symbol` and `company_name`
- Missing DB returns universe-only results (no crash)
- Never raises an exception (all errors return `[]`)

---

## Contract 3: `render_stock_detail` signature extension — `marketpulse/ui/stock_detail.py`

**Purpose**: Accept an optional live-fetched quote to show price for non-cached stocks.

**New signature**:
```python
def render_stock_detail(
    symbol: str,
    market: str,
    technical,
    news_items: list,
    ohlcv,
    key: str,
    live_quote=None,
) -> None
```

**New parameter**:
| Parameter | Type | Default | Effect |
|-----------|------|---------|--------|
| `live_quote` | `StockQuote or None` | `None` | When not None, the detail header displays `live_quote.current_price` as the current price and `live_quote.company_name` as the display name |

**Backward compatibility**: All existing call sites pass no `live_quote`; default `None` means existing behaviour is unchanged.

---

## Contract 4: UI error surface — `_render_explore_tab`

**Purpose**: Define how live-fetch errors are shown to the user (spec FR-006).

| Condition | UI Response |
|-----------|-------------|
| `fetch_quotes` raises `DataProviderError` | `st.error("Could not load data for {symbol}. Check your connection and try again.")` |
| `fetch_quotes` returns empty list | Same error message as above |
| `fetch_ohlcv_history` returns `(None, None)` | Chart section shows: `st.caption("Price history unavailable.")` — no crash |
| Network timeout / exception | Same `st.error` as DataProviderError case |
| Direct ticker lookup returns no data | `st.warning("No data found for ticker '{query}'. Verify the symbol and try again.")` |
