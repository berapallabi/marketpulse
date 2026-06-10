# Feature Specification: Watchlist & Holdings Refresh

**Feature Branch**: `010-watchlist-refresh`

**Created**: 2026-06-10

**Status**: Draft

**Input**: User description: "I should be able to refresh my watchlist/holding tabs. it should get the confidence score, all tech details, indicators, signal for the stocks listed in each section respectively."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Refresh Watchlist Analysis (Priority: P1)

A user has stocks in their watchlist under one or more cap-tier tabs (e.g., Large Cap, Mid Cap). They want up-to-date buy/sell/hold signals, confidence scores, and technical indicators for those specific stocks — without re-running analysis on the entire market.

**Why this priority**: The watchlist is the primary curation tool users rely on to track their shortlisted stocks. Stale signals on a hand-picked list directly impairs investment decision-making.

**Independent Test**: Can be tested by having at least one stock in the watchlist, clicking a "Refresh Watchlist" button in the tier tab, and verifying that signal, confidence score, RSI, MACD, Bollinger Bands, and SMA values update in the detail panel.

**Acceptance Scenarios**:

1. **Given** a user has stocks in their watchlist under the Large Cap tier tab, **When** they click "Refresh Watchlist" in that tab, **Then** only the watchlisted stocks in that tier are re-analysed and their signals, confidence scores, and technical indicators are updated.
2. **Given** the refresh is in progress, **When** the user views the tab, **Then** a loading indicator is shown and the previous data remains visible until new data arrives.
3. **Given** the refresh completes successfully, **When** the user selects a stock from the watchlist, **Then** the detail panel shows updated signal type, confidence score, RSI, MACD, Bollinger Bands, SMA-50, SMA-200, and price.
4. **Given** a watchlisted stock's data is unavailable during refresh, **When** the refresh completes, **Then** the stock is marked as unavailable and the rest of the list updates normally.

---

### User Story 2 — Refresh Holdings Analysis (Priority: P2)

A user has stocks in their holdings under one or more cap-tier tabs. They want fresh technical analysis and signals for their held positions to decide whether to add to, hold, or exit a position.

**Why this priority**: Holdings represent committed capital; users need accurate, current signals to manage risk, but the urgency is slightly lower than watchlist since holdings decisions are typically less time-sensitive than entry decisions.

**Independent Test**: Can be tested independently by having at least one stock in holdings, clicking "Refresh Holdings" in the tier tab, and verifying signal and technical data updates for only those stocks.

**Acceptance Scenarios**:

1. **Given** a user has stocks in holdings under a tier tab, **When** they click "Refresh Holdings" in that tab, **Then** only the held stocks in that tier are re-analysed and their data is updated.
2. **Given** the refresh completes, **When** the user views the holdings list, **Then** confidence score and signal type are current for each stock.
3. **Given** a holdings stock was previously unanalysed (added from Explore), **When** the refresh runs, **Then** it receives a full signal analysis for the first time and the placeholder "HOLD / 0" entry is replaced with real data.

---

### User Story 3 — Scoped Refresh per Tier Tab (Priority: P3)

A user with stocks spread across multiple cap-tier tabs (e.g., Large Cap watchlist and Mid Cap watchlist) wants to refresh only the tier they are currently viewing, rather than triggering analysis for all tiers at once.

**Why this priority**: Refreshing all tiers at once would be slow and consume unnecessary API quota. Per-tier scoping keeps the action fast and focused.

**Independent Test**: Can be tested by having watchlisted stocks in two different tier tabs, refreshing only the Large Cap tab, and verifying that Mid Cap watchlist stocks do not change.

**Acceptance Scenarios**:

1. **Given** watchlisted stocks exist in both Large Cap and Mid Cap tabs, **When** the user refreshes the Large Cap watchlist, **Then** only Large Cap watchlist stocks are re-analysed.
2. **Given** the user is viewing the Mid Cap tab, **When** they click refresh, **Then** only Mid Cap stocks in that section are refreshed.

---

### Edge Cases

- What happens when a watchlist or holdings section is empty? The refresh button should be absent or disabled with a tooltip.
- What happens when a stock's market data is unavailable during refresh? The stock is skipped with a visible "unavailable" indicator; the rest complete normally.
- What happens if the refresh is triggered again while a previous refresh is still running? The button is disabled for the duration to prevent duplicate fetches.
- What happens when all stocks in a section fail to fetch? An error message is shown and existing cached data is preserved.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each watchlist section within a tier tab MUST have a dedicated "Refresh" button that triggers analysis for only the stocks in that section.
- **FR-002**: Each holdings section within a tier tab MUST have a dedicated "Refresh" button that triggers analysis for only the stocks in that section.
- **FR-003**: The refresh MUST fetch and store: current price, signal type (BUY/SELL/HOLD), confidence score, RSI-14, MACD value, MACD signal line, Bollinger Bands (upper/middle/lower), SMA-50, and SMA-200 for each stock in the section.
- **FR-004**: The refresh MUST NOT re-analyse stocks outside the targeted section (scope isolation).
- **FR-005**: A loading indicator MUST be shown while the refresh is in progress; existing data MUST remain visible during the fetch.
- **FR-006**: The refresh button MUST be disabled while a refresh for that section is already in progress, preventing duplicate runs.
- **FR-007**: If a stock is unavailable during refresh, the system MUST skip it, record an unavailability count, and continue refreshing the remaining stocks.
- **FR-008**: After a successful refresh, the last-refreshed timestamp MUST be visible in the section header.
- **FR-009**: A stock that was previously added from Explore with a placeholder signal (HOLD, confidence 0) MUST be upgraded to a real signal after the section refresh runs.

### Key Entities

- **RefreshScope**: The combination of market (IN/US), section (watchlist or holdings), and cap-tier label that defines which stocks are included in a single refresh run.
- **StockAnalysisResult**: The per-stock output of a refresh — signal type, confidence score, technical snapshot (RSI, MACD, Bollinger, SMA), and current price.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Clicking "Refresh" in a watchlist or holdings section updates signals and technical indicators for all stocks in that section within 30 seconds for up to 10 stocks.
- **SC-002**: Only the targeted section's stocks are re-analysed; stocks in other sections show no data change after the refresh.
- **SC-003**: After refresh, every stock in the section displays a non-placeholder signal type and a confidence score greater than 0 (provided market data is available).
- **SC-004**: Stocks added from Explore (previously placeholder HOLD/0) receive a full analysis result after being included in a watchlist/holdings refresh.
- **SC-005**: The refresh button is visually disabled for the entire duration of an in-progress refresh, preventing double-submission.

## Assumptions

- The existing per-stock technical analysis and signal generation logic (currently used by the full-market refresh) will be reused as-is; this feature only changes the scope of which stocks are passed to it.
- Sentiment/news analysis is included in the refresh to keep signal quality consistent with the full-market refresh.
- The refresh is triggered manually by the user; automatic/scheduled refresh is out of scope.
- Each tier tab has separate refresh controls for its watchlist section and its holdings section (two buttons per tier where both sections have stocks).
- Network connectivity is assumed; offline handling beyond the existing error-skip pattern is out of scope.
