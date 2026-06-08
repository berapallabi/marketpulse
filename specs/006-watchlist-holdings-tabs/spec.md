# Feature Specification: Watchlist & My Holdings Tabs

**Feature Branch**: `007-watchlist-holdings-tabs`

**Created**: 2026-06-08

**Status**: Draft

**Input**: User description: "let's remove all/hold/sell tabs. and add Watchlist/My Holdings tab. That means, the new tabs should be Buy/Watchlist/My Holdings. All other functionalities should stay as in. No change in design"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Navigate Between Buy, Watchlist, and My Holdings (Priority: P1)

A user opens the dashboard and sees three tabs within each market cap tier: **Buy**, **Watchlist**, and **My Holdings**. The previous All/HOLD/SELL filter options are gone. The user clicks each tab to view the relevant stock list.

**Why this priority**: This is the structural replacement — the entire feature hinges on swapping the four-option filter (All/BUY/SELL/HOLD) with a three-tab layout (Buy/Watchlist/My Holdings). Everything else depends on this being correct first.

**Independent Test**: Open the dashboard, navigate to any market and cap tier. Verify that the segmented control shows exactly three options: Buy, Watchlist, My Holdings — and that All, SELL, and HOLD options are absent.

**Acceptance Scenarios**:

1. **Given** the dashboard is loaded and a market (India or US) is selected, **When** a user views any cap tier, **Then** the signal filter shows exactly three tabs: Buy, Watchlist, My Holdings — in that order.
2. **Given** the Buy tab is selected, **When** the user views the stock list, **Then** only stocks with a BUY signal are shown (same behaviour as the previous BUY filter).
3. **Given** the All, SELL, or HOLD options previously existed, **When** the updated dashboard is loaded, **Then** none of those options appear in the signal filter.

---

### User Story 2 — Add and View Stocks in Watchlist (Priority: P2)

A user identifies a stock they want to monitor without yet committing to a buy decision. They add it to their Watchlist from the stock detail panel or the stock row. When they switch to the Watchlist tab, the stock appears there.

**Why this priority**: Watchlist is the primary new capability introduced. It must work end-to-end before My Holdings adds further complexity.

**Independent Test**: Add one stock to the Watchlist, switch to the Watchlist tab, and verify the stock appears there. Remove the stock and verify it disappears.

**Acceptance Scenarios**:

1. **Given** a stock is displayed in the Buy tab or detail panel, **When** the user adds it to the Watchlist, **Then** it appears in the Watchlist tab across all sessions (persisted).
2. **Given** the Watchlist tab is active, **When** there are no stocks in the watchlist, **Then** an empty-state message is shown (e.g., "No stocks in your watchlist yet").
3. **Given** a stock is in the Watchlist, **When** the user removes it, **Then** it is immediately removed from the Watchlist tab.
4. **Given** a stock is in the Watchlist, **When** its signal updates (e.g., it becomes a BUY), **Then** its current signal and details are shown correctly in the Watchlist tab.

---

### User Story 3 — Add and View Stocks in My Holdings (Priority: P3)

A user tracks stocks they already own. They add a stock to My Holdings from the stock detail panel or row. When they switch to the My Holdings tab, those stocks are listed.

**Why this priority**: My Holdings mirrors the Watchlist pattern but represents owned positions. It follows the same persist/display cycle and builds on the same interaction model.

**Independent Test**: Add one stock to My Holdings, switch to the My Holdings tab, and verify it appears. Remove it and verify it disappears.

**Acceptance Scenarios**:

1. **Given** a stock is displayed in any tab, **When** the user adds it to My Holdings, **Then** it appears in the My Holdings tab and persists across sessions.
2. **Given** the My Holdings tab is active, **When** there are no stocks added, **Then** an empty-state message is shown (e.g., "No holdings added yet").
3. **Given** a stock is in My Holdings, **When** the user removes it, **Then** it is immediately removed from My Holdings.
4. **Given** a stock exists in both Watchlist and My Holdings, **When** the user views each tab, **Then** the stock appears correctly in both tabs independently.

---

### Edge Cases

- What happens when the same stock is added to Watchlist (or My Holdings) more than once — is duplication prevented?
- How does the Watchlist or My Holdings tab behave when the underlying market data has not yet loaded (loading state)?
- If a stock is delisted or removed from the universe, does it gracefully disappear from Watchlist/My Holdings or show a stale entry?
- Does adding a stock to Watchlist from one market (India) affect the Watchlist under the other market (US) — are watchlists per-market or global?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The signal filter within each cap tier MUST display exactly three options: **Buy**, **Watchlist**, **My Holdings** — replacing the previous All/BUY/SELL/HOLD options.
- **FR-002**: The **Buy** tab MUST display the same stock list as the previous BUY signal filter — stocks with a current BUY signal, including the enriched per-tier buy data when available.
- **FR-003**: The **Watchlist** tab MUST display stocks that the user has explicitly added to their watchlist.
- **FR-004**: The **My Holdings** tab MUST display stocks that the user has explicitly added as holdings.
- **FR-005**: Users MUST be able to add any stock to the Watchlist from the stock detail panel or the stock list row.
- **FR-006**: Users MUST be able to add any stock to My Holdings from the stock detail panel or the stock list row.
- **FR-007**: Users MUST be able to remove a stock from the Watchlist or My Holdings.
- **FR-008**: Watchlist and My Holdings entries MUST persist across page reloads and sessions (stored in the existing local database).
- **FR-009**: Each of Watchlist and My Holdings MUST display an empty-state message when no stocks have been added.
- **FR-010**: Duplicate entries in Watchlist or My Holdings (same stock added twice) MUST be prevented.
- **FR-011**: Watchlist and My Holdings MUST be scoped per market (India watchlist separate from US watchlist).
- **FR-012**: The visual design of the three-tab filter MUST match the existing segmented control style — no design changes.
- **FR-013**: All existing functionality unrelated to the removed All/SELL/HOLD filters (refresh, detail panel, tier tabs, market tabs) MUST remain unchanged.

### Key Entities

- **Watchlist Entry**: A user-saved stock symbol associated with a market, representing a stock the user wants to monitor.
- **Holding Entry**: A user-saved stock symbol associated with a market, representing a stock the user currently owns.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The signal filter on every cap tier shows exactly 3 tabs (Buy, Watchlist, My Holdings) with 0 occurrences of All, SELL, or HOLD options.
- **SC-002**: A stock added to the Watchlist or My Holdings appears in the correct tab within 1 page interaction (no manual refresh required).
- **SC-003**: Watchlist and My Holdings entries survive a full page reload — 100% persistence rate.
- **SC-004**: Adding a duplicate stock to Watchlist or My Holdings results in no new entry — the list count stays the same.
- **SC-005**: The Buy tab shows results identical to the previous BUY signal filter — 0 regression in stock list content.
- **SC-006**: All pre-existing features (refresh, detail panel, tier navigation, market navigation) pass existing tests without modification.

## Assumptions

- The existing segmented control component (`st.segmented_control`) will continue to be used for the three new tabs — only the options change, not the component type.
- Watchlist and My Holdings data will be stored in the existing SQLite cache database, following the same persistence pattern used for tier buy data.
- No authentication or multi-user support is required — this is a single-user local application.
- Stocks in Watchlist and My Holdings display the same columns and detail panel as the Buy tab — no custom column set per tab.
- The add-to-watchlist and add-to-holdings actions will be implemented as buttons in the stock detail panel and/or stock list row — exact placement to be decided during planning.
- A stock can appear in both Watchlist and My Holdings simultaneously without conflict.
- Watchlist and My Holdings are per-market (India and US are independent lists).
