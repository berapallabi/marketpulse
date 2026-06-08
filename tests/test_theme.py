"""TDD tests for marketpulse/ui/theme.py — written before implementation."""
import re


def test_palette_has_8_keys():
    from marketpulse.ui.theme import PALETTE
    assert len(PALETTE) == 8


def test_palette_values_are_valid_hex():
    from marketpulse.ui.theme import PALETTE
    pattern = re.compile(r"^#[0-9a-f]{6}$")
    for name, value in PALETTE.items():
        assert pattern.match(value), f"PALETTE[{name!r}] = {value!r} is not a valid hex colour"


def test_signal_badge_style_has_all_signals():
    from marketpulse.ui.theme import SIGNAL_BADGE_STYLE
    assert "BUY" in SIGNAL_BADGE_STYLE
    assert "SELL" in SIGNAL_BADGE_STYLE
    assert "HOLD" in SIGNAL_BADGE_STYLE


def test_signal_cell_style_buy_contains_fg_colour():
    from marketpulse.ui.theme import signal_cell_style
    result = signal_cell_style("BUY")
    assert "#4ade80" in result
    assert "background-color" not in result


def test_signal_cell_style_sell_contains_fg_colour():
    from marketpulse.ui.theme import signal_cell_style
    result = signal_cell_style("SELL")
    assert "#f87171" in result
    assert "background-color" not in result


def test_signal_cell_style_hold_contains_fg_colour():
    from marketpulse.ui.theme import signal_cell_style
    result = signal_cell_style("HOLD")
    assert "#fbbf24" in result
    assert "background-color" not in result


def test_signal_cell_style_unknown_returns_empty():
    from marketpulse.ui.theme import signal_cell_style
    assert signal_cell_style("UNKNOWN") == ""
    assert signal_cell_style("") == ""


def test_get_global_css_is_non_empty():
    from marketpulse.ui.theme import get_global_css
    css = get_global_css()
    assert isinstance(css, str)
    assert len(css) > 0


def test_get_global_css_colours_from_palette_only():
    from marketpulse.ui.theme import PALETTE, get_global_css
    css = get_global_css()
    palette_values = set(v.lower() for v in PALETTE.values())
    # find all 7-char hex values in the CSS
    found = set(h.lower() for h in re.findall(r"#[0-9a-fA-F]{6}", css))
    rogue = found - palette_values
    assert not rogue, f"CSS contains colours outside palette: {rogue}"
