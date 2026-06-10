# Implementation Plan: Watchlist & Holdings Refresh

**Branch**: `010-watchlist-refresh` | **Date**: 2026-06-10 | **Spec**: [spec.md](spec.md)

## Summary

Add per-tier refresh buttons to the Watchlist and My Holdings tabs that run the full analysis pipeline (quotes → OHLCV → technical indicators → sentiment → signal) scoped exclusively to the symbols in that section, then persist results to the cache and trigger a UI rerun.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Streamlit (UI + session state), SQLite (cache), yfinance (US data + OHLCV), nsepython (India data)

**Storage**: SQLite at `~/.cache/marketpulse/market_cache.db`; tables: `signals`, `stocks`, `price_snapshots`, `technical_snapshots`, `sentiment_snapshots`, `news_items`

**Testing**: pytest with temp SQLite paths; providers mocked via `unittest.mock`

**Target Platform**: macOS / Streamlit Cloud (Linux)

**Project Type**: Streamlit web app

**Performance Goals**: ≤30 s for 10 stocks per refresh (SC-001)

**Constraints**: No schema changes; no new Python dependencies; scope isolation — refresh must not modify signals for symbols outside the targeted (market, section, tier) triple

**Scale/Scope**: Watchlist + holdings each typically ≤30 stocks total; per-tier refresh handles a subset of that

## Constitution Check

- No new external dependencies
- No schema changes (reuses existing tables)
- Single-file UI change — no new modules needed
- New function `_refresh_section` added alongside existing `_refresh_tier_buy` in `dashboard.py`

## Project Structure

### Documentation (this feature)

```text
specs/010-watchlist-refresh/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── checklists/
    └── requirements.md
```

### Source Code (files to modify)

```text
marketpulse/
└── ui/
    └── dashboard.py      # New _refresh_section(); add refresh buttons to watchlist + holdings tabs

tests/
└── test_watchlist_refresh.py   # New test file
```

---

## Implementation Design

### New function: `_refresh_section(market, section, tier_label)`

Location: `dashboard.py`, alongside `_refresh_tier_buy`.

**Algorithm**:
1. Read symbol list: `cache.read_watchlist(market)` or `cache.read_holdings(market)` based on `section`
2. Read current `signal_rows = cache.read_signals(market)` to determine which symbols belong to `tier_label`
3. `tier_symbols = [r["symbol"] for r in signal_rows if r.get("cap_tier") == tier_label and r["symbol"] in symbol_set]`
4. If `tier_symbols` is empty, return early (no-op)
5. `fetch_quotes(tier_symbols)` → `write_quotes`
6. `fetch_market_articles(market)` (best-effort; empty list on failure)
7. For each quote: `fetch_ohlcv_history` → `compute_indicators` → `score_articles_for_stock` → `generate_signal` (with `cap_tier` recomputed via `classify_cap_tier`)
8. Unavailable stocks are skipped (caught by bare `except Exception: continue`)
9. Write: `write_signals`, `write_technical`, `write_sentiment`, `write_news`
10. Clear stale session state: `selected_{market}` and `_prev_rows_{market}_{signal_slug}_*` keys

**Key difference from `_refresh_tier_buy`**:
- Input is a scoped symbol list (watchlist/holdings ∩ tier), NOT the full 50/100 market symbols
- No session-state result cache (`tier_buy_…` key) — watchlist/holdings tabs re-read directly from `cache.read_signals` on next rerun
- No market summary update (watchlist/holdings are not the full market)

### UI changes

**Watchlist tab** (lines ~336–369 of `dashboard.py`):

Before the `list_col / detail_col` split, add the same `seg_col / btn_col` pattern as the BUY tab:
```text
filter_col, _ = st.columns([3, 2])
  seg_col, btn_col = st.columns([5, 4])
    segmented_control (existing, move inside seg_col)
    if watchlist_rows:
      if fetching: disabled "⏳ Refreshing…" → call _refresh_section → rerun
      else: "🔄 Refresh · last at HH:MM" button → set fetching_key → rerun
```

**Holdings tab** (lines ~371–404): same pattern, `signal_slug = "my_holdings"`.

### Session state keys

| Key | Purpose |
|-----|---------|
| `fetching_{market}_watchlist_{tier_slug}` | Refresh-in-progress flag for watchlist tier |
| `fetching_{market}_my_holdings_{tier_slug}` | Refresh-in-progress flag for holdings tier |

Keys cleared after refresh (same as BUY tab pattern):
- `selected_{market}` — stale detail panel
- `_prev_rows_{market}_{signal_slug}_{tier_slug}_*` — dataframe row tracking

---

## Step-by-Step Implementation

### Step 1 — Add `_refresh_section` function

Insert after `_refresh_tier_buy` (before `_rows_last_at`) in `dashboard.py`.

```python
def _refresh_section(market: str, section: str, tier_label: str) -> None:
    """Refresh full analysis for watchlist or holdings symbols in a single tier."""
    from marketpulse.analysis.cap_tiers import classify_cap_tier
    from marketpulse.analysis.indicators import compute_indicators
    from marketpulse.analysis.signals import generate_signal
    from marketpulse.data.sentiment import fetch_market_articles, score_articles_for_stock
    from marketpulse.data.types import DataProviderError

    if market == "IN":
        from marketpulse.data.india import fetch_ohlcv_history, fetch_quotes
    else:
        from marketpulse.data.us import fetch_ohlcv_history, fetch_quotes

    symbol_set = set(
        cache.read_watchlist(market) if section == "watchlist" else cache.read_holdings(market)
    )
    if not symbol_set:
        return

    signal_rows = cache.read_signals(market)
    tier_symbols = [
        r["symbol"] for r in signal_rows
        if r.get("cap_tier") == tier_label and r["symbol"] in symbol_set
    ]
    if not tier_symbols:
        return

    try:
        quotes = fetch_quotes(tier_symbols)
    except DataProviderError as e:
        st.error(f"⚠️ Could not fetch quotes: {e}")
        return

    cache.write_quotes(quotes)

    articles = []
    try:
        articles = fetch_market_articles(market)
    except Exception:
        pass

    ohlcv_cache: dict = st.session_state.setdefault(f"ohlcv_{market}", {})
    signals = []
    sentiments = []
    for quote in quotes:
        try:
            ohlcv, mc = fetch_ohlcv_history(quote.symbol)
            if ohlcv is None:
                continue
            market_cap = mc if market == "IN" else quote.market_cap
            technical = compute_indicators(quote.symbol, market, ohlcv)
            if technical is None:
                continue
            sentiment = score_articles_for_stock(articles, quote.symbol, quote.company_name)
            sentiment.market = market
            signal = generate_signal(technical, sentiment)
            signal.cap_tier = classify_cap_tier(market_cap, market)
            signals.append(signal)
            sentiments.append(sentiment)
            cache.write_technical(technical)
            cache.write_sentiment(sentiment)
            cache.write_news(quote.symbol, market, _news_items_from_sentiment(sentiment))
            ohlcv_cache[quote.symbol] = ohlcv
        except Exception:
            continue

    if signals:
        cache.write_signals(signals)

    slug = tier_label.replace(" ", "_").lower()
    st.session_state.pop(f"selected_{market}", None)
    for key in [k for k in st.session_state if k.startswith(f"_prev_rows_{market}_{section}_{slug}")]:
        st.session_state.pop(key, None)
```

### Step 2 — Update watchlist tab UI

Move the tier `segmented_control` into a `seg_col / btn_col` layout and add the refresh button pattern.

### Step 3 — Update holdings tab UI

Same changes as Step 2, with `section = "my_holdings"`.

### Step 4 — Write tests

File: `tests/test_watchlist_refresh.py`

Test cases:
1. `test_refresh_section_updates_watchlist_symbols` — only watchlisted tier symbols get new signals
2. `test_refresh_section_no_op_when_empty` — no crash/write when section is empty
3. `test_refresh_section_scope_isolation` — holdings signals unchanged after watchlist refresh
4. `test_refresh_section_skips_unavailable` — unavailable stock skipped; rest updated
5. `test_refresh_section_upgrades_placeholder_signal` — HOLD/0 from Explore → real signal after refresh
