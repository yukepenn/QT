# Features contract (audit)

- Feature modules must be **no-lookahead** at decision time.
- `build_features` owns deterministic column sets keyed by `feature_key`.
- Heavy Numba acceleration belongs behind parity tests (not expanded in this reset).

Audit table: `FEATURES_AUDIT.csv`.
