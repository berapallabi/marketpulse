# Feature Specification: Per-Tier BUY Refresh — Top 20 Buy Stocks

**Feature Branch**: `004-buy-focus-per-cap`

**Created**: 2026-06-08

**Status**: Draft

**Input**: User description: "let's now focus on only the buying stocks. and let's size it down a bit. for different caps, there should be different refresh buttons, clicking on each refresh button should fetch top 20 buy stocks.. let's keep the sell and hold tab as in for now. we will add new requirements for that later"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Per-Tier BUY Refresh: View Top 20 Buy Stocks for a Cap Tier (Priority: P1)

An investor opens the dashboard and wants to see the strongest BUY opportunities within a specific market-cap category — e.g., just Large Cap India or just Mega Cap US — without waiting for a full 50- or 100-stock refresh. They click a Refresh button scoped to that tier's BUY view, and within seconds see up to 20 stocks ranked by signal confidence, ready to explore.

**Why this priority**: This is the entire feature — a targeted, faster refresh that narrows the data fetch to one cap tier's BUY candidates. Delivering this alone is a complete, useful increment.

**Independent Test**: Navigate to India → Large Cap → BUY sub-tab. Click the tier Refresh button. Verify that only BUY signals are fetched and displayed (up to 20 stocks), ranked by confidence, without affecting the SELL or HOLD tabs or other cap tier tabs.

**Acceptance Scenarios**:

1. **Given** the India Large Cap BUY tab is open, **When** the user clicks the Large Cap BUY Refresh button, **Then** the system fetches fresh signal data for Large Cap India stocks only, displays up to 20 BUY signals sorted by confidence score descending, and the SELL and HOLD sub-tabs for the same tier remain unchanged.

2. **Given** a cap tier has fewer than 20 BUY signals, **When** the user clicks that tier's BUY Refresh button, **Then** all available BUY signals for that tier are displayed (not padded or errored).

3. **Given** the US Mega Cap BUY tab is open, **When** the user clicks the Mega Cap BUY Refresh button, **Then** fresh signals are fetched for Mega Cap US stocks and up to 20 BUY results are shown, while the US Large Cap, Mid Cap, and Small Cap BUY tabs retain their previous data.

4. **Given** a network or data error occurs during tier refresh, **When** the error is encountered, **Then** the error is shown inline in that tier's BUY tab without affecting other tabs or markets.

5. **Given** the user has not yet clicked any tier BUY Refresh button, **When** the BUY tab is first opened, **Then** a prompt to click Refresh is displayed (no stale data assumed).

---

### Edge Cases

- What happens when a cap tier has zero stocks classified into it (e.g., no Small Cap stocks in the Nifty 50 universe)? The Refresh button is still shown but the result is an empty list with a "No stocks in this tier" message.
- What happens when all stocks in a tier produce SELL or HOLD signals and zero BUY signals? Display "No BUY signals found for this tier" rather than an empty table.
- What if the SELL / HOLD tabs contain data from a previous full refresh and the user clicks a per-tier BUY Refresh? The SELL / HOLD data must not change.
- What if the user clicks multiple tier BUY Refresh buttons in quick succession? Each refresh is independent; results are shown per tier without cross-contamination.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each cap tier tab MUST contain a dedicated Refresh button scoped to that tier's BUY sub-tab.
- **FR-002**: Clicking a tier BUY Refresh button MUST fetch fresh signal data only for stocks already classified into that cap tier (not the full market universe).
- **FR-003**: The BUY sub-tab for a tier MUST display at most 20 stocks after a tier refresh, ranked by confidence score from highest to lowest.
- **FR-004**: If a tier contains fewer than 20 BUY signals, all available BUY signals for that tier MUST be shown.
- **FR-005**: The SELL and HOLD sub-tabs MUST NOT be affected by a tier BUY Refresh — their data remains from the last global refresh.
- **FR-006**: Other cap tier tabs (sibling tiers in the same market) MUST NOT be affected by a single tier's BUY Refresh.
- **FR-007**: The tier BUY Refresh button MUST be visually distinct from the global sidebar Refresh button.
- **FR-008**: While a tier BUY Refresh is in progress, the button MUST show a loading indicator and be non-interactive.
- **FR-009**: If no BUY signals are found for the tier after refresh, the BUY sub-tab MUST display an informative empty-state message rather than an error.
- **FR-010**: The existing global Refresh button in the sidebar MUST remain functional and continue to refresh all markets and tiers (for SELL/HOLD data and initial load).

### Key Entities

- **CapTierBuyResult**: A ranked list of up to 20 BUY signals for a specific (market, cap_tier) pair, fetched on demand. Key attributes: market, cap_tier, signals (list, max 20), fetched_at.
- **Signal**: Existing entity — unchanged. BUY signals are filtered from the existing signal set by signal_type = "BUY".

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A tier BUY Refresh returns and displays results within a time proportional to the number of stocks in that tier (typically faster than a full market refresh).
- **SC-002**: The BUY sub-tab never displays more than 20 stocks after a tier refresh.
- **SC-003**: SELL and HOLD tab contents are unchanged after a tier BUY Refresh — verifiable by comparing data before and after.
- **SC-004**: The tier Refresh button is clearly labelled and located inside the BUY view for each tier, so a user can identify and click it without reading a guide.
- **SC-005**: An empty-state message is shown (not an error or blank screen) when zero BUY signals exist for a tier after refresh.

## Assumptions

- The cap tier classification (Large Cap, Mid Cap, etc.) used for scoped refresh is derived from the most recent global refresh. If no global refresh has been run, the tier's stock list is empty and the Refresh prompt is shown.
- "Top 20 BUY stocks" means the 20 stocks with the highest confidence score among those with signal_type = "BUY" in a given tier.
- The global Refresh button in the sidebar is retained and remains unchanged in scope — it refreshes all symbols across all tiers for both markets and updates SELL and HOLD data.
- The per-tier BUY Refresh fetches fresh OHLCV and news data and recomputes signals for only the stocks in that tier; it does not use cached signal data.
- India and US markets each get the same per-tier BUY Refresh behaviour (dual-market parity).
- SELL and HOLD tabs continue to show data from the last global refresh and are out of scope for this feature.
