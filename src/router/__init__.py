"""Router package scaffold."""

from src.router.context import (
    ContextLabel,
    PermissionDecision,
    PlaybookMetadata,
    QualityScore,
    evaluate_permission,
    score_trade_quality,
)

__all__ = [
    "ContextLabel",
    "PermissionDecision",
    "PlaybookMetadata",
    "QualityScore",
    "evaluate_permission",
    "score_trade_quality",
]
