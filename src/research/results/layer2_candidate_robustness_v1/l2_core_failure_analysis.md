# l2_core failure analysis (singleton replay — **full 66** candidates)

This document summarizes **fixed-profile-style** singleton combiner replays (default audit envelope `layer2_fixed_vwap_mtp2.yaml`) across **early_oow**, **insample_ref**, **late_oow**. It is **not** a combination-grid audit.

## 1. Summary after full l2_core audit

| robustness_label | count (n=66) |
|------------------|-------------:|
| OOW_MIXED | 40 |
| ROBUST_POSITIVE | 10 |
| INSAMPLE_ONLY | 8 |
| ANTI_PREDICTIVE_CANDIDATE | 5 |
| OOW_NEGATIVE | 3 |
| TOO_SPARSE / HIGH_TURNOVER_FRAGILE | 0 |

**Headline:** VWAP and broad indicator weakness seen in the first slice **generalize for those families**, but **do not** describe the full core: **gap acceptance failure** and **PA buy/sell close trend** contribute **eight** of **ten** robust-positive YAMLs.

## 2. VWAP failure analysis

**Eight** YAMLs, **zero** `ROBUST_POSITIVE`. **Three** reclaim/reject variants are **`INSAMPLE_ONLY`** (**001**–**003**); pullbacks and **004** skew **`OOW_MIXED`**.

**Conclusion:** Fixed-profile VWAP OOW pain is **candidate-level** on this slice, not only combiner weighting.

## 3. Indicator failure analysis

**Nineteen** YAMLs; only **CCI_EXTREME_SNAPBACK_002** and **003** are **`ROBUST_POSITIVE`**. **MACD** cluster is **`INSAMPLE_ONLY`** or catastrophic OOW; **`MACD_MOMENTUM_TURN_003`** is **`ANTI_PREDICTIVE_CANDIDATE`**. RSI / Stochastic / Supertrend are mostly **`OOW_MIXED`** or drops.

**Conclusion:** Treat **indicator mtp stacks** as **high structural risk** unless overlap and turnover are explicitly modeled; **CCI** is the only robust pocket here.

## 4. Opening / trap analysis (`opening_trap` audit family, **12** YAMLs)

- **`GAP_ACCEPTANCE_FAILURE_001`–`004`:** all **`ROBUST_POSITIVE`** with **identical** window `total_r` in this audit — treat as **one effective configuration** for diversity planning.
- **`FAILED_ORB_*`:** **`OOW_MIXED`** — no robust-positive under thresholds.
- **`MULTI_DAY_LEVEL_TRAP_001`–`004`:** all **`ANTI_PREDICTIVE_CANDIDATE`** (positive insample, strongly negative OOW with adequate counts).

**Conclusion:** “Opening trap” is **split**: gap-failure variants are strong; multi-day level trap behaves like a **fade** of the long signal on OOW.

## 5. PA analysis (**16** YAMLs)

- **`PA_BUY_SELL_CLOSE_TREND_001`–`004`:** **`ROBUST_POSITIVE`** with large positive OOW on both windows for **001**–**003** and strong early / modest late for **004**.
- **`PA_FAILED_RANGE_BREAKOUT_TRAP_*`:** mostly **`OOW_MIXED`** with **catastrophic early_oow** on several IDs (large negative `total_r_early_oow`).
- **`PA_TRADING_RANGE_BLS_HS_001`–`003`:** **`OOW_NEGATIVE`** under the heuristic; **005** is **`INSAMPLE_ONLY`**.

**Conclusion:** PA is **not** uniformly good; strength concentrates in **buy/sell close trend**; range/trap PA templates need **watchlist** treatment.

## 6. Afternoon / other analysis

- **`afternoon`** (**4**): all **`OOW_MIXED`** — no robust-positive.
- **`other`** (**7**, ORB continuation + prior close reclaim): all **`OOW_MIXED`** — no robust-positive.

## 7. Candidate vs combination failure

Singleton evidence shows **per-candidate** breakage for VWAP and most indicators **before** any combination overlap argument. **Gap** and **PA close trend** positives show **candidate-level** OOW resilience under the same envelope — combination toxicity remains a **secondary** concern for v2 design, not the sole explanation for all failures.

## 8. Family concentration / redundancy

- **GAP** quadruplet: **identical** metrics → **one** effective signal for diversification counts.
- **PA_BUY_SELL_CLOSE_TREND** **001**–**003** share **identical** early/late `total_r` in metrics export — near-duplicate parameter stems; **004** differs slightly on insample/late.

## 9. Turnover and avg-R decay

`HIGH_TURNOVER_FRAGILE` did **not** trigger for any candidate under current thresholds. High trade counts on some PA robust names are **not** auto-excluded — monitor **avg_r** vs turnover in future gates.

## 10. Is fixed-profile failure representative of all l2_core?

**No.** VWAP/indicator weakness is **real** but **not universal**: **`opening_trap`** (gap) and **`pa`** (close trend) contribute the majority of **`ROBUST_POSITIVE`** counts.

## 11. Implications for Layer2 candidate selection

- Promote **gap acceptance failure** and **PA buy/sell close trend** families into **v2 core design** **only** with explicit **dedupe** rules and **no** OOW tuning.
- Keep **VWAP** and non-CCI **indicator** names on **watchlist / drop** unless new evidence arrives from a **different** audit contract.
- **`MULTI_DAY_LEVEL_TRAP`** should **not** enter a long-only core without a **separate** executable short research track.
