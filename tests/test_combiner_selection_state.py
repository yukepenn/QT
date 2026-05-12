"""Combiner selection + state helpers (no Layer2 runs)."""

from src.combiner.selection import choose_highest_priority, rank_candidates
from src.combiner.state import CombinerState


def test_choose_highest_priority_basic():
    rows = [{"p": 1.0, "id": "b"}, {"p": 2.0, "id": "a"}, {"p": 1.5, "id": "c"}]
    i = choose_highest_priority(rows, priority_key=lambda r: r["p"])
    assert i == 1


def test_choose_highest_priority_tie_stable():
    rows = [{"p": 1.0, "id": "z"}, {"p": 1.0, "id": "a"}]
    i = choose_highest_priority(
        rows,
        priority_key=lambda r: r["p"],
        tie_key=lambda r, idx: (r["id"], idx),
    )
    assert i == 1


def test_rank_candidates_order():
    rows = [
        {"priority": 1.0, "candidate_id": "c2"},
        {"priority": 3.0, "candidate_id": "c1"},
        {"priority": 3.0, "candidate_id": "c0"},
    ]
    order = rank_candidates(rows)
    assert order[0] == 2


def test_state_max_trades_per_day():
    s = CombinerState()
    s.ensure_day("2024-01-02")
    s.register_trade_open()
    s.register_trade_close(0.5)
    s.register_trade_open()
    assert s.max_trades_per_day_exceeded(2)


def test_state_cooldown():
    s = CombinerState()
    s.start_cooldown(from_bar=10, cooldown_bars=3)
    assert not s.can_enter_bar(12)
    assert s.can_enter_bar(13)


def test_state_daily_loss():
    s = CombinerState()
    s.ensure_day("2024-01-02")
    s.register_trade_open()
    s.register_trade_close(-1.5)
    assert s.daily_loss_exceeded(1.0)
