# Research: Per-Tier BUY Refresh

## Session State vs DB Persistence for Per-Tier BUY Results

**Decision**: Store per-tier BUY refresh results in Streamlit session state only — do NOT write to the SQLite `signals` table.

**Rationale**: Writing fresh signals back to the DB would upsert every stock in the tier, overwriting their signal_type, confidence_score, etc. SELL and HOLD tabs read directly from the DB; if a stock's signal changes from SELL to BUY after a tier refresh, it would silently disappear from the SELL tab. The spec explicitly requires SELL/HOLD data to be unaffected (FR-005). Session state is the correct isolation boundary — it is per-user, per-session, and cleared on global refresh just like the existing `ohlcv_{market}` cache.

**Session state key**: `tier_buy_{market}_{tier_slug}` where `tier_slug` is e.g. `large_cap`, `mega_cap`. Value: `list[dict]` in the same format as `cache.read_signals()` returns (symbol, signal_type, confidence_score, technical_score, sentiment_score, contributing_factors, generated_at, cap_tier, current_price, last_updated).

**Alternatives considered**:
- Write to a separate `tier_buy_cache` table — adds DB schema complexity for no benefit over session state (constitution Principle IV: YAGNI).
- Overwrite signals table — violates FR-005 by contaminating SELL/HOLD data.

---

## Tier Symbol Discovery

**Decision**: Derive the symbol list for a tier from `cache.read_signals(market)` filtered by `cap_tier == tier_label`. This gives the set of symbols that were classified into this tier during the last global refresh.

**Rationale**: The cap_tier classification is stored on each Signal row after feature 003. No separate index or lookup table is needed.

**Edge case**: If `cache.read_signals` returns no rows (no global refresh yet), the tier has zero symbols → show "Click the global Refresh first to classify stocks" message. The per-tier Refresh button is still rendered but does nothing useful without prior classification.

---

## Signal Computation Scope

**Decision**: The per-tier BUY Refresh uses the same signal computation pipeline as the global refresh (`fetch_quotes` → `fetch_ohlcv_history` → `compute_indicators` → `generate_signal`), scoped only to the tier's symbols.

**Rationale**: Reusing the existing pipeline guarantees consistency between per-tier BUY results and global refresh results. No new analysis logic is introduced.

**Performance**: India Large Cap is typically ~30 symbols; US Mega Cap ~20–30 symbols. A scoped refresh for one tier takes roughly 30–60% of a full market refresh.

---

## Top-20 Ranking and Filtering

**Decision**: After computing signals for all symbols in a tier, filter to `signal_type == "BUY"`, sort descending by `confidence_score`, and take the first 20. This happens in a pure helper function `_top_buy_signals(signals, limit=20)` that can be unit-tested independently of data providers.

**Rationale**: Isolating the ranking logic as a pure function satisfies constitution Principle III (TDD) — the business-critical ranking step is tested without Streamlit or network dependencies.

---

## UI Placement of Refresh Button

**Decision**: Place a `🔄 Refresh BUY` button at the top of each tier's BUY sub-tab, above the stock list. The button is visually scoped to the BUY view and labelled to distinguish it from the global sidebar Refresh.

**Rationale**: Placing the button inside the BUY sub-tab makes the scope of the action immediately obvious — the user sees the button next to the BUY results it will update. This satisfies FR-007 (visually distinct) without requiring new UI components.

---

## Cap Tier Assignment During Per-Tier Refresh

**Decision**: During a per-tier BUY refresh, re-classify market_cap → cap_tier for each symbol using the same `classify_cap_tier()` function. A stock could theoretically move tiers between a global refresh and a per-tier refresh; in that case, display it in the results where it currently belongs without updating the DB.

**Rationale**: Data integrity (constitution Principle I) requires that the cap_tier shown with per-tier BUY results is based on the freshest available market cap data.

---

## No New Dependencies

**Decision**: This feature requires no new Python packages.

**Rationale**: All required functionality exists in the current stack: session state via Streamlit, signal computation via the existing pipeline, filtering/sorting via Python builtins.
