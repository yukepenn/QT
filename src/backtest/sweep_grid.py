"""Grid expansion and stable config hashing."""

from __future__ import annotations

import hashlib
import itertools
import json
from typing import Any, Mapping


def expand_param_grid(grid: dict[str, list[Any]]) -> list[dict[str, Any]]:
    if not grid:
        return [{}]
    keys = list(grid.keys())
    vals: list[list[Any]] = []
    for k in keys:
        v = grid[k]
        if isinstance(v, (list, tuple)):
            vals.append(list(v))
        else:
            vals.append([v])
    return [dict(zip(keys, combo)) for combo in itertools.product(*vals)]


def config_hash(config: Mapping[str, Any]) -> str:
    blob = json.dumps(config, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:20]
