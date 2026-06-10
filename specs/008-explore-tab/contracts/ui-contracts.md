# UI Contracts: Explore Tab

## Contract 1: `search_stocks(query, market)` cache function

**Purpose**: Return stocks matching a search query for the given market.

**Input**:
- `query: str` — partial symbol or company name (case-insensitive)
- `market: str` — `"IN"` or `"US"`

**Output**: `list[dict]` — each dict has the same keys as `read_signals` rows plus `company_name`:

| Key | Type | Source | Nullable |
|-----|------|--------|----------|
| `symbol` | str | `stocks.symbol` | No |
| `company_name` | str | `stocks.company_name` | No |
| `market` | str | `stocks.market` | No |
| `signal_type` | str \| None | `signals.signal_type` | Yes — absent if never refreshed |
| `confidence_score` | float \| None | `signals.confidence_score` | Yes |
| `technical_score` | float \| None | `signals.technical_score` | Yes |
| `sentiment_score` | float \| None | `signals.sentiment_score` | Yes |
| `contributing_factors` | str \| None | `signals.contributing_factors` | Yes |
| `cap_tier` | str \| None | `signals.cap_tier` | Yes |
| `generated_at` | str \| None | `signals.generated_at` | Yes |
| `current_price` | float \| None | `price_snapshots.current_price` | Yes |
| `last_updated` | str \| None | `price_snapshots.last_updated` | Yes |

**Guarantees**:
- Returns `[]` when `len(query) < 2`
- Returns `[]` when DB does not exist
- Never raises; errors return `[]`
- Results ordered by `symbol` ascending

---

## Contract 2: Explore Tab Layout

**Trigger**: User clicks the "Explore" tab in the Buy / Watchlist / My Holdings / Explore tab row.

**Layout**:
```
[ Search input: "Search by name or symbol…" ]

[ Left col (3/5) ]          [ Right col (2/5) ]
  Result list                 Detail panel
  (render_stock_list)         (render_stock_detail)
  filter_signal="ALL"         or "← Select a stock"
```

**States**:

| Condition | Left column | Right column |
|-----------|-------------|--------------|
| Query empty or < 2 chars | "Enter at least 2 characters to search" | "← Select a stock to view details" |
| Query valid, no matches | "No results found" | "← Select a stock to view details" |
| Query valid, matches found | Result list (all signal types) | "← Select a stock to view details" |
| Stock selected from results | Result list (unchanged) | Full detail panel |

**Session state keys** (scoped to avoid cross-tab bleed):
- `explore_query_{market}` — current text input value (managed by Streamlit widget)
- `selected_explore_{market}` — symbol string of the selected stock, or None

**Key uniqueness**: All widget keys inside `_render_explore_tab` use `explore_{market}` prefix.
`render_stock_detail` called with `key=f"explore_{market}"`.
