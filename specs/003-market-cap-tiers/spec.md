# Feature Specification: Market Cap Tier Tabs

**Feature Branch**: `003-market-cap-tiers`

**Created**: 2026-06-08

**Status**: Draft

**Input**: User description: "let's add another feature, categorise the stocks market cap wise, like there should be different tabs under each market, representing different caps. Under each caps, there should be all/buy/sell/hold"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse Stocks by Market Cap Tier (Priority: P1)

As an investor, I open a market tab (India or US) and see a set of market-cap tier tabs — Large Cap, Mid Cap, Small Cap — so I can focus my research on the segment of the market most relevant to my risk appetite and investment style.

**Why this priority**: The tier navigation is the core of this feature. Without it, there is no value to deliver. All other behaviour (All/BUY/SELL/HOLD inside a tier, signals, drill-down) already exists and is inherited.

**Independent Test**: Open the India tab. Three cap-tier tabs are visible (Large Cap, Mid Cap, Small Cap). Clicking "Mid Cap" shows only mid-cap Indian stocks with BUY/SELL/HOLD signals. The All/BUY/SELL/HOLD sub-tabs inside Mid Cap filter those stocks by signal. The drill-down detail panel works for any selected stock.

**Acceptance Scenarios**:

1. **Given** the India tab is active, **When** data has loaded, **Then** three cap-tier tabs are visible: Large Cap, Mid Cap, Small Cap — in that order.
2. **Given** the US tab is active, **When** data has loaded, **Then** four cap-tier tabs are visible: Mega Cap, Large Cap, Mid Cap, Small Cap — in that order.
3. **Given** the "Mid Cap" tier tab is active under India, **When** the user clicks "BUY", **Then** only mid-cap Indian stocks with a BUY signal are shown, sorted by confidence score descending.
4. **Given** a cap tier has no stocks with BUY signals, **When** the user selects the BUY sub-tab, **Then** "No stocks match the selected filter." is shown and the risk disclaimer is still visible.
5. **Given** the user is in India > Large Cap > BUY, **When** they switch to India > Mid Cap, **Then** the Mid Cap tab opens on its last-selected signal sub-tab (defaulting to "All"), independently of the Large Cap sub-tab state.
6. **Given** a stock is shown in any tier tab, **When** the user clicks its row, **Then** the drill-down detail panel opens below the table as in the current implementation.

---

### Edge Cases

- A stock whose market cap cannot be determined (data unavailable) is placed in a catch-all "Other" bucket, counted as unavailable, and excluded from all tier tabs.
- Cap-tier tab selections for different tier/signal combinations are independent per market — switching tiers or markets preserves last-selected sub-tab state.
- The "All" signal sub-tab is always the default within a newly entered tier tab.
- All existing behaviours (staleness badge in sidebar, market-closed badge, sentiment gauge, risk disclaimer, unavailable counter) are preserved.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each market tab MUST contain cap-tier tabs as the first level of navigation inside the tab. India MUST have: Large Cap, Mid Cap, Small Cap. US MUST have: Mega Cap, Large Cap, Mid Cap, Small Cap.
- **FR-002**: Each cap-tier tab MUST contain the same four signal sub-tabs as today: All, BUY, SELL, HOLD — in that order.
- **FR-003**: Each stock MUST be assigned to exactly one cap tier based on its market capitalisation at the time of data refresh.
- **FR-004**: Cap tier thresholds MUST follow standard market definitions:
  - **India** (in INR): Large Cap ≥ ₹20,000 Cr; Mid Cap ₹5,000 Cr – ₹19,999 Cr; Small Cap < ₹5,000 Cr.
  - **US** (in USD): Mega Cap ≥ $200B; Large Cap $10B – $199.9B; Mid Cap $2B – $9.9B; Small Cap < $2B.
- **FR-005**: Market cap data MUST be fetched as part of the existing refresh flow — no separate refresh is required.
- **FR-006**: The stock universe remains the current Nifty 50 (India) and S&P 100 (US). Each stock is classified into whichever cap tier its actual market capitalisation falls into at refresh time. Mid Cap and Small Cap tabs will likely be empty or near-empty given these indices are large-cap dominated; empty tier tabs MUST still be shown with the standard empty state rather than hidden.
- **FR-007**: Stocks with unavailable market cap data MUST be excluded from all tier tabs and counted in the unavailable counter.
- **FR-008**: The confidence sort (descending) and colour-coded signals MUST be preserved within every tier/signal combination.

### Key Entities

- **MarketCapTier**: name (e.g. "Large Cap"), market ("IN" / "US"), lower bound (INR or USD), upper bound (INR or USD or ∞). Fixed per market; not user-configurable.
- **Stock** (existing, extended): gains a `market_cap` field (numeric, local currency) and a `cap_tier` field (string) populated at refresh time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every stock displayed in a cap-tier tab has a market cap that falls within that tier's defined bounds — zero misclassifications.
- **SC-002**: After a data refresh, cap tier tabs are populated and visible within the same time budget as the current signal load (no additional wait perceived by the user).
- **SC-003**: A user can identify the top 5 BUY candidates within a specific cap tier in under 2 minutes from opening the dashboard.
- **SC-004**: All existing acceptance scenarios from specs 001 and 002 continue to pass — no regression in signals, drill-down, disclaimers, or staleness indicators.

## Clarifications

### Session 2026-06-08

- Q: How broadly should the stock universe expand to populate cap tiers? → A: Keep current Nifty 50 / S&P 100; classify each stock into whichever tier its actual market cap falls into. Mid/Small Cap tabs will be empty or near-empty and shown as empty state.

## Assumptions

- Market cap values are fetched from the same data provider used for price data (yfinance for US; available via yfinance `.NS` for India) — no additional data source is required.
- Cap tier thresholds are fixed at the values in FR-004 and are not user-configurable in this version.
- The existing Nifty 50 / S&P 100 universe is unchanged. No new symbols are added. The signal computation pipeline is unchanged.
- Stocks in the current Nifty 50 / S&P 100 lists that fall outside their expected tier (due to market cap fluctuation) will be classified by their actual current market cap, not by their index membership.
- If a tier tab has zero stocks (e.g., no small-cap stocks in the fetched universe), the tab is still shown with the "Click 🔄 Refresh to load data." empty state rather than being hidden.
