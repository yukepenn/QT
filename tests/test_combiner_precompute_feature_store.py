"""Integration: Layer 2 precompute writes FeatureStore stats + still runs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.combiner.candidate import load_candidates
from src.combiner.precompute import precompute_candidate_signal_matrices


ROOT = Path(__file__).resolve().parents[1]
_CAND_ROOT = ROOT / "src/research/results/layer1_all10_qqq_2025_20260430_posthardening_v1/selected_candidates"


@pytest.mark.skipif(not _CAND_ROOT.is_dir(), reason="candidate library not present")
def test_precompute_writes_feature_store_stats(tmp_path: Path) -> None:
    raw = load_candidates(_CAND_ROOT)
    sel = [c for c in raw if c.candidate_id == "FAILED_ORB_001"]
    if len(sel) != 1:
        pytest.skip("FAILED_ORB_001 not in candidate library")

    out = tmp_path / "diag"
    out.mkdir(parents=True, exist_ok=True)
    profile = out / "candidate_precompute_profile.csv"
    _ = precompute_candidate_signal_matrices(
        candidates=sel,
        asset="equity",
        symbol="QQQ",
        start="2025-01-01",
        end="2025-01-31",
        data_dir="data/raw/ibkr",
        profile_csv_path=profile,
        use_signal_cache=False,
    )
    stats_path = out / "feature_store_stats.json"
    assert stats_path.is_file()
    d = json.loads(stats_path.read_text(encoding="utf-8"))
    assert int(d["feature_requests"]) >= 1
    assert int(d["raw_rows"]) > 0

