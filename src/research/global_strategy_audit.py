"""
Global Layer 1 preflight: inspect every loader-registered strategy for YAML,
fast-path, lookahead, validation, and side axes. Writes CSV/MD under
src/research/results/global_strategy_audit_v1/.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Any

import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.backtest.sweep import validate_testing_grid_for_strategy
from src.strategies.loader import (
    apply_overrides,
    available_strategies,
    expand_grid,
    grid_size,
    load_strategy,
    load_strategy_config,
    strategy_root,
)
from src.strategies.metadata import get_strategy_metadata


def _tuned_candidates(tp: Path, strategy: str) -> list[tuple[int, Path]]:
    out: list[tuple[int, Path]] = []
    if not tp.is_dir():
        return out
    pat = re.compile(rf"^{re.escape(strategy)}_tuned_v(\d+)\.yaml$")
    for p in tp.iterdir():
        if not p.is_file():
            continue
        m = pat.match(p.name)
        if m:
            out.append((int(m.group(1)), p))
    out.sort(key=lambda x: -x[0])
    return out


def pick_recommended_testing_yaml(strategy: str) -> tuple[Path | None, str]:
    """Return (path, reason_tag). Prefer highest *_tuned_vN.yaml, else *_focused.yaml, else <strategy>.yaml."""
    base = strategy_root() / "testing_parameters"
    tuned = _tuned_candidates(base, strategy)
    if tuned:
        return tuned[0][1], f"tuned_v{tuned[0][0]}"
    focused = base / f"{strategy}_focused.yaml"
    if focused.is_file():
        return focused, "focused"
    plain = base / f"{strategy}.yaml"
    if plain.is_file():
        return plain, "default_grid"
    return None, "missing"


def _has_lookahead(required: list[Any]) -> bool:
    for f in required:
        if "LOOKAHEAD" in str(f).upper():
            return True
    return False


def collect_signal_side_values(strategy: str, testing: dict[str, Any]) -> set[str]:
    base = load_strategy_config(strategy)
    fixed = testing.get("fixed") or {}
    sides: set[str] = set()
    for combo in expand_grid(testing):
        cfg = apply_overrides(base, combo)
        cfg = apply_overrides(cfg, fixed)
        sig = cfg.get("signal") or {}
        if isinstance(sig, dict) and "side" in sig:
            sides.add(str(sig["side"]).strip())
    cfg0 = apply_overrides(base, fixed)
    sig0 = cfg0.get("signal") or {}
    if isinstance(sig0, dict) and "side" in sig0:
        sides.add(str(sig0["side"]).strip())
    return sides


def infer_side_flags(sides: set[str]) -> tuple[bool, bool, bool, str]:
    """supports_long, supports_short, supports_both_capable, short_support_label."""
    if not sides:
        return True, False, False, "unknown_default_grid"
    norm = {s.lower().replace(" ", "_") for s in sides}
    long_ok = any(x in norm for x in ("long_only", "long", "both"))
    short_ok = any(x in norm for x in ("short_only", "short", "both"))
    both_only = norm == {"both"} or "both" in norm
    lbl_parts = []
    if long_ok:
        lbl_parts.append("long")
    if short_ok:
        lbl_parts.append("short")
    if both_only and len(norm) == 1:
        return True, True, True, "both"
    if long_ok and short_ok:
        return True, True, True, "long+short"
    if long_ok and not short_ok:
        return True, False, False, "long_only"
    if short_ok and not long_ok:
        return False, True, False, "short_only"
    return True, False, False, "|".join(sorted(sides))


def classify_status(
    *,
    loader_ok: bool,
    default_val_ok: bool,
    yaml_path: Path | None,
    testing_val_ok: bool,
    supports_fast: bool,
    lookahead: bool,
    raw_grid: int,
    max_grid: int,
    short_label: str,
) -> str:
    if not loader_ok:
        return "DEFER_IMPLEMENTATION_RISK"
    if lookahead:
        return "DEFER_IMPLEMENTATION_RISK"
    if yaml_path is None:
        return "DEFER_IMPLEMENTATION_RISK"
    if not default_val_ok:
        return "DEFER_IMPLEMENTATION_RISK"
    if not testing_val_ok:
        return "DEFER_IMPLEMENTATION_RISK"
    if not supports_fast:
        return "DEFER_IMPLEMENTATION_RISK"
    if raw_grid > max_grid:
        return "REVIEW_GRID_TOO_LARGE"
    if short_label == "unknown_default_grid":
        return "READY_LONG_ONLY"
    if "short" in short_label and "long" in short_label:
        return "READY_SHORT_OR_BOTH"
    if short_label in ("short_only",):
        return "READY_SHORT_OR_BOTH"
    return "READY_GLOBAL_L1"


def reason_for_row(status: str, notes: list[str]) -> str:
    parts = [status] + [n for n in notes if n]
    return "; ".join(parts)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--output-root",
        type=Path,
        default=_ROOT / "src/research/results/global_strategy_audit_v1",
    )
    ap.add_argument("--max-grid-size", type=int, default=1500)
    args = ap.parse_args(argv)

    out = args.output_root
    if not out.is_absolute():
        out = Path.cwd() / out
    out.mkdir(parents=True, exist_ok=True)

    tp = strategy_root() / "testing_parameters"
    pm = strategy_root() / "parameters"

    elig_rows: list[dict[str, Any]] = []
    side_rows: list[dict[str, Any]] = []

    for strategy in available_strategies():
        meta = get_strategy_metadata(strategy)
        family = str(meta.get("family", "unknown"))
        default_yaml = pm / f"{strategy}.yaml"
        has_default = default_yaml.is_file()
        has_focused = (tp / f"{strategy}_focused.yaml").is_file()
        has_tuned = bool(_tuned_candidates(tp, strategy))
        rec_path, rec_tag = pick_recommended_testing_yaml(strategy)
        notes: list[str] = []
        loader_ok = True
        strat = None
        supports_fast = False
        n_feat = 0
        lookahead = False
        default_val_ok = False
        testing_val_ok = False
        raw_grid = 0
        testing_doc: dict[str, Any] | None = None

        try:
            strat = load_strategy(strategy)
            supports_fast = bool(getattr(strat, "supports_fast", False))
            req = strat.required_features()
            n_feat = len(req) if isinstance(req, (list, tuple)) else 0
            lookahead = _has_lookahead(list(req) if isinstance(req, (list, tuple)) else [])
        except Exception as e:
            loader_ok = False
            notes.append(f"loader:{e}")

        if strat is not None and has_default:
            try:
                strat.validate_config(load_strategy_config(strategy))
                default_val_ok = True
            except Exception as e:
                default_val_ok = False
                notes.append(f"default_validate:{e}")
        elif strat is not None:
            notes.append("missing_default_parameters_yaml")
            default_val_ok = False

        if rec_path is not None and strat is not None:
            try:
                with rec_path.open(encoding="utf-8") as f:
                    testing_doc = yaml.safe_load(f)
                if not isinstance(testing_doc, dict) or testing_doc.get("strategy") != strategy:
                    raise ValueError("strategy field mismatch in testing YAML")
                validate_testing_grid_for_strategy(strategy, testing_doc)
                testing_val_ok = True
                raw_grid = grid_size(testing_doc)
            except Exception as e:
                testing_val_ok = False
                notes.append(f"testing_validate:{e}")
        elif rec_path is None:
            testing_val_ok = False

        sides: set[str] = set()
        if testing_doc is not None and testing_val_ok:
            try:
                sides = collect_signal_side_values(strategy, testing_doc)
            except Exception as e:
                notes.append(f"side_collect:{e}")
        sup_l, sup_s, sup_b, short_lbl = infer_side_flags(sides)

        status = classify_status(
            loader_ok=loader_ok,
            default_val_ok=default_val_ok,
            yaml_path=rec_path,
            testing_val_ok=testing_val_ok,
            supports_fast=supports_fast,
            lookahead=lookahead,
            raw_grid=raw_grid,
            max_grid=args.max_grid_size,
            short_label=short_lbl,
        )

        elig_rows.append(
            {
                "strategy": strategy,
                "family": family,
                "has_default_parameters_yaml": "yes" if has_default else "no",
                "has_focused_yaml": "yes" if has_focused else "no",
                "has_tuned_yaml": "yes" if has_tuned else "no",
                "recommended_testing_yaml": str(rec_path) if rec_path else "",
                "recommended_yaml_tag": rec_tag,
                "supports_fast": "yes" if supports_fast else "no",
                "required_features_count": str(n_feat),
                "required_lookahead": "yes" if lookahead else "no",
                "default_config_validates": "yes" if default_val_ok else "no",
                "testing_yaml_validates": "yes" if testing_val_ok else "no",
                "raw_grid_size": str(raw_grid),
                "supports_long": "yes" if sup_l else "no",
                "supports_short": "yes" if sup_s else "no",
                "supports_both_inferred": "yes" if sup_b else "no",
                "short_support_label": short_lbl,
                "current_status": status,
                "reason": reason_for_row(status, notes),
            }
        )

        side_rows.append(
            {
                "strategy": strategy,
                "family": family,
                "signal_side_values_observed": "|".join(sorted(sides)) if sides else "",
                "supports_long": "yes" if sup_l else "no",
                "supports_short": "yes" if sup_s else "no",
                "supports_both_inferred": "yes" if sup_b else "no",
                "short_support": short_lbl,
                "notes": "; ".join(notes) if notes else "",
            }
        )

    def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        keys = list(rows[0].keys())
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)

    def _md_table(path: Path, rows: list[dict[str, Any]], title: str) -> None:
        if not rows:
            path.write_text(f"# {title}\n\n(no rows)\n", encoding="utf-8")
            return
        keys = list(rows[0].keys())
        lines = [f"# {title}", "", "| " + " | ".join(keys) + " |", "| " + " | ".join(["---"] * len(keys)) + " |"]
        for r in rows:
            lines.append("| " + " | ".join(str(r.get(k, "")).replace("|", "\\|") for k in keys) + " |")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    _write_csv(out / "strategy_eligibility_matrix.csv", elig_rows)
    _md_table(out / "strategy_eligibility_matrix.md", elig_rows, "Strategy eligibility (global Layer 1)")
    _write_csv(out / "strategy_side_support_matrix.csv", side_rows)
    _md_table(out / "strategy_side_support_matrix.md", side_rows, "Strategy side support matrix")

    n_ready = sum(1 for r in elig_rows if r["current_status"] == "READY_GLOBAL_L1")
    n_long = sum(1 for r in elig_rows if r["current_status"] == "READY_LONG_ONLY")
    n_short = sum(1 for r in elig_rows if r["current_status"] == "READY_SHORT_OR_BOTH")
    n_review = sum(1 for r in elig_rows if r["current_status"] == "REVIEW_GRID_TOO_LARGE")
    n_defer = sum(1 for r in elig_rows if r["current_status"] == "DEFER_IMPLEMENTATION_RISK")

    summary = "\n".join(
        [
            "# Global strategy audit summary (v1)",
            "",
            f"- Strategies audited: **{len(elig_rows)}**",
            f"- `READY_GLOBAL_L1`: **{n_ready}**",
            f"- `READY_LONG_ONLY`: **{n_long}**",
            f"- `READY_SHORT_OR_BOTH`: **{n_short}**",
            f"- `REVIEW_GRID_TOO_LARGE` (raw grid > {args.max_grid_size}): **{n_review}**",
            f"- `DEFER_IMPLEMENTATION_RISK`: **{n_defer}**",
            "",
            "Artifacts:",
            "",
            "- `strategy_eligibility_matrix.csv` / `.md`",
            "- `strategy_side_support_matrix.csv` / `.md`",
            "",
            "Policy: no short axes are invented; unknown side grids default to **READY_LONG_ONLY**.",
            "",
            "Next: run `python src/research/run_global_layer1.py` with `--audit` pointing at the CSV.",
        ]
    )
    (out / "global_strategy_audit_summary.md").write_text(summary + "\n", encoding="utf-8")
    print(f"Wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
