"""Load frozen Layer 2 system YAMLs and merge into runnable combiner configs."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from src.walkforward.folds import SmokeFold

_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_DIR = _ROOT / "src" / "combiner" / "configs"

_LAYER2_TEMPLATE_BY_LAYER2_ROOT_NAME: dict[str, str] = {
    "layer2_qqq_2025_20260430_recent_check_v1": "layer2_qqq_2025_20260430_recent_check_v1.yaml",
    "layer2_qqq_2020_20260430_posthardening_strict_v1": "layer2_qqq_2020_20260430_posthardening_strict.yaml",
}


@dataclass(frozen=True)
class FrozenSystem:
    system_id: str
    path: Path
    candidate_root: Path
    candidate_ids: tuple[str, ...]
    combiner: dict[str, Any]
    cost: dict[str, Any]
    source: dict[str, Any]
    live_ready: bool
    research_status: str


def resolve_layer2_template(layer2_root: str | Path) -> Path:
    p = Path(layer2_root)
    name = p.name
    yaml_name = _LAYER2_TEMPLATE_BY_LAYER2_ROOT_NAME.get(name)
    if not yaml_name:
        raise ValueError(f"unknown layer2_root for template mapping: {name}")
    cand = _CONFIG_DIR / yaml_name
    if not cand.is_file():
        raise FileNotFoundError(cand)
    return cand


def load_frozen_system(path: Path) -> FrozenSystem:
    with Path(path).open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    sid = str(raw.get("system_id") or "")
    cr = raw.get("candidate_root") or ""
    ids = raw.get("candidate_ids") or []
    comb = raw.get("combiner") or {}
    cost = raw.get("cost") or {}
    src = raw.get("source") or {}
    return FrozenSystem(
        system_id=sid,
        path=Path(path).resolve(),
        candidate_root=Path(cr),
        candidate_ids=tuple(str(x) for x in ids),
        combiner=dict(comb),
        cost=dict(cost),
        source=dict(src),
        live_ready=bool(raw.get("live_ready", False)),
        research_status=str(raw.get("research_status") or ""),
    )


def validate_frozen_system(system: FrozenSystem, *, symbol: str) -> None:
    if system.live_ready:
        raise ValueError(f"{system.system_id}: live_ready must be false for smoke")
    mo = int(system.combiner.get("max_open_positions", 1))
    if mo != 1:
        raise ValueError(f"{system.system_id}: max_open_positions must be 1")
    if not system.candidate_ids:
        raise ValueError(f"{system.system_id}: candidate_ids required")
    root = system.candidate_root
    if not root.is_absolute():
        root = Path.cwd() / root
    if not root.is_dir():
        raise FileNotFoundError(f"candidate_root missing: {root}")
    for cid in system.candidate_ids:
        y = root / f"{cid}.yaml"
        if not y.is_file():
            raise FileNotFoundError(f"candidate YAML missing: {y}")
    if not system.cost:
        raise ValueError(f"{system.system_id}: cost section required")
    sym = str(symbol).upper()
    if sym != "QQQ":
        raise ValueError("smoke supports QQQ only")
    if "SPY" in system.system_id.upper():
        raise ValueError("SPY not allowed")


def candidate_yaml_paths(system: FrozenSystem) -> list[Path]:
    root = system.candidate_root
    if not root.is_absolute():
        root = Path.cwd() / root
    return [root / f"{cid}.yaml" for cid in system.candidate_ids]


def build_fold_combiner_config(
    system: FrozenSystem,
    fold: SmokeFold,
    smoke_config: dict[str, Any],
) -> dict[str, Any]:
    del fold  # fold dates applied at run time, not in YAML
    del smoke_config
    src = system.source
    layer2_root = src.get("layer2_root")
    if not layer2_root:
        raise ValueError("frozen system missing source.layer2_root")
    template_path = resolve_layer2_template(str(layer2_root))
    with template_path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    cfg = copy.deepcopy(cfg)

    cr = system.candidate_root
    if not cr.is_absolute():
        cr = Path.cwd() / cr
    cfg["candidate_root"] = str(cr.as_posix())

    cfg.setdefault("execution", {})
    cfg["execution"]["commission_per_trade"] = float(system.cost.get("commission_per_trade", 0.0))
    cfg["execution"]["slippage_per_share"] = float(system.cost.get("slippage_per_share", 0.01))
    if "no_new_after_minute" in system.combiner:
        cfg["execution"]["no_new_after_minute"] = int(system.combiner["no_new_after_minute"])

    cfg.setdefault("system", {})
    for k in (
        "max_open_positions",
        "max_trades_per_day",
        "daily_max_loss_r",
        "cooldown_after_loss_minutes",
    ):
        if k in system.combiner:
            cfg["system"][k] = system.combiner[k]
    cfg["system"]["max_open_positions"] = int(system.combiner.get("max_open_positions", 1))

    cfg.setdefault("conflict", {})
    if "priority_policy" in system.combiner:
        cfg["conflict"]["priority_policy"] = str(system.combiner["priority_policy"])

    return cfg
