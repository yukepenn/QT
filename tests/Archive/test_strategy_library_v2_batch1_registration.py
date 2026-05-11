from __future__ import annotations

import yaml

from src.strategies.loader import available_strategies, load_strategy, strategy_root
from src.strategies.metadata import get_strategy_metadata

BATCH1 = [
    "intraday_ma_crossover",
    "rsi_failure_swing",
    "bollinger_squeeze_breakout",
    "bollinger_band_fade_chop",
    "donchian_channel_breakout",
    "consecutive_bar_exhaustion",
]


def test_loader_lists_batch1() -> None:
    names = available_strategies()
    for s in BATCH1:
        assert s in names


def test_all_support_fast() -> None:
    for s in BATCH1:
        assert load_strategy(s).supports_fast is True


def test_focused_yaml_exists() -> None:
    base = strategy_root() / "testing_parameters"
    for s in BATCH1:
        assert (base / f"{s}_focused.yaml").is_file()


def test_parameters_yaml_exists() -> None:
    base = strategy_root() / "parameters"
    for s in BATCH1:
        assert (base / f"{s}.yaml").is_file()


def test_metadata_entries() -> None:
    for s in BATCH1:
        m = get_strategy_metadata(s)
        assert m.get("family") not in (None, "unknown")
        assert m.get("conflict_group") == "QQQ_directional"


def test_required_features_no_lookahead() -> None:
    for s in BATCH1:
        st = load_strategy(s)
        for c in st.required_features():
            assert "LOOKAHEAD" not in c


def test_validate_accepts_defaults() -> None:
    for s in BATCH1:
        st = load_strategy(s)
        path = strategy_root() / "parameters" / f"{s}.yaml"
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        st.validate_config(cfg)


def test_validate_rejects_bad_minutes() -> None:
    st = load_strategy("intraday_ma_crossover")
    path = strategy_root() / "parameters" / "intraday_ma_crossover.yaml"
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    cfg.setdefault("signal", {})["entry_start_minute"] = 200
    cfg.setdefault("signal", {})["entry_end_minute"] = 30
    try:
        st.validate_config(cfg)
        raised = False
    except ValueError:
        raised = True
    assert raised
