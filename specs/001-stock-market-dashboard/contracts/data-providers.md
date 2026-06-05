# Contract: Data Providers

**Module paths**: `marketpulse/data/india.py`, `marketpulse/data/us.py`, `marketpulse/data/sentiment.py`

---

## India Data Provider (`data/india.py`)

### `fetch_quotes(symbols: list[str]) -> list[StockQuote]`

Fetches current price data for the given NSE symbols using nsepython.

**Input**: List of NSE ticker symbols, e.g. `["RELIANCE", "TCS", "INFY"]`

**Output**: List of `StockQuote` objects. Symbols that fail to fetch are omitted; caller counts skipped symbols.

```python
@dataclass
class StockQuote:
    symbol: str
    market: str          # always "IN"
    company_name: str
    current_price: float
    open_price: float | None
    high_price: float | None
    low_price: float | None
    volume: int | None
    currency: str        # always "INR"
    fetched_at: str      # ISO 8601 UTC
```

**Error behaviour**: Raises `DataProviderError` with message if nsepython is entirely unreachable. Per-symbol failures are silently skipped (returned list is shorter than input).

---

### `fetch_ohlcv_history(symbol: str, days: int = 200) -> pd.DataFrame | None`

Fetches daily OHLCV history for a single NSE symbol using yfinance (`.NS` suffix).

**Input**: NSE symbol string, number of calendar days of history.

**Output**: pandas DataFrame with columns `[Date, Open, High, Low, Close, Volume]`, sorted ascending. Returns `None` if fewer than 50 rows are available (insufficient for indicator computation).

**Error behaviour**: Returns `None` on any fetch failure; caller marks stock as "Insufficient data".

---

## US Data Provider (`data/us.py`)

### `fetch_quotes(symbols: list[str]) -> list[StockQuote]`

Fetches current price data for the given US ticker symbols using yfinance.

**Input**: List of NYSE/NASDAQ ticker symbols, e.g. `["AAPL", "MSFT", "GOOGL"]`

**Output**: Same `StockQuote` structure; `market` is always `"US"`, `currency` is always `"USD"`.

**Error behaviour**: Same as India provider — `DataProviderError` on total failure, per-symbol silently skipped.

---

### `fetch_ohlcv_history(symbol: str, days: int = 200) -> pd.DataFrame | None`

Fetches daily OHLCV history for a single US symbol using yfinance.

**Output**: Same DataFrame contract as India provider. Returns `None` if fewer than 50 rows available.

---

## Sentiment Provider (`data/sentiment.py`)

### `fetch_market_articles(market: str) -> list[NewsArticle]`

Fetches and parses all articles from the configured RSS feeds for the given market.

**Input**: `"IN"` or `"US"`

**Output**: List of `NewsArticle` objects from all feeds for that market.

```python
@dataclass
class NewsArticle:
    headline: str
    summary: str         # may be empty string
    source: str          # feed name
    published_at: str | None   # ISO 8601 UTC, None if feed omits date
    fetched_at: str
```

**Error behaviour**: If a single feed fails, it is skipped; other feeds continue. If all feeds fail, returns empty list. Caller checks for empty and displays "Insufficient news data".

---

### `score_articles_for_stock(articles: list[NewsArticle], symbol: str, company_name: str) -> SentimentResult`

Filters articles matching the stock and returns a VADER-based sentiment score.

**Matching rule**: Article is attributed to stock if `symbol` or the first two words of `company_name` appear (case-insensitive) in `article.headline + article.summary`.

**Output**:

```python
@dataclass
class SentimentResult:
    symbol: str
    market: str
    sentiment_score: float   # 0.0 to 100.0, normalised from VADER compound
    article_count: int        # number of matched articles
    is_sufficient: bool       # True if article_count >= 2
    matched_articles: list[NewsArticle]  # for storage as news_items
```

**Score formula**:
```python
compound = mean([vader.polarity_scores(a.headline + " " + a.summary)["compound"] for a in matched])
sentiment_score = (compound + 1) / 2 * 100   # maps [-1,+1] → [0,100]
# If article_count < 2: sentiment_score = 50.0 (neutral default), is_sufficient = False
```

---

## Shared Types

```python
class DataProviderError(Exception):
    """Raised when an entire data provider is unreachable."""
    pass
```

Sentiment label mapping (for `news_items.sentiment_label`):
- VADER compound >= 0.05 → `"Positive"`
- VADER compound <= -0.05 → `"Negative"`
- else → `"Neutral"`

---

## Network Behaviour

**Per-request timeout**: All outbound network calls (nsepython, yfinance, feedparser/RSS) MUST apply a 30-second per-request timeout. A single-call timeout is treated as a per-symbol or per-feed failure (silently skipped); it does not raise `DataProviderError` unless the entire provider is unreachable.

**OHLCV caching**: The DataFrame returned by `fetch_ohlcv_history` is written to the SQLite cache and reused as the data source for the drill-down price chart. No separate `fetch_ohlcv_history` call is triggered when the user opens the detail view.
