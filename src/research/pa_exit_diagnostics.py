"""PA exit / economics diagnostics from a Layer 1 candidate YAML (full ``config`` block)."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.backtest.fast import prepare_backtest_arrays, run_fast_backtest_from_arrays
from src.data.read_bars import read_bars
from src.features.feature_key import build_features_from_config
from src.strategies.loader import load_strategy


def _cfg_from_candidate_yaml(path: Path) -> tuple[str, dict[str, Any]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("invalid yaml")
    strat_name = str(raw.get("strategy") or "")
    inner = raw.get("config")
    if not isinstance(inner, dict):
        raise ValueError("candidate yaml missing config: block")
    inner.setdefault("strategy", strat_name)
    inner.setdefault("asset", raw.get("asset"))
    inner.setdefault("symbol", raw.get("symbol"))
    return strat_name, inner


def run_candidate_yaml(
    yaml_path: Path,
    *,
    start: str,
    end: str,
    slippage_stress: float | None,
) -> dict[str, Any]:
    strategy_name, cfg = _cfg_from_candidate_yaml(yaml_path)
    strat = load_strategy(strategy_name)
    strat.validate_config(cfg)

    asset = str(cfg.get("asset") or "equity")
    symbol = str(cfg.get("symbol") or "QQQ")

    bars = read_bars(asset=asset, symbol=symbol, start=start, end=end)
    if bars.empty:
        raise RuntimeError("empty bars window")

    feat = build_features_from_config(bars, cfg).sort_values(
        "ts_utc", ignore_index=True
    )
    ctx = strat.prepare_signal_context(feat, cfg)
    sig = strat.generate_signal_arrays_from_context(ctx, cfg)

    bt = prepare_backtest_arrays(feat)
    back = cfg.get("backtest") or {}
    slip_base = float(back.get("slippage_per_share", 0.01))
    reco = bool(back.get("recompute_target_from_entry", True))
    mh = back.get("max_hold_minutes")

    m_base = run_fast_backtest_from_arrays(
        bt,
        sig,
        eod_exit_minute=int(back.get("eod_exit_minute", 389)),
        quantity=float(back.get("quantity", 1.0)),
        commission_per_trade=float(back.get("commission_per_trade", 0.0)),
        slippage_per_share=slip_base,
        recompute_target_from_entry=reco,
        max_hold_minutes=int(mh) if mh is not None else None,
    )

    out: dict[str, Any] = {
        "candidate_yaml": str(yaml_path).replace("\\", "/"),
        "strategy": strategy_name,
        "symbol": symbol,
        "start": start,
        "end": end,
        "slippage_per_share": slip_base,
        **{
            k: m_base[k]
            for k in (
                "trades",
                "total_r",
                "profit_factor",
                "avg_bars_held",
                "stop_count",
                "target_count",
                "max_hold_count",
            )
        },
    }

    if slippage_stress is not None:
        m_stress = run_fast_backtest_from_arrays(
            bt,
            sig,
            eod_exit_minute=int(back.get("eod_exit_minute", 389)),
            quantity=float(back.get("quantity", 1.0)),
            commission_per_trade=float(back.get("commission_per_trade", 0.0)),
            slippage_per_share=float(slippage_stress),
            recompute_target_from_entry=reco,
            max_hold_minutes=int(mh) if mh is not None else None,
        )
        out["slippage_stress"] = float(slippage_stress)
        out["total_r_at_slippage_stress"] = float(m_stress.get("total_r") or 0.0)
        out["profit_factor_at_slippage_stress"] = float(
            m_stress.get("profit_factor") or 0.0
        )

    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="PA exit diagnostics")
    p.add_argument("--candidate-yaml", type=Path, required=True)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--slippage-stress", type=float, default=0.02)
    p.add_argument("--output-root", type=Path, required=True)
    args = p.parse_args(argv)

    row = run_candidate_yaml(
        args.candidate_yaml,
        start=args.start,
        end=args.end,
        slippage_stress=args.slippage_stress,
    )

    args.output_root.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_root / "pa_exit_rows.csv"
    write_header = not csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            w.writeheader()
        w.writerow(row)

    print(json.dumps(row, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
