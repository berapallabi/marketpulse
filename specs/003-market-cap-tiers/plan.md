# Implementation Plan: Market Cap Tier Tabs

**Branch**: `003-market-cap-tiers` | **Date**: 2026-06-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-market-cap-tiers/spec.md`

## Summary

Classify each stock in the existing Nifty 50 / S&P 100 universe into a market-cap tier using the stock's actual market capitalisation fetched from the data provider. Display tier tabs (Large Cap / Mid Cap / Small Cap for India; Mega Cap / Large Cap / Mid Cap / Small Cap for US) as the first navigation level inside each market tab, with the existing All/BUY/SELL/HOLD signal sub-tabs nested inside each tier. No new dependencies, no universe expansion.

## Technical Context

**Language/Version**: Python 3.14 (locked per constitution)

**Primary Dependencies**: Streamlit, yfinance, nsepython, pandas, SQLite — all unchanged from base project

**Storage**: SQLite — add `cap_tier TEXT DEFAULT 'Unknown'` to the `signals` table via migration in `init_db()`

**Testing**: pytest (existing suite in `tests/`)

**Target Platform**: Local Streamlit app (`streamlit run app.py`)

**Project Type**: Streamlit dashboard (existing)

**Performance Goals**: No additional latency budget. Market cap is fetched from the same `ticker.info` dict already retrieved per-stock during `fetch_quotes()` — zero extra API calls for US. India requires one lightweight yfinance `.info` call per symbol during the existing OHLCV phase.

**Constraints**: No new external data sources. No universe expansion. Market cap unavailability must be handled gracefully (stock placed in "Unknown" tier, counted as unavailable for tier display purposes).

**Scale/Scope**: 50 India + 100 US stocks (unchanged)

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I — Data Accuracy | ✅ PASS | Market cap from yfinance (same verified source as OHLCV). Unavailable cap → "Unknown" tier, not fabricated. |
| II — User Safety | ✅ PASS | Tier tabs are navigation only; all existing risk disclaimers and signal presentation unchanged. |
| III — Test-First | ✅ PASS | `tests/test_cap_tiers.py` written and confirmed failing before `cap_tiers.py` is implemented. |
| IV — Simplicity | ✅ PASS | Adds one new module (`cap_tiers.py`), extends two dataclasses, touches two UI files. No new abstractions. |
| V — Dual-Market Parity | ✅ PASS | Both India and US get cap tier tabs in the same release. Thresholds are market-specific (INR vs USD). |

## Project Structure

### Documentation (this feature)

```
specs/003-market-cap-tiers/
├── plan.md          ← this file
├── research.md      ← Phase 0 output
├── data-model.md    ← Phase 1 output
├── contracts/
│   └── cap-tiers.md ← Phase 1 output
└── tasks.md         ← /speckit-tasks output (not created here)
```

### Source Code Changes

```
marketpulse/
├── data/
│   ├── types.py          # + market_cap: float | None on StockQuote
│   ├── india.py          # + fetch market_cap via yf.Ticker(.NS).info in fetch_ohlcv_history
│   └── us.py             # + read marketCap from existing ticker.info in fetch_quotes
├── analysis/
│   ├── cap_tiers.py      # NEW — classify_cap_tier(), INDIA_TIERS, US_TIERS
│   └── signals.py        # + cap_tier: str on Signal dataclass
├── storage/
│   └── cache.py          # + cap_tier column migration; write_signals/read_signals updated
└── ui/
    └── dashboard.py      # + cap tier st.tabs between market tab and signal sub-tabs

tests/
├── test_cap_tiers.py     # NEW — unit tests for classify_cap_tier()
└── test_cache.py         # + test cap_tier round-trips through write/read_signals
```

**No changes to**: `stock_list.py`, `stock_detail.py`, `sentiment_gauge.py`, `indicators.py`, `sentiment.py`, `market_summary.py`, `config.py`

## Complexity Tracking

No constitution violations.
