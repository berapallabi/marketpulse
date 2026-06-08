import logging
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

from marketpulse.data.types import DataProviderError, StockQuote

logging.getLogger("yfinance").setLevel(logging.CRITICAL)


def fetch_quotes(symbols: list[str]) -> list[StockQuote]:
    """Fetch current price data for US ticker symbols using yfinance."""
    results: list[StockQuote] = []
    failed = 0
    now = datetime.now(timezone.utc).isoformat()

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            price = (
                info.get("regularMarketPrice")
                or info.get("currentPrice")
                or info.get("previousClose")
            )
            if price is None:
                failed += 1
                continue
            results.append(StockQuote(
                symbol=symbol,
                market="US",
                company_name=info.get("longName") or info.get("shortName") or symbol,
                current_price=float(price),
                open_price=_float(info.get("regularMarketOpen") or info.get("open")),
                high_price=_float(info.get("dayHigh")),
                low_price=_float(info.get("dayLow")),
                volume=_int(info.get("regularMarketVolume") or info.get("volume")),
                currency="USD",
                fetched_at=now,
            ))
        except Exception:
            failed += 1

    if failed == len(symbols) and len(symbols) > 0:
        raise DataProviderError(f"yfinance failed for all {len(symbols)} symbols")

    return results


def fetch_ohlcv_history(symbol: str, days: int = 200) -> pd.DataFrame | None:
    """Fetch daily OHLCV history for a US symbol using yfinance."""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=f"{days}d", interval="1d", auto_adjust=True)
        if df is None or len(df) < 50:
            return None
        df = df.reset_index()
        if "Datetime" in df.columns:
            df = df.rename(columns={"Datetime": "Date"})
        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
        df = df.sort_values("Date").reset_index(drop=True)
        return df
    except Exception:
        return None


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
