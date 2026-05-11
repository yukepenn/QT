"""Trailing-stop helpers."""

from __future__ import annotations

from src.execution.types import TrailingRule


def atr_style_trail(distance_r: float) -> TrailingRule:
    return TrailingRule(distance_r=float(distance_r))
