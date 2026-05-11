"""Tests for candidate_signal_diversity helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.research.candidate_signal_diversity import pure_signal_hash_entries


def test_pure_signal_hash_identical_entries_match() -> None:
    a = [("2023-01-03T14:30:00+00:00", 1), ("2023-01-04T15:00:00+00:00", 1)]
    b = list(a)
    assert pure_signal_hash_entries(a) == pure_signal_hash_entries(b)


def test_pure_signal_hash_changes_when_timestamp_changes() -> None:
    a = [("2023-01-03T14:30:00+00:00", 1)]
    b = [("2023-01-03T14:31:00+00:00", 1)]
    assert pure_signal_hash_entries(a) != pure_signal_hash_entries(b)


def test_candidate_signal_diversity_csv_columns_written(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    cand_root = repo / "src/research/results/layer1_pa_batch_bc_tuned_qqq_2023_2024_v2"
    if not (cand_root / "selected_candidates").is_dir():
        pytest.skip("v2 candidate root not present in workspace")
    out = tmp_path / "div"
    import subprocess
    import sys

    cmd = [
        sys.executable,
        str(repo / "src/research/candidate_signal_diversity.py"),
        "--candidate-root",
        str(cand_root),
        "--asset",
        "equity",
        "--symbol",
        "QQQ",
        "--start",
        "2023-01-03",
        "--end",
        "2023-01-31",
        "--output-root",
        str(out),
    ]
    r = subprocess.run(cmd, cwd=str(repo), capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    csvp = out / "candidate_signal_diversity.csv"
    assert csvp.is_file()
    header = csvp.read_text(encoding="utf-8").splitlines()[0]
    for col in (
        "candidate_id",
        "pure_signal_hash",
        "n_signals",
        "strategy",
        "status",
    ):
        assert col in header
