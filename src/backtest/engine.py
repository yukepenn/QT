"""Single-symbol backtest using standard signal columns."""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.backtest.metrics import summarize_trades
from src.backtest.execution import (
    is_finite_price,
    valid_fixed_price_target_side,
    valid_stop_side,
    valid_target_r,
)
from src.data.read_bars import read_bars
from src.features.build_features import build_basic_features
from src.strategies.loader import deep_update, load_strategy, load_strategy_config
from src.strategies.strategy.base import validate_standard_signal_columns


@dataclass(frozen=True)
class BacktestConfig:
    session_col: str = "session_date"
    time_col: str = "ts_utc"
    ny_time_col: str = "ts_ny"
    minute_col: str = "minute_from_open"
    open_col: str = "open"
    high_col: str = "high"
    low_col: str = "low"
    close_col: str = "close"

    side_col: str = "sig_side"
    stop_col: str = "sig_stop"
    target_col: str = "sig_target"
    target_mode_col: str = "sig_target_mode"
    target_r_col: str = "sig_target_r"
    risk_col: str = "sig_risk_per_share"
    reason_col: str = "sig_reason"
    valid_col: str = "sig_valid"
    strategy_col: str = "sig_strategy"

    eod_exit_minute: int = 389
    quantity: float = 1.0
    commission_per_trade: float = 0.0
    slippage_per_share: float = 0.0
    recompute_target_from_entry: bool = True
    max_hold_minutes: int | None = None


def _bt_cfg_from_dict(d: dict[str, Any] | None) -> BacktestConfig:
    if not d:
        return BacktestConfig()
    b = d.get("backtest") or {}
    mh = b.get("max_hold_minutes", None)
    max_hold: int | None
    if mh is None:
        max_hold = None
    else:
        max_hold = int(mh)
        if max_hold <= 0:
            raise ValueError("backtest.max_hold_minutes must be > 0 when set")
    return BacktestConfig(
        eod_exit_minute=int(b.get("eod_exit_minute", 389)),
        quantity=float(b.get("quantity", 1.0)),
        commission_per_trade=float(b.get("commission_per_trade", 0.0)),
        slippage_per_share=float(b.get("slippage_per_share", 0.0)),
        recompute_target_from_entry=bool(b.get("recompute_target_from_entry", True)),
        max_hold_minutes=max_hold,
    )


def run_backtest(
    df: pd.DataFrame,
    *,
    config: BacktestConfig | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    cfg = config or BacktestConfig()
    validate_standard_signal_columns(df)

    need = [
        cfg.session_col,
        cfg.time_col,
        cfg.ny_time_col,
        cfg.minute_col,
        cfg.open_col,
        cfg.high_col,
        cfg.low_col,
        cfg.close_col,
        cfg.side_col,
        cfg.stop_col,
        cfg.target_col,
        cfg.target_mode_col,
        cfg.target_r_col,
        cfg.risk_col,
        cfg.valid_col,
    ]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise ValueError(f"run_backtest missing columns: {miss}")

    work = df.sort_values(cfg.time_col).reset_index(drop=True)
    trades: list[dict[str, Any]] = []
    trade_id = 0

    for sid, sub in work.groupby(cfg.session_col, sort=False):
        sub = sub.reset_index(drop=True)
        n = len(sub)
        i = 0
        in_pos = False
        entry_idx = -1
        side = 0
        stop_px = 0.0
        tgt_px = 0.0
        actual_risk = 0.0
        entry_price = 0.0
        sig_reason = ""
        strat_name = ""
        signal_ts_utc = pd.NaT
        signal_ts_ny = pd.NaT
        signal_close = float("nan")
        trade_target_mode = ""
        trade_target_r = float("nan")

        while i < n:
            row = sub.iloc[i]
            if not in_pos:
                v = row[cfg.valid_col]
                valid = not pd.isna(v) and bool(v)
                sd = int(row[cfg.side_col]) if not pd.isna(row[cfg.side_col]) else 0
                if valid and sd != 0 and i + 1 < n:
                    next_row = sub.iloc[i + 1]
                    if next_row[cfg.session_col] != row[cfg.session_col]:
                        i += 1
                        continue

                    ent_open_raw = float(next_row[cfg.open_col])
                    stop_raw = row[cfg.stop_col]
                    if pd.isna(stop_raw):
                        i += 1
                        continue
                    stop_px = float(stop_raw)
                    if sd == 1:
                        entry_price = ent_open_raw + cfg.slippage_per_share
                    else:
                        entry_price = ent_open_raw - cfg.slippage_per_share
                    if not (is_finite_price(entry_price) and is_finite_price(stop_px)):
                        i += 1
                        continue
                    if not valid_stop_side(sd, entry_price, stop_px):
                        i += 1
                        continue

                    actual_risk = (entry_price - stop_px) if sd == 1 else (stop_px - entry_price)
                    if not is_finite_price(actual_risk) or actual_risk <= 0:
                        i += 1
                        continue

                    min_r = 0.0
                    try:
                        min_r = float((row.get(cfg.risk_col) if cfg.risk_col in row.index else 0.0) or 0.0)
                    except Exception:
                        min_r = 0.0
                    # Prefer config-defined min_risk_per_share when present.
                    try:
                        cfg_min = float((df.attrs.get("_min_risk_per_share") or 0.0))
                        if cfg_min > 0:
                            min_r = max(min_r, cfg_min)
                    except Exception:
                        pass
                    if min_r > 0 and actual_risk < min_r:
                        i += 1
                        continue

                    tm = str(row[cfg.target_mode_col] or "").strip().lower()
                    tr_raw = row[cfg.target_r_col]
                    tr = float(tr_raw) if not pd.isna(tr_raw) else float("nan")
                    tgt_raw = row[cfg.target_col]
                    if pd.isna(tgt_raw):
                        i += 1
                        continue
                    sig_preview = float(tgt_raw)

                    if tm == "fixed_r":
                        if not valid_target_r(tr):
                            i += 1
                            continue
                        if cfg.recompute_target_from_entry:
                            if sd == 1:
                                tgt_px = entry_price + tr * actual_risk
                            else:
                                tgt_px = entry_price - tr * actual_risk
                        else:
                            tgt_px = sig_preview
                    elif tm == "fixed_price":
                        tgt_px = sig_preview
                        if not (is_finite_price(tgt_px) and valid_fixed_price_target_side(sd, entry_price, tgt_px)):
                            i += 1
                            continue
                    else:
                        raise ValueError(f"unknown sig_target_mode: {row[cfg.target_mode_col]!r}")

                    trade_id += 1
                    in_pos = True
                    entry_idx = i + 1
                    side = sd
                    sig_reason = str(row.get(cfg.reason_col, "") or "")
                    strat_name = str(row.get(cfg.strategy_col, "") or "")
                    signal_ts_utc = row[cfg.time_col]
                    signal_ts_ny = row[cfg.ny_time_col]
                    signal_close = float(row[cfg.close_col])
                    trade_target_mode = str(row[cfg.target_mode_col] or "")
                    trade_target_r = tr
                    i = entry_idx
                    continue
                i += 1
                continue

            bar = sub.iloc[i]
            hi = float(bar[cfg.high_col])
            lo = float(bar[cfg.low_col])
            clo = float(bar[cfg.close_col])
            m = int(bar[cfg.minute_col])

            ent_open_raw = float(sub.iloc[entry_idx][cfg.open_col])
            if side == 1:
                entry_price = ent_open_raw + cfg.slippage_per_share
            else:
                entry_price = ent_open_raw - cfg.slippage_per_share

            exit_reason = ""
            raw_exit = float("nan")
            exit_price = float("nan")

            if i >= entry_idx:
                if side == 1:
                    hit_stop = lo <= stop_px
                    hit_tgt = hi >= tgt_px
                    if hit_stop and hit_tgt:
                        exit_reason = "stop"
                        raw_exit = stop_px
                        exit_price = raw_exit - cfg.slippage_per_share
                    elif hit_stop:
                        exit_reason = "stop"
                        raw_exit = stop_px
                        exit_price = raw_exit - cfg.slippage_per_share
                    elif hit_tgt:
                        exit_reason = "target"
                        raw_exit = tgt_px
                        exit_price = raw_exit - cfg.slippage_per_share
                else:
                    hit_stop = hi >= stop_px
                    hit_tgt = lo <= tgt_px
                    if hit_stop and hit_tgt:
                        exit_reason = "stop"
                        raw_exit = stop_px
                        exit_price = raw_exit + cfg.slippage_per_share
                    elif hit_stop:
                        exit_reason = "stop"
                        raw_exit = stop_px
                        exit_price = raw_exit + cfg.slippage_per_share
                    elif hit_tgt:
                        exit_reason = "target"
                        raw_exit = tgt_px
                        exit_price = raw_exit + cfg.slippage_per_share

            if (
                not exit_reason
                and cfg.max_hold_minutes is not None
                and (i - entry_idx + 1) >= cfg.max_hold_minutes
            ):
                exit_reason = "max_hold"
                raw_exit = clo
                if side == 1:
                    exit_price = raw_exit - cfg.slippage_per_share
                else:
                    exit_price = raw_exit + cfg.slippage_per_share

            if not exit_reason and m >= cfg.eod_exit_minute:
                exit_reason = "eod"
                raw_exit = clo
                if side == 1:
                    exit_price = raw_exit - cfg.slippage_per_share
                else:
                    exit_price = raw_exit + cfg.slippage_per_share

            at_session_end = i == n - 1
            if not exit_reason and at_session_end:
                exit_reason = "end_of_data"
                raw_exit = clo
                if side == 1:
                    exit_price = raw_exit - cfg.slippage_per_share
                else:
                    exit_price = raw_exit + cfg.slippage_per_share

            if exit_reason:
                if side == 1:
                    gross_ps = exit_price - entry_price
                    r_mult = (exit_price - entry_price) / actual_risk if actual_risk > 0 else 0.0
                else:
                    gross_ps = entry_price - exit_price
                    r_mult = (entry_price - exit_price) / actual_risk if actual_risk > 0 else 0.0
                net_pnl = gross_ps * cfg.quantity - cfg.commission_per_trade

                sl_ent = sub.iloc[entry_idx : i + 1]
                mx_hi = float(sl_ent[cfg.high_col].max())
                mn_lo = float(sl_ent[cfg.low_col].min())
                if side == 1:
                    mfe = mx_hi - entry_price
                    mae = entry_price - mn_lo
                else:
                    mfe = entry_price - mn_lo
                    mae = mx_hi - entry_price

                trades.append(
                    {
                        "trade_id": trade_id,
                        "strategy": strat_name,
                        "session_date": sid,
                        "side": side,
                        "signal_ts_utc": signal_ts_utc,
                        "signal_ts_ny": signal_ts_ny,
                        "entry_ts_utc": sub.iloc[entry_idx][cfg.time_col],
                        "entry_ts_ny": sub.iloc[entry_idx][cfg.ny_time_col],
                        "exit_ts_utc": bar[cfg.time_col],
                        "exit_ts_ny": bar[cfg.ny_time_col],
                        "signal_close": signal_close,
                        "raw_entry_price": ent_open_raw,
                        "entry_price": entry_price,
                        "raw_exit_price": raw_exit,
                        "exit_price": exit_price,
                        "stop_price": stop_px,
                        "target_price": tgt_px,
                        "target_mode": trade_target_mode,
                        "target_r": trade_target_r,
                        "risk_per_share": actual_risk,
                        "quantity": cfg.quantity,
                        "gross_pnl_per_share": gross_ps,
                        "net_pnl": net_pnl,
                        "r_multiple": r_mult,
                        "exit_reason": exit_reason,
                        "bars_held": i - entry_idx + 1,
                        "signal_reason": sig_reason,
                        "mfe_per_share": mfe,
                        "mae_per_share": mae,
                    }
                )
                in_pos = False
                entry_idx = -1
                i += 1
                continue

            i += 1

    trades_df = pd.DataFrame(trades)
    if len(trades_df) == 0:
        trades_df = pd.DataFrame(
            columns=[
                "trade_id",
                "strategy",
                "session_date",
                "side",
                "signal_ts_utc",
                "signal_ts_ny",
                "entry_ts_utc",
                "entry_ts_ny",
                "exit_ts_utc",
                "exit_ts_ny",
                "signal_close",
                "raw_entry_price",
                "entry_price",
                "raw_exit_price",
                "exit_price",
                "stop_price",
                "target_price",
                "target_mode",
                "target_r",
                "risk_per_share",
                "quantity",
                "gross_pnl_per_share",
                "net_pnl",
                "r_multiple",
                "exit_reason",
                "bars_held",
                "signal_reason",
                "mfe_per_share",
                "mae_per_share",
            ]
        )
        equity_df = pd.DataFrame(
            columns=["trade_id", "exit_ts_utc", "session_date", "net_pnl", "cum_pnl", "r_multiple", "cum_r"]
        )
        return trades_df, equity_df, summarize_trades(trades_df)

    equity_rows: list[dict[str, Any]] = []
    cum_p = 0.0
    cum_rr = 0.0
    for _, t in trades_df.iterrows():
        cum_p += float(t["net_pnl"])
        cum_rr += float(t["r_multiple"])
        equity_rows.append(
            {
                "trade_id": int(t["trade_id"]),
                "exit_ts_utc": t["exit_ts_utc"],
                "session_date": t["session_date"],
                "net_pnl": float(t["net_pnl"]),
                "cum_pnl": cum_p,
                "r_multiple": float(t["r_multiple"]),
                "cum_r": cum_rr,
            }
        )
    equity_df = pd.DataFrame(equity_rows)
    metrics = summarize_trades(trades_df)
    return trades_df, equity_df, metrics


def run_strategy_backtest(
    *,
    strategy_name: str,
    asset: str,
    symbol: str | None,
    root: str | None,
    contract: str | None,
    start: str,
    end: str,
    config_override: dict | None = None,
    data_dir: str = "data/raw/ibkr",
) -> tuple[pd.DataFrame, pd.DataFrame, dict, dict]:
    base = load_strategy_config(strategy_name)
    cfg = deep_update(base, config_override) if config_override else deep_update(base, {})

    raw = read_bars(
        asset=asset,
        symbol=symbol,
        root=root,
        start=start,
        end=end,
        data_dir=data_dir,
        contract=contract,
    )
    if raw.empty:
        raise ValueError("no bars loaded")

    feat_cfg = cfg.get("features") or {}
    orb_m = int(feat_cfg.get("orb_open_minutes", 15))
    vb = tuple(feat_cfg.get("vwap_bands") or (1.0, 2.0))
    vw = tuple(feat_cfg.get("vol_windows") or (5, 15, 30))
    feat = build_basic_features(
        raw,
        orb_open_minutes=orb_m,
        vwap_bands=vb,
        vol_windows=vw,
        copy=True,
        allow_overwrite=False,
    )

    strat = load_strategy(strategy_name)
    miss = [c for c in strat.required_features() if c not in feat.columns]
    if miss:
        raise ValueError(f"feature build missing columns for {strategy_name}: {miss}")

    sig_df = strat.generate_signals(feat, cfg)
    validate_standard_signal_columns(sig_df)

    # Provide config-level min_risk_per_share to the backtest loop (signal-level may differ).
    try:
        sig_df.attrs["_min_risk_per_share"] = float((cfg.get("risk") or {}).get("min_risk_per_share") or 0.0)
    except Exception:
        sig_df.attrs["_min_risk_per_share"] = 0.0

    btc = _bt_cfg_from_dict(cfg)
    trades_df, equity_df, metrics = run_backtest(sig_df, config=btc)
    return trades_df, equity_df, metrics, cfg


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run single-symbol strategy backtest.")
    p.add_argument("--strategy", default="orb_continuation")
    p.add_argument("--asset", choices=["equity", "futures"], required=True)
    p.add_argument("--symbol", default=None)
    p.add_argument("--root", default=None)
    p.add_argument("--contract", default=None)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--data-dir", default="data/raw/ibkr")
    p.add_argument("--out-dir", default=None)
    p.add_argument("--head", type=int, default=20)

    p.add_argument("--orb-open-minutes", type=int, default=None)
    p.add_argument("--side", default=None)
    p.add_argument("--entry-end-minute", type=int, default=None)
    p.add_argument("--daily-signal-mode", default=None)
    p.add_argument("--stop-mode", default=None)
    p.add_argument("--target-r", type=float, default=None)
    p.add_argument("--commission-per-trade", type=float, default=None)
    p.add_argument("--slippage-per-share", type=float, default=None)
    p.add_argument("--max-hold-minutes", type=int, default=None)

    args = p.parse_args(argv)

    if args.asset == "equity" and not args.symbol:
        print("ERROR equity requires --symbol", file=sys.stderr)
        return 2
    if args.asset == "futures" and not args.root:
        print("ERROR futures requires --root", file=sys.stderr)
        return 2

    override: dict[str, Any] = {}
    if args.orb_open_minutes is not None:
        override.setdefault("features", {})["orb_open_minutes"] = int(args.orb_open_minutes)
        override.setdefault("signal", {})["entry_start_minute"] = int(args.orb_open_minutes)
    if args.side is not None:
        override.setdefault("signal", {})["side"] = args.side
    if args.entry_end_minute is not None:
        override.setdefault("signal", {})["entry_end_minute"] = int(args.entry_end_minute)
    if args.daily_signal_mode is not None:
        override.setdefault("signal", {})["daily_signal_mode"] = args.daily_signal_mode
    if args.stop_mode is not None:
        override.setdefault("risk", {})["stop_mode"] = args.stop_mode
    if args.target_r is not None:
        override.setdefault("risk", {})["target_r"] = float(args.target_r)
    if args.commission_per_trade is not None:
        override.setdefault("backtest", {})["commission_per_trade"] = float(args.commission_per_trade)
    if args.slippage_per_share is not None:
        override.setdefault("backtest", {})["slippage_per_share"] = float(args.slippage_per_share)
    if args.max_hold_minutes is not None:
        if int(args.max_hold_minutes) <= 0:
            print("ERROR --max-hold-minutes must be > 0", file=sys.stderr)
            return 2
        override.setdefault("backtest", {})["max_hold_minutes"] = int(args.max_hold_minutes)

    try:
        trades_df, equity_df, metrics, final_cfg = run_strategy_backtest(
            strategy_name=args.strategy,
            asset=args.asset,
            symbol=args.symbol,
            root=args.root,
            contract=args.contract,
            start=args.start,
            end=args.end,
            config_override=override if override else None,
            data_dir=args.data_dir,
        )
    except Exception as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 1

    print("final_config:", flush=True)
    print(yaml.safe_dump(final_cfg, sort_keys=False, default_flow_style=False), flush=True)
    print("metrics:", flush=True)
    print(json.dumps(metrics, indent=2), flush=True)
    h = max(0, int(args.head))
    if h and len(trades_df):
        print(f"first_{h}_trades:", flush=True)
        print(trades_df.head(h).to_string(), flush=True)

    if args.out_dir:
        out = Path(args.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        trades_df.to_csv(out / "trades.csv", index=False)
        equity_df.to_csv(out / "equity.csv", index=False)
        safe_m = {k: (None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v) for k, v in metrics.items()}
        (out / "metrics.json").write_text(json.dumps(safe_m, indent=2), encoding="utf-8")
        (out / "config_used.yaml").write_text(
            yaml.safe_dump(final_cfg, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
        print(f"Wrote: {out.resolve()}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
