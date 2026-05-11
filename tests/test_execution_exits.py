import pytest

from src.execution.exits import intrabar_stop_target_hit, resolve_stop_target_order
from src.execution.types import AmbiguityPolicy, ExitReason, Side


def test_stop_first_same_bar():
    st, tg = intrabar_stop_target_hit(
        side=Side.LONG,
        high=110.0,
        low=95.0,
        stop=96.0,
        target=108.0,
        ambiguity=AmbiguityPolicy.STOP_FIRST,
    )
    assert st and tg
    assert resolve_stop_target_order(st, tg, AmbiguityPolicy.STOP_FIRST) == ExitReason.STOP


def test_target_only():
    st, tg = intrabar_stop_target_hit(
        side=Side.LONG,
        high=110.0,
        low=100.0,
        stop=96.0,
        target=108.0,
        ambiguity=AmbiguityPolicy.STOP_FIRST,
    )
    assert resolve_stop_target_order(st, tg, AmbiguityPolicy.STOP_FIRST) == ExitReason.TARGET


def test_short_stop_hit():
    st, tg = intrabar_stop_target_hit(
        side=Side.SHORT,
        high=105.0,
        low=93.0,
        stop=104.0,
        target=92.0,
        ambiguity=AmbiguityPolicy.STOP_FIRST,
    )
    assert st and not tg
