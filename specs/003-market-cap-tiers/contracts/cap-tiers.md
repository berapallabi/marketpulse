# Contract: Cap Tier Classification

**Module**: `marketpulse/analysis/cap_tiers.py`

## `classify_cap_tier(market_cap, market) -> str`

Classifies a stock into a named market-cap tier.

### Inputs

| Parameter | Type | Description |
|-----------|------|-------------|
| market_cap | float \| None | Absolute market cap in local currency (INR for India, USD for US). |
| market | str | `"IN"` or `"US"` |

### Output

`str` — one of the tier labels defined below, or `"Unknown"` if `market_cap is None`.

### Tier Labels

**India (`market == "IN"`)** — INR absolute:
- `"Large Cap"` — market_cap ≥ 2×10¹¹
- `"Mid Cap"` — 5×10¹⁰ ≤ market_cap < 2×10¹¹
- `"Small Cap"` — market_cap < 5×10¹⁰

**US (`market == "US"`)** — USD absolute:
- `"Mega Cap"` — market_cap ≥ 2×10¹¹
- `"Large Cap"` — 1×10¹⁰ ≤ market_cap < 2×10¹¹
- `"Mid Cap"` — 2×10⁹ ≤ market_cap < 1×10¹⁰
- `"Small Cap"` — market_cap < 2×10⁹

**Any market** — `"Unknown"` when `market_cap is None`

### Behaviour Rules

- The function is pure (no side effects, no I/O).
- Raises `ValueError` if `market` is not `"IN"` or `"US"`.
- `market_cap = 0` is treated as Small Cap (≥ 0, < lower threshold).

### Test Requirements

| Scenario | Expected Output |
|----------|----------------|
| India, cap = None | `"Unknown"` |
| India, cap = 3×10¹¹ (₹3L Cr) | `"Large Cap"` |
| India, cap = 2×10¹¹ (exactly at threshold) | `"Large Cap"` |
| India, cap = 1×10¹¹ (₹1L Cr) | `"Mid Cap"` |
| India, cap = 5×10¹⁰ (exactly at threshold) | `"Mid Cap"` |
| India, cap = 1×10¹⁰ (₹10K Cr) | `"Small Cap"` |
| US, cap = None | `"Unknown"` |
| US, cap = 3×10¹¹ ($300B) | `"Mega Cap"` |
| US, cap = 5×10¹⁰ ($50B) | `"Large Cap"` |
| US, cap = 5×10⁹ ($5B) | `"Mid Cap"` |
| US, cap = 1×10⁹ ($1B) | `"Small Cap"` |
| Invalid market `"EU"` | `ValueError` |

## `INDIA_TIER_ORDER` and `US_TIER_ORDER`

Module-level constants listing tier labels in display order (largest to smallest), used by the dashboard to create tabs in the correct sequence.

```
INDIA_TIER_ORDER = ["Large Cap", "Mid Cap", "Small Cap"]
US_TIER_ORDER    = ["Mega Cap", "Large Cap", "Mid Cap", "Small Cap"]
```
