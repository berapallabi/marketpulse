# Contract: `marketpulse/ui/theme.py`

The design token and CSS injection module. Single source of truth for all visual constants.

---

## Exported Constants

### `PALETTE: dict[str, str]`

Exactly 8 named colour tokens. All values are 7-character hex strings (`#rrggbb`).

```python
PALETTE = {
    "PRIMARY":        "#1e3a5f",
    "INTERACTIVE":    "#2563eb",
    "BUY":            "#16a34a",
    "SELL":           "#dc2626",
    "HOLD":           "#b45309",
    "NEUTRAL_LIGHT":  "#f8fafc",
    "NEUTRAL_MID":    "#e2e8f0",
    "NEUTRAL_DARK":   "#0f172a",
}
```

### `SIGNAL_BADGE_STYLE: dict[str, dict[str, str]]`

Per-signal CSS properties for Pandas Styler. Keys are `"BUY"`, `"SELL"`, `"HOLD"`.

```python
SIGNAL_BADGE_STYLE = {
    "BUY":  {"bg": "#dcfce7", "fg": "#16a34a"},
    "SELL": {"bg": "#fee2e2", "fg": "#dc2626"},
    "HOLD": {"bg": "#fef3c7", "fg": "#b45309"},
}
```

---

## Exported Functions

### `get_global_css() -> str`

Returns the full CSS string for injection. Covers:
- Tab strip and tab state styles
- Type scale (h1, h2/h3, body, caption)
- Button border-radius and padding
- Metric label and value colours
- Status message (info/warning/error) consistent styling

**Behaviour rules**:
- Pure function — no side effects, no `st` calls.
- Returns a non-empty string.
- Every colour value in the returned string MUST be drawn from `PALETTE`.

### `inject_global_css() -> None`

Calls `st.markdown(f"<style>{get_global_css()}</style>", unsafe_allow_html=True)`.

Must be called once per page render, before any other `st.*` calls that render visible elements.

### `signal_cell_style(signal_type: str) -> str`

Returns a Pandas Styler-compatible CSS string for a single signal cell.

| Input | Output |
|-------|--------|
| `"BUY"` | `"background-color: #dcfce7; color: #16a34a; font-weight: bold"` |
| `"SELL"` | `"background-color: #fee2e2; color: #dc2626; font-weight: bold"` |
| `"HOLD"` | `"background-color: #fef3c7; color: #b45309; font-weight: bold"` |
| Any other | `""` (empty string — no styling) |

**Behaviour rules**:
- Pure function — no side effects.
- Unknown signal types return `""` (no error raised).

---

## Test Requirements

| Scenario | Expected |
|----------|----------|
| `PALETTE` has exactly 8 keys | `len(PALETTE) == 8` |
| All palette values are valid 7-char hex | Each value matches `^#[0-9a-f]{6}$` |
| `SIGNAL_BADGE_STYLE` has BUY, SELL, HOLD | All three keys present |
| `signal_cell_style("BUY")` returns non-empty string | String contains `#dcfce7` |
| `signal_cell_style("SELL")` returns non-empty string | String contains `#fee2e2` |
| `signal_cell_style("HOLD")` returns non-empty string | String contains `#fef3c7` |
| `signal_cell_style("UNKNOWN")` returns empty string | `== ""` |
| `get_global_css()` is non-empty | `len(get_global_css()) > 0` |
| All hex colours in `get_global_css()` are from `PALETTE` | No rogue colours |
