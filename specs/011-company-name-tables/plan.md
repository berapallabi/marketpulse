# Implementation Plan: Company Name in Stock Tables

**Branch**: `011-company-name-tables` | **Date**: 2026-06-10 | **Spec**: [spec.md](spec.md)

**Summary**: Add a LEFT JOIN to the `stocks` table in `read_signals` so that `company_name` flows through to all Market tab stock list tables (Buy, Watchlist, My Holdings). Also update the `_build_df` fallback from blank to the ticker symbol when no company name is available.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: SQLite (cache query), Streamlit (UI)

**Storage**: SQLite — `signals` joined with `price_snapshots` and `stocks` tables

**Testing**: pytest + temp SQLite DB

**Target Platform**: macOS / Streamlit Cloud

**Project Type**: Streamlit web app

**Performance Goals**: No measurable impact — same LEFT JOIN pattern already used for `price_snapshots`

**Constraints**: No schema changes; no new dependencies; read-path change only

**Scale/Scope**: One SQL query change + one fallback string change

## Constitution Check

- No new external dependencies
- No schema changes
- Single-query, single-line fix in `cache.py` + one-line fix in `stock_list.py`

## Project Structure

### Documentation (this feature)

```text
specs/011-company-name-tables/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
└── checklists/
    └── requirements.md
```

### Source Code (files to modify)

```text
marketpulse/
├── storage/
│   └── cache.py          # read_signals: add LEFT JOIN stocks st
└── ui/
    └── stock_list.py     # _build_df: fallback company name to symbol

tests/
└── test_company_name_tables.py   # New test file
```

## Implementation Design

### Change 1 — `cache.py`: `read_signals` query

```python
# Before
"SELECT s.*, p.current_price, p.last_updated "
"FROM signals s "
"LEFT JOIN price_snapshots p ON s.symbol = p.symbol AND s.market = p.market "
"WHERE s.market = ?"

# After
"SELECT s.*, p.current_price, p.last_updated, st.company_name "
"FROM signals s "
"LEFT JOIN price_snapshots p ON s.symbol = p.symbol AND s.market = p.market "
"LEFT JOIN stocks st ON s.symbol = st.symbol AND s.market = st.market "
"WHERE s.market = ?"
```

### Change 2 — `stock_list.py`: `_build_df` fallback

```python
# Before
"Company": r.get("company_name") or "",

# After
"Company": r.get("company_name") or r["symbol"],
```

### US2 Verify — Explore tab already correct

`search_stocks_live` in `cache.py` already returns `company_name` in each result dict. No code change needed.

## Complexity Tracking

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]

**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]

**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]

**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]

**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]

**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]

**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]

**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
