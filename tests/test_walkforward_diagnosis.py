"""Tests for Layer 3 component diagnosis tables."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.walkforward.diagnosis import (
    build_component_diagnosis_tables,
    write_diagnosis_report,
)


def _tiny_fold_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "system_id": "recent_failed_only",
                "fold_id": "y2023",
                "total_r": -1.0,
                "profit_factor_r": 0.9,
            },
            {
                "system_id": "recent_failed_only",
                "fold_id": "y2024",
                "total_r": 2.0,
                "profit_factor_r": 1.1,
            },
            {
                "system_id": "recent_failed_only",
                "fold_id": "recent_2025_202604",
                "total_r": 3.0,
                "profit_factor_r": 1.2,
            },
            {
                "system_id": "recent_failed_gap_mtd1",
                "fold_id": "y2023",
                "total_r": 0.0,
                "profit_factor_r": 1.0,
            },
            {
                "system_id": "recent_failed_gap_mtd1",
                "fold_id": "y2024",
                "total_r": 0.0,
                "profit_factor_r": 1.0,
            },
            {
                "system_id": "recent_failed_gap_mtd1",
                "fold_id": "recent_2025_202604",
                "total_r": 0.0,
                "profit_factor_r": 1.0,
            },
        ]
    )


def _tiny_system_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "system_id": "recent_failed_only",
                "total_trades": 30,
                "stitched_total_r": 4.0,
                "stitched_pf": 1.1,
                "stitched_pf_r": 1.05,
                "mean_fold_pf": 1.1,
                "mean_fold_pf_r": 1.05,
                "positive_fold_count": 2,
                "worst_fold_r": -1.0,
                "fold_concentration": 0.5,
                "cost_0_02_survives": True,
                "cost_0_03_survives": False,
            },
            {
                "system_id": "recent_gap_only",
                "total_trades": 20,
                "stitched_total_r": 1.0,
                "stitched_pf": 1.0,
                "stitched_pf_r": 0.99,
                "mean_fold_pf": 1.0,
                "mean_fold_pf_r": 0.99,
                "positive_fold_count": 1,
                "worst_fold_r": -2.0,
                "fold_concentration": 0.4,
                "cost_0_02_survives": True,
                "cost_0_03_survives": False,
            },
            {
                "system_id": "recent_prior_day_only",
                "total_trades": 10,
                "stitched_total_r": -1.0,
                "stitched_pf": 0.95,
                "stitched_pf_r": 0.9,
                "mean_fold_pf": 0.95,
                "mean_fold_pf_r": 0.9,
                "positive_fold_count": 0,
                "worst_fold_r": -3.0,
                "fold_concentration": 0.9,
                "cost_0_02_survives": False,
                "cost_0_03_survives": False,
            },
            {
                "system_id": "fullhist_failed_only",
                "total_trades": 15,
                "stitched_total_r": 2.0,
                "stitched_pf": 1.05,
                "stitched_pf_r": 1.02,
                "mean_fold_pf": 1.05,
                "mean_fold_pf_r": 1.02,
                "positive_fold_count": 2,
                "worst_fold_r": -0.5,
                "fold_concentration": 0.45,
                "cost_0_02_survives": True,
                "cost_0_03_survives": False,
            },
            {
                "system_id": "fullhist_gap_only",
                "total_trades": 12,
                "stitched_total_r": 0.5,
                "stitched_pf": 1.0,
                "stitched_pf_r": 0.98,
                "mean_fold_pf": 1.0,
                "mean_fold_pf_r": 0.98,
                "positive_fold_count": 1,
                "worst_fold_r": -1.0,
                "fold_concentration": 0.5,
                "cost_0_02_survives": True,
                "cost_0_03_survives": False,
            },
            {
                "system_id": "recent_failed_gap_mtd1",
                "total_trades": 50,
                "stitched_total_r": 5.0,
                "stitched_pf": 1.12,
                "stitched_pf_r": 1.08,
                "mean_fold_pf": 1.12,
                "mean_fold_pf_r": 1.08,
                "positive_fold_count": 2,
                "worst_fold_r": -0.5,
                "fold_concentration": 0.55,
                "cost_0_02_survives": True,
                "cost_0_03_survives": False,
            },
            {
                "system_id": "recent_failed_gap_mtd2",
                "total_trades": 60,
                "stitched_total_r": 3.0,
                "stitched_pf": 1.05,
                "stitched_pf_r": 1.0,
                "mean_fold_pf": 1.05,
                "mean_fold_pf_r": 1.0,
                "positive_fold_count": 2,
                "worst_fold_r": -2.0,
                "fold_concentration": 0.7,
                "cost_0_02_survives": True,
                "cost_0_03_survives": False,
            },
            {
                "system_id": "recent_trap_trio_mtd1",
                "total_trades": 55,
                "stitched_total_r": 6.0,
                "stitched_pf": 1.15,
                "stitched_pf_r": 1.1,
                "mean_fold_pf": 1.15,
                "mean_fold_pf_r": 1.1,
                "positive_fold_count": 2,
                "worst_fold_r": -0.2,
                "fold_concentration": 0.5,
                "cost_0_02_survives": True,
                "cost_0_03_survives": False,
            },
            {
                "system_id": "recent_trap_trio_mtd2",
                "total_trades": 70,
                "stitched_total_r": 7.0,
                "stitched_pf": 1.2,
                "stitched_pf_r": 1.12,
                "mean_fold_pf": 1.2,
                "mean_fold_pf_r": 1.12,
                "positive_fold_count": 3,
                "worst_fold_r": -0.1,
                "fold_concentration": 0.55,
                "cost_0_02_survives": True,
                "cost_0_03_survives": False,
            },
            {
                "system_id": "recent_opening_full_mtd2",
                "total_trades": 80,
                "stitched_total_r": 8.0,
                "stitched_pf": 1.2,
                "stitched_pf_r": 1.1,
                "mean_fold_pf": 1.2,
                "mean_fold_pf_r": 1.1,
                "positive_fold_count": 2,
                "worst_fold_r": -1.0,
                "fold_concentration": 0.6,
                "cost_0_02_survives": True,
                "cost_0_03_survives": False,
            },
            {
                "system_id": "fullhist_failed_gap_mtd1",
                "total_trades": 40,
                "stitched_total_r": 3.5,
                "stitched_pf": 1.08,
                "stitched_pf_r": 1.05,
                "mean_fold_pf": 1.08,
                "mean_fold_pf_r": 1.05,
                "positive_fold_count": 2,
                "worst_fold_r": -1.0,
                "fold_concentration": 0.5,
                "cost_0_02_survives": True,
                "cost_0_03_survives": False,
            },
            {
                "system_id": "fullhist_failed_gap_mtd2",
                "total_trades": 45,
                "stitched_total_r": 3.0,
                "stitched_pf": 1.06,
                "stitched_pf_r": 1.03,
                "mean_fold_pf": 1.06,
                "mean_fold_pf_r": 1.03,
                "positive_fold_count": 2,
                "worst_fold_r": -1.2,
                "fold_concentration": 0.52,
                "cost_0_02_survives": True,
                "cost_0_03_survives": False,
            },
        ]
    )


def test_component_table_builds():
    fold = _tiny_fold_summary()
    sysm = _tiny_system_summary()
    tables = build_component_diagnosis_tables(fold, sysm)
    ct = tables["component_table"]
    assert "recent_failed_only" in set(ct["system_id"])
    assert ct[ct["system_id"] == "recent_failed_only"]["stitched_total_r"].iloc[0] == pytest.approx(4.0)


def test_incremental_delta_total_r():
    fold = _tiny_fold_summary()
    sysm = _tiny_system_summary()
    inc = build_component_diagnosis_tables(fold, sysm)["incremental_table"]
    row = inc[(inc["base_system"] == "recent_failed_only") & (inc["variant_system"] == "recent_failed_gap_mtd1")]
    assert len(row) == 1
    assert row.iloc[0]["delta_total_r"] == pytest.approx(1.0)


def test_max_trades_sensitivity_mtd2_hurt():
    fold = _tiny_fold_summary()
    sysm = _tiny_system_summary()
    m = build_component_diagnosis_tables(fold, sysm)["max_trades_sensitivity"]
    row = m[m["mtd1_system"] == "recent_failed_gap_mtd1"]
    assert row.iloc[0]["mtd2_helps_headline_r"] is False


def test_recent_vs_fullhistory_missing_graceful():
    sysm = _tiny_system_summary()
    sysm = sysm[sysm["system_id"] != "fullhist_failed_only"]
    fold = _tiny_fold_summary()
    rv = build_component_diagnosis_tables(fold, sysm)["recent_vs_fullhistory"]
    row = rv[rv["recent_system"] == "recent_failed_only"]
    assert "missing" in str(row.iloc[0]["interpretation"])


def test_write_diagnosis_report_creates_files(tmp_path: Path):
    fold = _tiny_fold_summary()
    sysm = _tiny_system_summary()
    p = write_diagnosis_report(tmp_path, fold, sysm)
    assert p.is_file()
    assert (tmp_path / "component_table.csv").is_file()
    assert (tmp_path / "incremental_table.csv").is_file()
    assert (tmp_path / "fold_heatmap.csv").is_file()
