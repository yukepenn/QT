# l2_core failure analysis (singleton replay, vwap + indicator slice)

## 1. VWAP candidate failure analysis

Across **8** VWAP-class YAMLs under singleton replay (same combiner envelope as fixed-profile VWAP mtp2):

- **Zero** candidates received **`ROBUST_POSITIVE`**.
- **Three** reclaim-reject variants are **`INSAMPLE_ONLY`** (`VWAP_RECLAIM_REJECT_001`–`003`): strong 2023–2024 replay, materially negative on both OOW windows in this audit.
- Pullback variants are mostly **`OOW_MIXED`** (one OOW window better than the other under the heuristic).

**Interpretation:** VWAP **combination** failure in fixed-profile OOW is **not** explained by one bad apple alone; the VWAP slice shows **broad** insample-vs-OOW decay at the candidate level.

## 2. Indicator candidate failure analysis

Across **19** indicator YAMLs:

- **Two** CCI snapback rows are **`ROBUST_POSITIVE`** (`CCI_EXTREME_SNAPBACK_002`, `003`) under this heuristic — the only robust-positive hits in the audited slice.
- **Four** MACD rows are **`INSAMPLE_ONLY`** or mixed; **`MACD_MOMENTUM_TURN_003`** is flagged **`ANTI_PREDICTIVE_CANDIDATE`** (weak insample vs strongly negative OOW with adequate trade counts).
- RSI / Supertrend / Stochastic rows skew **`OOW_MIXED`** or **`INSAMPLE_ONLY`** rather than clean OOW strength.

**Interpretation:** indicator **mtp** fixed profiles combine many names; singleton evidence shows **most** individuals still fail cross-window tests, while a **narrow** CCI subset looks less bad. Combination toxicity (overlap, trade caps) remains plausible but **cannot** rescue the broad indicator basket on its own.

## 3. Family-level comparison

| audit_family | candidates | robust_positive | dominant failure mode |
|----------------|-------------|-----------------|------------------------|
| vwap | 8 | 0 | insample_only + mixed |
| indicator | 19 | 2 | mixed + insample_only |

Opening-trap / PA / afternoon families were **not** audited in v1 pack.

## 4. High-turnover / avg-R decay

`HIGH_TURNOVER_FRAGILE` did **not** trigger in this slice under current thresholds (insample turnover + avg_r gate). Indicator turnover stress seen in **mtp3** fixed profiles is primarily a **combination** phenomenon; candidate-level singletons still show weak OOW without always tripping the turnover-fragile bucket.

## 5. Correlation / redundancy

No pairwise signal correlation matrix was computed in v1 (would require additional diagnostics or cached signal arrays). Qualitative overlap remains a risk for indicator **mtp2/3** profiles.

## 6. Implications for l2_core policy

- VWAP names should remain **watchlist / diagnostic** until **per-candidate** OOW stability exists.
- Indicator **mtp** stacks should be **capped** unless backed by candidate-level audits showing non-redundant edges.
- Extend audit to **PA** and **opening_trap** before any “robust core v2” construction.
