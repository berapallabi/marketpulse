# Implementation Plan: Per-Tier BUY Refresh — Top 20 Buy Stocks

**Branch**: `004-buy-focus-per-cap` | **Date**: 2026-06-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-buy-focus-per-cap/spec.md`

## Summary

Add a dedicated Refresh button to each cap tier's BUY sub-tab. Clicking it fetches fresh signal data for only the stocks in that tier (derived from the last global refresh classification), filters to BUY signals, and displays the top 20 ranked by confidence score. Results are held in session state — the SQLite signals table is not written, preserving SELL/HOLD data from the last global refresh.

## Technical Context

**Language/Version**: Python 3.14 (locked per constitution)

**Primary Dependencies**: Streamlit, yfinance, nsepython, pandas, SQLite — all unchanged from base project

**Storage**: No DB schema changes. Per-tier BUY results stored in `st.session_state["tier_buy_{market}_{slug}"]`.

**Testing**: pytest (existing suite in `tests/`)

**Target Platform**: Local Streamlit app (`streamlit run app.py`)

**Project Type**: Streamlit dashboard (existing)

**Performance Goals**: Per-tier refresh is scoped to one tier's symbols (typically 10–35 stocks vs 50–100 for a full refresh), completing faster than a global refresh.

**Constraints**: No new external data sources. No new Python packages. SELL/HOLD signal data in DB must not be modified.

**Scale/Scope**: Nifty 50 (50 stocks across 3 India tiers) and S&P 100 (100 stocks across 4 US tiers) — unchanged universe.

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I — Data Accuracy | ✅ PASS | Fresh data fetched on button click. Spinner shown. Timestamps displayed. Session state cleared on global refresh. |
| II — User Safety | ✅ PASS | Disclaimer in `render_stock_list` remains unchanged. "Top 20 BUY" framing carries no implied guarantee. |
| III — Test-First | ✅ PASS | `_top_buy_signals()` pure function written test-first. Contract in `contracts/tier-buy-refresh.md` defines 7 test scenarios. |
| IV — Simplicity | ✅ PASS | Only `dashboard.py` changes. No new modules, no new DB tables, no new dependencies. Session state reuses existing pattern. |
| V — Dual-Market Parity | ✅ PASS | India and US both get per-tier BUY Refresh buttons for their respective tier sets. |

## Project Structure

### Documentation (this feature)

```
specs/004-buy-focus-per-cap/
├── plan.md          ← this file
├── spec.md
├── research.md
├── data-model.md
└── contracts/
    └── tier-buy-refresh.md
```

### Source Code Changes

```
marketpulse/
└── ui/
    └── dashboard.py   # + _top_buy_signals() pure helper
                       # + _refresh_tier_buy() UI orchestrator
                       # + BUY sub-tab Refresh button in _render_market_tab()

tests/
└── test_dashboard_buy.py  # NEW — unit tests for _top_buy_signals()
```

**No changes to**: `stock_list.py`, `stock_detail.py`, `sentiment_gauge.py`, `indicators.py`, `signals.py`, `cap_tiers.py`, `cache.py`, `india.py`, `us.py`, `types.py`, `config.py`

## Key Design Decisions

### 1. Session state, not DB, for per-tier BUY results

Per-tier BUY refresh computes fresh signals but stores them only in `st.session_state["tier_buy_{market}_{slug}"]`. Writing to the DB would overwrite existing signal_type values for those stocks, silently removing them from SELL/HOLD tabs — violating FR-005. Session state is isolated and cleared automatically on global refresh.

### 2. Symbol discovery from DB

```python
existing = cache.read_signals(market)
tier_symbols = [r["symbol"] for r in existing if r.get("cap_tier") == tier_label]
```

If `tier_symbols` is empty (no global refresh run yet), store `[]` and show the empty-state prompt.

### 3. `_top_buy_signals` pure function

```python
def _top_buy_signals(signals: list, limit: int = 20) -> list:
    buys = [s for s in signals if s.signal_type == "BUY"]
    return sorted(buys, key=lambda s: s.confidence_score, reverse=True)[:limit]
```

Extracted from orchestration so it can be unit-tested without Streamlit or network dependencies. Returns Signal objects; caller converts to dicts for session state storage.

### 4. Refresh button placement and label

Button text: `"🔄 Refresh BUY"`. Placed at top of the BUY sub-tab inside each tier tab. The global sidebar button continues to say `"🔄 Refresh Data"`. Two distinct labels, two distinct scopes — satisfying FR-007.

### 5. Result format in session state

The list stored in session state uses the same dict format as `cache.read_signals()` returns, so `render_stock_list()` requires zero changes. The BUY sub-tab passes `tier_buy_rows` (from session state) instead of `tier_rows` (from DB) when a per-tier refresh has been done.

## Complexity Tracking

No constitution violations. Change limited to `dashboard.py` plus one new test file. Complexity delta is minimal.
