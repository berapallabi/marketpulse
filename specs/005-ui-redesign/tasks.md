---
description: "Task list for UI Design System"
---

# Tasks: UI Design System

**Input**: Design documents from `specs/005-ui-redesign/`

**Prerequisites**: plan.md, spec.md, research.md, contracts/theme-module.md

**Tests**: Included per constitution Principle III (TDD mandatory). `tests/test_theme.py` written before `theme.py` is created.

---

## Phase 1: Setup

**Purpose**: Verify clean baseline before any changes.

- [X] T001 Verify `PYTHONPATH=. .venv/bin/pytest tests/ -q` passes (68 tests green) before any changes

---

## Phase 2: Foundational

**Purpose**: Global Streamlit base theme — must exist before any component CSS is applied.

- [ ] T002 Create `.streamlit/config.toml` with `primaryColor = "#2563eb"`, `backgroundColor = "#f8fafc"`, `secondaryBackgroundColor = "#e2e8f0"`, `textColor = "#0f172a"`, `font = "sans"` — this propagates to all built-in Streamlit widgets automatically

---

## Phase 3: User Story 1 — Unified Visual Identity (Priority: P1) 🎯 MVP

**Goal**: Every colour on screen is drawn from a single 8-tone palette. A central `theme.py` module owns all design tokens and CSS. `dashboard.py` calls `inject_global_css()` instead of the current ad-hoc `_TAB_CSS` block.

**Independent Test**: Open the app. All tab indicators use `#2563eb` (not the former `#ff4b4b`). The page background is `#f8fafc`. Every colour visible in the browser developer tools' computed styles maps to one of the 8 PALETTE tokens.

### TDD: Write failing tests first

- [ ] T003 [US1] Write `tests/test_theme.py` with 9 tests per `contracts/theme-module.md`: (1) `PALETTE` has exactly 8 keys; (2) all palette values match `^#[0-9a-f]{6}$`; (3) `SIGNAL_BADGE_STYLE` has BUY, SELL, HOLD keys; (4) `signal_cell_style("BUY")` contains `"#dcfce7"`; (5) `signal_cell_style("SELL")` contains `"#fee2e2"`; (6) `signal_cell_style("HOLD")` contains `"#fef3c7"`; (7) `signal_cell_style("UNKNOWN")` returns `""`; (8) `get_global_css()` returns non-empty string; (9) every 7-char hex value in `get_global_css()` output appears in `PALETTE.values()`. Run and confirm ALL 9 FAIL before T004.

### Implementation

- [ ] T004 [US1] Create `marketpulse/ui/theme.py` with: `PALETTE` dict (8 tokens per research.md Decision 3); `SIGNAL_BADGE_STYLE` dict; `signal_cell_style(signal_type: str) -> str` pure function returning `"background-color: {bg}; color: {fg}; font-weight: bold"` for BUY/SELL/HOLD, `""` for unknown; `get_global_css() -> str` returning CSS covering tab strip/states (porting `_TAB_CSS` colours to palette tokens), type scale (`h1`/`h2`/`h3` sizes and `PRIMARY` colour, `.stCaption` size), and `inject_global_css() -> None` calling `st.markdown(f"<style>{get_global_css()}</style>", unsafe_allow_html=True)`. Make all 9 T003 tests pass.

- [ ] T005 [US1] Update `marketpulse/ui/dashboard.py`: remove `_TAB_CSS` constant and the `st.markdown(_TAB_CSS, unsafe_allow_html=True)` call; add `from marketpulse.ui.theme import inject_global_css`; call `inject_global_css()` immediately after `st.set_page_config(...)`.

- [ ] T006 [US1] Run `PYTHONPATH=. .venv/bin/pytest tests/ -q` — 77 tests (68 existing + 9 new) must all pass.

---

## Phase 4: User Story 2 — Consistent Component Language (Priority: P2)

**Goal**: Signal badges in the stock table show a coloured background cell (not just coloured text). The price chart and all inline colours reference palette tokens. All Streamlit metrics inherit the base theme from config.toml with no component-level overrides needed.

**Independent Test**: Navigate to any BUY sub-tab after a tier refresh. Each row's Signal cell has a distinct coloured background (green tint for BUY, red tint for SELL, amber tint for HOLD). Open the stock detail panel — the price chart line colour matches `PALETTE["INTERACTIVE"]`.

- [ ] T007 [US2] Update `marketpulse/ui/stock_list.py`: add `from marketpulse.ui.theme import signal_cell_style`; remove `_SIGNAL_COLOURS` dict; replace `_colour_signal_col(row)` body with: for the `"Signal"` column return `signal_cell_style(row["Signal"])`, all other columns return `""`.

- [ ] T008 [US2] Update `marketpulse/ui/stock_detail.py`: add `from marketpulse.ui.theme import PALETTE`; replace hardcoded `color="#3b82f6"` chart line colour with `color=PALETTE["INTERACTIVE"]`; replace coloured-circle emoji RSI/SMA labels (`🔴`, `🟢`, `⚪`) with plain-text labels (`"Overbought"`, `"Oversold"`, `"Neutral"`, `"Golden Cross"`, `"Death Cross"`) — visual hierarchy comes from the metric widget, not emojis.

- [ ] T009 [US2] Update `marketpulse/ui/sentiment_gauge.py`: add `from marketpulse.ui.theme import PALETTE`; replace `_COLOURS` dict (`"normal"` / `"off"` / `"inverse"` delta colours) with explicit `delta_color` values where applicable. Keep `_ICONS` dict (chart emoji icons are meaningful, not decorative colour carriers).

- [ ] T010 [US2] Run `PYTHONPATH=. .venv/bin/pytest tests/ -q` — all tests must pass.

---

## Phase 5: User Story 3 — Readable Data Presentation (Priority: P3)

**Goal**: Signal and Confidence are the first two columns visible in the stock table (leftmost = highest scan priority). Empty states look calm and distinct from error states.

**Independent Test**: Open any tier's All tab. Without scrolling horizontally, the Signal badge and Confidence score are the first two columns. Navigate to an empty tier BUY tab — the empty state message is styled differently from the red error banner shown when a network error occurs.

- [ ] T011 [US3] Update `marketpulse/ui/stock_list.py` `_build_df()`: reorder the dict keys so `"Signal"` and `"Confidence"` come first — `{"Signal": ..., "Confidence": ..., "Symbol": ..., "Price": ..., "Updated": ...}`. This controls the column order in the rendered dataframe.

- [ ] T012 [US3] Update `marketpulse/ui/stock_list.py` empty and no-data states: change `st.info("Click 🔄 Refresh to load data.")` to `st.caption("No data loaded yet. Click 🔄 Refresh BUY to fetch signals.")` (calm, caption-level); change `st.caption("No stocks match the selected filter.")` to `st.info("No {filter_signal} signals in this tier.")` (informational, not alarming).

- [ ] T013 [US3] Run `PYTHONPATH=. .venv/bin/pytest tests/ -q` — all tests must pass.

---

## Phase 6: Polish & Validation

- [ ] T014 Manual smoke test: `streamlit run app.py`. Visually verify all 5 success criteria from spec.md: (SC-001) all visible colours map to the 8 palette tones — no rogue `#ff4b4b` or `#22c55e`; (SC-002) text uses only 4 type levels — no ad-hoc sizes; (SC-003) BUY/SELL/HOLD badges look identical across All, BUY, SELL, HOLD sub-tabs; (SC-004) Signal and Confidence columns are leftmost; (SC-005) active tab has consistent blue (`#2563eb`) bottom border across all three tab levels.

---

## Dependencies & Execution Order

- **T001** (baseline): First
- **T002** (config.toml): Before T005 (inject_global_css needs base theme in place)
- **T003** (failing tests): Before T004 (TDD red step)
- **T004** (theme.py): After T003 — makes tests green
- **T005** (dashboard.py): After T004 — imports from theme.py
- **T006** (test run): After T005 — full suite check
- **T007** (stock_list.py badges): After T004 — imports signal_cell_style
- **T008** (stock_detail.py colours): After T004 — imports PALETTE
- **T009** (sentiment_gauge.py): After T004 — imports PALETTE
- **T010** (test run): After T007–T009
- **T011, T012** (column order + empty states): After T007 (same file)
- **T013** (test run): After T011–T012
- **T014** (smoke test): After T013

T007, T008, T009 all touch different files and can run in parallel after T004 completes.

---

## Notes

- `theme.py` must be importable without triggering Streamlit initialisation — `inject_global_css()` contains the `st.markdown` call; all other exports are pure Python constants and functions.
- `get_global_css()` colours: the test in T003 (item 9) verifies all hex values in the CSS output are from PALETTE. When writing `get_global_css()`, use f-string interpolation from PALETTE rather than hardcoded hex strings to pass this test automatically.
- Tab CSS in `get_global_css()` replaces `_TAB_CSS` exactly — the `[data-baseweb="tab-list"]`, `[data-baseweb="tab"]`, and `[aria-selected="true"]` selectors are preserved, with colours swapped to PALETTE tokens.
- The `_SIGNAL_COLOURS` dict in `stock_list.py` is deleted entirely; `signal_cell_style()` replaces its role.
