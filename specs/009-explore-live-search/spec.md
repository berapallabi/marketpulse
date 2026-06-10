# Feature Specification: Explore Live Search — Any Stock

**Feature Branch**: `009-explore-live-search`

**Created**: 2026-06-10

**Status**: Draft

**Input**: User description: "now let's enhance this explore feature. it should not get result only from cached data, but it should be able to search any stocks."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Search Any Stock by Name or Symbol (Priority: P1)

A user types a company name or ticker symbol into the Explore search box. The results include stocks from the full exchange universe — not just the ~50 Nifty / ~100 S&P stocks currently tracked. A user researching a mid-cap Indian company or a small US tech stock that isn't in the tracked universe can find it and view its basic details.

**Why this priority**: The current Explore tab is only useful if you already know a Nifty 50 or S&P 100 stock. Expanding to the full exchange universe is the core value of this enhancement.

**Independent Test**: Type "Bajaj Auto" (not in Nifty 50) in the India Explore search. Confirm it appears in results. Type "Palantir" (not in S&P 100) in the US Explore search. Confirm it appears.

**Acceptance Scenarios**:

1. **Given** the Explore tab is open on the India market, **When** the user searches for a company not in the current tracked 50, **Then** that company appears in the results list with its symbol and name.
2. **Given** the Explore tab is open on the US market, **When** the user searches for a stock not in the current tracked 100, **Then** that stock appears in the results.
3. **Given** a search query returns both cached and non-cached stocks, **When** results are displayed, **Then** all matching stocks appear together in a single list — no separate "cached vs. live" distinction visible to the user.
4. **Given** a valid query is entered, **When** no matching stocks exist on the relevant exchange, **Then** a "No results found" message is shown.
5. **Given** the data source is temporarily unavailable, **When** a search is attempted, **Then** a clear error message is shown and no crash occurs.

---

### User Story 2 - View Live Price and Details for Any Found Stock (Priority: P2)

Having found a stock that isn't in the tracked universe, the user selects it from the results. The app fetches and displays current price data and an OHLCV chart for that stock on demand. The user gets enough information to decide whether to add it to their watchlist or holdings.

**Why this priority**: Finding a stock is only half the value — seeing its current state is what drives the decision to track it. Without live data on selection, results are just names with no actionable context.

**Independent Test**: Search for a non-cached stock, select it, and confirm a current price and chart are shown within a reasonable wait time.

**Acceptance Scenarios**:

1. **Given** a non-cached stock is selected from results, **When** the detail panel opens, **Then** the current price is fetched and displayed.
2. **Given** a non-cached stock is selected, **When** the detail panel opens, **Then** a price history chart is shown (or a clear message if history is unavailable).
3. **Given** a stock is already in the cache (a tracked stock), **When** selected from Explore results, **Then** its cached data is shown immediately without a redundant fetch.
4. **Given** a live fetch for a non-cached stock fails, **When** the detail panel opens, **Then** an informative error is shown (e.g., "Could not load data for this stock") rather than a blank panel.
5. **Given** a non-cached stock's details are displayed, **When** the user adds it to watchlist or holdings, **Then** the stock is saved and visible in those tabs.

---

### Edge Cases

- What happens when the same symbol exists on both exchanges (e.g., "INFY" is on NSE and NYSE as an ADR)? — Results are always scoped to the currently active market tab; the same symbol will appear only in the correct market's results.
- What happens when a search query is very broad (e.g., "A")? — Minimum 2-character rule still applies; very broad queries may return many results but are shown in full.
- What happens if live price fetch takes too long? — Show a loading indicator while fetching; if it exceeds a reasonable timeout, show the cached price if available, or an error if not.
- What happens for stocks with very limited trading history? — Show whatever history is available; the chart renders with whatever data exists.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Explore search MUST cover two complementary modes: (a) name/symbol matching against a curated list of Nifty 500 stocks (India) and S&P 500 stocks (US), and (b) direct ticker lookup — if the user's query exactly matches a stock symbol not in the curated list, the app MUST attempt to fetch and display that ticker directly.
- **FR-002**: Search results MUST include stocks not present in the local cache, not just the currently tracked Nifty 50 / S&P 100 universe.
- **FR-003**: All results MUST be presented in a single unified list; the user MUST NOT need to distinguish between "cached" and "live" results.
- **FR-004**: When a user selects a stock that has no cached data, the app MUST fetch and display current price data on demand.
- **FR-005**: When a user selects a stock that has no cached data, the app MUST fetch and display recent price history (OHLCV chart) on demand.
- **FR-006**: If a live fetch fails, the detail panel MUST show a clear error message rather than crashing or showing a blank panel.
- **FR-007**: For stocks already in the cache, the detail panel MUST use cached data without triggering a redundant fetch.
- **FR-008**: A loading indicator MUST be shown while a live data fetch is in progress.
- **FR-009**: The add-to-watchlist and add-to-holdings controls MUST work for any stock found via search, whether cached or not.
- **FR-010**: Search scope MUST be market-aware: India market search covers Indian stocks only; US market search covers US stocks only.
- **FR-011**: All existing Explore tab behaviour for cached stocks MUST be preserved.

### Key Entities

- **Searchable stock**: Any stock from the expanded universe (beyond current tracked list). Identified by symbol, company name, and market. May have no cached signal, technical, or price data.
- **On-demand price snapshot**: Current price and recent OHLCV history fetched live for a non-cached stock when selected. Ephemeral — not necessarily persisted to the local cache between sessions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can find a stock outside the current tracked universe (e.g., any NSE mid-cap or any US small-cap) by typing its name or symbol in the Explore search box.
- **SC-002**: Selecting a non-cached stock shows its current price within 5 seconds under normal network conditions.
- **SC-003**: The unified result list shows no visible difference in presentation between cached and non-cached stocks.
- **SC-004**: All existing Explore, Buy, Watchlist, and My Holdings tab behaviour is preserved after this change.
- **SC-005**: A failed live fetch never crashes the app — an error message is shown instead.

## Assumptions

- The user has an active internet connection when searching for stocks outside the cache; live search and on-demand fetch require network access.
- "Any stocks" is scoped to the two markets the app supports (India/NSE and US/NYSE+NASDAQ). Global stocks on other exchanges are out of scope.
- On-demand fetches from the detail panel are triggered only on explicit stock selection; no background pre-fetching for search result rows.
- Signal generation (BUY/HOLD/SELL) is NOT performed for on-demand fetched stocks — only price and chart data are shown. The user can add the stock to watchlist/holdings but won't see a computed signal for it.
- The stock symbol universe for each market is obtained from the same data providers already used (nsepython for India, yfinance for US); no new external APIs are introduced.
