"""Tests for marketpulse/data/sentiment.py — write first, confirm FAIL, then implement."""
from datetime import datetime, timezone

import pytest

from marketpulse.data.sentiment import NewsArticle, score_articles_for_stock


def _article(headline: str, summary: str = "") -> NewsArticle:
    now = datetime.now(timezone.utc).isoformat()
    return NewsArticle(headline=headline, summary=summary, source="Test", published_at=now, fetched_at=now)


def test_article_matched_by_symbol_in_headline():
    articles = [_article("RELIANCE posts strong results"), _article("Market update")]
    result = score_articles_for_stock(articles, "RELIANCE", "Reliance Industries")
    assert result.article_count == 1


def test_article_matched_by_company_name_in_summary():
    articles = [_article("Stock news", summary="Tata Consultancy wins major deal")]
    result = score_articles_for_stock(articles, "TCS", "Tata Consultancy Services")
    assert result.article_count == 1


def test_sentiment_score_in_range(sample_news_articles):
    result = score_articles_for_stock(sample_news_articles, "RELIANCE", "Reliance Industries")
    assert 0.0 <= result.sentiment_score <= 100.0


def test_insufficient_when_fewer_than_2_articles():
    articles = [_article("AAPL rallies")]
    result = score_articles_for_stock(articles, "AAPL", "Apple Inc")
    assert result.is_sufficient is False
    assert result.sentiment_score == 50.0


def test_sufficient_when_2_or_more_articles():
    articles = [
        _article("AAPL stock surges on strong earnings"),
        _article("Apple quarterly revenue beats expectations"),
    ]
    result = score_articles_for_stock(articles, "AAPL", "Apple Inc")
    assert result.is_sufficient is True


def test_positive_articles_produce_score_above_50():
    articles = [
        _article("AAPL soars to record high on amazing results"),
        _article("Apple reports fantastic earnings, investors rejoice"),
        _article("AAPL beats all expectations with stellar growth"),
    ]
    result = score_articles_for_stock(articles, "AAPL", "Apple Inc")
    assert result.sentiment_score > 50.0


def test_zero_matching_articles_returns_neutral():
    articles = [_article("General market news"), _article("Economy update")]
    result = score_articles_for_stock(articles, "AAPL", "Apple Inc")
    assert result.is_sufficient is False
    assert result.sentiment_score == 50.0
    assert result.article_count == 0


def test_case_insensitive_symbol_match():
    articles = [
        _article("aapl stock rises today"),
        _article("aapl earnings beat expectations"),
    ]
    result = score_articles_for_stock(articles, "AAPL", "Apple Inc")
    assert result.article_count == 2
