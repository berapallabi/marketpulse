from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import mean

import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from marketpulse import config

_vader = SentimentIntensityAnalyzer()


@dataclass
class NewsArticle:
    headline: str
    summary: str
    source: str
    published_at: str | None
    fetched_at: str


@dataclass
class SentimentResult:
    symbol: str
    market: str
    sentiment_score: float
    article_count: int
    is_sufficient: bool
    matched_articles: list = field(default_factory=list)


def fetch_market_articles(market: str) -> list[NewsArticle]:
    """Fetch all articles from configured RSS feeds for the given market."""
    feeds = config.INDIA_FEEDS if market == "IN" else config.US_FEEDS
    articles: list[NewsArticle] = []
    now = datetime.now(timezone.utc).isoformat()

    for source_name, url in feeds.items():
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries:
                headline = entry.get("title", "")
                summary = entry.get("summary", entry.get("description", ""))
                published_at = _parse_date(entry)
                articles.append(NewsArticle(
                    headline=headline,
                    summary=summary,
                    source=source_name,
                    published_at=published_at,
                    fetched_at=now,
                ))
        except Exception:
            continue

    return articles


def score_articles_for_stock(
    articles: list[NewsArticle],
    symbol: str,
    company_name: str,
) -> SentimentResult:
    """Filter articles matching the stock and compute VADER sentiment score."""
    name_words = [w for w in company_name.split()[:2] if len(w) > 2]
    matched = []

    for article in articles:
        text = (article.headline + " " + article.summary).lower()
        if symbol.lower() in text or any(w.lower() in text for w in name_words):
            matched.append(article)

    if len(matched) < 2:
        return SentimentResult(
            symbol=symbol,
            market="",
            sentiment_score=50.0,
            article_count=len(matched),
            is_sufficient=False,
            matched_articles=matched,
        )

    compounds = [
        _vader.polarity_scores(a.headline + " " + a.summary)["compound"]
        for a in matched
    ]
    compound_avg = mean(compounds)
    score = (compound_avg + 1) / 2 * 100

    return SentimentResult(
        symbol=symbol,
        market="",
        sentiment_score=score,
        article_count=len(matched),
        is_sufficient=True,
        matched_articles=matched,
    )


def _sentiment_label(compound: float) -> str:
    if compound >= 0.05:
        return "Positive"
    if compound <= -0.05:
        return "Negative"
    return "Neutral"


def _parse_date(entry) -> str | None:
    try:
        import time
        t = entry.get("published_parsed") or entry.get("updated_parsed")
        if t:
            return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc).isoformat()
    except Exception:
        pass
    return None
