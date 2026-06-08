"""Feature 007 — Swap Tab Hierarchy.

Buy/Watchlist/My Holdings → outer st.tabs() (bold style)
Cap tiers → inner st.segmented_control() (compact style)
"""
import inspect

from marketpulse.ui import dashboard


class TestOuterTabIsSignal:
    """T002 — outer tab row uses signal labels, not tier labels."""

    def test_outer_tabs_are_buy_watchlist_holdings(self):
        src = inspect.getsource(dashboard._render_market_tab)
        assert 'st.tabs(["Buy", "Watchlist", "My Holdings"])' in src

    def test_old_outer_tier_tabs_call_absent(self):
        """T003 — old tier_tabs = st.tabs(tier_labels) outer loop is removed."""
        src = inspect.getsource(dashboard._render_market_tab)
        assert "tier_tabs = st.tabs(tier_labels)" not in src


class TestInnerTierIsSegmentedControl:
    """T004 — inner tier row uses st.segmented_control keyed as tier_{market}_{signal_slug}."""

    def test_inner_tier_key_starts_with_tier(self):
        src = inspect.getsource(dashboard._render_market_tab)
        assert 'key=f"tier_{market}' in src

    def test_inner_tier_key_does_not_use_old_signal_prefix(self):
        src = inspect.getsource(dashboard._render_market_tab)
        assert 'key=f"signal_{market}_{slug}"' not in src


class TestKeyNamespacingIncludesSignalSlug:
    """T005 — all widget/session-state keys include signal_slug to prevent duplicate key errors."""

    def test_signal_slug_variable_used_in_render_market_tab(self):
        src = inspect.getsource(dashboard._render_market_tab)
        assert "signal_slug" in src

    def test_render_stock_detail_key_includes_signal_slug(self):
        src = inspect.getsource(dashboard._render_market_tab)
        assert 'key=f"{signal_slug}_{slug}"' in src

    def test_tier_buy_session_key_includes_signal_slug(self):
        src = inspect.getsource(dashboard._render_market_tab)
        assert "tier_buy_{market}_{signal_slug}_{slug}" in src

    def test_refresh_button_key_includes_signal_slug(self):
        src = inspect.getsource(dashboard._render_market_tab)
        assert "btn_tier_buy_{market}_{signal_slug}_{slug}" in src


class TestVisualDesignSwap:
    """T012 — visual hierarchy achieved by component choice; no manual CSS overrides."""

    def test_outer_component_is_st_tabs(self):
        """st.tabs() on outer row provides the bold tab style automatically."""
        src = inspect.getsource(dashboard._render_market_tab)
        assert 'st.tabs(["Buy", "Watchlist", "My Holdings"])' in src

    def test_inner_component_is_segmented_control(self):
        """st.segmented_control() on inner row provides the compact pill style automatically."""
        src = inspect.getsource(dashboard._render_market_tab)
        assert 'key=f"tier_{market}' in src

    def test_no_signal_css_override_in_theme(self):
        """Visual swap must come from component choice, not CSS overrides targeting signal labels."""
        from marketpulse.ui import theme
        src = inspect.getsource(theme.inject_global_css)
        assert '"Buy"' not in src
        assert '"Watchlist"' not in src
        assert '"My Holdings"' not in src
