"""
Non-executable sign proxy for fixed-profile total R (research-only).

The combiner has no supported side-inversion replay flag. Negating aggregate `total_r`
is NOT an executable short/contrarian backtest (asymmetric stops/targets, path dependence).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Sign-flip proxy on fixed-profile metrics (non-executable).")
    p.add_argument(
        "--metrics-csv",
        default="src/research/results/fixed_profile_oow_v1/oow/fixed_profile_oow_metrics.csv",
    )
    p.add_argument("--output-dir", default="src/research/results/layer2_candidate_robustness_v1/side_flip")
    p.add_argument(
        "--profiles",
        default="indicator_mtp1,indicator_mtp2,indicator_mtp3",
        help="Comma-separated profile_id values from metrics CSV",
    )
    args = p.parse_args(argv)
    cwd = Path.cwd()
    import pandas as pd

    mpath = Path(args.metrics_csv)
    if not mpath.is_absolute():
        mpath = cwd / mpath
    outd = Path(args.output_dir)
    if not outd.is_absolute():
        outd = cwd / outd
    outd.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(mpath)
    want = {x.strip() for x in args.profiles.split(",") if x.strip()}
    sub = df[df["profile_id"].astype(str).isin(want)].copy()
    sub["side_flip_proxy_total_r"] = -sub["total_r"].astype(float)
    sub["diagnostic_kind"] = "non_executable_sign_proxy"
    sub.to_csv(outd / "side_flip_metrics.csv", index=False)
    note = (
        "# Side-flip diagnostic (non-executable)\n\n"
        "`side_flip_proxy_total_r` is **−total_r** from the fixed-profile combiner replay CSV. "
        "It is **not** a replay of inverted stops/targets or mirrored limit logic. "
        "Do not treat as production short evidence.\n"
    )
    (outd / "side_flip_interpretation.md").write_text(note, encoding="utf-8")
    lines = ["| profile_id | window_id | total_r | side_flip_proxy_total_r |", "|---|---|---|---|"]
    for _, r in sub.iterrows():
        lines.append(
            f"| {r['profile_id']} | {r['window_id']} | {r['total_r']} | {r['side_flip_proxy_total_r']} |"
        )
    (outd / "side_flip_summary.md").write_text(note + "\n## Rows\n\n" + "\n".join(lines), encoding="utf-8")
    print(f"[side_flip] wrote {outd / 'side_flip_metrics.csv'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
