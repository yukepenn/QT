"""Parameter sweep using testing_parameters YAML grids (Numba fast path only)."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.backtest.fast import prepare_backtest_arrays, run_fast_backtest_from_arrays
from src.data.read_bars import read_bars
from src.features.build_features import build_basic_features
from src.strategies.loader import (
    apply_overrides,
    expand_grid,
    get_nested,
    load_strategy,
    load_strategy_config,
    load_testing_config,
    set_nested,
    strategy_root,
)

SWEEP_ENGINE = "numba_fast"


def _safe_tag(tag: str) -> str:
    s = tag.strip().replace(" ", "_").replace("/", "_").replace("\\", "_")
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", s)


def _load_testing_yaml(path: Path, *, expected_strategy: str) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"invalid testing YAML: {path}")
    gs = data.get("strategy")
    if gs != expected_strategy:
        raise ValueError(
            f"testing YAML strategy field is {gs!r}, expected {expected_strategy!r} ({path})"
        )
    return data


def _apply_display_filters(df: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    """Optional sweep display filters (console / summary only; results.csv unchanged)."""
    out = df
    if args.max_avg_bars_held is not None:
        out = out[out["avg_bars_held"].astype(float) <= float(args.max_avg_bars_held)]
    if args.max_eod_count is not None:
        out = out[out["eod_count"].astype(int) <= int(args.max_eod_count)]
    if args.max_end_of_data_count is not None:
        out = out[out["end_of_data_count"].astype(int) <= int(args.max_end_of_data_count)]
    if args.min_profit_factor is not None:
        out = out[out["profit_factor"].astype(float) >= float(args.min_profit_factor)]
    if args.min_total_r is not None:
        out = out[out["total_r"].astype(float) >= float(args.min_total_r)]
    if args.max_drawdown_r is not None:
        out = out[out["max_drawdown_r"].astype(float) >= float(args.max_drawdown_r)]
    return out


def _flatten_config_section(prefix: str, obj: Any) -> dict[str, Any]:
    """Flatten one config section (features / signal / risk / backtest) to dotted keys."""
    out: dict[str, Any] = {}
    if not isinstance(obj, dict):
        return out
    for k, v in obj.items():
        key = f"{prefix}.{k}"
        if isinstance(v, dict):
            out.update(_flatten_config_section(key, v))
        elif isinstance(v, (list, tuple)):
            out[key] = json.dumps(list(v), default=str)
        elif isinstance(v, set):
            out[key] = json.dumps(sorted(v, key=str), default=str)
        else:
            out[key] = v
    return out


def _flat_config_params(cfg: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for section in ("features", "signal", "risk", "backtest"):
        out.update(_flatten_config_section(section, cfg.get(section) or {}))
    return out


def _display_columns(df: pd.DataFrame, _strategy: str) -> list[str]:
    """Narrow columns for console / summary; full CSV keeps all flattened params."""
    preferred = [
        "strategy",
        "symbol",
        "trades",
        "win_rate",
        "total_net_pnl",
        "total_r",
        "profit_factor",
        "max_drawdown_r",
        "features.orb_open_minutes",
        "signal.side",
        "signal.entry_start_minute",
        "signal.entry_end_minute",
        "signal.daily_signal_mode",
        "risk.stop_mode",
        "risk.target_mode",
        "risk.target_r",
        "signal.extension_band",
        "signal.confirm_mode",
        "signal.require_vwap_slope_filter",
        "signal.slope_filter_mode",
        "risk.target_ref",
        "risk.swing_lookback",
        "signal.require_vwap_side",
        "signal.require_vwap_slope",
        "backtest.max_hold_minutes",
        "max_hold_count",
        "avg_bars_held",
        "eod_count",
        "end_of_data_count",
    ]
    return [c for c in preferred if c in df.columns]


# TODO: when more strategies require different feature parameters, move feature_key into strategy plugin.
def _feat_key(feat: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(feat.get("orb_open_minutes", 15)),
        tuple(feat.get("vwap_bands") or (1.0, 2.0)),
        tuple(feat.get("vol_windows") or (5, 15, 30)),
    )


def _finalize_combo_config(cfg: dict[str, Any]) -> None:
    est = get_nested(cfg, "signal.entry_start_minute")
    if est is None:
        orb_m = int(get_nested(cfg, "features.orb_open_minutes", 15))
        set_nested(cfg, "signal.entry_start_minute", orb_m)


def _metrics_row(
    *,
    strategy: str,
    asset: str,
    symbol: str | None,
    root: str | None,
    contract: str | None,
    start: str,
    end: str,
    cfg: dict[str, Any],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    flat_params = _flat_config_params(cfg)
    row: dict[str, Any] = {
        "strategy": strategy,
        "asset": asset,
        "symbol": symbol or "",
        "root": root or "",
        "contract": contract or "",
        "start": start,
        "end": end,
        "params_json": json.dumps(flat_params, default=str, sort_keys=True),
    }
    row.update(flat_params)
    row.update(metrics)
    return row


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run parameter sweep from testing_parameters YAML (Numba fast path).")
    p.add_argument("--strategy", default="orb_continuation")
    p.add_argument("--asset", choices=["equity", "futures"], default="equity")
    p.add_argument("--symbols", nargs="+", default=None)
    p.add_argument("--root", default=None)
    p.add_argument("--contract", default=None)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--data-dir", default="data/raw/ibkr")
    p.add_argument("--top", type=int, default=30)
    p.add_argument("--min-trades", type=int, default=30)
    p.add_argument("--sort-by", default="profit_factor")
    p.add_argument("--out-dir", default=None)
    p.add_argument("--no-save", action="store_true")
    p.add_argument("--profile", action="store_true")
    p.add_argument("--max-combos", type=int, default=None)
    p.add_argument("--progress-every", type=int, default=25)
    p.add_argument("--testing-config", type=str, default=None, help="Path to testing grid YAML (must match --strategy).")
    p.add_argument("--tag", type=str, default=None, help="Suffix for result folder name (sanitized).")
    p.add_argument("--max-avg-bars-held", type=float, default=None)
    p.add_argument("--max-eod-count", type=int, default=None)
    p.add_argument("--max-end-of-data-count", type=int, default=None)
    p.add_argument("--min-profit-factor", type=float, default=None)
    p.add_argument("--min-total-r", type=float, default=None)
    p.add_argument("--max-drawdown-r", type=float, default=None)
    args = p.parse_args(argv)

    try:
        strat = load_strategy(args.strategy)
    except ValueError as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 2

    if not strat.supports_fast:
        print(
            f"ERROR strategy {args.strategy!r} does not implement fast signal arrays (supports_fast is False)",
            file=sys.stderr,
        )
        return 2

    if args.asset == "equity" and not args.symbols:
        print("ERROR equity requires --symbols", file=sys.stderr)
        return 2
    if args.asset == "futures" and not args.root:
        print("ERROR futures requires --root", file=sys.stderr)
        return 2

    t0 = time.perf_counter()
    t_read = t_feat = t_prep = t_ctx = t_sig = t_bt = t_save = 0.0

    base = load_strategy_config(args.strategy)
    if args.testing_config:
        tcp = Path(args.testing_config)
        testing = _load_testing_yaml(tcp, expected_strategy=args.strategy)
        testing_config_display = str(tcp.resolve())
    else:
        testing = load_testing_config(args.strategy)
        _tp = strategy_root() / "testing_parameters"
        _f = _tp / f"{args.strategy}.yaml"
        if not _f.is_file():
            _f = _tp / f"{args.strategy}_focused.yaml"
        testing_config_display = str(_f.resolve())
    grid_list = expand_grid(testing)
    fixed = testing.get("fixed") or {}
    feat_required = strat.required_features()

    symbols = [s.upper().strip() for s in (args.symbols or [])]
    planned = len(grid_list) * len(symbols)
    print(f"engine={SWEEP_ENGINE}", flush=True)
    print(f"strategy={args.strategy}", flush=True)
    print(f"grid_size={len(grid_list)}", flush=True)
    print(f"symbols={symbols}", flush=True)
    if args.max_combos is not None:
        print(f"max_combos(whole_run)={args.max_combos}", flush=True)
    print(f"combinations_planned={planned}", flush=True)
    print(f"testing_config_path={testing_config_display}", flush=True)
    if args.tag:
        print(f"tag={args.tag!r} safe_tag={_safe_tag(args.tag)!r}", flush=True)

    rows: list[dict[str, Any]] = []
    combo_count = 0
    combos_skipped_duplicate = 0

    for sym in symbols:
        t_r0 = time.perf_counter()
        raw = read_bars(
            asset=args.asset,
            symbol=sym,
            root=args.root,
            start=args.start,
            end=args.end,
            data_dir=args.data_dir,
            contract=args.contract,
        )
        t_read += time.perf_counter() - t_r0
        if raw.empty:
            print(f"WARNING empty bars for {sym}", flush=True)
            continue

        feat_cache: dict[tuple[Any, ...], pd.DataFrame] = {}
        array_cache: dict[tuple[Any, ...], dict[str, Any]] = {}
        context_cache: dict[tuple[Any, ...], Any] = {}
        seen_param_keys: set[tuple[Any, ...]] = set()
        stop_symbol = False

        for combo_flat in grid_list:
            cfg = apply_overrides(base, combo_flat)
            cfg = apply_overrides(cfg, fixed)
            _finalize_combo_config(cfg)

            dup_key = (sym, strat.normalized_param_key(cfg))
            if dup_key in seen_param_keys:
                combos_skipped_duplicate += 1
                continue
            seen_param_keys.add(dup_key)

            if args.max_combos is not None and combo_count >= args.max_combos:
                stop_symbol = True
                break

            feat_cfg = cfg.get("features") or {}
            fk = _feat_key(feat_cfg)
            if fk not in feat_cache:
                t_f0 = time.perf_counter()
                feat_cache[fk] = build_basic_features(
                    raw,
                    orb_open_minutes=fk[0],
                    vwap_bands=fk[1],
                    vol_windows=fk[2],
                    copy=True,
                    allow_overwrite=False,
                ).sort_values("ts_utc", ignore_index=True)
                t_feat += time.perf_counter() - t_f0
                t_p0 = time.perf_counter()
                array_cache[fk] = prepare_backtest_arrays(feat_cache[fk])
                t_prep += time.perf_counter() - t_p0

            feat_df = feat_cache[fk]
            miss = [c for c in feat_required if c not in feat_df.columns]
            if miss:
                raise ValueError(f"missing features: {miss}")

            b = cfg.get("backtest") or {}
            recomp = bool(b.get("recompute_target_from_entry", True))

            ck = (fk, strat.context_key(cfg))
            if ck not in context_cache:
                t_c0 = time.perf_counter()
                context_cache[ck] = strat.prepare_signal_context(feat_df, cfg)
                t_ctx += time.perf_counter() - t_c0

            t_s0 = time.perf_counter()
            sig_arr = strat.generate_signal_arrays_from_context(context_cache[ck], cfg)
            t_sig += time.perf_counter() - t_s0
            t_b0 = time.perf_counter()
            mh_raw = b.get("max_hold_minutes")
            max_hold_kw = None if mh_raw is None else int(mh_raw)

            metrics = run_fast_backtest_from_arrays(
                array_cache[fk],
                sig_arr,
                eod_exit_minute=int(b.get("eod_exit_minute", 389)),
                quantity=float(b.get("quantity", 1.0)),
                commission_per_trade=float(b.get("commission_per_trade", 0.0)),
                slippage_per_share=float(b.get("slippage_per_share", 0.0)),
                recompute_target_from_entry=recomp,
                max_hold_minutes=max_hold_kw,
            )
            t_bt += time.perf_counter() - t_b0

            rows.append(
                _metrics_row(
                    strategy=args.strategy,
                    asset=args.asset,
                    symbol=sym,
                    root=args.root,
                    contract=args.contract,
                    start=args.start,
                    end=args.end,
                    cfg=cfg,
                    metrics=metrics,
                )
            )
            combo_count += 1

            pe = max(1, int(args.progress_every))
            if combo_count % pe == 0:
                elapsed = time.perf_counter() - t0
                print(
                    f"progress symbol={sym} combo={combo_count} elapsed_sec={elapsed:.3f}",
                    flush=True,
                )

        if stop_symbol:
            break

    elapsed = time.perf_counter() - t0
    print(f"combinations_completed={combo_count}", flush=True)
    print(f"combinations_skipped_duplicate={combos_skipped_duplicate}", flush=True)
    if args.profile:
        print(
            f"profile_sec total={elapsed:.3f} read_bars={t_read:.3f} feature_build={t_feat:.3f} "
            f"prepare_arrays={t_prep:.3f} context_prepare={t_ctx:.3f} signal_build={t_sig:.3f} backtest={t_bt:.3f}",
            flush=True,
        )

    res = pd.DataFrame(rows)
    if res.empty:
        print("no results", flush=True)
        return 0

    sort_col = args.sort_by
    if sort_col not in res.columns:
        print(f"WARNING unknown sort-by {sort_col!r}, using profit_factor", flush=True)
        sort_col = "profit_factor"

    filt = res[res["trades"] >= int(args.min_trades)].copy()
    filt_disp = _apply_display_filters(filt, args)
    if sort_col == "profit_factor":
        sorted_disp = filt_disp.sort_values(
            sort_col,
            ascending=False,
            key=lambda s: s.astype(float).replace(float("inf"), 1e308),
        )
    else:
        sorted_disp = filt_disp.sort_values(sort_col, ascending=False)
    topn = min(int(args.top), len(sorted_disp))
    head = sorted_disp.head(topn)

    display_cols = _display_columns(res, args.strategy)

    print(f"\nafter min_trades={args.min_trades}, display_filters -> rows={len(filt_disp)} (from {len(filt)} post-min-trades)", flush=True)
    print(f"top {topn} by {sort_col} (display only):", flush=True)
    if topn:
        show_cols = [c for c in display_cols if c in head.columns]
        print(head[show_cols].to_string(), flush=True)

    for sym in symbols:
        sub = sorted_disp[sorted_disp["symbol"] == sym]
        if len(sub):
            best = sub.iloc[0]
            print(f"\nbest_{sym}:", flush=True)
            bcols = [c for c in display_cols if c in best.index]
            print(best[bcols].to_string(), flush=True)

    if not args.no_save:
        t_sv0 = time.perf_counter()
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        if args.out_dir:
            out = Path(args.out_dir)
        else:
            suf = f"_{_safe_tag(args.tag)}" if args.tag else ""
            out = strategy_root() / "testing_parameters_results" / args.strategy / f"sweep_{ts}{suf}"
        out.mkdir(parents=True, exist_ok=True)
        res.to_csv(out / "results.csv", index=False)
        sum_show = [c for c in display_cols if c in head.columns]
        filt_parts = [
            f"min_trades>={args.min_trades}",
            *( [f"avg_bars_held<={args.max_avg_bars_held}"] if args.max_avg_bars_held is not None else [] ),
            *( [f"eod_count<={args.max_eod_count}"] if args.max_eod_count is not None else [] ),
            *( [f"end_of_data_count<={args.max_end_of_data_count}"] if args.max_end_of_data_count is not None else [] ),
            *( [f"profit_factor>={args.min_profit_factor}"] if args.min_profit_factor is not None else [] ),
            *( [f"total_r>={args.min_total_r}"] if args.min_total_r is not None else [] ),
            *( [f"max_drawdown_r>={args.max_drawdown_r}"] if args.max_drawdown_r is not None else [] ),
        ]
        summary_lines = [
            f"strategy={args.strategy}",
            f"engine={SWEEP_ENGINE}",
            f"testing_config_path={testing_config_display}",
            f"tag={args.tag or ''}",
            f"grid_size={len(grid_list)}",
            f"symbols={symbols}",
            f"combinations_completed={combo_count}",
            f"combinations_skipped_duplicate={combos_skipped_duplicate}",
            f"elapsed_sec={elapsed:.3f}",
            f"min_trades={args.min_trades}",
            f"display_filters={'; '.join(filt_parts)}",
            f"rows_after_display_filters={len(filt_disp)}",
            f"sort_by={sort_col}",
            "",
            "top (display columns; full params in results.csv):",
            head[sum_show].to_string() if topn else "(empty)",
        ]
        (out / "summary.txt").write_text("\n".join(summary_lines), encoding="utf-8")
        (out / "base_config.yaml").write_text(
            yaml.safe_dump(base, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
        (out / "testing_config.yaml").write_text(
            yaml.safe_dump(testing, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
        t_save += time.perf_counter() - t_sv0
        if args.profile:
            print(f"profile_sec save={t_save:.3f}", flush=True)
        print(f"\nWrote sweep results to: {out.resolve()}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
