# Fixed-profile out-of-window validation v1 — summary

## 1. Purpose

Replay **five fixed Layer-2 profiles** (VWAP mtp=2 / mtp=1; indicator mtp=1 / 2 / 3) on **multiple calendar windows** without parameter changes, then summarize economics, trade-number stability, **target-limit-aware exit/slip overlay**, offline **quality-score transfer**, and **regime / `regime_unknown`** stability — using existing candidates and combiner semantics only.

## 2. Prior state (Trade Quality Router v1.5)

- VWAP offline **top80** score did **not** survive primary **2023→2024** holdout in-sample.
- VWAP **trade #2** was **positive** in both 2023 and 2024.
- Indicator **mtp=2** added total R but **diluted avg R**; **mtp=3** only weakly additive.
- **`regime_unknown`** is **mixed / mid-session** — treat as **neutral** until labels improve.
- Target-limit slip **overlay** improves interpretation vs symmetric stress; **not** a simulator change.

## 3. Data availability

Run:

`python -m src.research.fixed_profile_oow inspect-data --output-root src/research/results/fixed_profile_oow_v1`

Outputs: `data_availability.md`, `data_availability.csv`, optional `data_availability_by_year.csv`.

Windows (clipped to available data when possible): **early_oow**, **insample_ref**, **late_oow**, **full_available** — see `fixed_profile_oow_lib.default_windows`.

## 4. Fixed profiles tested

See `fixed_profile_definitions.md` + `fixed_profile_definitions.csv` and YAMLs under `configs/`.

## 5. In-sample sanity replay

All five profiles **`OK`** on **2023-01-01 → 2024-12-31** (`insample_sanity/insample_sanity_metrics.csv`).

- **VWAP** matches the original Global L2–style references (~337 / +42.2R; ~294 / +36.7R).
- **Indicator** trade counts match older narratives (502 / 1002 / 1327) but **total R differs** from v1.5 headline figures; see `insample_sanity/insample_sanity_failure.md`. `insample_expected_rows()` is anchored to **this** combiner replay.

## 6. OOW performance by profile / window

Curated table: `oow/fixed_profile_oow_metrics.csv` (local combiner runs under `local_runs/`).

**Highlights (published R, baseline slip 0.01/share):**

| profile | early_oow | late_oow | full_available |
|---------|-----------|----------|------------------|
| vwap_mtp2 | −43.1R / 482 tr | −14.1R / 208 tr | −14.9R / 1027 tr |
| vwap_mtp1 | −40.1R / 422 tr | −17.5R / 188 tr | −20.9R / 904 tr |
| indicator_mtp1 | −29.8R / 754 tr | −3.3R / 332 tr | −14.3R / 1588 tr |
| indicator_mtp2 | −104.2R / 1508 tr | −14.7R / 662 tr | −72.4R / 3172 tr |
| indicator_mtp3 | −163.7R / 1938 tr | −33.5R / 848 tr | −139.2R / 4113 tr |

No primary profile is **positive** on both **early_oow** and **late_oow**.

## 7. Trade-number stability

`trade_number/vwap_trade_number_oow.csv`, `trade_number/indicator_trade_number_oow.csv`.

- **VWAP mtp=2:** trade #2 is **not** reliably positive in **early_oow** (per-year mix; aggregate trade#2 negative).
- **Indicator mtp=2:** second-trade bucket **negative** in **late_oow** and strongly negative **early_oow** vs mtp=1.
- **Indicator mtp=3:** third-trade bucket adds **negative** marginal R OOW — keep **diagnostic only**; no evidence for mtp=5.

## 8. Target-limit-aware exit / slip overlay

`exit_slip/oow_exit_slip_scenario_comparison.csv`: **symmetric_stress** (0.02) is harshest; **target_limit_stress** partially recovers vs symmetric on target-heavy windows; **symmetric_extreme** (0.03) is a warning tier.

**Conclusion:** overlay **changes loss depth** but **does not** produce positive OOW economics for VWAP or indicator profiles in this run — pass/fail ordering vs published baseline is unchanged at the “go / no-go” level.

## 9. Quality score transfer

`quality_score_transfer/score_transfer_key_findings.csv`, `vwap_score_transfer.csv`, `indicator_score_transfer.csv`.

- **VWAP / indicator `insample_ref`:** all session dates fall in the train window → **top80/top60 test cohorts empty** within that file (expected artifact of train-on-2023–2024 definition).
- **OOW windows:** thresholds often **collapse to 0** (topK equals full sample) or **score_ge_60** has tiny **N** — no evidence that offline score is **router-ready**.

## 10. Regime / unknown stability

`regime_stability/regime_by_window.csv`, `unknown_by_window.csv`, `vwap_regime_oow.csv`, `indicator_regime_oow.csv` populated for **enriched** runs (`insample_ref`, **early_oow**, **late_oow** for VWAP + indicator mtp1/2). **`full_available`** and **indicator_mtp3** were not enriched in this pass (optional follow-up).

## 11. max_trades_per_day 2 / 3 / 5

- **mtp=2 (VWAP):** does not rescue **late_oow**; **early_oow** still bad.
- **mtp=2 (indicator):** **worse** than mtp=1 on **early_oow**; **late_oow** still negative.
- **mtp=3:** marginal / negative — **no** support for raising cap toward **5**.

## 12. Router readiness

**No** default-off router: OOW economics fail; score transfer does not show clean OOW uplift; regime tables are exploratory only.

## 13. Decision

**`REVISIT_LAYER2_CANDIDATE_SELECTION`** — see `fixed_profile_oow_decision.md` (auto label from primary-profile OOW totals).

## 14. Explicit non-runs

mini-WFO; full rolling WFO; live/paper; SPY; Global L1 rerun; broad Global L2 grid; strategy/feature/selected-candidate YAML changes; hard regime filter; combiner `regime_router`; parameter optimization on OOW; OOW-driven YAML selection; heavy artifact commits.

## 15. Recommended next step

**`REVISIT_LAYER2_CANDIDATE_SELECTION`** — re-evaluate which candidates belong in a **global** VWAP / indicator core for QQQ given **2020–2022** and **2025–2026** weakness under fixed execution rules, **before** any Layer3 fixed-profile smoke.

### Commands (orchestration)

```powershell
python -m src.research.fixed_profile_oow inspect-data --output-root src/research/results/fixed_profile_oow_v1
python -m src.research.fixed_profile_oow run --output-root src/research/results/fixed_profile_oow_v1 --skip-existing
python -m src.research.fixed_profile_oow enrich --output-root src/research/results/fixed_profile_oow_v1
python -m src.research.fixed_profile_oow postprocess --output-root src/research/results/fixed_profile_oow_v1
```

Do **not** pass `--use-signal-cache` on unsafe OneDrive roots. Raw outputs remain under `local_runs/` (**local-only**).
