"""Optional tiny combiner smoke (execution-backed engine). Requires user paths."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Thin wrapper: forward to src.combiner.run with execution_backed + dry-run.")
    p.add_argument("--candidate-root", type=Path, required=True)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--symbol", default="QQQ")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--candidate-set", default=None)
    p.add_argument("--candidate-ids", nargs="*", default=None)
    p.add_argument("--data-dir", default="data/raw/ibkr")
    args, rest = p.parse_known_args(argv)

    from src.combiner.run import main as run_main

    fwd = [
        "--candidate-root",
        str(args.candidate_root),
        "--config",
        str(args.config),
        "--symbol",
        args.symbol,
        "--start",
        args.start,
        "--end",
        args.end,
        "--data-dir",
        args.data_dir,
        "--engine",
        "execution_backed",
        "--dry-run",
        "--no-save",
    ]
    if args.candidate_set:
        fwd += ["--candidate-set", args.candidate_set]
    if args.candidate_ids:
        fwd += ["--candidate-ids", *args.candidate_ids]
    fwd += rest
    return int(run_main(fwd))


if __name__ == "__main__":
    raise SystemExit(main())
