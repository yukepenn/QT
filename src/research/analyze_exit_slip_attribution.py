"""
Research-only exit/slip attribution overlay (does not change simulator).

Combiner `simulator.py` applies a single `slippage_per_share` symmetrically:
- long entry: entry_raw + slip
- long exit: exit_raw - slip (adverse for targets and stops alike)

This script documents that and builds **adjusted R** scenarios as additive deltas vs published `r_multiple`,
using `risk_per_share` as the R denominator (same as simulator R scaling).
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.research.trade_quality_helpers import exit_reason_flags, profit_factor_r

BASE = 0.01
STRESS = 0.02


def marginal_r_from_slip_delta(risk: float, slip_delta_total: float) -> float:
    """ΔR ≈ -(slip_delta_total) / risk for long-only adverse aggregate on entry+exit (diagnostic)."""
    if risk is None or (isinstance(risk, float) and (math.isnan(risk) or risk <= 0)):
        return 0.0
    return float(-slip_delta_total / risk)


def compute_row_adjustments(risk: float, exit_reason: str) -> dict[str, float]:
    t, s, frc = exit_reason_flags(exit_reason)
    is_target = bool(t)
    is_stop = bool(s)
    is_forced = bool(frc)
    m = marginal_r_from_slip_delta
    out: dict[str, float] = {}
    # +0.01 slip on each leg vs baseline already in published → -0.02/risk
    out["symmetric_stress_extra_r"] = m(risk, 2.0 * (STRESS - BASE))
    # vs symmetric stress, target exit does not take extra exit slip → +0.01/risk
    out["target_limit_stress_vs_symmetric_r"] = m(risk, -(STRESS - BASE)) if is_target else 0.0
    # stop/eod: keep symmetric stress on exit (no change vs symmetric here)
    out["stop_only_exit_extra_r"] = m(risk, (STRESS - BASE)) if (is_stop or is_forced) else 0.0
    # toy: limit target at raw → remove baseline exit slip effect → +BASE/risk on target
    out["target_limit_baseline_recover_exit_r"] = m(risk, -BASE) if is_target else 0.0
    return out


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def _row_adj(row: pd.Series) -> pd.Series:
        rk = float(row["risk_per_share"]) if pd.notna(row["risk_per_share"]) else float("nan")
        return pd.Series(compute_row_adjustments(rk, str(row["exit_reason"])))

    adj = df.apply(_row_adj, axis=1)
    for c in adj.columns:
        df[c] = adj[c]
    rs = df["r_multiple"].astype(float)
    df["symmetric_stress_r"] = rs + df["symmetric_stress_extra_r"]
    df["target_limit_adjusted_stress_r"] = (
        rs + df["symmetric_stress_extra_r"] + df["target_limit_stress_vs_symmetric_r"]
    )
    df["target_limit_baseline_r"] = rs + df["target_limit_baseline_recover_exit_r"]
    df["stop_only_stress_r"] = rs + df["stop_only_exit_extra_r"]
    return df


def summarize_system(df: pd.DataFrame, label: str) -> pd.DataFrame:
    rows = []
    for scenario, col in [
        ("published", "r_multiple"),
        ("symmetric_stress", "symmetric_stress_r"),
        ("target_limit_stress", "target_limit_adjusted_stress_r"),
        ("target_limit_baseline_recover", "target_limit_baseline_r"),
        ("stop_only_stress", "stop_only_stress_r"),
    ]:
        v = df[col].astype(float)
        pf = profit_factor_r(v)
        rows.append(
            {
                "system": label,
                "scenario": scenario,
                "trades": len(v),
                "total_r": float(v.sum()),
                "avg_r": float(v.mean()),
                "pf_r": float(pf) if math.isfinite(pf) else None,
            }
        )
    return pd.DataFrame(rows)


def exit_reason_table(df: pd.DataFrame, label: str) -> pd.DataFrame:
    rows = []
    for ex, g in df.groupby(df["exit_reason"].astype(str)):
        rs = g["r_multiple"].astype(float)
        pf = profit_factor_r(rs)
        rows.append(
            {
                "system": label,
                "exit_reason": ex,
                "trades": len(g),
                "total_r": float(rs.sum()),
                "avg_r": float(rs.mean()),
                "pf_r": float(pf) if math.isfinite(pf) else None,
            }
        )
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--enriched-root", required=True)
    p.add_argument("--output-root", required=True)
    args = p.parse_args(argv)
    root = Path(args.enriched_root)
    if not root.is_absolute():
        root = Path.cwd() / root
    out = Path(args.output_root)
    if not out.is_absolute():
        out = Path.cwd() / out
    out.mkdir(parents=True, exist_ok=True)
    all_cmp = []
    doc = [
        "# Exit / slippage attribution (research overlay)",
        "",
        "## Simulator behavior (unchanged)",
        "",
        "- `src/combiner/simulator.py` uses one `slippage_per_share` for **both** entry and exit fills (`_py_exit_price`).",
        "- Published `r_multiple` already reflects that constant.",
        "",
        "## Overlay scenarios (additive deltas vs published)",
        "",
        "- `symmetric_stress_extra_r`: marginal **+0.01 slip/share on entry and exit** vs baseline 0.01 → **-0.02/risk** R.",
        "- `target_limit_adjusted_stress_r`: symmetric stress, but **target** exits do not take the extra exit-leg slip vs STRESS.",
        "- `target_limit_baseline_r`: toy recovery of **baseline exit slip** on targets only (limit-at-raw).",
        "- `stop_only_stress_r`: baseline published R plus **one-leg** extra stress on stop/forced exits only.",
        "",
    ]
    (out / "exit_slip_attribution_summary.md").write_text("\n".join(doc), encoding="utf-8")
    for ep in sorted(root.glob("*_enriched.csv")):
        df = pd.read_csv(ep).copy()
        label = ep.stem.replace("_enriched", "")
        df2 = aggregate(df)
        summarize_system(df2, label).to_csv(out / f"{label}_target_limit_adjusted_summary.csv", index=False)
        exit_reason_table(df2, label).to_csv(out / f"{label}_exit_reason_cost_table.csv", index=False)
        all_cmp.append(summarize_system(df2, label))
    if all_cmp:
        pd.concat(all_cmp, ignore_index=True).to_csv(out / "exit_slip_scenario_comparison.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
