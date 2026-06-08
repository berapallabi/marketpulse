"""Tests for marketpulse/analysis/cap_tiers.py — written before implementation (TDD)."""
import pytest


def test_india_none_returns_unknown():
    from marketpulse.analysis.cap_tiers import classify_cap_tier
    assert classify_cap_tier(None, "IN") == "Unknown"


def test_india_large_cap_above_threshold():
    from marketpulse.analysis.cap_tiers import classify_cap_tier
    assert classify_cap_tier(3e11, "IN") == "Large Cap"


def test_india_large_cap_at_exact_threshold():
    from marketpulse.analysis.cap_tiers import classify_cap_tier
    assert classify_cap_tier(2e11, "IN") == "Large Cap"


def test_india_mid_cap():
    from marketpulse.analysis.cap_tiers import classify_cap_tier
    assert classify_cap_tier(1e11, "IN") == "Mid Cap"


def test_india_mid_cap_at_exact_lower_threshold():
    from marketpulse.analysis.cap_tiers import classify_cap_tier
    assert classify_cap_tier(5e10, "IN") == "Mid Cap"


def test_india_small_cap():
    from marketpulse.analysis.cap_tiers import classify_cap_tier
    assert classify_cap_tier(1e10, "IN") == "Small Cap"


def test_us_none_returns_unknown():
    from marketpulse.analysis.cap_tiers import classify_cap_tier
    assert classify_cap_tier(None, "US") == "Unknown"


def test_us_mega_cap():
    from marketpulse.analysis.cap_tiers import classify_cap_tier
    assert classify_cap_tier(3e11, "US") == "Mega Cap"


def test_us_large_cap():
    from marketpulse.analysis.cap_tiers import classify_cap_tier
    assert classify_cap_tier(5e10, "US") == "Large Cap"


def test_us_mid_cap():
    from marketpulse.analysis.cap_tiers import classify_cap_tier
    assert classify_cap_tier(5e9, "US") == "Mid Cap"


def test_us_small_cap():
    from marketpulse.analysis.cap_tiers import classify_cap_tier
    assert classify_cap_tier(1e9, "US") == "Small Cap"


def test_invalid_market_raises_value_error():
    from marketpulse.analysis.cap_tiers import classify_cap_tier
    with pytest.raises(ValueError):
        classify_cap_tier(1e11, "EU")


def test_india_tier_order_constant():
    from marketpulse.analysis.cap_tiers import INDIA_TIER_ORDER
    assert INDIA_TIER_ORDER == ["Large Cap", "Mid Cap", "Small Cap"]


def test_us_tier_order_constant():
    from marketpulse.analysis.cap_tiers import US_TIER_ORDER
    assert US_TIER_ORDER == ["Mega Cap", "Large Cap", "Mid Cap", "Small Cap"]
