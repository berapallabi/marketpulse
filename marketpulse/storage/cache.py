import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from marketpulse.config import DB_PATH, STALE_HOURS


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db(db_path: Path | None = None) -> None:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        c = conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS stocks (
                symbol       TEXT NOT NULL,
                market       TEXT NOT NULL CHECK (market IN ('IN', 'US')),
                company_name TEXT NOT NULL,
                sector       TEXT,
                currency     TEXT NOT NULL CHECK (currency IN ('INR', 'USD')),
                PRIMARY KEY (symbol, market)
            );

            CREATE TABLE IF NOT EXISTS price_snapshots (
                symbol        TEXT NOT NULL,
                market        TEXT NOT NULL,
                current_price REAL NOT NULL,
                open_price    REAL,
                high_price    REAL,
                low_price     REAL,
                volume        INTEGER,
                last_updated  TEXT NOT NULL,
                PRIMARY KEY (symbol, market),
                FOREIGN KEY (symbol, market) REFERENCES stocks (symbol, market)
            );

            CREATE TABLE IF NOT EXISTS technical_snapshots (
                symbol          TEXT NOT NULL,
                market          TEXT NOT NULL,
                rsi_14          REAL,
                macd_val        REAL,
                macd_signal     REAL,
                bb_upper        REAL,
                bb_middle       REAL,
                bb_lower        REAL,
                sma_50          REAL,
                sma_200         REAL,
                rsi_score       REAL,
                macd_score      REAL,
                bb_score        REAL,
                sma_score       REAL,
                technical_score REAL,
                computed_at     TEXT NOT NULL,
                PRIMARY KEY (symbol, market),
                FOREIGN KEY (symbol, market) REFERENCES stocks (symbol, market)
            );

            CREATE TABLE IF NOT EXISTS sentiment_snapshots (
                symbol          TEXT NOT NULL,
                market          TEXT NOT NULL,
                sentiment_score REAL NOT NULL,
                article_count   INTEGER NOT NULL,
                is_sufficient   INTEGER NOT NULL CHECK (is_sufficient IN (0, 1)),
                computed_at     TEXT NOT NULL,
                PRIMARY KEY (symbol, market),
                FOREIGN KEY (symbol, market) REFERENCES stocks (symbol, market)
            );

            CREATE TABLE IF NOT EXISTS signals (
                symbol               TEXT NOT NULL,
                market               TEXT NOT NULL,
                signal_type          TEXT NOT NULL CHECK (signal_type IN ('BUY', 'SELL', 'HOLD')),
                confidence_score     INTEGER NOT NULL,
                technical_score      REAL NOT NULL,
                sentiment_score      REAL NOT NULL,
                contributing_factors TEXT,
                generated_at         TEXT NOT NULL,
                PRIMARY KEY (symbol, market),
                FOREIGN KEY (symbol, market) REFERENCES stocks (symbol, market)
            );

            CREATE TABLE IF NOT EXISTS news_items (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol          TEXT NOT NULL,
                market          TEXT NOT NULL,
                headline        TEXT NOT NULL,
                source          TEXT NOT NULL,
                published_at    TEXT,
                sentiment_label TEXT NOT NULL CHECK (sentiment_label IN ('Positive', 'Neutral', 'Negative')),
                fetched_at      TEXT NOT NULL,
                FOREIGN KEY (symbol, market) REFERENCES stocks (symbol, market)
            );

            CREATE INDEX IF NOT EXISTS idx_news_symbol_market
                ON news_items (symbol, market);

            CREATE TABLE IF NOT EXISTS market_summaries (
                market            TEXT NOT NULL PRIMARY KEY CHECK (market IN ('IN', 'US')),
                overall_sentiment TEXT NOT NULL CHECK (overall_sentiment IN ('Bullish', 'Neutral', 'Bearish')),
                sentiment_score   REAL NOT NULL,
                buy_count         INTEGER NOT NULL,
                sell_count        INTEGER NOT NULL,
                hold_count        INTEGER NOT NULL,
                last_updated      TEXT NOT NULL
            );

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
        """)
        conn.commit()
        try:
            conn.execute("ALTER TABLE signals ADD COLUMN cap_tier TEXT DEFAULT 'Unknown'")
            conn.commit()
        except Exception:
            pass
    finally:
        conn.close()


def _upsert(conn: sqlite3.Connection, table: str, pk_cols: list[str], row: dict) -> None:
    cols = list(row.keys())
    placeholders = ", ".join("?" for _ in cols)
    col_list = ", ".join(cols)
    update_clause = ", ".join(
        f"{c} = excluded.{c}" for c in cols if c not in pk_cols
    )
    sql = (
        f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) "
        f"ON CONFLICT({', '.join(pk_cols)}) DO UPDATE SET {update_clause}"
    )
    conn.execute(sql, [row[c] for c in cols])


def write_quotes(quotes: list, db_path: Path | None = None) -> None:
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    try:
        for q in quotes:
            _upsert(conn, "stocks", ["symbol", "market"], {
                "symbol": q.symbol, "market": q.market,
                "company_name": q.company_name, "sector": None,
                "currency": q.currency,
            })
            _upsert(conn, "price_snapshots", ["symbol", "market"], {
                "symbol": q.symbol, "market": q.market,
                "current_price": q.current_price, "open_price": q.open_price,
                "high_price": q.high_price, "low_price": q.low_price,
                "volume": q.volume, "last_updated": q.fetched_at,
            })
        conn.commit()
    finally:
        conn.close()


def write_technical(snapshot, db_path: Path | None = None) -> None:
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    try:
        _upsert(conn, "technical_snapshots", ["symbol", "market"], {
            "symbol": snapshot.symbol, "market": snapshot.market,
            "rsi_14": snapshot.rsi_14, "macd_val": snapshot.macd_val,
            "macd_signal": snapshot.macd_signal, "bb_upper": snapshot.bb_upper,
            "bb_middle": snapshot.bb_middle, "bb_lower": snapshot.bb_lower,
            "sma_50": snapshot.sma_50, "sma_200": snapshot.sma_200,
            "rsi_score": snapshot.rsi_score, "macd_score": snapshot.macd_score,
            "bb_score": snapshot.bb_score, "sma_score": snapshot.sma_score,
            "technical_score": snapshot.technical_score, "computed_at": snapshot.computed_at,
        })
        conn.commit()
    finally:
        conn.close()


def write_sentiment(result, db_path: Path | None = None) -> None:
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    try:
        _upsert(conn, "sentiment_snapshots", ["symbol", "market"], {
            "symbol": result.symbol, "market": result.market,
            "sentiment_score": result.sentiment_score,
            "article_count": result.article_count,
            "is_sufficient": 1 if result.is_sufficient else 0,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        })
        conn.commit()
    finally:
        conn.close()


def write_signals(signals: list, db_path: Path | None = None) -> None:
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    try:
        for sig in signals:
            _upsert(conn, "signals", ["symbol", "market"], {
                "symbol": sig.symbol, "market": sig.market,
                "signal_type": sig.signal_type,
                "confidence_score": sig.confidence_score,
                "technical_score": sig.technical_score,
                "sentiment_score": sig.sentiment_score,
                "contributing_factors": json.dumps(sig.contributing_factors),
                "generated_at": sig.generated_at,
                "cap_tier": sig.cap_tier,
            })
        conn.commit()
    finally:
        conn.close()


def write_news(symbol: str, market: str, news_items: list, db_path: Path | None = None) -> None:
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    try:
        conn.execute("DELETE FROM news_items WHERE symbol = ? AND market = ?", (symbol, market))
        for item in news_items:
            conn.execute(
                "INSERT INTO news_items (symbol, market, headline, source, published_at, sentiment_label, fetched_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (symbol, market, item.headline, item.source,
                 item.published_at, item.sentiment_label, item.fetched_at),
            )
        conn.commit()
    finally:
        conn.close()


def write_market_summary(summary, db_path: Path | None = None) -> None:
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    try:
        _upsert(conn, "market_summaries", ["market"], {
            "market": summary.market,
            "overall_sentiment": summary.overall_sentiment,
            "sentiment_score": summary.sentiment_score,
            "buy_count": summary.buy_count,
            "sell_count": summary.sell_count,
            "hold_count": summary.hold_count,
            "last_updated": summary.last_updated,
        })
        conn.commit()
    finally:
        conn.close()


def read_signals(market: str, db_path: Path | None = None) -> list[dict]:
    path = db_path or DB_PATH
    if not path.exists():
        return []
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT s.*, p.current_price, p.last_updated "
            "FROM signals s "
            "LEFT JOIN price_snapshots p ON s.symbol = p.symbol AND s.market = p.market "
            "WHERE s.market = ?",
            (market,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def read_technical(symbol: str, market: str, db_path: Path | None = None) -> dict | None:
    path = db_path or DB_PATH
    if not path.exists():
        return None
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM technical_snapshots WHERE symbol = ? AND market = ?",
            (symbol, market),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def read_news(symbol: str, market: str, db_path: Path | None = None) -> list[dict]:
    path = db_path or DB_PATH
    if not path.exists():
        return []
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM news_items WHERE symbol = ? AND market = ? "
            "ORDER BY published_at DESC NULLS LAST LIMIT 10",
            (symbol, market),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def search_stocks(query: str, market: str, db_path: Path | None = None) -> list[dict]:
    if len(query) < 2:
        return []
    path = db_path or DB_PATH
    if not path.exists():
        return []
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    pattern = f"%{query}%"
    try:
        rows = conn.execute(
            "SELECT st.symbol, st.company_name, st.market, "
            "       s.signal_type, s.confidence_score, s.technical_score, "
            "       s.sentiment_score, s.contributing_factors, s.generated_at, "
            "       s.cap_tier, p.current_price, p.last_updated "
            "FROM stocks st "
            "LEFT JOIN signals s ON st.symbol = s.symbol AND st.market = s.market "
            "LEFT JOIN price_snapshots p ON st.symbol = p.symbol AND st.market = p.market "
            "WHERE st.market = ? "
            "  AND (UPPER(st.symbol) LIKE UPPER(?) OR UPPER(st.company_name) LIKE UPPER(?)) "
            "ORDER BY st.symbol",
            (market, pattern, pattern),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def read_market_summary(market: str, db_path: Path | None = None) -> dict | None:
    path = db_path or DB_PATH
    if not path.exists():
        return None
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM market_summaries WHERE market = ?", (market,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def check_staleness(market: str, db_path: Path | None = None) -> bool:
    """Return True if cached data is older than STALE_HOURS or absent."""
    summary = read_market_summary(market, db_path)
    if not summary:
        return True
    try:
        last = datetime.fromisoformat(summary["last_updated"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return (now - last).total_seconds() > STALE_HOURS * 3600
    except (ValueError, KeyError):
        return True


# ── Watchlist ─────────────────────────────────────────────────────────────────

def add_to_watchlist(symbol: str, market: str, db_path: Path | None = None) -> None:
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    try:
        _upsert(conn, "watchlist", ["symbol", "market"], {
            "symbol": symbol, "market": market,
            "added_at": datetime.now(timezone.utc).isoformat(),
        })
        conn.commit()
    finally:
        conn.close()


def remove_from_watchlist(symbol: str, market: str, db_path: Path | None = None) -> None:
    path = db_path or DB_PATH
    if not path.exists():
        return
    conn = sqlite3.connect(path)
    try:
        conn.execute("DELETE FROM watchlist WHERE symbol = ? AND market = ?", (symbol, market))
        conn.commit()
    finally:
        conn.close()


def read_watchlist(market: str, db_path: Path | None = None) -> list[str]:
    path = db_path or DB_PATH
    if not path.exists():
        return []
    conn = sqlite3.connect(path)
    try:
        rows = conn.execute(
            "SELECT symbol FROM watchlist WHERE market = ? ORDER BY added_at",
            (market,),
        ).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


# ── Holdings ──────────────────────────────────────────────────────────────────

def add_to_holdings(symbol: str, market: str, db_path: Path | None = None) -> None:
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    try:
        _upsert(conn, "holdings", ["symbol", "market"], {
            "symbol": symbol, "market": market,
            "added_at": datetime.now(timezone.utc).isoformat(),
        })
        conn.commit()
    finally:
        conn.close()


def remove_from_holdings(symbol: str, market: str, db_path: Path | None = None) -> None:
    path = db_path or DB_PATH
    if not path.exists():
        return
    conn = sqlite3.connect(path)
    try:
        conn.execute("DELETE FROM holdings WHERE symbol = ? AND market = ?", (symbol, market))
        conn.commit()
    finally:
        conn.close()


def read_holdings(market: str, db_path: Path | None = None) -> list[str]:
    path = db_path or DB_PATH
    if not path.exists():
        return []
    conn = sqlite3.connect(path)
    try:
        rows = conn.execute(
            "SELECT symbol FROM holdings WHERE market = ? ORDER BY added_at",
            (market,),
        ).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()
