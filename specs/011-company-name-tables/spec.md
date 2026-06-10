# Feature Specification: Company Name in Stock Tables

**Feature Branch**: `011-company-name-tables`

**Created**: 2026-06-10

**Status**: Draft

**Input**: User description: "add company name also in all the tables"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Company Name Visible in Market Tab Tables (Priority: P1)

A user viewing the Buy, Watchlist, or My Holdings tab sees a populated "Company" column alongside each stock's ticker symbol in the table. Instead of a blank name field, they see the full company name (e.g., "Tata Consultancy Services" next to "TCS"), making it easier to identify stocks without knowing all ticker symbols by heart.

**Why this priority**: The Company column already exists in the table layout but shows blank for all rows. This is immediately visible to any user and reduces the utility of the table — fixing it is high impact with no new UX surface area required.

**Independent Test**: Open any Market tab (Buy, Watchlist, or My Holdings) with at least one stock loaded. Verify that the "Company" column in the table shows a non-empty company name for each stock row.

**Acceptance Scenarios**:

1. **Given** the Buy tab is open with BUY signal rows loaded, **When** the user views the stock table, **Then** each row shows the company's full name in the Company column alongside the ticker symbol.
2. **Given** the Watchlist tab is open with stocks in the watchlist, **When** the user views the watchlist table, **Then** each stock row shows its company name.
3. **Given** the My Holdings tab is open with stocks in holdings, **When** the user views the holdings table, **Then** each stock row shows its company name.
4. **Given** a stock was added from the Explore tab (with company name stored), **When** it appears in the watchlist or holdings table, **Then** its company name is shown correctly.

---

### User Story 2 — Company Name Visible in Explore Search Results (Priority: P2)

A user searching for stocks in the Explore tab sees the company name alongside each result's ticker symbol in the search results table, making it easy to confirm they have the right stock before clicking through to its details.

**Why this priority**: The Explore tab is the primary entry point for discovering new stocks. Showing company names in search results is table-stakes for usability and consistent with the Market tab behaviour once US1 is fixed.

**Independent Test**: Open the Explore tab, type a partial company name (e.g., "Tata"), and verify that the results table shows company names for all matching rows.

**Acceptance Scenarios**:

1. **Given** the user searches for a partial ticker or company name in the Explore tab, **When** results appear, **Then** each result row shows the company's full name.
2. **Given** a result was fetched live (not from cached data), **When** it appears in the table, **Then** the company name is still shown (using the name from the search index if the live fetch does not yet have it).

---

### Edge Cases

- What happens when a company name is not available for a stock? The cell shows the ticker symbol as a fallback rather than a blank or error.
- What happens when a stock was added before company names were stored? The company name is fetched from the stored stock record; if absent, the ticker is used as a fallback.
- What happens for stocks added via direct ticker input in Explore (where the company name may only be available after a live fetch)? A reasonable fallback (ticker or "—") is shown until the name is available.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every row in the Buy tab signal table MUST display the company's full name in the Company column.
- **FR-002**: Every row in the Watchlist tab table MUST display the company's full name in the Company column.
- **FR-003**: Every row in the My Holdings tab table MUST display the company's full name in the Company column.
- **FR-004**: Every row in the Explore tab search results table MUST display the company's full name alongside the ticker symbol.
- **FR-005**: When a company name is not available, the system MUST display the ticker symbol as a fallback — never a blank cell.
- **FR-006**: Company name display MUST be consistent across all four table surfaces (Buy, Watchlist, Holdings, Explore) for the same stock.

### Key Entities

- **StockRow**: A row in any stock table, consisting of at minimum: ticker symbol, company name, signal type, confidence score, and price. The company name must be sourced from the stored stock record.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After the fix, 100% of rows in the Buy, Watchlist, Holdings, and Explore tables show a non-blank Company column for stocks that have been analysed or searched.
- **SC-002**: No existing table columns are removed or reordered as a result of this change.
- **SC-003**: The company name shown matches the name stored for that stock — no mismatches between the detail panel and the table row.

## Assumptions

- The company name is already stored in the stocks table in the database for every stock that has been fetched or analysed; this feature only ensures it is surfaced in the table query results.
- The Explore search result rows already include company names from the stock universe; US2 may require only minor validation or a fallback fix.
- The fix applies to both India (IN) and US markets.
- No new UI columns are introduced — the existing "Company" column is populated, not replaced.
