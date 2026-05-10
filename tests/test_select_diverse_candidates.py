"""Tests for select_diverse_candidates CLI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


def test_select_diverse_runs_on_v2_bundle(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    root = repo / "src/research/results/layer1_pa_batch_bc_tuned_qqq_2023_2024_v2"
    div = tmp_path / "div" / "candidate_signal_diversity.csv"
    if not (root / "selected_candidates.csv").is_file():
        pytest.skip("v2 selected_candidates.csv not present")
    div.parent.mkdir(parents=True, exist_ok=True)
    # minimal diversity rows: must merge on candidate_id+strategy
    import pandas as pd

    ydir = root / "selected_candidates"
    yamls = sorted(ydir.glob("*.yaml"))[:3]
    if len(yamls) < 2:
        pytest.skip("not enough yaml fixtures")
    rows = []
    import yaml

    for yp in yamls:
        doc = yaml.safe_load(yp.read_text(encoding="utf-8"))
        rows.append(
            {
                "candidate_id": doc.get("candidate_id"),
                "strategy": doc.get("strategy"),
                "pure_signal_hash": f"fake_{doc.get('candidate_id')}",
            }
        )
    pd.DataFrame(rows).to_csv(div, index=False)

    out_root = tmp_path / "diverse"
    cmd = [
        sys.executable,
        str(repo / "src/research/select_diverse_candidates.py"),
        "--candidate-root",
        str(root),
        "--diversity-csv",
        str(div),
        "--output-root",
        str(out_root),
        "--top-per-strategy",
        "2",
        "--min-unique-signal-hashes",
        "1",
    ]
    r = subprocess.run(cmd, cwd=str(repo), capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert (out_root / "selected_candidates.csv").is_file()
    assert (out_root / "diversity_selection_summary.md").is_file()


def test_select_diverse_missing_csv_errors(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    cmd = [
        sys.executable,
        str(repo / "src/research/select_diverse_candidates.py"),
        "--candidate-root",
        str(tmp_path / "nope"),
        "--diversity-csv",
        str(tmp_path / "nope.csv"),
        "--output-root",
        str(tmp_path / "out"),
    ]
    r = subprocess.run(cmd, cwd=str(repo), capture_output=True, text=True)
    assert r.returncode != 0
