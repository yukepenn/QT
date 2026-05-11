import pytest

from src.combiner.run import _combiner_cfg_from_yaml


def test_max_open_positions_guard_raises():
    cfg = {
        "execution": {"eod_exit_minute": 389},
        "system": {"max_open_positions": 2},
        "conflict": {},
    }
    with pytest.raises(NotImplementedError):
        _combiner_cfg_from_yaml(cfg)

