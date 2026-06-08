from pathlib import Path

DB_PATH = Path.home() / ".marketpulse" / "cache.db"

BUY_THRESHOLD = 60
SELL_THRESHOLD = 40
STALE_HOURS = 1

NIFTY_50_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK",
    "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "HCLTECH",
    "SUNPHARMA", "TITAN", "ULTRACEMCO", "WIPRO", "NTPC",
    "POWERGRID", "BAJFINANCE", "BAJAJFINSV", "TECHM", "ONGC",
    "ADANIENT", "ADANIPORTS", "COALINDIA", "JSWSTEEL", "TATAMOTORS",
    "TATASTEEL", "GRASIM", "INDUSINDBK", "M&M", "EICHERMOT",
    "BPCL", "HEROMOTOCO", "DIVISLAB", "DRREDDY", "CIPLA",
    "BRITANNIA", "SBILIFE", "HDFCLIFE", "APOLLOHOSP", "NESTLEIND",
    "HINDALCO", "TATACONSUM", "UPL", "SHRIRAMFIN", "BEL",
]

SP100_SYMBOLS = [
    "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "GOOG", "META", "TSLA", "BRK.B", "LLY",
    "V", "UNH", "JPM", "XOM", "JNJ", "WMT", "MA", "PG", "AVGO", "HD",
    "CVX", "MRK", "ABBV", "COST", "ADBE", "CRM", "PEP", "TMO", "KO", "MCD",
    "ACN", "CSCO", "BAC", "ABT", "DHR", "NFLX", "TXN", "CMCSA", "PFE", "NEE",
    "WFC", "AMD", "ORCL", "PM", "IBM", "INTC", "UPS", "CAT", "AMGN", "GE",
    "INTU", "QCOM", "LOW", "AMAT", "HON", "SPGI", "GS", "ELV", "LMT", "BKNG",
    "AXP", "SBUX", "DE", "MS", "T", "C", "NOW", "MDLZ", "MMC", "TJX",
    "BMY", "ADI", "REGN", "VRTX", "MO", "CI", "ETN", "PLD", "BLK", "ZTS",
    "CB", "ADP", "SO", "SHW", "GILD", "ISRG", "DUK", "NOC", "USB", "NSC",
    "RTX", "PNC", "MU", "EMR", "TFC", "F", "GM", "D", "HCA", "EW",
]

INDIA_FEEDS = {
    "Economic Times Markets": "https://economictimes.indiatimes.com/markets/rss.cms",
    "Moneycontrol News": "https://www.moneycontrol.com/rss/latestnews.xml",
}

US_FEEDS = {
    "Yahoo Finance News": "https://finance.yahoo.com/news/rssindex",
    "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
}
