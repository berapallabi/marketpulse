import logging
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

from marketpulse.data.types import DataProviderError, StockQuote

logging.getLogger("yfinance").setLevel(logging.CRITICAL)

try:
    from nsepython import nse_eq
except Exception:
    nse_eq = None


def fetch_quotes(symbols: list[str]) -> list[StockQuote]:
    """Fetch current price data for NSE symbols using nsepython."""
    if nse_eq is None:
        raise DataProviderError("nsepython not available")

    results: list[StockQuote] = []
    failed = 0
    now = datetime.now(timezone.utc).isoformat()

    for symbol in symbols:
        try:
            data = nse_eq(symbol)
            results.append(StockQuote(
                symbol=symbol,
                market="IN",
                company_name=data.get("companyName", symbol),
                current_price=float(data.get("lastPrice", 0)),
                open_price=_float(data.get("open")),
                high_price=_float(data.get("dayHigh")),
                low_price=_float(data.get("dayLow")),
                volume=_int(data.get("totalTradedVolume")),
                currency="INR",
                fetched_at=now,
            ))
        except Exception:
            failed += 1

    if failed == len(symbols) and len(symbols) > 0:
        raise DataProviderError(f"nsepython failed for all {len(symbols)} symbols")

    return results


def fetch_ohlcv_history(symbol: str, days: int = 200) -> tuple[pd.DataFrame | None, float | None]:
    """Fetch daily OHLCV history and market cap for an NSE symbol via yfinance."""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        market_cap = _float(ticker.info.get("marketCap"))
        df = ticker.history(period=f"{days}d", interval="1d", auto_adjust=True)
        if df is None or len(df) < 50:
            return None, market_cap
        df = df.reset_index()
        if "Datetime" in df.columns:
            df = df.rename(columns={"Datetime": "Date"})
        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
        df = df.sort_values("Date").reset_index(drop=True)
        return df, market_cap
    except Exception:
        return None, None


def _float(val) -> float | None:
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def _int(val) -> int | None:
    try:
        return int(val) if val is not None else None
    except (TypeError, ValueError):
        return None
