"""Tests for _top_buy_signals() — written before implementation (TDD)."""
from dataclasses import dataclass


@dataclass
class _Signal:
    symbol: str
    signal_type: str
    confidence_score: int


def _make(symbol, signal_type, confidence):
    return _Signal(symbol=symbol, signal_type=signal_type, confidence_score=confidence)


def test_empty_list_returns_empty():
    from marketpulse.ui.dashboard import _top_buy_signals
    assert _top_buy_signals([]) == []


def test_all_sell_signals_returns_empty():
    from marketpulse.ui.dashboard import _top_buy_signals
    signals = [_make("A", "SELL", 80), _make("B", "SELL", 70)]
    assert _top_buy_signals(signals) == []


def test_all_hold_signals_returns_empty():
    from marketpulse.ui.dashboard import _top_buy_signals
    signals = [_make("A", "HOLD", 55), _make("B", "HOLD", 50)]
    assert _top_buy_signals(signals) == []


def test_all_buy_fewer_than_limit_returns_all_sorted():
    from marketpulse.ui.dashboard import _top_buy_signals
    signals = [_make("A", "BUY", 65), _make("B", "BUY", 80), _make("C", "BUY", 72)]
    result = _top_buy_signals(signals)
    assert len(result) == 3
    assert [s.confidence_score for s in result] == [80, 72, 65]


def test_mixed_signals_returns_only_buy_sorted():
    from marketpulse.ui.dashboard import _top_buy_signals
    signals = [
        _make("A", "BUY", 75),
        _make("B", "SELL", 85),
        _make("C", "HOLD", 55),
        _make("D", "BUY", 90),
    ]
    result = _top_buy_signals(signals)
    assert len(result) == 2
    assert result[0].symbol == "D"
    assert result[1].symbol == "A"
    assert all(s.signal_type == "BUY" for s in result)


def test_more_than_20_buy_returns_top_20():
    from marketpulse.ui.dashboard import _top_buy_signals
    signals = [_make(str(i), "BUY", i) for i in range(25)]
    result = _top_buy_signals(signals)
    assert len(result) == 20
    assert result[0].confidence_score == 24
    assert result[-1].confidence_score == 5


def test_exactly_20_buy_returns_all_20_sorted():
    from marketpulse.ui.dashboard import _top_buy_signals
    signals = [_make(str(i), "BUY", i * 2) for i in range(20)]
    result = _top_buy_signals(signals)
    assert len(result) == 20
    assert result[0].confidence_score == 38
    assert result[-1].confidence_score == 0


def test_custom_limit_respected():
    from marketpulse.ui.dashboard import _top_buy_signals
    signals = [_make(str(i), "BUY", i) for i in range(10)]
    result = _top_buy_signals(signals, limit=5)
    assert len(result) == 5
    assert result[0].confidence_score == 9
    assert result[-1].confidence_score == 5
