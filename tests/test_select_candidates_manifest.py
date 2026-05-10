"""Manifest-mode select_candidates accepts multiple strategy sweep CSVs."""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd
import pytest

from src.research import select_candidates


def _minimal_results_row(
    strategy: str,
    *,
    trades: int,
    pf: float,
    total_r: float,
    mdd: float,
    avg_bars: float,
    eod: int = 0,
    eod_data: int = 0,
) -> dict:
    return {
        "strategy": strategy,
        "symbol": "QQQ",
        "asset": "equity",
        "trades": trades,
        "profit_factor": pf,
        "total_r": total_r,
        "max_drawdown_r": mdd,
        "win_rate": 0.5,
        "total_net_pnl": 0.0,
        "avg_r": 0.0,
        "avg_net_pnl": 0.0,
        "max_drawdown_pnl": 0.0,
        "avg_bars_held": avg_bars,
        "stop_count": 0,
        "target_count": 0,
        "eod_count": eod,
        "end_of_data_count": eod_data,
        "max_hold_count": 0,
        "params_json": "{}",
    }


def test_manifest_mode_two_strategies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    strat_a = "fake_manifest_a"
    strat_b = "fake_manifest_b"
    dir_a = tmp_path / "sweep_a"
    dir_b = tmp_path / "sweep_b"
    dir_a.mkdir()
    dir_b.mkdir()
    csv_a = dir_a / "results.csv"
    csv_b = dir_b / "results.csv"
    df_a = pd.DataFrame(
        [
            _minimal_results_row(strat_a, trades=50, pf=1.2, total_r=5.0, mdd=-10.0, avg_bars=5.0),
            _minimal_results_row(strat_a, trades=45, pf=1.1, total_r=3.0, mdd=-12.0, avg_bars=6.0),
        ]
    )
    df_b = pd.DataFrame(
        [
            _minimal_results_row(strat_b, trades=60, pf=1.06, total_r=1.0, mdd=-20.0, avg_bars=8.0),
        ]
    )
    df_a.to_csv(csv_a, index=False)
    df_b.to_csv(csv_b, index=False)

    manifest = tmp_path / "sweep_manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["strategy", "status", "results_csv"])
        w.writerow([strat_a, "ok", str(csv_a)])
        w.writerow([strat_b, "ok", str(csv_b)])

    out_dir = tmp_path / "out"
    monkeypatch.chdir(tmp_path)
    import src.research.select_candidates as sc

    _orig_meta = sc.get_strategy_metadata

    def _meta(name: str) -> dict:
        if name in (strat_a, strat_b):
            return {
                "family": "test_family",
                "conflict_group": "QQQ_directional",
                "default_priority": 50,
                "default_active_start_minute": 30,
                "default_active_end_minute": 330,
            }
        return _orig_meta(name)

    monkeypatch.setattr(sc, "get_strategy_metadata", _meta)

    argv = [
        "--manifest",
        str(manifest),
        "--out-dir",
        str(out_dir),
        "--top-per-strategy",
        "2",
        "--min-trades",
        "40",
        "--min-profit-factor",
        "1.05",
        "--min-total-r",
        "0",
        "--max-drawdown-r",
        "-60",
        "--max-avg-bars-held",
        "120",
        "--max-eod-count",
        "0",
        "--max-end-of-data-count",
        "0",
        "--allow-relaxed-fallback",
        "--relaxed-min-trades",
        "25",
        "--relaxed-min-profit-factor",
        "1.0",
        "--relaxed-min-total-r",
        "-5",
        "--relaxed-max-drawdown-r",
        "-70",
    ]
    assert select_candidates.main(argv) == 0
    sel = pd.read_csv(out_dir / "selected_candidates.csv")
    assert len(sel) == 3  # 2 from A + 1 from B (strict)
    assert set(sel["strategy"]) == {strat_a, strat_b}


def test_unflatten_config_nested_features_indicators() -> None:
    row = pd.Series(
        {
            "features.orb_open_minutes": 15,
            "features.indicators.macd_tuples": "[[8, 21, 9]]",
            "features.indicators.ema_windows": "[20]",
            "features.vol_windows": "[5, 15]",
            "signal.side": "long_only",
            "params_json": "{}",
        }
    )
    cfg = select_candidates.unflatten_config_from_row(row)
    ind = cfg.get("features", {}).get("indicators", {})
    assert ind.get("macd_tuples") == [[8, 21, 9]]
    assert ind.get("ema_windows") == [20]
    assert cfg["features"]["orb_open_minutes"] == 15
