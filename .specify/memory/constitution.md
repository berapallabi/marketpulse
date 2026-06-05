<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.0 → 1.1.0 (MINOR — new Technology Stack section added)

Sections added:
  - Technology Stack (locks in Python + Streamlit + data libraries for local-only use)

Modified sections:
  - Development Workflow — added local run instructions and dependency management rules

Deferred items resolved:
  - Technology stack decision: now locked (was deferred in v1.0.0)

Templates reviewed:
  ✅ .specify/templates/plan-template.md  — Technical Context section aligns with locked stack
  ✅ .specify/templates/spec-template.md  — No changes needed
  ✅ .specify/templates/tasks-template.md — No changes needed
  ✅ .specify/memory/constitution.md      — This file (updated)
-->

# MarketPulse Constitution

## Core Principles

### I. Data Accuracy & Reliability

All market data, signals, stock scores, and analytical outputs displayed to the user MUST originate
from verified, authoritative data providers. Stale, unvalidated, or estimated data MUST be clearly
labeled as such — it MUST NOT be presented as current or actionable without a recency timestamp.

Data pipelines MUST fail loudly: a missing or degraded data source MUST surface as a visible
warning in the UI rather than silently serving outdated values. Partial data is preferable to
fabricated data; fabricated data is never acceptable.

**Rationale**: Investment decisions carry real financial consequences. Users trusting inaccurate
signals can incur direct monetary loss. Data integrity is the foundation every other principle
depends on.

### II. User Safety & Risk Transparency

Every buy or sell signal, recommendation, or ranked list MUST be accompanied by explicit risk
context. No output may be framed as a guaranteed outcome or a professional financial advisory.

Risk disclosures MUST be co-located with the signal — not buried in footnotes or a separate
legal page. The system MUST make clear it is an informational tool, not a licensed advisor.

**Rationale**: Financial products are regulated domains. Presenting signals without risk context
exposes users to uninformed decisions and exposes the product to legal and ethical liability.

### III. Test-First Development (NON-NEGOTIABLE)

Tests MUST be written before implementation. The Red-Green-Refactor cycle is mandatory:
write a failing test → get user or reviewer sign-off → implement until green → refactor.

No feature branch may be merged without automated test coverage for its primary acceptance
scenarios. Data transformation logic, signal calculation, and API integrations MUST each have
unit or integration tests.

**Rationale**: Market data pipelines are complex and silently wrong code is dangerous in a
financial context. Tests are the primary safety net against regressions that could corrupt
signals shown to users.

### IV. Simplicity Over Features (YAGNI)

Every feature addition MUST justify its presence against the core user goal: a clear, actionable
dashboard showing what to buy and what to sell. Features that do not directly serve that goal
MUST be deferred or discarded.

Abstractions are introduced only when the same pattern appears three or more times. No
speculative infrastructure. No feature flags for hypothetical future use. No half-built
integrations.

**Rationale**: A cluttered dashboard erodes the signal-to-noise ratio that makes the product
valuable. Simplicity is a product quality, not a shortcut.

### V. Dual-Market Parity

Indian market (NSE/BSE) and US market (NYSE/NASDAQ) features MUST be treated as first-class
citizens. Any capability delivered for one market MUST be planned and scoped for the other
within the same release cycle.

Market-specific rules (trading hours, lot sizes, circuit breakers, tax treatment) MUST be
modeled explicitly — not approximated using the other market's rules.

**Rationale**: The product's core value proposition covers both markets equally. Shipping
US-only features as "done" while Indian market support lags creates a misleading product
and technical debt that compounds over time.

## Technology Stack

This stack is locked for all features. Deviations require a constitution amendment.

| Layer | Tool | Notes |
|---|---|---|
| Language | Python 3.11+ | All logic, data processing, and UI |
| Dashboard UI | Streamlit | Runs at `localhost:8501`; no deployment |
| Charts | Plotly | Interactive charts via `st.plotly_chart` |
| US market data | `yfinance` | NYSE/NASDAQ price history, OHLCV, fundamentals |
| Indian market data | `nsepython` + `nsetools` | NSE/BSE; preferred over yfinance for India |
| Technical indicators | `pandas-ta` | 150+ indicators computed locally |
| Sentiment analysis | `feedparser` + `vaderSentiment` | RSS feeds + local NLP; zero rate limits |
| Data processing | `pandas` + `numpy` | All data transformation |
| Local cache / storage | SQLite (`sqlite3`) | Built into Python; no database server |

**Runtime**: Local only. Start with `streamlit run app.py`. Stop by closing the terminal.
No Docker, no background services, no cloud dependencies.

**Dependency management**: `requirements.txt` at project root. All packages MUST be
pinned to a minimum version. No unpinned wildcard dependencies.

## Market Coverage Standards

- Both NSE/BSE (Indian) and NYSE/NASDAQ (US) markets MUST be supported with equivalent
  data freshness, signal quality, and UI treatment.
- Market-specific trading calendars (holidays, pre/post-market hours) MUST be respected;
  signals outside active trading hours MUST be clearly marked.
- Currency, lot size, and instrument type differences between markets MUST be handled
  explicitly — no silent conversions or assumptions.
- Data providers for each market MUST be documented in the feature plan before implementation
  begins.

## Development Workflow

- All work is captured in a feature spec (`spec.md`) before implementation begins.
- No implementation task starts without a corresponding spec and plan.
- The `Constitution Check` gate in `plan.md` MUST pass before Phase 0 research is complete
  and MUST be re-checked after Phase 1 design.
- Each user story MUST be independently testable and runnable via `streamlit run app.py`.
- Commits MUST be atomic and scoped to a single logical change.
- Breaking changes to data contracts or signal definitions MUST be versioned and documented
  before merging.
- New Python dependencies MUST be added to `requirements.txt` with a minimum version pin
  before the implementing task is considered complete.

## Governance

This constitution supersedes all other development guidelines and informal team practices.
Amendments require:
1. A written rationale explaining why the principle change is necessary.
2. An impact assessment identifying features or tasks already in-flight that would be affected.
3. A migration plan for any work that violates the amended principle.
4. Version increment per semantic versioning rules (MAJOR for removals/redefinitions,
   MINOR for additions, PATCH for clarifications).

All pull requests and spec reviews MUST verify compliance with Principles I through V.
Complexity or scope violations MUST be documented in the `Complexity Tracking` section
of the relevant `plan.md` before they can be approved.

**Version**: 1.1.0 | **Ratified**: 2026-06-05 | **Last Amended**: 2026-06-05
