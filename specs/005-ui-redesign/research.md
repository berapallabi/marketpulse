# Research: UI Design System

## Decision 1: Theming Mechanism — config.toml + CSS Injection

**Decision**: Use `.streamlit/config.toml` for base colour/font, and a centralised CSS injection module for component-level overrides.

**Rationale**: Streamlit exposes two complementary theming layers. `config.toml` controls global tokens (`primaryColor`, `backgroundColor`, `secondaryBackgroundColor`, `textColor`, `font`) — these propagate to all built-in components (buttons, metrics, sliders) automatically with zero code. Component-level overrides (tab shapes, badge cells, expander headers) require injected `<style>` blocks via `st.markdown(unsafe_allow_html=True)`. Using both in concert covers every visible element.

**Alternatives considered**:
- CSS injection only (no config.toml): Works but requires overriding Streamlit's internal colour variables everywhere — brittle against version upgrades.
- Streamlit `st.theme()` API: Experimental as of Streamlit 1.x — not stable enough for production use.

---

## Decision 2: Centralised Design Token Module (`theme.py`)

**Decision**: Create `marketpulse/ui/theme.py` as the single source of truth for all colour constants, CSS templates, and the `inject_global_css()` call. All other UI files import from it.

**Rationale**: Currently, colours are scattered — `#ff4b4b` in `dashboard.py`, `#22c55e` in `stock_list.py`, `#3b82f6` in `stock_detail.py` — with no shared palette. A single module eliminates this fragmentation, makes future palette changes a one-line edit, and is unit-testable (palette completeness, hex format validity).

**Alternatives considered**:
- Inline constants per file: Current approach — identified as root cause of scattered look.
- External CSS file loaded at runtime: Streamlit doesn't support static file serving without custom components; adds complexity with no benefit.

---

## Decision 3: Colour Palette — Slate-Navy Professional

**Decision**: 8-tone slate/navy palette designed for financial data readability.

| Token | Hex | Usage |
|-------|-----|-------|
| `PRIMARY` | `#1e3a5f` | Page title, section headings, dominant text |
| `INTERACTIVE` | `#2563eb` | Active tab indicator, primary buttons |
| `BUY` | `#16a34a` | BUY signal badge — professional green |
| `SELL` | `#dc2626` | SELL signal badge — professional red |
| `HOLD` | `#b45309` | HOLD signal badge — amber-brown |
| `NEUTRAL_LIGHT` | `#f8fafc` | Page background, tab strip |
| `NEUTRAL_MID` | `#e2e8f0` | Inactive tab background, dividers |
| `NEUTRAL_DARK` | `#0f172a` | Body text, active tab foreground |

**Rationale**: Slate/navy is the dominant palette in professional financial tools (Bloomberg-style). The signal colours are semantically unambiguous (green/red/amber) but slightly desaturated versus the current values (`#22c55e`, `#ef4444`, `#f59e0b`) — giving a more considered, less "traffic light" appearance. All 8 tones are traceable to the same hue family (cool neutral).

**Alternatives considered**:
- Warm neutral (beige/cream): Less conventional for financial data; harder to read coloured signals against.
- Pure dark theme: Spec explicitly excluded "pure dark"; also harder to print/screenshot.
- Keep existing colours: Does not solve the unified palette problem (current colours are from different families).

---

## Decision 4: Signal Badge Styling in Dataframe

**Decision**: Use Pandas Styler `background-color` + `color` + `font-weight` on the Signal column cell. No HTML injection into cell values.

**Rationale**: Streamlit's `st.dataframe` with Styler supports a limited but sufficient CSS subset: `color`, `background-color`, `font-weight`, `font-style`, `text-decoration`. Adding `background-color` to the signal cell (e.g., light green tint + dark green text for BUY) creates a visible badge-like appearance within dataframe constraints. HTML injection into cell values requires `st.markdown` tables — which lose interactive row selection (`on_select="rerun"`), a core feature.

**Alternatives considered**:
- `st.data_editor` with column_config: Loses row-click-to-drill-down interaction.
- Full HTML table via `st.markdown`: Loses `on_select="rerun"` — cannot be used.
- Emoji prefix in cell value: Adds noise without consistent visual treatment.

Signal cell styling:
- BUY: `background-color: #dcfce7; color: #16a34a; font-weight: bold`
- SELL: `background-color: #fee2e2; color: #dc2626; font-weight: bold`
- HOLD: `background-color: #fef3c7; color: #b45309; font-weight: bold`

---

## Decision 5: Typography — System Sans-Serif via config.toml

**Decision**: Set `font = "sans"` in `.streamlit/config.toml`. Define a 4-level type scale via CSS (`h1`–`h3`, `.stCaption`) without importing external fonts.

**Rationale**: The app runs locally with no guaranteed internet access. Google Fonts CDN would fail offline. The system sans-serif stack (SF Pro on macOS, Segoe UI on Windows, Roboto on Linux) is already high-quality and consistent per platform. `font = "sans"` in config.toml activates this stack for all built-in components.

CSS type scale applied via injected `<style>`:
- Page title (`h1`): `font-size: 1.75rem; font-weight: 700; color: #1e3a5f`
- Section heading (`h2`, `h3`): `font-size: 1.1rem; font-weight: 600; color: #1e3a5f`
- Body (default): `font-size: 0.9rem; font-weight: 400; color: #0f172a`
- Caption (`.stCaption`): `font-size: 0.75rem; color: #64748b`

**Alternatives considered**:
- Bundled webfont (woff2 in static/): Requires Streamlit custom component setup; disproportionate complexity.
- Monospace font: Appropriate for code but not financial data prose.

---

## Decision 6: No New Python Dependencies

**Decision**: Zero new packages required. All styling uses Streamlit built-ins, CSS strings in Python, and `.streamlit/config.toml`.

**Rationale**: Constitution IV (Simplicity/YAGNI) and the locked technology stack. Streamlit's built-in theming is sufficient. No `streamlit-extras`, no custom components, no additional CSS preprocessors.
