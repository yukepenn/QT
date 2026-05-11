"""Integration: precompute with on-disk signal cache matches cache-off matrices."""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pytest

from src.combiner.candidate import load_candidates
from src.combiner.precompute import precompute_candidate_signal_matrices


ROOT = Path(__file__).resolve().parents[1]
_CAND_ROOT = ROOT / "src/research/results/layer1_all10_qqq_2025_20260430_posthardening_v1/selected_candidates"


@pytest.mark.skipif(not _CAND_ROOT.is_dir(), reason="candidate library not present")
def test_precompute_signal_cache_cold_warm_match_off(tmp_path: Path) -> None:
    raw = load_candidates(_CAND_ROOT)
    sel = [c for c in raw if c.candidate_id == "FAILED_ORB_001"]
    if len(sel) != 1:
        pytest.skip("FAILED_ORB_001 not in candidate library")

    cache_dir = tmp_path / "sigcache"

    off = precompute_candidate_signal_matrices(
        candidates=sel,
        asset="equity",
        symbol="QQQ",
        start="2025-01-01",
        end="2025-01-31",
        data_dir="data/raw/ibkr",
        use_signal_cache=False,
    )
    cold = precompute_candidate_signal_matrices(
        candidates=sel,
        asset="equity",
        symbol="QQQ",
        start="2025-01-01",
        end="2025-01-31",
        data_dir="data/raw/ibkr",
        use_signal_cache=True,
        signal_cache_root=cache_dir,
        refresh_signal_cache=True,
    )
    warm = precompute_candidate_signal_matrices(
        candidates=sel,
        asset="equity",
        symbol="QQQ",
        start="2025-01-01",
        end="2025-01-31",
        data_dir="data/raw/ibkr",
        use_signal_cache=True,
        signal_cache_root=cache_dir,
        refresh_signal_cache=False,
    )

    for name, a, b, c in [
        ("side", off.side, cold.side, warm.side),
        ("valid", off.valid, cold.valid, warm.valid),
        ("stop", off.stop, cold.stop, warm.stop),
        ("target_preview", off.target_preview, cold.target_preview, warm.target_preview),
        ("target_mode_code", off.target_mode_code, cold.target_mode_code, warm.target_mode_code),
        ("target_r", off.target_r, cold.target_r, warm.target_r),
        ("risk_preview", off.risk_preview, cold.risk_preview, warm.risk_preview),
    ]:
        np.testing.assert_array_equal(a, b, err_msg=name)
        np.testing.assert_array_equal(b, c, err_msg=name)

    shutil.rmtree(cache_dir, ignore_errors=True)
