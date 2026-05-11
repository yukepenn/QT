from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path("src/research/results/robust_l2_core_v2_design")


def _read_csv(name: str) -> pd.DataFrame:
    p = ROOT / name
    assert p.is_file(), f"missing {p}"
    return pd.read_csv(p)


def test_design_csvs_parse_and_have_no_absolute_paths() -> None:
    csvs = sorted(ROOT.rglob("*.csv"))
    assert csvs, "expected design CSVs to exist"
    for p in csvs:
        df = pd.read_csv(p)
        s = df.astype(str).to_string()
        assert "D:/" not in s
        assert "C:/" not in s
        assert "OneDrive" not in s


def test_primary_and_balanced_sets_match_spec() -> None:
    df = _read_csv("candidate_sets_design.csv")

    def members(set_name: str) -> list[str]:
        return sorted(df.loc[df["candidate_set"] == set_name, "candidate_id"].astype(str).tolist())

    assert members("primary_representative_core") == sorted(
        ["GAP_ACCEPTANCE_FAILURE_001", "PA_BUY_SELL_CLOSE_TREND_003", "CCI_EXTREME_SNAPBACK_003"]
    )

    assert members("balanced_representative_core") == sorted(
        [
            "GAP_ACCEPTANCE_FAILURE_001",
            "PA_BUY_SELL_CLOSE_TREND_003",
            "PA_BUY_SELL_CLOSE_TREND_004",
            "CCI_EXTREME_SNAPBACK_003",
            "CCI_EXTREME_SNAPBACK_002",
        ]
    )


def test_deduped_equivalents_not_in_primary_or_balanced() -> None:
    rep = _read_csv("representative_candidate_manifest.csv")
    in_primary = set(rep.loc[rep["include_in_primary_core"] == "yes", "candidate_id"].astype(str).tolist())
    in_balanced = set(rep.loc[rep["include_in_balanced_core"] == "yes", "candidate_id"].astype(str).tolist())

    # GAP cluster
    for cid in ["GAP_ACCEPTANCE_FAILURE_002", "GAP_ACCEPTANCE_FAILURE_003", "GAP_ACCEPTANCE_FAILURE_004"]:
        assert cid not in in_primary
        assert cid not in in_balanced

    # PA trade-identical cluster
    for cid in ["PA_BUY_SELL_CLOSE_TREND_001", "PA_BUY_SELL_CLOSE_TREND_002"]:
        assert cid not in in_primary
        assert cid not in in_balanced


def test_config_skeletons_marked_design_only() -> None:
    skel_dir = ROOT / "config_skeletons"
    assert skel_dir.is_dir()
    yamls = sorted(skel_dir.glob("*.yaml"))
    assert yamls, "expected config skeleton YAMLs"
    for p in yamls:
        head = p.read_text(encoding="utf-8").splitlines()[:5]
        joined = "\n".join(head)
        assert "DESIGN ONLY" in joined
        assert "NOT RUN" in joined

