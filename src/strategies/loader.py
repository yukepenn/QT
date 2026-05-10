"""Load strategy plugins and YAML configs; grid expansion and overrides."""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.strategies.strategy.adx_dmi_trend_continuation import (
    AdxDmiTrendContinuationStrategy,
)
from src.strategies.strategy.afternoon_continuation import AfternoonContinuationStrategy
from src.strategies.strategy.base import (
    BaseStrategy,
    validate_required_features_no_lookahead,
)
from src.strategies.strategy.bollinger_band_fade_chop import (
    BollingerBandFadeChopStrategy,
)
from src.strategies.strategy.bollinger_squeeze_breakout import (
    BollingerSqueezeBreakoutStrategy,
)
from src.strategies.strategy.cci_extreme_snapback import CciExtremeSnapbackStrategy
from src.strategies.strategy.consecutive_bar_exhaustion import (
    ConsecutiveBarExhaustionStrategy,
)
from src.strategies.strategy.donchian_channel_breakout import (
    DonchianChannelBreakoutStrategy,
)
from src.strategies.strategy.failed_orb import FailedOrbStrategy
from src.strategies.strategy.gap_acceptance_failure import GapAcceptanceFailureStrategy
from src.strategies.strategy.intraday_ma_crossover import IntradayMaCrossoverStrategy
from src.strategies.strategy.large_candle_failure import LargeCandleFailureStrategy
from src.strategies.strategy.macd_momentum_turn import MacdMomentumTurnStrategy
from src.strategies.strategy.midday_compression_breakout import (
    MiddayCompressionBreakoutStrategy,
)
from src.strategies.strategy.multi_day_level_trap import MultiDayLevelTrapStrategy
from src.strategies.strategy.orb_continuation import ORBContinuationStrategy
from src.strategies.strategy.orb_retest_continuation import (
    OrbRetestContinuationStrategy,
)
from src.strategies.strategy.prior_close_reclaim import PriorCloseReclaimStrategy
from src.strategies.strategy.prior_day_level_trap import PriorDayLevelTrapStrategy
from src.strategies.strategy.pa_broad_channel_zone import PaBroadChannelZoneStrategy
from src.strategies.strategy.pa_buy_sell_close_trend import PaBuySellCloseTrendStrategy
from src.strategies.strategy.pa_climax_reversal import PaClimaxReversalStrategy
from src.strategies.strategy.pa_failed_range_breakout_trap import (
    PaFailedRangeBreakoutTrapStrategy,
)
from src.strategies.strategy.pa_generic_breakout_pullback import (
    PaGenericBreakoutPullbackStrategy,
)
from src.strategies.strategy.pa_mtr_reversal import PaMtrReversalStrategy
from src.strategies.strategy.pa_second_entry_pullback import (
    PaSecondEntryPullbackStrategy,
)
from src.strategies.strategy.pa_tight_channel_pullback import (
    PaTightChannelPullbackStrategy,
)
from src.strategies.strategy.pa_trading_range_bls_hs import PaTradingRangeBlsHsStrategy
from src.strategies.strategy.pa_wedge_reversal import PaWedgeReversalStrategy
from src.strategies.strategy.rsi_failure_swing import RsiFailureSwingStrategy
from src.strategies.strategy.sma20_reclaim_reject import Sma20ReclaimRejectStrategy
from src.strategies.strategy.stochastic_oversold_cross import (
    StochasticOversoldCrossStrategy,
)
from src.strategies.strategy.supertrend_atr_flip import SupertrendAtrFlipStrategy
from src.strategies.strategy.vwap_reclaim_reject import VwapReclaimRejectStrategy
from src.strategies.strategy.vwap_reversal import VWAPReversalStrategy
from src.strategies.strategy.vwap_trend_pullback import VwapTrendPullbackStrategy


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def strategy_root() -> Path:
    return Path(__file__).resolve().parent


_STRATEGY_BY_NAME: dict[str, type[BaseStrategy]] = {
    "intraday_ma_crossover": IntradayMaCrossoverStrategy,
    "rsi_failure_swing": RsiFailureSwingStrategy,
    "bollinger_squeeze_breakout": BollingerSqueezeBreakoutStrategy,
    "bollinger_band_fade_chop": BollingerBandFadeChopStrategy,
    "donchian_channel_breakout": DonchianChannelBreakoutStrategy,
    "consecutive_bar_exhaustion": ConsecutiveBarExhaustionStrategy,
    "orb_continuation": ORBContinuationStrategy,
    "vwap_reversal": VWAPReversalStrategy,
    "failed_orb": FailedOrbStrategy,
    "orb_retest_continuation": OrbRetestContinuationStrategy,
    "vwap_trend_pullback": VwapTrendPullbackStrategy,
    "vwap_reclaim_reject": VwapReclaimRejectStrategy,
    "prior_day_level_trap": PriorDayLevelTrapStrategy,
    "gap_acceptance_failure": GapAcceptanceFailureStrategy,
    "midday_compression_breakout": MiddayCompressionBreakoutStrategy,
    "afternoon_continuation": AfternoonContinuationStrategy,
    "sma20_reclaim_reject": Sma20ReclaimRejectStrategy,
    "macd_momentum_turn": MacdMomentumTurnStrategy,
    "stochastic_oversold_cross": StochasticOversoldCrossStrategy,
    "cci_extreme_snapback": CciExtremeSnapbackStrategy,
    "adx_dmi_trend_continuation": AdxDmiTrendContinuationStrategy,
    "supertrend_atr_flip": SupertrendAtrFlipStrategy,
    "large_candle_failure": LargeCandleFailureStrategy,
    "multi_day_level_trap": MultiDayLevelTrapStrategy,
    "prior_close_reclaim": PriorCloseReclaimStrategy,
    "pa_trading_range_bls_hs": PaTradingRangeBlsHsStrategy,
    "pa_failed_range_breakout_trap": PaFailedRangeBreakoutTrapStrategy,
    "pa_tight_channel_pullback": PaTightChannelPullbackStrategy,
    "pa_mtr_reversal": PaMtrReversalStrategy,
    "pa_broad_channel_zone": PaBroadChannelZoneStrategy,
    "pa_climax_reversal": PaClimaxReversalStrategy,
    "pa_second_entry_pullback": PaSecondEntryPullbackStrategy,
    "pa_wedge_reversal": PaWedgeReversalStrategy,
    "pa_buy_sell_close_trend": PaBuySellCloseTrendStrategy,
    "pa_generic_breakout_pullback": PaGenericBreakoutPullbackStrategy,
}


def available_strategies() -> list[str]:
    return sorted(_STRATEGY_BY_NAME.keys())


def load_strategy(name: str) -> BaseStrategy:
    cls = _STRATEGY_BY_NAME.get(name)
    if cls is None:
        raise ValueError(f"unknown strategy: {name!r}")
    s = cls()
    validate_required_features_no_lookahead(
        strategy_name=s.name, required_features=s.required_features()
    )
    return s


def load_strategy_config(name: str) -> dict[str, Any]:
    path = strategy_root() / "parameters" / f"{name}.yaml"
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_testing_config(name: str) -> dict[str, Any]:
    """Load default testing grid: prefer `testing_parameters/<name>.yaml`, else `<name>_focused.yaml`."""
    base = strategy_root() / "testing_parameters"
    for fname in (f"{name}.yaml", f"{name}_focused.yaml"):
        path = base / fname
        if path.is_file():
            with path.open(encoding="utf-8") as f:
                return yaml.safe_load(f)
    raise FileNotFoundError(f"no testing config for {name!r} under {base}")


def deep_update(base: dict, overrides: dict) -> dict:
    out = deepcopy(base)
    for k, v in overrides.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_update(out[k], v)
        else:
            out[k] = deepcopy(v)
    return out


def set_nested(config: dict, dotted_key: str, value: Any) -> None:
    parts = dotted_key.split(".")
    cur: dict = config
    for p in parts[:-1]:
        nxt = cur.get(p)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[p] = nxt
        cur = nxt
    cur[parts[-1]] = value


def get_nested(config: dict, dotted_key: str, default: Any = None) -> Any:
    cur: Any = config
    for p in dotted_key.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def expand_grid(testing_config: dict) -> list[dict[str, Any]]:
    grid = testing_config.get("grid") or {}
    if not grid:
        return [{}]
    keys = list(grid.keys())
    vals = []
    for k in keys:
        v = grid[k]
        if isinstance(v, (list, tuple)):
            vals.append(list(v))
        else:
            vals.append([v])
    out: list[dict[str, Any]] = []
    for combo in itertools.product(*vals):
        out.append(dict(zip(keys, combo)))
    return out


def apply_overrides(base_config: dict, flat_overrides: dict[str, Any]) -> dict:
    cfg = deepcopy(base_config)
    for k, v in flat_overrides.items():
        set_nested(cfg, k, deepcopy(v))
    return cfg


def grid_size(testing_config: dict) -> int:
    return len(expand_grid(testing_config))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Strategy loader utilities.")
    p.add_argument(
        "--list",
        action="store_true",
        help="Print registered strategy names and exit (alias for default run).",
    )
    p.add_argument("--strategy", default="orb_continuation")
    p.add_argument("--show-config", action="store_true")
    p.add_argument("--show-testing-grid", action="store_true")
    args = p.parse_args(argv)

    print("available_strategies:", available_strategies(), flush=True)
    if args.list:
        return 0
    if args.show_config:
        cfg = load_strategy_config(args.strategy)
        print("base_config:", flush=True)
        print(json.dumps(cfg, indent=2, default=str), flush=True)
    if args.show_testing_grid:
        tcfg = load_testing_config(args.strategy)
        n = grid_size(tcfg)
        print(f"testing_grid_size={n}", flush=True)
        print("testing_config:", flush=True)
        print(json.dumps(tcfg, indent=2, default=str), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
