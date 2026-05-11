"""Tests for walkforward fold loading."""

from __future__ import annotations

import pytest

from src.walkforward.folds import SmokeFold, load_smoke_folds, validate_smoke_folds


def test_load_valid_folds():
    cfg = {
        "folds": [
            {
                "fold_id": "a",
                "label": "l",
                "test_start": "2023-01-01",
                "test_end": "2023-06-01",
            }
        ]
    }
    folds = load_smoke_folds(cfg)
    assert len(folds) == 1
    assert folds[0].fold_id == "a"


def test_invalid_dates_fail():
    cfg = {
        "folds": [
            {
                "fold_id": "bad",
                "label": "l",
                "test_start": "2023-06-01",
                "test_end": "2023-01-01",
            }
        ]
    }
    with pytest.raises(ValueError):
        load_smoke_folds(cfg)


def test_duplicate_fold_id_fails():
    cfg = {
        "folds": [
            {"fold_id": "x", "label": "a", "test_start": "2023-01-01", "test_end": "2023-06-01"},
            {"fold_id": "x", "label": "b", "test_start": "2024-01-01", "test_end": "2024-06-01"},
        ]
    }
    with pytest.raises(ValueError, match="duplicate"):
        load_smoke_folds(cfg)


def test_validate_smoke_folds_ok():
    folds = [
        SmokeFold(fold_id="z", label="", test_start="2023-01-01", test_end="2023-02-01"),
    ]
    validate_smoke_folds(folds)
