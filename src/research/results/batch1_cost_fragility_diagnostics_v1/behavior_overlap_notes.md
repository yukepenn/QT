# Behavior overlap notes (Batch 1 Layer 2 v1)

From prior `candidate_overlap_matrix.csv` on the **un-tuned** 20-candidate universe:

- **Bollinger squeeze** YAMLs (`_001`…`_005`) share **very high same-bar overlap** (~479 bars): near-duplicate parameterizations.
- **RSI** candidates overlap heavily with each other on the same bar; once combined with squeeze, **squeeze wins priority** and RSI contributes few marginal fills.
- **Relaxed fade / exhaustion** add **trade count** and **selection conflicts** without improving **0.02 slippage** robustness on the squeeze-heavy stack.

This tuning pass targets **fewer, stricter squeeze rows** and a **cleaner RSI lane** so Layer 2 overlap and per-trade cost load improve.
