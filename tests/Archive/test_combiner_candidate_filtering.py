"""Tests for generic Layer 2 sweep candidate-universe resolution (no strategy names required)."""

from __future__ import annotations

from src.combiner.candidate import Candidate, resolve_candidate_universe_for_grid, select_candidate_set


def _c(
    cid: str,
    strategy: str,
    *,
    rank: int = 1,
    warning: str = "",
) -> Candidate:
    return Candidate(
        candidate_id=cid,
        strategy=strategy,
        asset="equity",
        symbol="QQQ",
        candidate_rank=rank,
        source_sweep_path="",
        source_results_csv="",
        params_hash="deadbeef",
        config={},
        metrics={},
        metadata={},
        selection={"warning": warning} if warning else {},
        family="test_family",
        conflict_group="test",
        default_priority=50,
        default_active_start_minute=0,
        default_active_end_minute=389,
        warning=warning,
    )


def test_select_warnings_excluded_when_include_warnings_false():
    raw = [_c("c_strict", "s_a", rank=1), _c("c_warn", "s_a", rank=2, warning="relaxed_filter")]
    prof = {"strategies": ["s_a"], "include_warnings": False, "max_per_strategy": 5}
    sel = select_candidate_set(raw, prof, top_per_strategy=5)
    assert [x.candidate_id for x in sel] == ["c_strict"]


def test_select_warnings_included_when_include_warnings_true():
    raw = [_c("c_strict", "s_a", rank=1), _c("c_warn", "s_a", rank=2, warning="relaxed_filter")]
    prof = {"strategies": ["s_a"], "include_warnings": True, "max_per_strategy": 5}
    sel = select_candidate_set(raw, prof, top_per_strategy=5)
    assert {x.candidate_id for x in sel} == {"c_strict", "c_warn"}


def test_resolve_union_across_grid_rows_and_top_per_strategy_caps():
    raw = [
        _c("a1", "s_a", rank=1),
        _c("a2", "s_a", rank=2),
        _c("a3", "s_a", rank=3),
        _c("b1", "s_b", rank=1),
        _c("b2", "s_b", rank=2),
    ]
    base_cfg = {
        "candidate_sets": {
            "only_a": {"strategies": ["s_a"], "include_warnings": True, "max_per_strategy": 5},
            "both_one_each": {
                "strategies": ["s_a", "s_b"],
                "include_warnings": True,
                "max_per_strategy": 5,
            },
        }
    }
    combos = [
        {"candidate_set": "only_a", "top_per_strategy": 2},
        {"candidate_set": "both_one_each", "top_per_strategy": 1},
    ]
    u = resolve_candidate_universe_for_grid(raw, base_cfg, combos)
    ids = {c.candidate_id for c in u}
    assert ids == {"a1", "a2", "b1"}


def test_resolve_empty_grid_names_falls_back_to_full_eligible():
    raw = [_c("x", "s_x", rank=1)]
    base_cfg = {"candidate_sets": {"set_a": {"strategies": ["s_x"], "include_warnings": True}}}
    combos: list[dict] = [{"candidate_set": "unknown", "top_per_strategy": 5}]
    u = resolve_candidate_universe_for_grid(raw, base_cfg, combos)
    assert len(u) == 1 and u[0].candidate_id == "x"
