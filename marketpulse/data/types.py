from dataclasses import dataclass


@dataclass
class StockQuote:
    symbol: str
    market: str
    company_name: str
    current_price: float
    open_price: float | None
    high_price: float | None
    low_price: float | None
    volume: int | None
    currency: str
    fetched_at: str  # ISO 8601 UTC
    market_cap: float | None = None


class DataProviderError(Exception):
    """Raised when an entire data provider is unreachable."""
    pass
