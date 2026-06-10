# Feature Specification: Explore Tab — Stock Search

**Feature Branch**: `009-explore-tab`

**Created**: 2026-06-10

**Status**: Draft

**Input**: User description: "let's add another feature. along with buy/watchlist/holdings tab, there should be one new tab called Explore. This tab does not need the cap tier or the refresh button. On this tab, user should be able to search for any stock by their name/symbol, the result list should appear, on selection, it should show the details, and it can be added to either watchlist or holdings. Other tab feature should stay as in"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Search and View Stock Details (Priority: P1)

A user wants to look up a specific stock they have in mind — perhaps a company they read about — without browsing by cap tier. They type part of the company name or ticker symbol into a search box. A list of matching stocks appears. They click a stock to see its full detail panel: price, signal, technical indicators, OHLCV chart, and recent news.

**Why this priority**: This is the core value of the Explore tab. Without search and detail view, the tab has no purpose.

**Independent Test**: Can be fully tested by typing a query in the Explore tab's search box, verifying matching results appear, selecting one, and confirming the detail panel shows.

**Acceptance Scenarios**:

1. **Given** the Explore tab is active and no query is entered, **When** the user views the tab, **Then** a search input is shown with a prompt, and the result list is empty.
2. **Given** a search query of 2+ characters is entered, **When** the query matches one or more stocks by name or symbol, **Then** a result list shows those stocks with symbol, company name, and current signal type.
3. **Given** a search query is entered, **When** the query matches no stocks, **Then** a "No results found" message is shown.
4. **Given** results are shown, **When** the user selects a stock, **Then** the detail panel on the right shows full details for that stock (price, signal, chart, news).
5. **Given** a stock is selected, **When** the user switches to another tab and returns to Explore, **Then** the search state and selection are preserved within the session.

---

### User Story 2 - Add to Watchlist or Holdings from Explore (Priority: P2)

Having found and reviewed a stock in Explore, the user wants to track it. From the detail panel they can add it to their watchlist or holdings using the same controls available in other tabs.

**Why this priority**: Explore would be read-only without this. Adding to watchlist/holdings closes the loop between discovery and tracking.

**Independent Test**: Can be tested by finding a stock via search, clicking "Add to Watchlist" in the detail panel, switching to the Watchlist tab, and confirming the stock appears there.

**Acceptance Scenarios**:

1. **Given** a stock is selected in Explore and is not in the watchlist, **When** the user clicks "Add to Watchlist", **Then** the stock is added and the button label changes to "Remove from Watchlist".
2. **Given** a stock is selected in Explore and is already in the watchlist, **When** the detail panel opens, **Then** the button shows "Remove from Watchlist".
3. **Given** a stock is added to watchlist from Explore, **When** the user switches to the Watchlist tab, **Then** the stock appears there immediately.
4. **Given** a stock is selected in Explore, **When** the user adds it to holdings, **Then** the same behaviour applies: button state updates and the stock appears in the My Holdings tab.

---

### Edge Cases

- What happens when the search query is a single character? — Require a minimum of 2 characters; show a hint rather than results.
- What happens when no data has been loaded yet (empty cache)? — Show a message indicating no stock data is available and suggest refreshing a tier in the Buy tab first.
- What happens when the user clears the search box? — The result list clears; the detail panel retains the last selected stock until a new selection is made.
- What happens when a selected stock has no cached technical or news data? — The detail panel shows available data and gracefully omits missing sections without an error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The dashboard MUST include an "Explore" tab alongside the existing Buy, Watchlist, and My Holdings tabs.
- **FR-002**: The Explore tab MUST display a text search input at the top; it MUST NOT include a cap tier selector or a refresh button.
- **FR-003**: The search input MUST filter the known stock universe by partial, case-insensitive match on symbol or company name.
- **FR-004**: Search results MUST update as the user types; no submit button is required.
- **FR-005**: A minimum of 2 characters MUST be entered before results are shown.
- **FR-006**: Each result row MUST show at minimum: ticker symbol, company name, and current signal type (BUY / HOLD / SELL) if available, or a neutral indicator if no signal data exists.
- **FR-007**: Selecting a result MUST display the stock's full detail panel, identical to the panel used in Buy, Watchlist, and My Holdings tabs.
- **FR-008**: The detail panel in Explore MUST include "Add to Watchlist / Remove from Watchlist" and "Add to Holdings / Remove from Holdings" controls.
- **FR-009**: Watchlist and holdings changes made from Explore MUST persist to the same store used by the other tabs, with changes immediately visible on tab switch.
- **FR-010**: When no search query is entered, the result list MUST be empty and a prompt MUST be shown.
- **FR-011**: When a query returns no matches, a "No results found" message MUST be displayed.
- **FR-012**: All existing tabs (Buy, Watchlist, My Holdings) MUST remain unchanged in behaviour and layout.

### Key Entities

- **Stock search result**: A stock known to the system, identified by symbol and company name, with an optional current signal type. Derived from cached signal and quote data; not a new persistent entity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can find a stock by typing 2 or more characters and see matching results without any additional interaction beyond typing.
- **SC-002**: Selecting a stock from results and viewing its detail panel requires no more than 2 user interactions (type query → click result → detail appears).
- **SC-003**: A stock added to watchlist or holdings from Explore is visible in the respective tab immediately on switching — no reload required.
- **SC-004**: All existing tab functionality (Buy signals, Watchlist, My Holdings) continues to work exactly as before after the Explore tab is added.
- **SC-005**: When the stock cache is empty, the Explore tab shows a clear empty state rather than an error.

## Assumptions

- Search is scoped to stocks currently in the local cache (the tracked Nifty 50 and S&P 100 universes). Searching outside that universe is out of scope.
- The Explore tab is market-aware: the India / US market toggle at the top level determines which stock universe is searched.
- Technical detail data shown in the detail panel is read from the local cache. If a stock has never been refreshed, only available data is shown; missing sections are omitted gracefully.
- No new data fetching is triggered from the Explore tab — it reads from existing cached data only. Users refresh data via the tier refresh button in the Buy tab.
- Minimum search query length is 2 characters to avoid an overwhelming result set on single-character input.
