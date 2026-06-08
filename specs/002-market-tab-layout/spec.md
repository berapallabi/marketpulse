# Feature Specification: Market Tab Layout Restructure

**Feature Branch**: `002-market-tab-layout`

**Created**: 2026-06-08

**Status**: Draft

**Input**: User description: "let's modify the UI a bit. main two tabs - India market/US market. both tabs should have similar structure - All, buy, sell, hold."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Signal Filter as Tabs (Priority: P1)

As an investor, I open the dashboard and see two top-level market tabs (India, US). Inside each tab, four sub-tabs — All, BUY, SELL, HOLD — replace the radio-button filter currently used, so the filter feels like a first-class navigation element rather than a form widget.

**Why this priority**: This is the entire scope of the feature. The sub-tab layout is a direct replacement of the radio-button filter; no other interaction model changes.

**Independent Test**: Open the dashboard. Each market tab (India, US) contains exactly four sub-tabs labelled "All", "BUY", "SELL", "HOLD". Clicking a sub-tab shows only stocks matching that signal type (or all stocks for "All"). The stock table and detail panel behave identically to the current implementation.

**Acceptance Scenarios**:

1. **Given** the India tab is active and data has been loaded, **When** the user clicks the "BUY" sub-tab, **Then** only stocks with a BUY signal are displayed, sorted by confidence score descending.
2. **Given** the India tab is active and "BUY" sub-tab is selected, **When** the user switches to the US tab, **Then** the US tab opens on its previously selected sub-tab (or "All" by default) — the India sub-tab selection is preserved independently.
3. **Given** a sub-tab filter returns zero matching stocks, **When** the sub-tab is active, **Then** the table area shows "No stocks match the selected filter." and the risk disclaimer remains visible.
4. **Given** the dashboard has no cached data, **When** any sub-tab is active, **Then** the empty state "Click 🔄 Refresh to load data." is shown and the risk disclaimer is still rendered.
5. **Given** the US tab is active with "SELL" sub-tab selected, **When** the user selects a stock row, **Then** the drill-down detail panel opens below the table as before.

---

### Edge Cases

- Sub-tab selections for India and US are independent — switching market tabs preserves each market's last-selected signal sub-tab.
- The "All" sub-tab is always the default when data first loads or the dashboard is opened cold.
- The risk disclaimer (FR-004 from the base spec) remains visible within every sub-tab, including when zero rows are shown.
- The staleness warning and "Market Closed" badge (FR-009, FR-016) appear at the market-tab level, not per sub-tab.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each market tab (India, US) MUST contain four signal filter sub-tabs labelled "All", "BUY", "SELL", "HOLD" in that order.
- **FR-002**: The "All" sub-tab MUST be the default active sub-tab for each market on initial load and after a data refresh.
- **FR-003**: Selecting a signal sub-tab MUST display only stocks whose signal type matches the sub-tab label; "All" displays every stock regardless of signal.
- **FR-004**: Sub-tab selection state for India and US MUST be independent — changing the active sub-tab in one market tab MUST NOT affect the other.
- **FR-005**: All existing behaviours from the base spec MUST be preserved within the sub-tab structure: confidence sort, colour-coded signals, staleness badges, risk disclaimer, drill-down detail panel, unavailable stock counter, empty states, market-closed badge.
- **FR-006**: The radio-button signal filter currently rendered in each market tab MUST be removed and replaced entirely by the sub-tab layout.

### Key Entities

No new data entities are introduced. This feature modifies navigation/layout only.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each market tab exposes exactly four sub-tabs (All, BUY, SELL, HOLD) — verifiable by inspection.
- **SC-002**: Clicking a signal sub-tab filters the stock list within one visible re-render with no full page reload.
- **SC-003**: All existing acceptance scenarios from the base spec (001-stock-market-dashboard) pass without modification after this change — no regression in signal display, filtering, drill-down, disclaimers, or staleness warnings.
- **SC-004**: Sub-tab state is independent per market: selecting "SELL" in the India tab and then switching to the US tab shows the US tab on "All" (or its previously selected sub-tab), not "SELL".

## Assumptions

- The existing top-level tab structure (India tab | US tab) is unchanged — this feature only modifies what is rendered inside each tab.
- Sub-tab persistence across market tab switches is session-scoped (in-memory); it does not need to survive page reloads.
- No design changes to the stock table rows, confidence column, colour coding, or detail panel are in scope.
- The refresh button in the sidebar continues to trigger a full data reload for the active market; sub-tab selection resets to "All" after a refresh completes.
