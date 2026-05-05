"""Load strategy metadata from YAML (family, priority, active windows)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_FALLBACK = {
    "family": "unknown",
    "conflict_group": "QQQ_directional",
    "default_priority": 50,
    "default_active_start_minute": 0,
    "default_active_end_minute": 389,
}


@lru_cache(maxsize=1)
def load_strategy_metadata() -> dict[str, Any]:
    path = Path(__file__).resolve().parent / "metadata.yaml"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return raw if isinstance(raw, dict) else {}


def get_strategy_metadata(strategy_name: str) -> dict[str, Any]:
    meta = load_strategy_metadata().get(strategy_name)
    if not isinstance(meta, dict):
        return dict(_FALLBACK)
    out = dict(_FALLBACK)
    out.update(meta)
    return out
