"""Management package: builds ``ExitPlan`` consumed by ``execution``."""

from src.management.modes import ManagementMode, exit_plan_for_mode
from src.management.no_followthrough import nft_after_bars
from src.management.scaleout import fixed_scaleouts
from src.management.trailing import atr_style_trail

__all__ = [
    "ManagementMode",
    "atr_style_trail",
    "exit_plan_for_mode",
    "fixed_scaleouts",
    "nft_after_bars",
]
