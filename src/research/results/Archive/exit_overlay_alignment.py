"""
Research-only combiner-aligned long replay for exit-overlay diagnostics.

Mirrors key long-side semantics from ``src/combiner/simulator.py`` (_simulate_combiner_numba):
next-bar open fill (+slip), stop from panel, target from panel or target_r * act_risk,
same-bar stop+target with configurable ambiguity, exit prices with long-side slip on fills,
max-hold and EOD ordering consistent with the simulator loop.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Iterator, Literal

import numpy as np
import pandas as pd

from src.research.exit_overlay_sim import (
    AmbiguityPolicy,
    SimResult,
    minute_from_open,
)
from src.research.exit_overlay_sim import _intrabar_resolution  # noqa: PLC2701

EOD_EXIT_MINUTE = 389
COMBINER_DEFAULT_SLIP = 0.01
DEFAULT_MAX_HOLD_MINUTES = 120

StartBarPolicyT = Literal["entry_bar", "bar_after_entry"]
EntryPriceSourceT = Literal["panel_entry_price", "bar_open_plus_slip"]
ExitPriceSourceT = Literal["simulated_bar_price", "panel_exit_price_when_original"]
SlippagePolicyT = Literal["already_in_panel", "apply_like_combiner", "none"]
RiskPolicyT = Literal["panel_risk_per_share", "abs_entry_minus_stop"]
SameBarPolicyT = Literal["stop_first", "target_first", "skip_ambiguous"]
ForcedExitPolicyT = Literal["panel_exit_idx", "eod_exit_minute", "max_hold"]
TargetPolicyT = Literal["panel_target_price", "entry_plus_target_r_times_risk"]
MaxHoldPriorityT = Literal[
    "intrabar_first",
    "forced_first_on_terminal_bar",
    "panel_exit_reason_authoritative",
    "skip_terminal_bar_conflicts",
]


@dataclass(frozen=True)
class CloneReplayConfig:
    """Serializable switch bundle for combiner-clone replay diagnostics."""

    config_id: str
    start_bar_policy: StartBarPolicyT
    entry_price_source: EntryPriceSourceT
    exit_price_source: ExitPriceSourceT
    slippage_policy: SlippagePolicyT
    risk_policy: RiskPolicyT
    same_bar_policy: SameBarPolicyT
    forced_exit_policy: ForcedExitPolicyT
    target_policy: TargetPolicyT
    max_hold_priority: MaxHoldPriorityT = "intrabar_first"

    def to_dict(self) -> dict[str, str]:
        return {k: str(v) for k, v in asdict(self).items()}

    @staticmethod
    def from_mapping(m: dict[str, Any]) -> CloneReplayConfig:
        keys = (
            "config_id",
            "start_bar_policy",
            "entry_price_source",
            "exit_price_source",
            "slippage_policy",
            "risk_policy",
            "same_bar_policy",
            "forced_exit_policy",
            "target_policy",
        )
        base = {k: m[k] for k in keys}
        mhp = m.get("max_hold_priority", "intrabar_first")
        base["max_hold_priority"] = str(mhp)
        return CloneReplayConfig(**base)  # type: ignore[arg-type]


def _slip_for_exit(cfg: CloneReplayConfig) -> float:
    if cfg.slippage_policy == "apply_like_combiner":
        return float(COMBINER_DEFAULT_SLIP)
    return 0.0


def _slip_for_entry_open(cfg: CloneReplayConfig) -> float:
    if cfg.entry_price_source != "bar_open_plus_slip":
        return 0.0
    if cfg.slippage_policy == "apply_like_combiner":
        return float(COMBINER_DEFAULT_SLIP)
    if cfg.slippage_policy == "none":
        return 0.0
    return float(COMBINER_DEFAULT_SLIP)


def _ambiguity_enum(same_bar: SameBarPolicyT) -> AmbiguityPolicy:
    if same_bar == "target_first":
        return AmbiguityPolicy.target_first
    if same_bar == "skip_ambiguous":
        return AmbiguityPolicy.skip_ambiguous
    return AmbiguityPolicy.stop_first


def _exit_px_long(*, raw_level: float, slip: float) -> float:
    return float(raw_level) - float(slip)


def normalize_exit_reason(x: Any) -> str:
    """Public alias for exit-reason alignment checks."""
    return _normalize_exit_reason(x)


def _normalize_exit_reason(x: Any) -> str:
    s = str(x or "").strip().lower()
    if s.startswith("ex_"):
        s = s[3:]
    return s


def _resolve_entry_position(
    session_bars: pd.DataFrame,
    row: pd.Series,
    *,
    start_bar_policy: StartBarPolicyT,
) -> int:
    ts = pd.to_datetime(session_bars["ts_utc"], utc=True)
    entry_ts = pd.Timestamp(row["entry_ts_utc"])
    if entry_ts.tzinfo is None:
        entry_ts = entry_ts.tz_localize("UTC")
    else:
        entry_ts = entry_ts.tz_convert("UTC")
    pos = int(ts.searchsorted(entry_ts, side="left"))
    if start_bar_policy == "bar_after_entry":
        pos = min(pos + 1, max(len(session_bars) - 1, 0))
    return pos


def _entry_price_long(
    session_bars: pd.DataFrame,
    pos: int,
    row: pd.Series,
    *,
    entry_price_source: EntryPriceSourceT,
    slip: float,
) -> float:
    if entry_price_source == "panel_entry_price":
        return float(row["entry_price"])
    o0 = float(session_bars["open"].iloc[pos])
    return o0 + float(slip)


def _target_price_long(
    row: pd.Series,
    *,
    ent_price: float,
    act_risk: float,
    target_policy: TargetPolicyT,
) -> float:
    if target_policy == "panel_target_price":
        return float(row["target_price"])
    tr = float(pd.to_numeric(row.get("target_r"), errors="coerce") or 0.0)
    return float(ent_price + tr * act_risk)


def _act_risk_long(*, ent_price: float, stop_px: float, risk_policy: RiskPolicyT, row: pd.Series) -> float:
    if risk_policy == "panel_risk_per_share":
        return float(row["risk_per_share"])
    return float(ent_price - stop_px)


def combiner_clone_long_walk(
    *,
    session_bars: pd.DataFrame,
    row: pd.Series,
    cfg: CloneReplayConfig,
    max_hold_minutes: int = DEFAULT_MAX_HOLD_MINUTES,
    eod_minute: int = EOD_EXIT_MINUTE,
) -> SimResult:
    """
    Deterministic long walk for one row. Returns ``SimResult`` compatible with overlay harness.
    """
    if not len(session_bars):
        return SimResult(0.0, float(row.get("entry_price", 0.0)), "no_bars", 0, False, False, -1)

    exit_slip = _slip_for_exit(cfg)
    entry_open_slip = _slip_for_entry_open(cfg)

    pos = _resolve_entry_position(session_bars, row, start_bar_policy=cfg.start_bar_policy)
    if pos >= len(session_bars):
        return SimResult(0.0, float(row.get("entry_price", 0.0)), "entry_not_found", 0, False, False, -1)

    ent_price = _entry_price_long(
        session_bars,
        pos,
        row,
        entry_price_source=cfg.entry_price_source,
        slip=entry_open_slip,
    )
    stop_px = float(row["stop_price"])
    act_risk = _act_risk_long(ent_price=ent_price, stop_px=stop_px, risk_policy=cfg.risk_policy, row=row)
    if act_risk <= 0 or not math.isfinite(act_risk):
        return SimResult(0.0, ent_price, "bad_risk", 0, False, False, -1)

    tgt = _target_price_long(row, ent_price=ent_price, act_risk=act_risk, target_policy=cfg.target_policy)
    amb_policy = _ambiguity_enum(cfg.same_bar_policy)

    h = session_bars["high"].to_numpy(float)
    l = session_bars["low"].to_numpy(float)
    c = session_bars["close"].to_numpy(float)
    ts = pd.to_datetime(session_bars["ts_utc"], utc=True)
    n = len(session_bars)

    cap_j = n
    if cfg.forced_exit_policy == "panel_exit_idx" and "exit_idx" in row and pd.notna(row.get("exit_idx")):
        cap_j = min(n, int(row["exit_idx"]) + 1)

    max_hold_m = max_hold_minutes if cfg.forced_exit_policy in ("max_hold", "panel_exit_idx", "eod_exit_minute") else -1
    if max_hold_m <= 0:
        max_hold_m = DEFAULT_MAX_HOLD_MINUTES

    any_amb = False
    panel_exr_n = _normalize_exit_reason(row.get("exit_reason"))
    panel_exit_i = int(row["exit_idx"]) if "exit_idx" in row and pd.notna(row.get("exit_idx")) else None

    for j in range(pos, cap_j):
        bars_held = j - pos + 1
        ts_j = ts.iloc[j]
        ts_nyj = ts_j.tz_convert("America/New_York") if ts_j.tzinfo else ts_j
        mfo = minute_from_open(pd.Timestamp(ts_nyj))

        exr = ""
        raw_ex = 0.0

        mh_priority = cfg.max_hold_priority
        forced_terminal = (
            mh_priority == "forced_first_on_terminal_bar" and max_hold_m > 0 and bars_held == max_hold_m
        )
        panel_auth_here = (
            mh_priority == "panel_exit_reason_authoritative"
            and panel_exr_n == "max_hold"
            and panel_exit_i is not None
            and int(j) == int(panel_exit_i)
        )

        if panel_auth_here:
            exr = "max_hold"
            raw_ex = float(row["exit_price"])
        elif forced_terminal:
            exr = "max_hold"
            raw_ex = float(c[j])
        else:
            lo, hi = float(l[j]), float(h[j])
            res, is_amb = _intrabar_resolution(low=lo, high=hi, stop=stop_px, target=tgt, policy=amb_policy)
            if is_amb:
                any_amb = True

            if j >= pos:
                if res == "ambiguous_skip":
                    pass
                elif res == "stop":
                    exr = "stop"
                    raw_ex = stop_px
                elif res == "target":
                    exr = "target"
                    raw_ex = tgt

            if not exr and max_hold_m > 0 and bars_held >= max_hold_m:
                exr = "max_hold"
                raw_ex = float(c[j])

        if not exr and mfo >= int(eod_minute):
            exr = "eod_exit"
            raw_ex = float(c[j])

        if not exr and j == n - 1:
            exr = "session_end"
            raw_ex = float(c[j])

        if exr:
            panel_exr = _normalize_exit_reason(row.get("exit_reason"))
            use_panel_px = cfg.exit_price_source == "panel_exit_price_when_original" and panel_exr == _normalize_exit_reason(exr)
            if use_panel_px:
                ex_price = float(row["exit_price"])
            else:
                ex_price = _exit_px_long(raw_level=raw_ex, slip=exit_slip)
            r_mult = (ex_price - ent_price) / act_risk if act_risk > 0 else 0.0
            return SimResult(float(r_mult), float(ex_price), exr, int(bars_held), bool(any_amb), False, int(j))

    last = max(cap_j - 1, pos)
    raw_ex = float(c[last])
    ex_price = _exit_px_long(raw_level=raw_ex, slip=exit_slip)
    bars_held = last - pos + 1
    r_mult = (ex_price - ent_price) / act_risk if act_risk > 0 else 0.0
    return SimResult(float(r_mult), float(ex_price), "panel_cap_close", int(bars_held), bool(any_amb), False, int(last))


def alignment_label(
    *,
    mean_abs: float,
    median_abs: float,
    max_abs: float,
    total_r_diff: float,
) -> str:
    if not math.isfinite(mean_abs):
        return "ALIGNMENT_DATA_LIMITED"
    if mean_abs <= 0.05 and median_abs <= 0.02 and abs(total_r_diff) <= 5.0:
        return "ALIGNMENT_PASS"
    if mean_abs <= 0.08 and median_abs <= 0.04 and abs(total_r_diff) <= 15.0:
        return "ALIGNMENT_PASS_WITH_WARNINGS"
    return "ALIGNMENT_FAIL"


def iter_default_alignment_grid() -> Iterator[CloneReplayConfig]:
    """
    Curated grid (tractable on ~10k rows) covering the main drift hypotheses.
    """
    raw: list[tuple[str, ...]] = [
        # Baseline combiner-like
        (
            "cfg_0001",
            "entry_bar",
            "bar_open_plus_slip",
            "simulated_bar_price",
            "apply_like_combiner",
            "abs_entry_minus_stop",
            "stop_first",
            "max_hold",
            "panel_target_price",
        ),
        (
            "cfg_0002",
            "entry_bar",
            "panel_entry_price",
            "simulated_bar_price",
            "apply_like_combiner",
            "panel_risk_per_share",
            "stop_first",
            "max_hold",
            "panel_target_price",
        ),
        (
            "cfg_0003",
            "entry_bar",
            "bar_open_plus_slip",
            "simulated_bar_price",
            "apply_like_combiner",
            "panel_risk_per_share",
            "stop_first",
            "max_hold",
            "panel_target_price",
        ),
        (
            "cfg_0004",
            "entry_bar",
            "bar_open_plus_slip",
            "simulated_bar_price",
            "apply_like_combiner",
            "abs_entry_minus_stop",
            "stop_first",
            "max_hold",
            "entry_plus_target_r_times_risk",
        ),
        ("cfg_0005", "entry_bar", "bar_open_plus_slip", "simulated_bar_price", "none", "abs_entry_minus_stop", "stop_first", "max_hold", "panel_target_price"),
        ("cfg_0006", "entry_bar", "panel_entry_price", "simulated_bar_price", "none", "panel_risk_per_share", "stop_first", "max_hold", "panel_target_price"),
        ("cfg_0007", "bar_after_entry", "bar_open_plus_slip", "simulated_bar_price", "apply_like_combiner", "abs_entry_minus_stop", "stop_first", "max_hold", "panel_target_price"),
        ("cfg_0008", "bar_after_entry", "panel_entry_price", "simulated_bar_price", "apply_like_combiner", "panel_risk_per_share", "stop_first", "max_hold", "panel_target_price"),
        ("cfg_0009", "entry_bar", "bar_open_plus_slip", "simulated_bar_price", "already_in_panel", "abs_entry_minus_stop", "stop_first", "max_hold", "panel_target_price"),
        ("cfg_0010", "entry_bar", "panel_entry_price", "simulated_bar_price", "already_in_panel", "panel_risk_per_share", "stop_first", "max_hold", "panel_target_price"),
        ("cfg_0011", "entry_bar", "bar_open_plus_slip", "simulated_bar_price", "apply_like_combiner", "abs_entry_minus_stop", "target_first", "max_hold", "panel_target_price"),
        ("cfg_0012", "entry_bar", "bar_open_plus_slip", "simulated_bar_price", "apply_like_combiner", "abs_entry_minus_stop", "skip_ambiguous", "max_hold", "panel_target_price"),
        ("cfg_0013", "entry_bar", "bar_open_plus_slip", "simulated_bar_price", "apply_like_combiner", "abs_entry_minus_stop", "stop_first", "panel_exit_idx", "panel_target_price"),
        ("cfg_0014", "entry_bar", "panel_entry_price", "panel_exit_price_when_original", "apply_like_combiner", "panel_risk_per_share", "stop_first", "panel_exit_idx", "panel_target_price"),
        ("cfg_0015", "entry_bar", "bar_open_plus_slip", "panel_exit_price_when_original", "apply_like_combiner", "abs_entry_minus_stop", "stop_first", "panel_exit_idx", "panel_target_price", "intrabar_first"),
        (
            "cfg_0016_mh_forced",
            "entry_bar",
            "bar_open_plus_slip",
            "panel_exit_price_when_original",
            "apply_like_combiner",
            "abs_entry_minus_stop",
            "stop_first",
            "panel_exit_idx",
            "panel_target_price",
            "forced_first_on_terminal_bar",
        ),
        (
            "cfg_0017_mh_panelauth",
            "entry_bar",
            "bar_open_plus_slip",
            "panel_exit_price_when_original",
            "apply_like_combiner",
            "abs_entry_minus_stop",
            "stop_first",
            "panel_exit_idx",
            "panel_target_price",
            "panel_exit_reason_authoritative",
        ),
        (
            "cfg_0018_mh_skipconf",
            "entry_bar",
            "bar_open_plus_slip",
            "panel_exit_price_when_original",
            "apply_like_combiner",
            "abs_entry_minus_stop",
            "stop_first",
            "panel_exit_idx",
            "panel_target_price",
            "skip_terminal_bar_conflicts",
        ),
    ]
    for tup in raw:
        base = tup[:9]
        mhp: MaxHoldPriorityT = tup[9] if len(tup) > 9 else "intrabar_first"  # type: ignore[assignment]
        yield CloneReplayConfig(
            config_id=base[0],
            start_bar_policy=base[1],  # type: ignore[arg-type]
            entry_price_source=base[2],  # type: ignore[arg-type]
            exit_price_source=base[3],  # type: ignore[arg-type]
            slippage_policy=base[4],  # type: ignore[arg-type]
            risk_policy=base[5],  # type: ignore[arg-type]
            same_bar_policy=base[6],  # type: ignore[arg-type]
            forced_exit_policy=base[7],  # type: ignore[arg-type]
            target_policy=base[8],  # type: ignore[arg-type]
            max_hold_priority=mhp,
        )


def pick_best_config(agg: pd.DataFrame) -> CloneReplayConfig | None:
    if agg.empty or "mean_abs_r_diff" not in agg.columns:
        return None
    sub = agg.copy()
    if "same_bar_policy" in sub.columns:
        sf = sub[sub["same_bar_policy"].astype(str) == "stop_first"]
        if len(sf):
            sub = sf
    if "max_hold_priority" in sub.columns:
        prefer = sub[sub["max_hold_priority"].astype(str).isin(("intrabar_first", "forced_first_on_terminal_bar"))]
        if len(prefer):
            sub = prefer
    sub = sub.sort_values(["mean_abs_r_diff", "median_abs_r_diff", "max_abs_r_diff"], ascending=True)
    row = sub.iloc[0].to_dict()
    return CloneReplayConfig.from_mapping(row)


def aggregate_alignment_per_config_slice(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    parts: list[dict[str, Any]] = []
    for key, g in df.groupby(group_cols, dropna=False):
        keys = key if isinstance(key, tuple) else (key,)
        g_use = g
        if "max_hold_priority" in g.columns and len(g) and str(g["max_hold_priority"].iloc[0]) == "skip_terminal_bar_conflicts":
            if "panel_exit_reason" in g.columns:
                pe = g["panel_exit_reason"].map(_normalize_exit_reason) == "max_hold"
                er = g["exit_reason_replay"].map(_normalize_exit_reason).isin(["stop", "target"])
                g_use = g[~(pe & er)]
            else:
                g_use = g
        orig = pd.to_numeric(g_use["r_original"], errors="coerce")
        rep = pd.to_numeric(g_use["r_replay"], errors="coerce")
        diff = (rep - orig).abs()
        signed = rep - orig
        n = int(len(g_use))
        matched_exit = None
        if "exit_reason_match" in g_use.columns:
            matched_exit = float(pd.to_numeric(g_use["exit_reason_match"], errors="coerce").mean())
        sign_match = float((np.sign(orig.fillna(0)) == np.sign(rep.fillna(0))).mean()) if n else 0.0
        amb_ct = int(g_use["ambiguous_bar"].sum()) if "ambiguous_bar" in g_use.columns else 0
        row_dict: dict[str, Any] = {c: keys[i] for i, c in enumerate(group_cols)}
        row_dict.update(
            {
                "trades": n,
                "mean_abs_r_diff": float(diff.mean()) if n else math.nan,
                "median_abs_r_diff": float(diff.median()) if n else math.nan,
                "p90_abs_r_diff": float(diff.quantile(0.9)) if n else math.nan,
                "max_abs_r_diff": float(diff.max()) if n else math.nan,
                "total_r_original": float(orig.sum()) if n else math.nan,
                "total_r_replay": float(rep.sum()) if n else math.nan,
                "total_r_diff": float(signed.sum()) if n else math.nan,
                "sign_match_pct": sign_match * 100.0,
                "exit_reason_match_pct": matched_exit * 100.0 if matched_exit is not None else math.nan,
                "ambiguous_count": amb_ct,
                "ambiguous_pct": (100.0 * amb_ct / n) if n else 0.0,
            }
        )
        row_dict["label"] = alignment_label(
            mean_abs=float(row_dict["mean_abs_r_diff"]) if pd.notna(row_dict["mean_abs_r_diff"]) else math.nan,
            median_abs=float(row_dict["median_abs_r_diff"]) if pd.notna(row_dict["median_abs_r_diff"]) else math.nan,
            max_abs=float(row_dict["max_abs_r_diff"]) if pd.notna(row_dict["max_abs_r_diff"]) else math.nan,
            total_r_diff=float(row_dict["total_r_diff"]) if pd.notna(row_dict["total_r_diff"]) else math.nan,
        )
        parts.append(row_dict)
    return pd.DataFrame(parts)
