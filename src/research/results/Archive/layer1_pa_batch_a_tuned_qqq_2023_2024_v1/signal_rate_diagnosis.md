# Signal / trade-rate diagnosis — tuned v1 vs original Layer 1

## Manifest caveat

`sweep_manifest.csv` “best” rows use **highest finite `profit_factor`**. For **`pa_tight_channel_pullback`**, the top-PF row is a **single-trade** fingerprint (`profit_factor=inf`), which **masks** activity. Supplemental stats below use each strategy’s local `results.csv`.

## Summary

| Strategy | Verdict |
|----------|---------|
| pa_trading_range_bls_hs | **Major improvement:** positive **total R** on strict-export fingerprints; max trades ~415. |
| pa_failed_range_breakout_trap | **Improved** total R on PF-ranked row (~35 R vs ~3 R) and **better DD** vs original manifest; grid contains very high-R churn rows (~86 R @ 373 trades) that do not drive manifest “best PF”. |
| pa_tight_channel_pullback | **Signal rate up** (max **58** trades vs **14**), but **no** combo with **≥30 trades** passes **PF ≥ 1.05** and **total R ≥ 0** — **weak edge** after loosening. |
| pa_mtr_reversal | **Still sub-threshold:** max **12** trades / combo; **0** combos with **≥30** trades. |

## Original vs tuned (key numbers)

- **Trading range:** best total R **-6.9 → +25.6** (manifest PF-ranked row); strict candidates **0 → 5**.
- **Failed trap:** best total R **+2.8 → +34.9** (manifest row); max trades **331 → 378**; DD **~-47 → ~-43** (manifest).
- **Tight channel:** max trades **14 → 58**; among rows with **≥30** trades, best total R stays **deeply negative** (high churn / poor expectancy).
- **MTR:** max trades **1 → 12**; still **no** strict Layer-1-ready economics.
