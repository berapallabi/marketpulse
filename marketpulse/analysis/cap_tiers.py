INDIA_TIER_ORDER = ["Large Cap", "Mid Cap", "Small Cap"]
US_TIER_ORDER = ["Mega Cap", "Large Cap", "Mid Cap"]

# Each entry: (label, lower_bound_inclusive, upper_bound_exclusive | None)
_INDIA_TIERS = [
    ("Large Cap", 2e11, None),
    ("Mid Cap",   5e10, 2e11),
    ("Small Cap", 0,    5e10),
]

_US_TIERS = [
    ("Mega Cap",  2e11, None),
    ("Large Cap", 1e10, 2e11),
    ("Mid Cap",   0,    1e10),
]


def classify_cap_tier(market_cap: float | None, market: str) -> str:
    """Classify a stock into a named market-cap tier.

    Returns "Unknown" when market_cap is None.
    Raises ValueError for unrecognised market codes.
    """
    if market == "IN":
        tiers = _INDIA_TIERS
    elif market == "US":
        tiers = _US_TIERS
    else:
        raise ValueError(f"Unknown market: {market!r}. Expected 'IN' or 'US'.")

    if market_cap is None:
        return "Unknown"

    for label, lower, upper in tiers:
        if market_cap >= lower and (upper is None or market_cap < upper):
            return label

    return "Unknown"
