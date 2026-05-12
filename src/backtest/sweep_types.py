"""Dataclasses and labels for Layer 1 parameter sweeps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.backtest.backtest_config import BacktestConfig

ENGINE_LABEL = "reference"
SYNTHETIC_SIGNAL_ROW = 3


@dataclass(frozen=True)
class SweepCombo:
    combo_id: str
    params: dict[str, Any]


@dataclass
class SweepResult:
    combo_id: str
    strategy: str
    config_hash: str
    trade_count: int
    total_r: float
    total_net_pnl: float
    total_gross_r: float
    max_drawdown_r: float
    avg_r: float
    win_rate: float
    profit_factor_r: float
    execution_semantics_version: str
    engine: str
    result_lineage: str
    symbol: str = ""
    start: str = ""
    end: str = ""
    params_json: str = ""
    notes: str = ""
    asset: str = "equity"
    data_source: str = ""
    feature_config_hash: str = ""
    signal_contract_version: str = ""


@dataclass
class SweepRunConfig:
    strategy: str = "synthetic_smoke"
    symbol: str = "SYNTH"
    start: str = "2024-01-02"
    end: str = "2024-01-02"
    data_root: str = ""
    output_root: Any = None  # Path | None
    max_combos: int | None = None
    no_save: bool = True
    backtest: BacktestConfig | None = None
    policy: Any = None  # ExecutionPolicy | None
    asset: str = "equity"
