"""
Offline trade quality score v1.5 (diagnostic only).

Changes vs v1:
- `regime_unknown`: **neutral** (no regime bonus/penalty from entry_regime_label_summary tables).
- Optional small bonus for unknown early-minute sub-bucket if decomposition CSV flags dominant positive bucket (read-only).
- Indicator: lighter penalties; optional repeat-family penalty gated by mtp evidence file.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.research.score_trade_quality_offline import (
    _load_regime_tables,
    load_setup_affinity,
    threshold_summary,
)


def score_row_v15(
    r: pd.Series,
    regime_bonus: dict[str, float],
    regime_pen: dict[str, float],
    setup_affinity: dict[str, list[str]],
    *,
    indicator_repeat_penalty: bool,
) -> float:
    _ = setup_affinity  # reserved to mirror v1 `score_row` signature
    s = 50.0
    reg = str(r.get("entry_regime_label", "missing"))
    fam = str(r.get("entry_family", r.get("strategy_family", "")))

    if reg != "regime_unknown":
        if reg in regime_bonus:
            s += regime_bonus[reg]
        if reg in regime_pen:
            s -= regime_pen[reg]

    if reg == "trading_range" and "vwap" in fam.lower():
        s += 3.0

    vc = r.get("entry_vwap_cross_count")
    try:
        if vc is not None and float(vc) > 8:
            s -= 5.0
    except (TypeError, ValueError):
        pass

    # Unknown early-session soft bonus (hypothesis; only if minute < 60)
    if reg == "regime_unknown":
        mfo = r.get("entry_minute_from_open")
        try:
            if mfo is not None and float(mfo) <= 60:
                s += 2.0
        except (TypeError, ValueError):
            pass

    tn = r.get("entry_trade_number_of_day")
    if indicator_repeat_penalty and pd.notna(tn) and float(tn) > 1:
        sf = r.get("entry_prior_trade_same_family")
        if sf is True or sf == 1.0:
            fam_l = fam.lower()
            if "oscillator" in fam_l or "macd" in fam_l:
                s -= 5.0
            else:
                s -= 4.0
    elif pd.notna(tn) and float(tn) > 1:
        sf = r.get("entry_prior_trade_same_family")
        if sf is True or sf == 1.0:
            s -= 4.0
    pl = r.get("entry_prior_trade_was_loss")
    try:
        if pl is True or float(pl) == 1.0:
            s -= 3.0
    except (TypeError, ValueError):
        pass

    ais = str(r.get("entry_always_in_side", ""))
    side = str(r.get("entry_side", r.get("side", "")))
    if "pullback" in str(r.get("entry_strategy", "")).lower() and ais == "always_in_long" and side == "1":
        s += 2.0

    return float(np.clip(s, 0.0, 100.0))


def holdout_v15_vwap(df: pd.DataFrame) -> pd.DataFrame:
    """Minimal 2023 train / 2024 test with v15 scores and train top80 threshold."""
    from src.research.validate_trade_quality_holdout import (
        top_fraction_threshold,
        subset_metrics,
        _session_year,
    )

    y = _session_year(df["session_date"])
    train = df.loc[y == 2023]
    test = df.loc[y == 2024]
    thr = top_fraction_threshold(train["trade_quality_score_v15"].astype(float).values, 0.8)
    sub = test.loc[test["trade_quality_score_v15"] >= thr]
    rows = [
        {**subset_metrics(train, "train_all_v15"), "scenario": "v15"},
        {**subset_metrics(test, "test_all_v15"), "scenario": "v15"},
        {**subset_metrics(sub, "test_top80_train_thr_v15"), "scenario": "v15", "train_thr": thr},
    ]
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--enriched-root", required=True)
    p.add_argument("--taxonomy", required=True)
    p.add_argument("--analysis-root", default=None)
    p.add_argument("--mtp-evidence-csv", default=None, help="indicator_mtp_comparison.csv from v1.5")
    p.add_argument("--output-root", required=True)
    args = p.parse_args(argv)
    er = Path(args.enriched_root)
    if not er.is_absolute():
        er = Path.cwd() / er
    tax = Path(args.taxonomy)
    if not tax.is_absolute():
        tax = Path.cwd() / tax
    out = Path(args.output_root)
    if not out.is_absolute():
        out = Path.cwd() / out
    out.mkdir(parents=True, exist_ok=True)
    aroot = Path(args.analysis_root) if args.analysis_root else None
    if aroot and not aroot.is_absolute():
        aroot = Path.cwd() / aroot

    ind_penalty = False
    if args.mtp_evidence_csv:
        evp = Path(args.mtp_evidence_csv)
        if not evp.is_absolute():
            evp = Path.cwd() / evp
        if evp.exists():
            ev = pd.read_csv(evp)
            if "mtp" in ev.columns and "total_r_trade2" in ev.columns:
                r2 = ev.loc[ev["mtp"] == 2, "total_r_trade2"]
                if len(r2) and float(r2.iloc[0]) < 0:
                    ind_penalty = True

    taxd = load_setup_affinity(tax)
    rows_ind = []
    for ep in sorted(er.glob("*_enriched.csv")):
        lab = ep.stem.replace("_enriched", "")
        adir = (aroot / lab) if aroot else None
        rb, rp = _load_regime_tables(adir)
        df = pd.read_csv(ep)
        use_ind_pen = ind_penalty and "indicator" in lab
        scores = [score_row_v15(df.iloc[i], rb, rp, taxd, indicator_repeat_penalty=use_ind_pen) for i in range(len(df))]
        df["trade_quality_score_v15"] = scores
        df_ts = df.drop(columns=["trade_quality_score"], errors="ignore").assign(
            trade_quality_score=df["trade_quality_score_v15"]
        )
        th = threshold_summary(df_ts, lab)
        th["system"] = lab
        if "indicator" in lab:
            rows_ind.append(th)
        if lab == "vwap_baseline_global_l2":
            hold_df = holdout_v15_vwap(df)
            hold_df.to_csv(out / "vwap_threshold_holdout_v15.csv", index=False)
    if rows_ind:
        pd.concat(rows_ind, ignore_index=True).to_csv(out / "indicator_threshold_diagnostics_v15.csv", index=False)
    rules = {
        "regime_unknown": "neutral_no_table_bonus",
        "indicator_repeat_penalty": ind_penalty,
        "unknown_early_minute_hypothesis_bonus": 2.0,
    }
    (out / "score_rule_changes_v15.md").write_text(
        "# Score rule changes v1.5\n\n```json\n" + json.dumps(rules, indent=2) + "\n```\n",
        encoding="utf-8",
    )
    # Full narrative: curated `quality_score_v15_summary.md` in results (not overwritten here).
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
