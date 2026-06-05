# Feature Specification: MarketPulse Investment Dashboard

**Feature Branch**: `001-stock-market-dashboard`

**Created**: 2026-06-05

**Status**: Draft

**Input**: User description: "I want to build an app which will help me invest in stock market. This is for both Indian stock market and US market. My idea is to have a simple dashboard which will show stocks to buy and stocks to sell. This should be based on market analysis, market sentiment, stock analysis, and other market indicators which are applicable."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — View Buy/Sell Signals for Indian Stocks (Priority: P1)

As an investor, I open the dashboard and immediately see a ranked list of Indian stocks (Nifty 50 universe) with clear BUY, SELL, or HOLD signals, each backed by technical indicator analysis and news sentiment, so I can make informed decisions without manual research.

**Why this priority**: This is the core value proposition of the product. Without this, the app delivers no investment value. Indian market is a primary focus for the user.

**Independent Test**: Open the dashboard with internet access. The Indian Stocks panel shows at least 10 stocks with signal labels (BUY/SELL/HOLD), a confidence score, and a last-updated timestamp. Filtering to BUY-only shows only BUY-labelled rows.

**Acceptance Scenarios**:

1. **Given** the dashboard is opened with internet access, **When** data loads, **Then** the Indian stocks panel displays a list of stocks from the Nifty 50 universe, each showing symbol, company name, current price, signal (BUY/SELL/HOLD), confidence score (0–100), and last-updated timestamp.
2. **Given** the dashboard has loaded, **When** the user selects the BUY filter, **Then** only stocks with a BUY signal are displayed, sorted by confidence score descending.
3. **Given** a stock's data is stale (older than 1 hour), **When** it is displayed, **Then** a visible staleness warning appears next to the stock row.
4. **Given** the data source is unavailable, **When** the dashboard loads, **Then** a clear error banner is shown and no signals are displayed for that market — no stale or fabricated data is silently served.

---

### User Story 2 — View Buy/Sell Signals for US Stocks (Priority: P2)

As an investor, I open the dashboard and see the same signal-based ranked list for US stocks (S&P 100 universe), consistent in format with the Indian stocks panel, so I can compare opportunities across both markets.

**Why this priority**: The product's dual-market value depends on both markets being functional. P2 because the Indian market panel (P1) establishes the core pattern; US reuses it.

**Independent Test**: The US Stocks panel loads independently of the Indian panel. It shows at least 10 US stocks with BUY/SELL/HOLD signals, confidence scores, and timestamps. Filtering works identically to the Indian panel.

**Acceptance Scenarios**:

1. **Given** the dashboard is opened, **When** data loads, **Then** the US stocks panel displays stocks from the S&P 100 universe with the same fields as the Indian panel (symbol, name, price in USD, signal, confidence, timestamp).
2. **Given** both panels are loaded, **When** the user views the dashboard, **Then** Indian stocks show prices in INR and US stocks show prices in USD — no silent currency conversion occurs.
3. **Given** the US market is closed (outside NYSE trading hours), **When** signals are displayed, **Then** a "Market Closed" badge appears and prices are marked as last-close values.

---

### User Story 3 — View Market Sentiment Overview (Priority: P3)

As an investor, I want to see an at-a-glance sentiment summary for both markets — overall bullish, bearish, or neutral — based on aggregated news and market breadth, so I can gauge macro conditions before looking at individual stocks.

**Why this priority**: Provides broader context that improves signal interpretation. Valuable but the app is usable without it (P1 and P2 deliver standalone value).

**Independent Test**: The top of the dashboard shows two sentiment gauges (one per market) labelled Bullish / Neutral / Bearish. Each gauge shows the aggregated sentiment score and the number of news articles analysed.

**Acceptance Scenarios**:

1. **Given** the dashboard loads, **When** sentiment data is available, **Then** a sentiment summary panel at the top shows Indian Market Sentiment and US Market Sentiment as labelled gauges (Bullish/Neutral/Bearish) with a score and article count.
2. **Given** fewer than 5 stocks in the market have sufficient news sentiment data (defined as ≥2 matched articles per stock), **When** the sentiment gauge is rendered, **Then** it displays "Insufficient data" rather than a potentially misleading score.

---

### User Story 4 — Drill Down into a Single Stock (Priority: P4)

As an investor, I want to click on any stock in the list and see a detailed view showing its price chart, key technical indicator values (RSI, MACD, Bollinger Bands), and recent news headlines with individual sentiment scores, so I can understand why a signal was generated.

**Why this priority**: Adds transparency and trust to signals. Users who want to validate a BUY/SELL recommendation need this. Lower priority because the list view (P1/P2) is independently valuable.

**Independent Test**: Clicking any stock row opens a detail panel or page showing a 3-month price chart, RSI/MACD/Bollinger Band values, and at least 3 recent news headlines with sentiment labels (Positive/Negative/Neutral).

**Acceptance Scenarios**:

1. **Given** a stock is displayed in the list, **When** the user clicks its row, **Then** a detail view opens showing: price chart (90-day history), RSI value with overbought/oversold indicator, MACD line and signal line values, Bollinger Band position, and recent news headlines.
2. **Given** the detail view is open, **When** the user views news headlines, **Then** each headline shows the source, publication time, and a sentiment label (Positive/Neutral/Negative).
3. **Given** the detail view is open, **Then** a risk disclaimer is prominently displayed: "This is informational only. Not financial advice."

---

### Edge Cases

- What happens when the internet connection drops mid-refresh? The dashboard MUST display the last successfully cached data with a clear "Using cached data — connection lost" warning (covered by FR-010).
- What happens when a stock symbol is delisted or unavailable from the data provider? That stock is silently skipped and a summary count of skipped stocks is shown ("3 stocks unavailable"). When all stocks in a market are unavailable, the market tab shows an error banner with an empty table (covered by FR-010).
- What happens when all technical indicators produce conflicting signals (e.g., RSI says BUY, MACD says SELL)? The system shows HOLD with a low confidence score; the conflicting sub-scores appear in `contributing_factors`, visible in the drill-down detail view (US4) only.
- What happens when the app is opened outside market hours for both markets? All data is served from cache; staleness warnings appear; no new fetch is triggered unless the user manually refreshes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Dashboard MUST display a ranked list of Indian stocks (Nifty 50 universe) with BUY, SELL, or HOLD signals on load.
- **FR-002**: Dashboard MUST display a ranked list of US stocks (S&P 100 universe) with BUY, SELL, or HOLD signals on load.
- **FR-003**: Each stock row MUST show: symbol, company name, current price (in local currency), signal type, confidence score (0–100), and last-updated timestamp. Signals MUST be colour-coded: BUY=green (#22c55e), SELL=red (#ef4444), HOLD=amber (#f59e0b). The confidence score is displayed as a plain integer (0–100); no qualitative tier label (e.g., "weak BUY") is shown — the signal type alone conveys the recommendation direction.
- **FR-004**: Every signal MUST be accompanied by a co-located risk disclaimer identifying the app as informational and not financial advice. Standard disclaimer text: "⚠️ Informational only — not financial advice." The disclaimer renders once per market table (immediately below the filter controls, above the stock rows). It MUST remain visible at all times — including when the list is filtered to zero results, when all providers have failed, and when no data has been fetched yet.
- **FR-005**: System MUST compute the following technical indicators per stock: RSI (14-period), MACD (12/26/9), Bollinger Bands (20-period), 50-day and 200-day Simple Moving Average. When only a subset of indicators is computable (e.g., SMA200 unavailable because fewer than 200 days of history exist), the signal is computed from available indicators only; missing indicators are noted in `contributing_factors`. When all indicators return NaN (fewer than 50 days of history), the stock is excluded from the signal table and counted as unavailable.
- **FR-006**: System MUST fetch broad financial market RSS feeds (e.g., Economic Times Markets, Yahoo Finance News, Moneycontrol) and filter articles per stock by matching stock symbol or company name. Sentiment per stock is derived by VADER-scoring all matched articles and averaging the result.
- **FR-007**: Signal generation MUST combine technical indicator signals and sentiment score using a weighted rule-based algorithm: 70% weight on technical indicators, 30% on news sentiment. No ML model required. Weights are fixed and not user-configurable.
- **FR-008**: System MUST display an overall market sentiment gauge (Bullish/Neutral/Bearish) for each market, derived from aggregated stock sentiment.
- **FR-009**: System MUST display a data freshness timestamp for every data point; data older than 1 hour MUST trigger a visible staleness warning. Staleness is measured from the API fetch time (`fetched_at` / `computed_at`), not from the market data's own timestamp (e.g., last trade time). The 1-hour threshold is the canonical value defined in `config.py` (`STALE_HOURS = 1`). When both a staleness warning and a "Market Closed" badge apply to the same tab, both are displayed simultaneously — the "Market Closed" badge takes visual precedence. Stale signals retain their BUY/SELL/HOLD colour; no visual degradation (e.g., greying out) is applied beyond the staleness badge.
- **FR-010**: System MUST fail loudly on data source errors — no fabricated or silently stale data may be displayed. Refresh failures are isolated per market: if India refresh succeeds and US refresh fails, India data is cached and displayed normally while the US tab shows an error banner. If the network connection drops mid-refresh, the system serves the last cached data with a "Using cached data — connection lost" warning. If all stocks in a market fail to fetch, the market tab shows an error banner and an empty stock list.
- **FR-011**: System MUST cache all fetched data to local SQLite storage to minimise repeated API calls within the same session. Each refresh overwrites the previous cache — no historical snapshots are retained. Partial cache writes within a market are committed: stocks that successfully fetched are written; per-stock failures are skipped and counted as unavailable. OHLCV history fetched for indicator computation is cached and reused for the drill-down price chart — no separate OHLCV fetch is triggered when the user opens the detail view.
- **FR-012**: User MUST be able to manually trigger a full data refresh via a refresh button. The system MUST NOT auto-refresh in the background — all data fetches are on-demand only.
- **FR-013**: User MUST be able to filter the stock list by signal type (BUY / SELL / HOLD / ALL) per market.
- **FR-014**: User MUST be able to click a stock to view its detail panel (price chart, indicator values, news headlines).
- **FR-015**: Indian stock prices MUST be displayed in INR; US stock prices MUST be displayed in USD — no implicit conversion.
- **FR-016**: System MUST indicate when a market is currently closed (outside trading hours).
- **FR-017**: Each outbound API call (nsepython, yfinance, RSS feed fetch) MUST have a per-request timeout of 30 seconds. A timed-out call is treated as a per-symbol failure (silently skipped and counted as unavailable); it does not raise `DataProviderError` unless all symbols in the batch time out.

### Key Entities

- **Stock**: symbol, company name, market (IN/US), sector, current price, currency, last updated
- **Signal**: stock reference, signal type (BUY/SELL/HOLD), confidence score (0–100), contributing factors, generated at. One record per stock; overwritten on each refresh — no history retained.
- **TechnicalSnapshot**: stock reference, RSI, MACD value, MACD signal, upper/middle/lower Bollinger Band, SMA50, SMA200, computed at
- **SentimentSnapshot**: stock reference, aggregate sentiment score, matched article count, computed at. Articles matched by filtering broad market RSS feeds against stock symbol or company name.
- **NewsItem**: stock reference, headline, source, published at, sentiment label
- **MarketSummary**: market (IN/US), overall sentiment, breadth score, last updated

### Display Behaviour

- **Default sort**: Stock lists are sorted by confidence score descending on initial load and after each refresh; filter changes preserve the sort order.
- **Empty state — pre-refresh**: When the cache is empty, each market tab shows "Click 🔄 Refresh to load data." The risk disclaimer (FR-004) is still rendered.
- **Empty state — filtered**: When the active signal filter returns zero rows, the table is replaced by "No stocks match the selected filter." The risk disclaimer remains visible.
- **Empty state — news**: When the drill-down has no matched articles, the news section shows "No recent news found for this stock."
- **Chart type**: The 90-day price history chart in the drill-down view is a line chart of the daily closing price (not a candlestick or OHLC bar chart).
- **Max headlines**: The drill-down view shows at most 10 news headlines per stock, sorted by publication date descending.
- **Refresh in progress**: Streamlit's native button-disable mechanism prevents concurrent refresh invocations; no explicit queueing or cancellation logic is required.
- **Unavailable counter**: The "X stocks unavailable" counter is shown only when X > 0; it is hidden when all stocks loaded successfully.
- **Null publication date**: News articles with no publication date display "Date unknown" in the date field.
- **Empty article text**: When a matched article has no headline or summary text, VADER returns `compound = 0.0` (neutral); the article still counts toward `article_count`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Dashboard displays signals for a minimum of 30 Indian stocks and 30 US stocks on initial load.
- **SC-002**: Initial data load (fresh fetch) completes and renders within 60 seconds on a standard home internet connection. Clock starts on Refresh button click; clock stops when the last signal row is visible in the UI.
- **SC-003**: Subsequent loads using cached data render within 5 seconds. Clock starts when the app tab is opened (or page reloaded); clock stops when the last signal row is rendered. This target applies even when staleness badges are present — the 5-second budget covers render time only.
- **SC-004**: 100% of displayed signals have a co-located risk disclaimer visible without scrolling within the stock row.
- **SC-005**: 100% of data points display a last-updated timestamp; staleness warnings appear for all data older than 1 hour.
- **SC-006**: User can identify the top 5 BUY candidates per market in under 2 minutes from opening the dashboard.
- **SC-007**: Data source errors are surfaced as visible warnings within 10 seconds of the failure — zero silent failures. Clock starts when `DataProviderError` is caught during refresh; clock stops when the error banner is rendered in the UI.

## Clarifications

### Session 2026-06-05

- Q: Should the dashboard auto-refresh while open, or only refresh on demand? → A: Manual only — data fetches happen exclusively when the user clicks the Refresh button; no background or timer-based refresh.
- Q: How should technical indicators and sentiment be weighted when generating a signal? → A: Technical-heavy — 70% weight on technical indicators, 30% on news sentiment.
- Q: Should the app keep a history of past signals per stock, or only the latest? → A: Latest only — each refresh overwrites the previous signal; no signal history is stored.
- Q: How should news sentiment be sourced — per-stock feeds or broad market feeds filtered by keyword? → A: Broad market feeds filtered by keyword — fetch top financial RSS feeds (e.g., Economic Times Markets, Yahoo Finance, Moneycontrol) and filter articles by stock symbol or company name.

## Assumptions

- The app is for personal, single-user use only; no authentication or multi-user support is required.
- Internet access is required to fetch fresh market data; fully offline operation is out of scope.
- The initial stock universe is fixed: Nifty 50 for India, S&P 100 for US. User-defined watchlists are a future enhancement.
- Signal generation is rule-based (weighted combination of technical indicators + sentiment); machine learning models are out of scope for v1.
- No actual trade execution is in scope — the app is read-only and informational.
- The app runs locally on the user's machine via `streamlit run app.py`; no hosting or deployment is required.
- Data providers: `nsepython`/`nsetools` for Indian data, `yfinance` for US data, broad financial RSS feeds (Economic Times, Yahoo Finance, Moneycontrol) + VADER for sentiment — all free, no paid APIs.
- BSE (Bombay Stock Exchange) data is secondary; NSE is the primary Indian exchange.
- Tax calculations, portfolio tracking, and order management are out of scope.
- RSS feed URLs are treated as best-effort dependencies. If a configured feed becomes unreachable or returns a non-RSS response, that feed is silently skipped; other feeds continue. Updating a broken URL requires a manual edit to `config.py`; no automated feed-health monitoring is in scope.
- The Nifty 50 and S&P 100 symbol lists are manually maintained in `config.py`. When an index is rebalanced, the user updates the hardcoded list and reruns the app; no automated rebalancing detection is in scope.
- Not all Nifty 50 symbols may be fully supported by nsepython or yfinance. Symbols that return no data are silently skipped and counted as unavailable. SC-001's 30-stock floor is a target; the app remains functional with fewer stocks when provider gaps exist.
- The SQLite cache (`~/.marketpulse/cache.db`) has no enforced size limit. For single-user use with ~150 stocks and no history retention, the database is expected to remain under 100 MB. No cleanup policy is required for v1.
