"""Sweep artifact I/O (CSV, JSON manifest, markdown summary)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.sweep_types import ENGINE_LABEL


def git_sha() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, timeout=5)
            .decode()
            .strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return ""


def write_real_sweep_artifacts(df: pd.DataFrame, out_dir: Path, manifest: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "sweep_results.csv", index=False)
    (out_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    lines = [
        "# Sweep summary",
        "",
        f"- engine: `{manifest.get('engine', '')}`",
        f"- execution_semantics_version: `{manifest.get('execution_semantics_version', '')}`",
        f"- strategy: `{manifest.get('strategy', '')}`",
        f"- symbol: `{manifest.get('symbols', '')}`",
        f"- window: `{manifest.get('start', '')}` … `{manifest.get('end', '')}`",
        f"- combos: {len(df)}",
        "",
        "Per-combo metrics are in `sweep_results.csv`.",
    ]
    (out_dir / "sweep_summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_smoke_artifacts(df: pd.DataFrame, out_dir: Path, *, execution_semantics_version: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "sweep_smoke.csv", index=False)
    meta = {
        "engine": ENGINE_LABEL,
        "result_lineage": "mainline",
        "execution_semantics_version": execution_semantics_version,
    }
    (out_dir / "sweep_meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")


def default_run_manifest(
    *,
    pol_semantics: str,
    args: Any,
    no_save: bool,
    dry_run: bool,
) -> dict[str, Any]:
    return {
        "git_sha": "",
        "command": " ".join(sys.argv),
        "timestamp": "",  # filled by caller if needed
        "engine": ENGINE_LABEL,
        "execution_semantics_version": str(pol_semantics),
        "symbols": getattr(args, "symbol", ""),
        "strategy": getattr(args, "strategy", ""),
        "start": getattr(args, "start", ""),
        "end": getattr(args, "end", ""),
        "config_path": getattr(args, "config", "") or "",
        "grid_path": getattr(args, "grid", "") or "",
        "no_save": bool(no_save),
        "dry_run": bool(dry_run),
        "result_lineage": "mainline",
        "asset": getattr(args, "asset", "equity"),
        "data_root": getattr(args, "data_root", "") or "",
    }
