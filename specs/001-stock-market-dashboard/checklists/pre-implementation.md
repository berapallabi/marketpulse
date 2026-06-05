# Pre-Implementation Checklist: MarketPulse Investment Dashboard

**Purpose**: Comprehensive requirements quality review across data/signal, UI/UX, and risk/safety domains — author self-review before implementation begins.
**Created**: 2026-06-05
**Feature**: [spec.md](../spec.md)
**Audience**: Author (pre-implementation self-review)
**Depth**: Comprehensive — data & signal quality + UI/UX + risk & safety

---

## Signal Computation Requirements

- [x] CHK001 Are the RSI overbought/oversold thresholds (>70=SELL, <30=BUY) and the neutral-zone rule (30–70=0) documented in a spec or contract artifact that an implementer can reference without reading research.md? [Completeness, Gap, Spec §FR-005] ✅ Confirmed in contracts/signal-engine.md scoring table
- [x] CHK002 Is it specified whether the MACD crossover signal uses the latest single bar or requires confirmation over multiple bars — or is a single-bar crossover the explicit rule? [Clarity, Ambiguity, Spec §FR-005] ✅ contracts/signal-engine.md defines `macd_val > macd_signal` with no multi-bar confirmation — single-bar is the explicit rule
- [x] CHK003 Are the Bollinger Band scoring rules (close < lower=BUY, close > upper=SELL, between=neutral) and the SMA crossover rule (SMA50>SMA200=BUY) captured in a requirements or contract document rather than only in research.md? [Completeness, Gap] ✅ Confirmed in contracts/signal-engine.md scoring table
- [x] CHK004 Is the formula for converting the raw technical mean (−1 to +1) to a normalised 0–100 score (`(raw + 1) / 2 * 100`) documented in a spec or contract artifact accessible during implementation? [Clarity, Gap, Spec §FR-007] ✅ Confirmed in contracts/signal-engine.md Aggregation section
- [x] CHK005 Are the final signal classification thresholds (≥60=BUY, ≤40=SELL, between=HOLD) specified in the spec or only embedded in research.md and config notes? [Completeness, Spec §FR-007] ✅ Confirmed in contracts/signal-engine.md Classification section
- [x] CHK006 Is it specified how the confidence score is interpreted qualitatively — e.g., is confidence=61 a "weak BUY" treated the same as confidence=95 from a display perspective? [Clarity, Ambiguity, Spec §FR-003] ✅ Added to FR-003: plain integer display, no tier label — signal type alone conveys direction
- [x] CHK007 Are requirements defined for how the signal is computed when only a subset of indicators can be calculated — e.g., SMA200 unavailable due to < 200 days of history but RSI and MACD are available? [Edge Case, Gap, Spec §FR-005] ✅ Added to FR-005 and contracts/signal-engine.md: score from available indicators; missing noted in contributing_factors
- [x] CHK008 Is it specified what signal is assigned to a stock when pandas-ta returns NaN for all indicators (e.g., stock has < 50 days of history)? [Edge Case, Gap, Spec §FR-005] ✅ Added to FR-005 and contracts/signal-engine.md: stock excluded from table, counted as unavailable

---

## Data Integrity & Freshness Requirements

- [x] CHK009 Is the staleness threshold (1 hour) defined in a single canonical location — or is it spread across spec §FR-009, research.md, and config notes without a single source of truth? [Consistency, Spec §FR-009] ✅ Added to FR-009: `STALE_HOURS = 1` in `config.py` is the canonical value; spec references it as the single source of truth
- [x] CHK010 Is "data freshness" defined with the same measurement basis across all entity types — e.g., is price staleness measured from API fetch time, and is sentiment staleness measured the same way? [Clarity, Ambiguity, Spec §FR-009] ✅ Added to FR-009: staleness measured from API fetch time (`fetched_at`/`computed_at`) consistently for all entity types
- [x] CHK011 Is it specified whether staleness is computed from the time of the API call or from the market data's own timestamp (e.g., last trade time vs. fetch time)? [Ambiguity, Spec §FR-009] ✅ Added to FR-009: API fetch time is the staleness basis — not the market data's own timestamp
- [x] CHK012 Are requirements defined for partial refresh failure — if India data succeeds but US data fails mid-refresh, is the India data written to cache while US remains stale, or is the entire refresh rolled back? [Edge Case, Gap, Spec §FR-011] ✅ Added to FR-010: per-market isolation — India cached and displayed; US shows error banner
- [x] CHK013 Is it specified whether a partial cache write (some stocks within a market succeeded, some failed) is committed or rolled back? [Completeness, Gap, Spec §FR-011] ✅ Added to FR-011: partial writes committed — successful stocks written, failed stocks skipped and counted
- [x] CHK014 Is the minimum article count threshold for "sufficient" sentiment (≥2 matched articles) consistent across FR-006, the contracts/signal-engine.md spec, and US3 acceptance scenario 2? [Consistency, Spec §FR-006, §US3] ✅ Already resolved by H1 remediation — all three locations now use ≥2 matched articles
- [x] CHK015 Is the VADER normalisation formula (compound → 0–100) documented in a requirements artifact — not only in research.md — so it can be verified against implementation? [Completeness, Gap, Spec §FR-006] ✅ Confirmed in contracts/data-providers.md: `sentiment_score = (compound + 1) / 2 * 100`

---

## UI/UX Requirements Quality

- [x] CHK016 Are colour semantics for the signal column explicitly specified (e.g., BUY=green, SELL=red, HOLD=grey) or is "colour-coded" left open to implementer interpretation? [Clarity, Ambiguity, Spec §FR-001] ✅ Added to FR-003: BUY=#22c55e, SELL=#ef4444, HOLD=#f59e0b
- [x] CHK017 Is the default sort order of the stock list on initial load (before any filter is applied) explicitly specified — confidence descending, alphabetical, or another order? [Clarity, Gap, Spec §FR-001] ✅ Added to Display Behaviour: confidence score descending; confirmed by US1 acceptance scenario 2
- [x] CHK018 Are requirements defined for the empty state of each market tab — what is displayed when no data has been fetched yet (first open, cache empty)? [Coverage, Gap, Spec §US1] ✅ Added to Display Behaviour: "Click 🔄 Refresh to load data" with disclaimer still visible
- [x] CHK019 Is the exact placement of the per-signal risk disclaimer specified — is it shown once per table, once per page, or inline on every row? FR-004 says "co-located with signal" but the stock list shows one disclaimer below the table. [Consistency, Spec §FR-004] ✅ Resolved in FR-004: once per table, immediately below filter controls, above stock rows
- [x] CHK020 Is it specified whether both a staleness warning and a "Market Closed" badge can appear simultaneously on the same tab, and if so, which takes visual precedence? [Clarity, Gap, Spec §FR-009, §FR-016] ✅ Added to FR-009: both shown simultaneously; "Market Closed" badge takes visual precedence
- [x] CHK021 Are requirements defined for the maximum number of news headlines displayed in the drill-down view, or is it open-ended? [Completeness, Gap, Spec §FR-014] ✅ Added to Display Behaviour: max 10 headlines, sorted by publication date descending
- [x] CHK022 Is the chart type for the 90-day price history in the drill-down view explicitly specified (line chart, candlestick, OHLC bar)? [Clarity, Ambiguity, Spec §FR-014] ✅ Added to Display Behaviour: line chart of daily closing price
- [x] CHK023 Are requirements defined for what happens when the Refresh button is clicked while a previous refresh is still in progress — is the second click ignored, queued, or cancels the first? [Edge Case, Gap, Spec §FR-012] ✅ Added to Display Behaviour: Streamlit's native button-disable prevents concurrent invocations; no custom logic needed
- [x] CHK024 Is it specified how the "X stocks unavailable" count is displayed when zero stocks are unavailable — is the counter hidden, or shown as "0 stocks unavailable"? [Clarity, Gap, Spec §Edge Cases] ✅ Added to Display Behaviour: counter hidden when X = 0
- [x] CHK025 Are requirements defined for the drill-down view when a stock's news_items cache is empty (no matched articles) — is the news section hidden, or shown with an "No news available" message? [Edge Case, Gap, Spec §FR-014] ✅ Added to Display Behaviour: "No recent news found for this stock"

---

## Risk & Safety Requirements

- [x] CHK026 Is the exact wording of the risk disclaimer standardised across all surfaces (stock list caption, detail view, page banner), or is it permitted to vary? [Consistency, Spec §FR-004] ✅ Added to FR-004: standard text is "⚠️ Informational only — not financial advice." used consistently across all surfaces
- [x] CHK027 Is it specified whether the risk disclaimer must remain visible when the stock list is filtered to zero results (empty filtered state)? [Edge Case, Gap, Spec §FR-004] ✅ Added to FR-004: disclaimer visible even when list filtered to zero results
- [x] CHK028 Are requirements defined for whether the risk disclaimer is always shown regardless of data availability state — including when all providers have failed and no signals are displayed? [Completeness, Spec §FR-004] ✅ Added to FR-004: disclaimer shown at all times including provider failure and pre-refresh states
- [x] CHK029 Is the prominence of the risk disclaimer specified with measurable criteria — e.g., minimum font size, contrast ratio, or spatial proximity to the signal it accompanies? [Clarity, Ambiguity, Spec §FR-004] ✅ Personal tool — renders as `st.warning()` which provides Streamlit's standard yellow warning box; no additional measurable criteria needed at this scope
- [x] CHK030 Is the SC-007 requirement ("errors surfaced within 10 seconds") defined with a measurable trigger event — what clock-starts the 10 seconds, and what constitutes "surfaced"? [Measurability, Spec §SC-007] ✅ Added to SC-007: clock starts when `DataProviderError` caught; stops when error banner rendered
- [x] CHK031 Are requirements defined for whether stale signals (data older than 1 hour) should be visually degraded (e.g., greyed out) or treated identically to fresh signals apart from the warning badge? [Completeness, Gap, Spec §FR-009] ✅ Added to FR-009: stale signals retain BUY/SELL/HOLD colour — no greying out; staleness badge is the sole data-quality indicator

---

## Edge Case & Failure Handling Requirements

- [x] CHK032 Is the "connection drops mid-refresh" edge case mapped to a Functional Requirement (FR), or is it only described in the Edge Cases narrative without a traceable requirement? [Traceability, Gap, Spec §Edge Cases] ✅ Edge Case updated with "(covered by FR-010)"; FR-010 now includes the connection-lost handling requirement
- [x] CHK033 Are requirements defined for the scenario where a stock exists in the hardcoded symbol list but returns no data from any provider (both price and OHLCV unavailable)? [Edge Case, Spec §FR-001] ✅ Covered by FR-005 (all-NaN → excluded + unavailable count) and FR-011 (partial cache write committed; failed stocks skipped)
- [x] CHK034 Is it specified what the dashboard displays when all stocks in a market are unavailable — i.e., total provider failure results in an empty tab rather than a partial table? [Edge Case, Spec §FR-010] ✅ Added to FR-010 and Edge Cases: error banner + empty stock list; also added to Edge Cases narrative
- [x] CHK035 Are requirements defined for how conflicting indicator sub-scores (e.g., RSI=+1, MACD=−1, BB=+1, SMA=−1) are surfaced to the user — is the "contributing factors" list always shown, or only in the drill-down? [Clarity, Spec §Edge Cases] ✅ Added to Edge Cases: contributing_factors visible in drill-down (US4) only; Display Behaviour confirms this
- [x] CHK036 Is it specified whether historically fetched OHLCV data (used for indicators) is cached and reused for the drill-down price chart, or whether the chart always triggers a separate fetch? [Completeness, Gap, Spec §FR-014] ✅ Added to FR-011 and contracts/data-providers.md: cached OHLCV reused for drill-down; no separate fetch
- [x] CHK037 Are requirements defined for the scenario where an RSS feed returns articles with no publication date — is `published_at=null` acceptable, and how is it displayed in the headlines table? [Edge Case, Gap, Spec §FR-006] ✅ Already handled in contracts/data-providers.md (`published_at: str | None`); Display Behaviour now specifies "Date unknown" as the display value
- [x] CHK038 Is it specified how the sentiment score behaves when matched articles contain no meaningful text (empty titles and summaries) — does VADER return a valid compound score, and what is the fallback? [Edge Case, Gap, Spec §FR-006] ✅ Added to Display Behaviour: VADER returns compound=0.0 (neutral); article still counts toward article_count

---

## Non-Functional Requirements Quality

- [x] CHK039 Are the performance targets (SC-002: <60s initial load, SC-003: <5s cached render) defined with explicit start/end events — e.g., does the clock start on Refresh click or on first network call? [Measurability, Spec §SC-002, §SC-003] ✅ SC-002 updated: clock starts on Refresh click, ends on last signal row visible. SC-003: clock starts on tab open, ends on last signal row rendered
- [x] CHK040 Is it specified how "cached render" (SC-003) is defined when some cached data is stale (>1 hour) and the staleness warning must be computed and displayed? [Clarity, Ambiguity, Spec §SC-003] ✅ Added to SC-003: 5-second target covers render time only; staleness badges do not exempt the render from the target
- [x] CHK041 Are requirements defined for app behaviour under slow network conditions (individual API calls timing out at 30s+) as distinct from total provider failure — is there a per-request timeout specified? [Coverage, Gap] ✅ Added FR-017: 30-second per-request timeout; timeout = per-symbol failure (skipped), not DataProviderError
- [x] CHK042 Is the SQLite cache file size growth bounded by any requirement — e.g., is there a maximum size or a cleanup policy for old news_items rows? [Completeness, Gap, Spec §FR-011] ✅ Added to Assumptions: no enforced size limit; expected under 100 MB for single-user ~150-stock use; no cleanup policy for v1
- [x] CHK043 Is SC-001 ("≥30 Indian stocks and ≥30 US stocks") achievable given the known data gaps for some NSE symbols via yfinance `.NS` suffix — is there a fallback requirement if fewer than 30 stocks have sufficient history? [Measurability, Spec §SC-001] ✅ Added to Assumptions: SC-001 is a target; app functional with fewer stocks when provider gaps exist

---

## Dependencies & Assumptions Quality

- [x] CHK044 Is the assumption that all 50 Nifty 50 symbols are supported by nsepython validated — or is it possible that some symbols return no data, reducing coverage below SC-001's 30-stock floor? [Assumption, Spec §Assumptions] ✅ Added to Assumptions: not all symbols guaranteed; skipped symbols counted as unavailable; SC-001 is a target not a hard gate
- [x] CHK045 Are the RSS feed URLs treated as stable long-term dependencies — is there a requirement for what happens when a feed URL changes or returns a non-RSS response? [Assumption, Gap, Spec §Assumptions] ✅ Added to Assumptions: feeds are best-effort; broken feeds silently skipped; URL updates require manual config.py edit; no automated monitoring
- [x] CHK046 Are requirements defined for index rebalancing — when a stock is added to or removed from Nifty 50 or S&P 100, is there a defined process for updating the hardcoded symbol list? [Coverage, Gap, Spec §Assumptions] ✅ Added to Assumptions: manual update to config.py; no automated rebalancing detection in scope

---

## Notes

- Check items off as completed: `[x]`
- Add inline findings: `- [x] CHK001 ✅ Confirmed in contracts/signal-engine.md` or `- [x] CHK001 ⚠️ Gap found — added to spec`
- Items marked `[Gap]` indicate requirements that are absent and may need to be added to spec.md before implementation
- Items marked `[Ambiguity]` indicate requirements that exist but need clarification before coding
- Items marked `[Consistency]` indicate cross-document alignment to verify manually
