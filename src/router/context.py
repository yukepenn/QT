"""Router scaffold (disabled by default)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ContextLabel(str, Enum):
    UNKNOWN = "unknown"


@dataclass
class PlaybookMetadata:
    name: str = "default"


@dataclass
class PermissionDecision:
    allowed: bool = True
    reason: str = "router_disabled"


@dataclass
class QualityScore:
    score: float = 0.0


def evaluate_permission(*_args, **_kwargs) -> PermissionDecision:
    return PermissionDecision()


def score_trade_quality(*_args, **_kwargs) -> QualityScore:
    return QualityScore()
