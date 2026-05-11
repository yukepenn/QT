"""Scale-out helpers."""

from __future__ import annotations

from src.execution.types import ScaleOutRule


def fixed_scaleouts(*rules: ScaleOutRule) -> tuple[ScaleOutRule, ...]:
    return tuple(rules)
