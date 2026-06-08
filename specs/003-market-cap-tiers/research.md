# Research: Market Cap Tier Tabs

## Market Cap Data Availability

**Decision**: Use `yfinance` for market cap for both India and US.

**Rationale**: `ticker.info["marketCap"]` is available for all yfinance-supported symbols, including NSE (`.NS` suffix). For US stocks, `ticker.info` is already fetched inside `fetch_quotes()` in `us.py` — `marketCap` is a free field in the same dict, costing zero extra API calls. For India stocks, `nsepython.nse_eq()` does not expose a reliable market cap field; the `.NS` yfinance info fetch is the consistent fallback, run alongside the existing OHLCV fetch in `india.py`.

**Alternatives considered**:
- NSEPython `nse_eq()` for India market cap — field availability is inconsistent across symbols; rejected.
- Separate market cap API endpoint — adds a new external dependency; rejected per constitution Principle IV.

---

## Cap Tier Thresholds

**Decision**: Use the following fixed thresholds (from spec FR-004):

| Market | Tier | Lower Bound | Upper Bound |
|--------|------|-------------|-------------|
| India (INR) | Large Cap | ₹20,000 Cr (2×10¹¹) | ∞ |
| India (INR) | Mid Cap | ₹5,000 Cr (5×10¹⁰) | ₹19,999 Cr |
| India (INR) | Small Cap | 0 | ₹4,999 Cr |
| US (USD) | Mega Cap | $200B (2×10¹¹) | ∞ |
| US (USD) | Large Cap | $10B (10¹⁰) | $199.9B |
| US (USD) | Mid Cap | $2B (2×10⁹) | $9.9B |
| US (USD) | Small Cap | 0 | $1.9B |

**Note on INR crore units**: yfinance returns `marketCap` in absolute rupees (e.g., 2,000,000,000,000 for ₹2L Cr = 2×10¹². One crore = 10⁷. So ₹20,000 Cr = 2×10¹¹ rupees. Thresholds in code use absolute rupee values, not crore notation.

**Rationale**: SEBI-standard tiers for India; standard US market convention for US. Both are well-recognised by retail investors, reducing confusion.

**Alternatives considered**:
- Relative percentile tiers (top/mid/bottom third by market cap within the index) — user-unfamiliar; inconsistent with industry language; rejected.
- Single "Large Cap" label for everything — loses all tier-differentiation value; rejected.

---

## SQLite Migration Strategy

**Decision**: In `init_db()`, after the `CREATE TABLE IF NOT EXISTS` for `signals`, run `ALTER TABLE signals ADD COLUMN cap_tier TEXT DEFAULT 'Unknown'` inside a try/except that silently ignores `sqlite3.OperationalError` (which SQLite raises when the column already exists). This is the standard SQLite migration pattern for additive column changes.

**Rationale**: Avoids dropping the existing database on first run after upgrade. The `cap_tier` column defaults to `'Unknown'` for rows written before this feature, which is correct — they will be refreshed on next user-initiated refresh.

---

## Dashboard Navigation Hierarchy

**Decision**: Inside `_render_market_tab(market)`, add `st.tabs([tier_labels])` as the outer level, and inside each tier tab call the existing `render_stock_list(tier_rows, market, filter_signal)` inside nested `st.tabs(["All", "BUY", "SELL", "HOLD"])` — same as the current signal sub-tabs.

**Rationale**: Streamlit nests tabs correctly. The existing `render_stock_list` is unchanged; only the dashboard splits `signal_rows` by `cap_tier` before passing them in.

**Selected symbol session state**: The existing `f"selected_{market}"` pattern is retained. The drill-down renders below all tier tabs.
