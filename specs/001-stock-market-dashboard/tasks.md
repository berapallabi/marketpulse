---

description: "Task list for MarketPulse Investment Dashboard"
---

# Tasks: MarketPulse Investment Dashboard

**Input**: Design documents from `specs/001-stock-market-dashboard/`

**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/

**Tests**: Included — constitution Principle III (Test-First) is NON-NEGOTIABLE. Write tests first, confirm they FAIL, then implement.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Exact file paths are included in every task description

---

## Phase 1: Setup

**Purpose**: Project scaffolding and configuration — no logic, just structure.

- [ ] T001 Create project directory structure: `marketpulse/`, `marketpulse/data/`, `marketpulse/analysis/`, `marketpulse/storage/`, `marketpulse/ui/`, `tests/`; add `__init__.py` to each `marketpulse/` subdirectory
- [ ] T002 Create `requirements.txt` with pinned minimum versions: streamlit>=1.35, plotly>=5.20, yfinance>=0.2, nsepython>=2.9, nsetools>=1.0.11, pandas-ta>=0.3.14b, feedparser>=6.0, vaderSentiment>=3.3, pandas>=2.1, numpy>=1.26, pytest>=8.0
- [ ] T003 [P] Create `.gitignore` including: `__pycache__/`, `*.pyc`, `.venv/`, `.env`, `*.db`, `~/.marketpulse/` note as comment

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Config, cache infrastructure, and shared test fixtures that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Create `marketpulse/config.py` with: `NIFTY_50_SYMBOLS` list (50 NSE tickers), `SP100_SYMBOLS` list (100 US tickers), signal thresholds (`BUY_THRESHOLD=60`, `SELL_THRESHOLD=40`), staleness limit (`STALE_HOURS=1`), RSS feed URLs dict (`INDIA_FEEDS`, `US_FEEDS`), and `DB_PATH = Path.home() / ".marketpulse" / "cache.db"`
- [ ] T004a Create `marketpulse/data/types.py` defining shared dataclasses: `StockQuote` (symbol, market, company_name, current_price, open_price, high_price, low_price, volume, currency, fetched_at) and `DataProviderError` exception class. Both `data/india.py` and `data/us.py` MUST import these from `marketpulse/data/types.py` — never from each other.
- [ ] T005 Create `marketpulse/storage/cache.py` with SQLite schema initialisation: `init_db()` function that creates all 6 tables (`stocks`, `price_snapshots`, `technical_snapshots`, `sentiment_snapshots`, `signals`, `news_items`, `market_summaries`) with `CREATE TABLE IF NOT EXISTS` per `data-model.md` schema
- [ ] T006 [P] Create `tests/conftest.py` with shared pytest fixtures: `sample_ohlcv_df` (200-row DataFrame with Date/Open/High/Low/Close/Volume), `sample_news_articles` (list of 5 mock NewsArticle objects, mixed sentiment), `tmp_db` (temporary SQLite DB path), `mock_india_quotes` and `mock_us_quotes` (lists of StockQuote imported from `marketpulse/data/types.py` — used by test_india.py and test_us.py respectively)
- [ ] T007 Write `tests/test_cache.py` tests — **run and confirm they FAIL before T008**: test `init_db()` creates all 6 tables; test `write_signals()` inserts rows; test overwrite on second `write_signals()` call (row count stays the same); test `check_staleness()` returns True when `last_updated` > 1 hour ago
- [ ] T008 Complete `marketpulse/storage/cache.py` with full CRUD: `write_quotes()`, `write_technical()`, `write_sentiment()`, `write_signals()`, `write_news()`, `write_market_summary()`, `read_signals(market)`, `read_news(symbol, market)`, `read_market_summary(market)`, `check_staleness(market)` — make T007 tests pass

**Checkpoint**: Cache tests all green. Foundation ready for user story implementation.

---

## Phase 3: User Story 1 — Indian Stocks Panel (Priority: P1) 🎯 MVP

**Goal**: Display ranked BUY/SELL/HOLD signals for Nifty 50 stocks with confidence scores and timestamps.

**Independent Test**: `streamlit run app.py` → India tab shows ≥10 Nifty 50 stocks with BUY/SELL/HOLD labels, confidence scores, and last-updated timestamps. BUY filter shows only BUY rows sorted by confidence.

### Tests for User Story 1 ⚠️ Write and confirm FAIL before implementing

- [ ] T009 [P] [US1] Write `tests/test_indicators.py` — test `compute_indicators()` with `sample_ohlcv_df`: RSI score is +1 when RSI<30, -1 when RSI>70, 0 otherwise; MACD score is +1 when macd_val > macd_signal; BB score is +1 when close < bb_lower; technical_score is in [0, 100]; returns None when DataFrame has < 50 rows
- [ ] T010 [P] [US1] Write `tests/test_signals.py` — test `generate_signal()`: final_score = 0.7×technical + 0.3×sentiment; signal_type="BUY" when score≥60, "SELL" when ≤40, "HOLD" otherwise; confidence_score equals round(final_score); conflicting indicators produce HOLD with score near 50; sentiment defaults to 50 when is_sufficient=False
- [ ] T011 [P] [US1] Write `tests/test_sentiment.py` — test `score_articles_for_stock()`: article matched when symbol in headline; article matched when first two words of company_name in summary; sentiment_score in [0, 100]; is_sufficient=False and score=50.0 when < 2 articles match; positive articles produce score > 50
- [ ] T011a [P] [US1] Write `tests/test_india.py` — test `fetch_quotes()` with mocked nsepython responses: returns list of StockQuote with correct symbol/market/currency fields; raises DataProviderError when nsepython is entirely unreachable; returns partial list when a single symbol fails. Test `fetch_ohlcv_history()` with mocked yfinance: returns DataFrame with Date/Open/High/Low/Close/Volume columns sorted ascending; returns None when fewer than 50 rows available. Use `mock_india_quotes` fixture from conftest.py. Must FAIL before T012.

### Implementation for User Story 1

- [ ] T012 [P] [US1] Create `marketpulse/data/india.py` implementing `fetch_quotes(symbols) -> list[StockQuote]` using nsepython for current price/OHLC, and `fetch_ohlcv_history(symbol, days=200) -> pd.DataFrame | None` using yfinance with `.NS` suffix; import `StockQuote`, `DataProviderError` from `marketpulse/data/types.py`; raise `DataProviderError` on total nsepython failure; make T011a tests pass
- [ ] T013 [US1] Create `marketpulse/data/sentiment.py` implementing `fetch_market_articles(market) -> list[NewsArticle]` using feedparser on `config.INDIA_FEEDS`/`config.US_FEEDS`, and `score_articles_for_stock(articles, symbol, company_name) -> SentimentResult`; define `NewsArticle`, `SentimentResult` dataclasses; make T011 tests pass
- [ ] T014 [US1] Create `marketpulse/analysis/indicators.py` implementing `compute_indicators(symbol, market, ohlcv) -> TechnicalSnapshot | None` using pandas-ta for RSI(14), MACD(12,26,9), BBands(20), SMA(50), SMA(200); apply scoring rules from `contracts/signal-engine.md`; make T009 tests pass
- [ ] T015 [US1] Create `marketpulse/analysis/signals.py` implementing `generate_signal(technical, sentiment) -> Signal` with 70/30 weighting, BUY/SELL/HOLD classification, and `contributing_factors` list; define `Signal` dataclass; make T010 tests pass
- [ ] T016 [US1] Create `marketpulse/ui/stock_list.py` with `render_stock_list(signals_df, market)`: `st.radio` filter (ALL/BUY/SELL/HOLD), `st.dataframe` with colour-coded signal column (green/red/grey), confidence sort descending, staleness warning badge for data > 1hr, risk disclaimer as `st.caption` below table
- [ ] T017 [US1] Create `marketpulse/app.py` (entry point) and `marketpulse/ui/dashboard.py` with `render_dashboard()`: `st.warning` risk disclaimer banner, `st.sidebar` Refresh button, `st.tabs(["🇮🇳 India", "🇺🇸 US"])` skeleton
- [ ] T018 [US1] Wire India tab end-to-end in `marketpulse/ui/dashboard.py`: on Refresh click → `india.fetch_quotes()` + `fetch_ohlcv_history()` → `indicators.compute_indicators()` → `sentiment.fetch_market_articles("IN")` + `score_articles_for_stock()` → `signals.generate_signal()` → `cache.write_*()` → `stock_list.render_stock_list()` with prices in INR

**Checkpoint**: India tab fully functional. BUY/SELL/HOLD signals display with filter, timestamps, and disclaimer.

---

## Phase 4: User Story 2 — US Stocks Panel (Priority: P2)

**Goal**: Display ranked BUY/SELL/HOLD signals for S&P 100 stocks in the US tab, consistent with India tab format.

**Independent Test**: US tab shows ≥10 S&P 100 stocks with BUY/SELL/HOLD labels in USD. "Market Closed" badge appears when NYSE is outside trading hours. Filtering and confidence sort work identically to India tab.

### Tests for User Story 2 ⚠️ Write and confirm FAIL before implementing

- [ ] T018a [P] [US2] Write `tests/test_us.py` — test `fetch_quotes()` with mocked yfinance responses: returns list of StockQuote with currency="USD" and market="US"; raises DataProviderError on total yfinance failure; returns partial list on single-symbol failure. Test `fetch_ohlcv_history()`: returns None when fewer than 50 rows available. Use `mock_us_quotes` fixture from conftest.py. Must FAIL before T019.

### Implementation for User Story 2

- [ ] T019 [P] [US2] Create `marketpulse/data/us.py` implementing `fetch_quotes(symbols) -> list[StockQuote]` and `fetch_ohlcv_history(symbol, days=200) -> pd.DataFrame | None` using yfinance (no `.NS` suffix); import `StockQuote`, `DataProviderError` from `marketpulse/data/types.py`; make T018a tests pass
- [ ] T020 [US2] Wire US tab end-to-end in `marketpulse/ui/dashboard.py`: on Refresh click → `us.fetch_quotes()` + `fetch_ohlcv_history()` → `indicators.compute_indicators()` → `sentiment.fetch_market_articles("US")` + `score_articles_for_stock()` → `signals.generate_signal()` → `cache.write_*()` → `stock_list.render_stock_list()` with prices in USD
- [ ] T021 [US2] Add market-hours detection to `marketpulse/ui/dashboard.py`: check current UTC time against NSE hours (09:15–15:30 IST) and NYSE hours (09:30–16:00 ET); render `st.info("🔴 Market Closed — showing last-close data")` badge in the relevant tab when market is closed

**Checkpoint**: Both India and US tabs display signals independently. Currency (INR vs USD) is correct per tab.

---

## Phase 5: User Story 3 — Market Sentiment Overview (Priority: P3)

**Goal**: Bullish/Neutral/Bearish gauges at the top of the dashboard summarising macro sentiment for each market.

**Independent Test**: Two sentiment metric widgets render above the tabs — one for India, one for US — each showing Bullish/Neutral/Bearish label, a score, and article count. "Insufficient data" appears when fewer than 5 stocks have valid sentiment.

### Tests for User Story 3 ⚠️ Write and confirm FAIL before implementing

- [ ] T021a [US3] Write `tests/test_market_summary.py` — test `compute_market_summary()`: avg sentiment ≥60 → "Bullish", ≤40 → "Bearish", between → "Neutral"; buy/sell/hold counts match input signals list; when fewer than 5 stocks have `is_sufficient=True`, returns `overall_sentiment="Neutral"` with `insufficient_data=True` flag. Must FAIL before T022.

### Implementation for User Story 3

- [ ] T022 [US3] Create `marketpulse/analysis/market_summary.py` implementing `compute_market_summary(market, signals, sentiments) -> MarketSummary`: averages sentiment scores, classifies Bullish/Neutral/Bearish (≥60/≤40/between), counts BUY/SELL/HOLD; returns Neutral with flag when < 5 stocks have sufficient sentiment data
- [ ] T023 [US3] Create `marketpulse/ui/sentiment_gauge.py` with `render_sentiment_gauge(summary: MarketSummary)`: `st.metric` widget showing label (colour-coded), score rounded to 1 decimal, and article count subtext; shows "Insufficient data" string when summary flag is set
- [ ] T024 [US3] Integrate sentiment gauges into `marketpulse/ui/dashboard.py` header zone: add two-column layout above tabs, call `render_sentiment_gauge()` for India and US after each refresh; read cached `market_summaries` on load

**Checkpoint**: Sentiment gauges visible above tabs on dashboard load.

---

## Phase 6: User Story 4 — Stock Drill-Down (Priority: P4)

**Goal**: Click any stock to see a 90-day price chart, indicator values, and recent news headlines with sentiment labels.

**Independent Test**: Selecting any stock from either tab opens a detail panel showing: Plotly 90-day price chart, RSI/MACD/BB values with labels, ≥3 news headlines with Positive/Neutral/Negative badges, and a "Not financial advice" disclaimer.

### Implementation for User Story 4

- [ ] T025 [US4] Create `marketpulse/ui/stock_detail.py` with `render_stock_detail(symbol, market, technical, news_items, ohlcv_df)`: Plotly line chart of 90-day Close prices via `st.plotly_chart`; indicator value display (RSI with overbought/oversold label, MACD value and signal, BB position); news headlines table with source, published_at, and colour-coded sentiment badge; `st.warning("This is informational only. Not financial advice.")` at top
- [ ] T026 [US4] Add stock selection to `marketpulse/ui/stock_list.py`: replace plain `st.dataframe` with `st.dataframe` using `on_select="rerun"` and row selection config; return selected symbol to caller
- [ ] T027 [US4] Wire drill-down in `marketpulse/ui/dashboard.py`: when a stock row is selected → read `technical_snapshots`, `news_items` from cache for that symbol → fetch 90-day OHLCV if not cached → call `stock_detail.render_stock_detail()` in a `st.expander` below the stock list

**Checkpoint**: Full drill-down works for any stock in both markets including chart, indicators, and news.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, data quality labels, and end-to-end validation across all stories.

- [ ] T028 [P] Add `DataProviderError` handling in `marketpulse/ui/dashboard.py`: wrap each market's fetch block in try/except; on `DataProviderError` show `st.error("⚠️ India data unavailable — check connection")` or US equivalent; ensure no silent failures (FR-010)
- [ ] T029 [P] Add "X stocks unavailable" counter to `marketpulse/ui/dashboard.py`: track skipped symbols during fetch; display `st.caption(f"{n} stocks unavailable")` in each market tab
- [ ] T030 [P] Verify staleness display completeness in `marketpulse/ui/stock_list.py` and `marketpulse/ui/stock_detail.py`: every rendered data point must show `last_updated`; add amber warning icon next to any timestamp older than `config.STALE_HOURS`
- [ ] T031 Run end-to-end quickstart.md validation in a fresh virtualenv: `pip install -r requirements.txt` → `streamlit run app.py` → click Refresh → verify India tab (US1), US tab (US2), sentiment gauges (US3), drill-down (US4) all function; fix any import or runtime errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Phase 2 — no dependency on US2/US3/US4
- **US2 (Phase 4)**: Depends on Phase 2 + US1 complete (reuses indicators, signals, sentiment modules)
- **US3 (Phase 5)**: Depends on Phase 2 + US1 complete (reuses sentiment data pipeline)
- **US4 (Phase 6)**: Depends on Phase 2 + US1 complete (reuses cache, indicator, news data)
- **Polish (Phase 7)**: Depends on all user stories complete

### Within Each User Story

- Tests MUST be written first and MUST FAIL before implementation begins
- Data providers before analysis modules
- Analysis modules before UI components
- Core wiring last (end-to-end integration task)

### Parallel Opportunities

- T002, T003 — run in parallel after T001
- T004a, T005, T006 — run in parallel after T004
- T009, T010, T011, T011a, T012 — all run in parallel (different files, all after T008; T012 also needs T004a)
- T013, T014 — run in parallel after T009/T010/T011/T011a/T012
- T018a, T019 — run in parallel during US1 (different files; T019 also needs T004a)
- T021a — write before T022; can start once Phase 2 is complete

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T008) — **CRITICAL blocker**
3. Complete Phase 3: User Story 1 (T009–T018)
4. **STOP and VALIDATE**: `streamlit run app.py` — India tab shows signals, filter works, timestamps show
5. Demo MVP: Indian stock BUY/SELL/HOLD dashboard is live

### Incremental Delivery

1. Setup + Foundational → Cache and config ready
2. US1 → Indian signals → Test independently → **MVP achieved**
3. US2 → US signals → Test independently (both tabs work)
4. US3 → Sentiment gauges → Test independently (header gauges show)
5. US4 → Drill-down → Test independently (detail view works)
6. Polish → All stories hardened and end-to-end validated

---

## Notes

- `[P]` tasks have no file conflicts — safe to work on simultaneously
- TDD is non-negotiable (constitution Principle III): tests written → confirmed FAIL → implement → confirm PASS
- Each user story checkpoint should be validated before starting the next story
- Cache location `~/.marketpulse/cache.db` is outside the repo — never committed to git
- `DataProviderError` is the single exception type for total provider failure — per-symbol failures are silently skipped with a count
