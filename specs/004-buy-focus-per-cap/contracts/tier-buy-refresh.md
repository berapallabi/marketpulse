# Contract: Per-Tier BUY Refresh

## `_top_buy_signals(signals, limit=20) -> list`

Pure helper that filters and ranks signals to produce the per-tier BUY display list.

### Inputs

| Parameter | Type | Description |
|-----------|------|-------------|
| signals | list[Signal] | All signals computed for a tier's symbols during this refresh |
| limit | int | Maximum number of results to return. Default: 20. |

### Output

`list[Signal]` — signals with `signal_type == "BUY"`, sorted by `confidence_score` descending, length ≤ `limit`.

### Behaviour Rules

- Filters to `signal_type == "BUY"` only; discards SELL and HOLD.
- Sorts by `confidence_score` descending (highest confidence first).
- Returns at most `limit` items; returns fewer if fewer BUY signals exist.
- Returns `[]` if no BUY signals found (no error raised).
- Pure function: no side effects, no I/O, no Streamlit calls.

### Test Requirements

| Scenario | Expected Output |
|----------|----------------|
| Empty list | `[]` |
| All SELL signals | `[]` |
| All BUY signals, fewer than limit | All signals, sorted by confidence desc |
| Mix of BUY/SELL/HOLD | Only BUY signals, sorted by confidence desc |
| More than 20 BUY signals | Top 20 by confidence desc |
| Exactly 20 BUY signals | All 20, sorted by confidence desc |
| limit=5 with 10 BUY signals | Top 5 by confidence desc |

---

## `_refresh_tier_buy(market, tier_label)` — UI function (Streamlit)

Orchestrates the per-tier BUY refresh: discovers symbols, fetches data, computes signals, stores results in session state.

### Inputs

| Parameter | Type | Description |
|-----------|------|-------------|
| market | str | `"IN"` or `"US"` |
| tier_label | str | e.g. `"Large Cap"`, `"Mega Cap"` |

### Side Effects

- Reads `cache.read_signals(market)` to find symbols in the tier.
- Calls `fetch_quotes`, `fetch_ohlcv_history`, `compute_indicators`, `generate_signal` for each symbol.
- Stores result in `st.session_state[f"tier_buy_{market}_{slug}"]` — a list of dicts matching `read_signals()` format, capped at 20 BUY signals.
- Clears `_prev_rows_{market}_{slug}buy` so stale row selection doesn't persist.
- Does NOT write to SQLite (no `cache.write_signals` call).

### Behaviour Rules

- If no symbols exist for the tier (empty DB), stores `[]` and shows empty-state message.
- Shows a Streamlit spinner while fetching.
- On any per-symbol error: skips that symbol (same pattern as `_refresh_market`).
- Does not affect SELL/HOLD data in session state or DB.
