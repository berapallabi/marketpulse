# Feature Specification: Swap Tab Hierarchy

**Feature Branch**: `008-swap-tab-hierarchy`

**Created**: 2026-06-08

**Status**: Draft

**Input**: User description: "let's swap the two tab rows. currently the main tab is cap tier, inside that we have buy/watchlist/holdings. it should be the other way. Top tier should be buy/watchlist/holding, under that we should have cap tiers. Designs should also be changed accordingly. Current design for buy row should be applied to cap row. vice versa"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Navigate by Intent First, Then by Tier (Priority: P1)

A user opens a market (India or US) and immediately sees three top-level tabs: **Buy**, **Watchlist**, and **My Holdings**. They choose their intent first — e.g. "I want to look at buy opportunities" — and then narrow by cap tier inside that tab. The previous layout required the user to pick a tier first and then a signal filter, which was backwards relative to how most users think.

**Why this priority**: This is the structural inversion that defines the entire feature. Every other change depends on this being correct.

**Independent Test**: Open the app, select any market. The first tab row visible shows Buy, Watchlist, My Holdings — not cap tier labels. Selecting "Buy" then shows a second row of cap tier tabs (Large Cap, Mid Cap, Small Cap / Mega Cap, etc.) beneath it.

**Acceptance Scenarios**:

1. **Given** the dashboard is loaded and a market is selected, **When** the user views the market section, **Then** the outermost tab row shows exactly: Buy, Watchlist, My Holdings — in that order.
2. **Given** the user selects the Buy tab, **When** the Buy tab is active, **Then** a second row of cap tier tabs appears beneath it (one tab per tier for that market).
3. **Given** the user selects the Watchlist tab, **When** the Watchlist tab is active, **Then** a second row of cap tier tabs appears beneath it.
4. **Given** the user selects the My Holdings tab, **When** it is active, **Then** a second row of cap tier tabs appears beneath it.
5. **Given** any outer tab is selected, **When** the user switches to a different cap tier tab within it, **Then** the outer tab selection is preserved and only the tier content changes.

---

### User Story 2 — Visual Design Swapped to Match New Hierarchy (Priority: P2)

The visual weight of each tab row reflects its role in the hierarchy. The outer (primary) row — now Buy/Watchlist/My Holdings — uses the bold, prominent tab style that the cap tier row previously used. The inner (secondary) row — now cap tiers — uses the compact segmented-control style that Buy/Watchlist/My Holdings previously used.

**Why this priority**: Without the design swap, the visual hierarchy would contradict the navigation hierarchy — the inner row would look more prominent than the outer row, which would confuse users.

**Independent Test**: Open the app and compare the two tab rows. The outer row (Buy/Watchlist/My Holdings) is visually dominant — it uses the larger, bold tab style. The inner cap tier row is visually subordinate — it uses the compact segmented-control style.

**Acceptance Scenarios**:

1. **Given** both tab rows are visible, **When** compared visually, **Then** the outer Buy/Watchlist/My Holdings row uses the same prominent style that cap tiers previously used.
2. **Given** both tab rows are visible, **When** compared visually, **Then** the inner cap tier row uses the same compact style that Buy/Watchlist/My Holdings previously used.
3. **Given** the outer tab is on Buy and an inner tier tab is selected, **When** the user switches the outer tab to Watchlist, **Then** the same tier tabs appear in the same compact style within Watchlist.

---

### Edge Cases

- What is the default selected tab when a market tab is first opened — Buy tab, first tier?
- If a user's Watchlist contains stocks from only one cap tier, do all tier tabs still appear (with empty states for tiers that have no watchlisted stocks)?
- If a user switches from Buy → Watchlist and back to Buy, is the previously selected cap tier remembered or reset?
- Does the layout work correctly when the market has an uneven number of tiers (e.g., India has 3, US has 4)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Within each market section, the outermost tab row MUST display exactly three tabs in order: **Buy**, **Watchlist**, **My Holdings**.
- **FR-002**: Within each outer tab (Buy, Watchlist, My Holdings), a second inner tab row MUST display the cap tier tabs for that market (e.g., Large Cap, Mid Cap, Small Cap for India).
- **FR-003**: The cap tier tabs in the inner row MUST be the same tiers as previously shown in the outer row — no tiers added or removed.
- **FR-004**: The stock list displayed inside each inner cap tier tab MUST follow the same filtering logic as before: Buy tab shows BUY signals, Watchlist tab shows watchlisted stocks, My Holdings tab shows held stocks — scoped to the selected tier.
- **FR-005**: The visual style of the outer Buy/Watchlist/My Holdings tab row MUST use the design previously applied to the cap tier tab row (the more prominent, bold style).
- **FR-006**: The visual style of the inner cap tier tab row MUST use the design previously applied to the Buy/Watchlist/My Holdings row (the compact segmented-control style).
- **FR-007**: The refresh button and detail panel layout MUST continue to appear correctly within each inner cap tier tab.
- **FR-008**: The default selection when first loading a market MUST be the Buy tab (outer) and the first cap tier (inner).
- **FR-009**: All existing behaviours — add/remove from Watchlist, add/remove from Holdings, stock detail panel, refresh — MUST remain fully functional with no regressions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The outer tab row shows exactly 3 tabs (Buy, Watchlist, My Holdings) on every market view — 0 occurrences of cap tier labels in the outer row.
- **SC-002**: Each outer tab contains the correct number of inner cap tier tabs — 3 for India (Large/Mid/Small Cap), 4 for US (Mega/Large/Mid/Small Cap) — verified across all tabs.
- **SC-003**: The visual prominence order is correct: outer tab row is visually dominant over inner tab row on 100% of views.
- **SC-004**: All pre-existing features (watchlist add/remove, holdings add/remove, refresh, detail panel) pass existing tests with 0 regressions.
- **SC-005**: Switching between outer tabs preserves the inner tab selection — the previously active tier remains selected when returning to the same outer tab within a session.

## Assumptions

- Cap tier labels and counts per market remain unchanged (India: Large Cap / Mid Cap / Small Cap; US: Mega Cap / Large Cap / Mid Cap / Small Cap).
- The "prominent tab style" refers to the `st.tabs()` component styling as currently applied to cap tiers; the "compact segmented-control style" refers to the `st.segmented_control()` component currently applied to Buy/Watchlist/My Holdings.
- The default outer tab on market load is Buy; the default inner tab is the first cap tier in the market's tier order.
- The refresh button and detail panel remain within the inner cap tier context (not moved to the outer level).
- No changes to the India/US market tab row at the very top — only the two rows below it are affected.
