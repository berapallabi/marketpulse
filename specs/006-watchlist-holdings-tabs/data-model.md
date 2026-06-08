# Data Model: Watchlist & My Holdings Tabs

## New Entities

### watchlist

Represents a stock symbol the user has chosen to monitor.

| Column     | Type | Constraints                         | Description                              |
|------------|------|-------------------------------------|------------------------------------------|
| symbol     | TEXT | NOT NULL, PK(symbol, market)        | Stock ticker (e.g., RELIANCE.NS, AAPL)   |
| market     | TEXT | NOT NULL, CHECK IN ('IN', 'US')     | Market scope                             |
| added_at   | TEXT | NOT NULL                            | ISO-8601 UTC timestamp of when added     |

**Primary key**: `(symbol, market)`
**Uniqueness rule**: A symbol+market pair may appear at most once — duplicate adds are silently ignored (upsert, no error).

---

### holdings

Represents a stock the user currently owns.

| Column     | Type | Constraints                         | Description                              |
|------------|------|-------------------------------------|------------------------------------------|
| symbol     | TEXT | NOT NULL, PK(symbol, market)        | Stock ticker                             |
| market     | TEXT | NOT NULL, CHECK IN ('IN', 'US')     | Market scope                             |
| added_at   | TEXT | NOT NULL                            | ISO-8601 UTC timestamp of when added     |

**Primary key**: `(symbol, market)`
**Uniqueness rule**: Same as watchlist — upsert on duplicate.

---

## Schema Changes in cache.py

Both tables are added to the `executescript` block inside `init_db()`:

```sql
CREATE TABLE IF NOT EXISTS watchlist (
    symbol   TEXT NOT NULL,
    market   TEXT NOT NULL CHECK (market IN ('IN', 'US')),
    added_at TEXT NOT NULL,
    PRIMARY KEY (symbol, market)
);

CREATE TABLE IF NOT EXISTS holdings (
    symbol   TEXT NOT NULL,
    market   TEXT NOT NULL CHECK (market IN ('IN', 'US')),
    added_at TEXT NOT NULL,
    PRIMARY KEY (symbol, market)
);
```

`CREATE TABLE IF NOT EXISTS` makes the migration additive and safe for existing databases.

---

## New Storage Functions

Added to `marketpulse/storage/cache.py`, following the existing `_upsert` / `read_*` / `write_*` conventions:

| Function | Signature | Description |
|----------|-----------|-------------|
| `add_to_watchlist` | `(symbol, market, db_path=None) → None` | Upsert a row into `watchlist` |
| `remove_from_watchlist` | `(symbol, market, db_path=None) → None` | Delete by `(symbol, market)` |
| `read_watchlist` | `(market, db_path=None) → list[str]` | Return list of symbols in watchlist for market |
| `add_to_holdings` | `(symbol, market, db_path=None) → None` | Upsert a row into `holdings` |
| `remove_from_holdings` | `(symbol, market, db_path=None) → None` | Delete by `(symbol, market)` |
| `read_holdings` | `(market, db_path=None) → list[str]` | Return list of symbols in holdings for market |

---

## Relationships

Both `watchlist` and `holdings` reference stocks that exist in the `stocks` table. However, no foreign key constraint is enforced (consistent with the existing schema style — other tables use `FOREIGN KEY` declaratively but SQLite does not enforce them by default). Stale entries (where the underlying stock is removed from the universe) are filtered out implicitly — if a symbol is in the watchlist but absent from the signals query result, no row is shown.

---

## State Transitions (signal filter)

```
segmented_control value
       │
       ├── "Buy"           → filter signal_rows where signal_type == "BUY"
       │                     (uses tier_buy_rows from session_state if available)
       │
       ├── "Watchlist"     → read_watchlist(market) → set of symbols
       │                     filter tier_rows where symbol in watchlist_symbols
       │
       └── "My Holdings"   → read_holdings(market) → set of symbols
                             filter tier_rows where symbol in holdings_symbols
```
