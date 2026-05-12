# Strategies contract (audit)

- Strategies emit the **standard signal columns** (`sig_*`) defined in `strategy/base.py`.
- `metadata.yaml` + `metadata.py` provide **family / playbook / management defaults** via `get_strategy_metadata`.
- Canonical column mapping for execution is documented in `SIGNAL_CONTRACT.md`.

Audit table: `docs/STRATEGIES_AUDIT.csv` (loader list × metadata merge).
