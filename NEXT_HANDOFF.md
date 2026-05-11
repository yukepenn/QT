# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Main research commit (full **66×3** audit + tooling + curated outputs) | **`3fd30b71409f9c23e289f503790b5c993d418cf7`** (`3fd30b7`) — `Research: complete layer2 candidate robustness audit` |
| Prior milestone (vwap+indicator slice only) | `7e5da17b89c91e01f7eb3a8f5743eda015ed0da3` — `Research: audit layer2 candidate robustness` |
| Repo tip | **Docs-only follow-up** — `Docs(handoff): sync NEXT_HANDOFF audit SHA` (run `git log -1 --oneline` after pull for exact SHA above **`3fd30b7`**) |
| Push status | **Pushed** `main` → `origin` (research **`3fd30b7`**, then small docs commits through tip **`f80ab6c`**) |
| Working tree | Expect modified tracked research/docs; **do not** stage `local_runs/**`, `.cache/**`, raw `trades.csv`, combiner `sweep_*` / `top_runs/` |
| Expected untracked local-only artifacts | `src/research/results/layer2_candidate_robustness_v1/local_runs/**`, `src/research/results/fixed_profile_oow_v1/local_runs/**`, `.cache/qt/candidate_signals/**` |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK (re-run after edits) |
| `python -m pytest -q` | **424** passed |
| `python -m src.strategies.loader --list` | **35** strategies |
| New / touched tests | `test_audit_l2_candidates_oow.py`, `test_l2_core_policy_v2.py` (+ `test_robust_core_accepts_diverse_pool`) |
| Tracked-heavy check | `git ls-files \| Select-String -Pattern "top_runs|trades.csv|compact_trades|enriched.csv|scored_trades|\.parquet|\.npy|\.npz|\.memmap"` — **no** matches |

## C. Execution

| Item | Value |
|------|-------|
| Audit command (extended wave) | `python -m src.research.audit_l2_candidates_oow run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates --output-root src/research/results/layer2_candidate_robustness_v1 --windows-root src/research/results/fixed_profile_oow_v1 --families opening_trap,pa,afternoon,other --skip-existing --no-signal-cache` |
| First wave (already in repo history) | `--families vwap,indicator` (**27** candidates × **3** = **81** runs) |
| Candidates / families this completion | **opening_trap**, **pa**, **afternoon**, **other** — **39** candidates × **3** = **117** new combiner jobs |
| Total candidates after this turn | **66 / 66** |
| Windows | **early_oow**, **insample_ref**, **late_oow** |
| New local runs (extended wave) | **117** executed combiner directories |
| Total local runs discovered (`run_discovery_manifest.csv`) | **198** (**66×3**) |
| Local raw run root | `src/research/results/layer2_candidate_robustness_v1/local_runs/` |
| Manifests | `candidate_audit_run_manifest.csv` (last `run` invocation — **117** rows for extended wave), `run_execution_manifest.csv` (copy), `run_discovery_manifest.csv` (**198** discovered `run_*`) |
| Inventory | `remaining_candidate_inventory.{csv,md}`, `extended_audit_inventory.md` (`inventory` subcommand) |
| Postprocess | `python -m src.research.audit_l2_candidates_oow postprocess --candidate-root …/selected_candidates --output-root …/layer2_candidate_robustness_v1` |

## D. Candidate-level OOW audit

| Metric | Count (n=**66**) |
|--------|----------------:|
| total candidates audited | **66** |
| ROBUST_POSITIVE | **10** |
| INSAMPLE_ONLY | **8** |
| OOW_MIXED | **40** |
| OOW_NEGATIVE | **3** |
| TOO_SPARSE | **0** |
| HIGH_TURNOVER_FRAGILE | **0** |
| ANTI_PREDICTIVE_CANDIDATE | **5** |
| not audited | **0** |

**ROBUST_POSITIVE:** `CCI_EXTREME_SNAPBACK_002`, `CCI_EXTREME_SNAPBACK_003`, `GAP_ACCEPTANCE_FAILURE_001`–`004`, `PA_BUY_SELL_CLOSE_TREND_001`–`004`  
**ANTI_PREDICTIVE:** `MACD_MOMENTUM_TURN_003`, `MULTI_DAY_LEVEL_TRAP_001`–`004`  
**OOW_NEGATIVE:** `PA_TRADING_RANGE_BLS_HS_001`–`003`

## E. Family-level summary

| audit_family | candidates | robust_positive | insample_only | mixed+negative (mixed + OOW_NEG) | anti | action summary | key comment |
|----------------|-------------:|----------------:|--------------:|-----------------------------------:|-----:|------------------|-------------|
| vwap | 8 | 0 | 3 | 5 | 0 | watchlist / drop | no robust singletons |
| indicator | 19 | 2 | 4 | 12 | 1 | watchlist + tiny keep | CCI pocket only |
| opening_trap | 12 | 4 | 0 | 4 | 4 | split | GAP robust; MDLT anti |
| pa | 16 | 4 | 1 | 11 | 0 | mixed | close-trend strong; range templates weak |
| afternoon | 4 | 0 | 0 | 4 | 0 | watchlist | all mixed |
| other | 7 | 0 | 0 | 7 | 0 | watchlist | ORB / prior-close reclaim mixed |

## F. Candidate highlights

| Bucket | IDs (compact) |
|--------|----------------|
| Top robust (insample `total_r` order in `top_robust_candidates.csv`) | PA close-trend + GAP + CCI (see CSV) |
| Worst OOW sum (`worst_oow_candidates.csv`) | MACD/stoch/VWAP reclaim cluster |
| Positive **both** OOW windows | **9** names (`positive_both_oow_candidates.csv`) — includes **8** robust + `CCI_EXTREME_SNAPBACK_003` |
| KEEP_CORE (`policy_action`) | **10** |
| DROP_FROM_CORE | **8** |
| WATCHLIST_DIAGNOSTIC | **43** |
| REQUIRES_SIDE_FLIP_RESEARCH | **5** |

## G. VWAP / indicator / opening-trap / PA / afternoon-other interpretation

- **VWAP:** Still **zero** robust-positive; reclaim/reject **001**–**003** remain **insample-only**; fixed-profile VWAP weakness is **candidate-level**.
- **Indicator:** Only **CCI** **002**/**003** are robust; **MACD/RSI/Stoch/Supertrend** remain mostly mixed or insample-only; **MACD_003** anti-predictive.
- **Opening/trap:** **Gap acceptance failure** is **strong** OOW (but **four** YAMLs show **identical** metrics — dedupe for design). **Failed ORB** mixed. **Multi-day level trap** is a **clean anti-predictive cluster** (four-for-four).
- **PA:** **Buy/sell close trend** is the **standout** robust family; **failed range breakout trap** shows **catastrophic early_oow** on several IDs; **trading range BLS/HS** hits **`OOW_NEGATIVE`** on **001**–**003**.
- **Afternoon / other:** No robust hits — all **`OOW_MIXED`**.

## H. Robust l2_core policy v2

| Item | Value |
|------|-------|
| Policy docs | `l2_core_policy_v2.md`, `l2_core_policy_v2_candidate_actions.csv`, `l2_core_policy_v2_action_summary*.csv` |
| KEEP_CORE count | **10** |
| Families with KEEP_CORE | **3** (`indicator`, `opening_trap`, `pa`) |
| Robust core dry-run | **PASS** — `robust_core_dry_run/selected_candidates_manifest.csv`, `robust_core_dry_run_summary.md` |
| Caveat | **GAP** **001**–**004** are metric-identical in this audit — count as **one** effective signal for diversification |

## I. Side-flip / inverse status

| Question | Answer |
|----------|--------|
| Executable short replay? | **No** |
| Proxy meaning | **non_executable_sign_proxy** only |
| New anti-predictive vs slice | **`MULTI_DAY_LEVEL_TRAP_001`–`004`** added to research queue |
| Watchlist CSV | `side_flip/future_side_flip_watchlist.csv` |
| Inverse hypothesis | **Still unsupported** for production or promotion |

## J. Decision

**Exactly one:** **`CREATE_ROBUST_L2_CORE_V2_DESIGN`**

- **Rationale:** **66 / 66** audited; **198 / 198** metric rows **`OK`**.
- **Rationale:** **Ten** **`ROBUST_POSITIVE`** across **three** families; scripted dry-run **PASS**.
- **Rationale:** VWAP/indicator weakness is **real** but **not** universal — gap + PA templates provide OOW strength.
- **Rationale:** Side-flip remains **non-executable**; anti-predictive names are **research-only**.
- **Rationale:** Dedupe / overlap work is now the **design** bottleneck, not “run more audits” on this envelope.

## K. Explicit non-runs and risks

mini-WFO; full WFO; live/paper; SPY; Global L1 rerun; broad Global L2 grid; strategy signal edits; new feature primitives; edits to selected candidate YAMLs; `regime_router`; hard regime filters; production short support; OOW parameter optimization; `--use-signal-cache` on unsafe OneDrive roots; committing `local_runs/` / raw row-level trades / heavy artifacts; `git add .`

## L. Recommended next step

**Exactly one:** Author **`robust l2_core v2` design** (documentation + dedupe rules starting from `robust_core_dry_run/`, **no** Layer2 sweep / **no** YAML edits in that design-only pass unless separately scoped).
