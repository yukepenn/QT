# Tests and smoke checks

## Purpose

- **Unit tests** under `tests/` use **synthetic or small fixtures** and should **not** require Parquet or IBKR unless a test is explicitly documented as an integration/smoke test (none in CI by default).
- **Full Layer 1 / Layer 2 sweeps** are **not** unit tests and are **not** run by `pytest`.

## Test groups (by topic)

| Area | Example files |
|------|----------------|
| Metrics / drawdown | `test_metrics_drawdown.py` (if present), cost/R in `test_cost_as_r_metrics.py` |
| Execution validation | `test_execution_validation.py`, `test_combiner_execution.py` |
| Feature performance / concat refactor | `test_feature_performance_equivalence.py` |
| Feature no-lookahead | `test_feature_no_lookahead.py` |
| Feature key | `test_feature_key.py` |
| Strategy config validation | `test_strategy_config_validation.py` |
| Context key | `test_strategy_context_keys.py` |
| PA context cache scope | `test_pa_context_key_scope.py` |
| Strategy helper namespace (`common.pa` + shims) | `test_strategy_helper_namespace.py` |
| PA swing side-specific ages | `test_pa_swing_side_specific_primitives.py` |
| PA Brooks feature registry / feature_key | `test_pa_brooks_feature_registry.py` |
| PA Brooks bar primitives | `test_pa_bar_primitives.py` |
| PA Brooks swing primitives | `test_pa_swing_primitives.py` |
| PA regime / router features | `test_pa_regime_router_features.py` |
| PA magnet / level features | `test_pa_level_magnet_features.py` |
| PA common helpers | `test_pa_common.py` |
| PA required_features no LOOKAHEAD | `test_pa_required_features_no_lookahead.py` |
| Combiner behavior hash | `test_combiner_behavior.py` |
| Cost-as-R metrics | `test_cost_as_r_metrics.py` |
| Daily metrics | `test_daily_metrics.py` |
| Postprocess helpers | `test_combiner_postprocess.py` |
| Layer 1 candidate / raw-sweep signal diversity | `test_candidate_signal_diversity.py`, `test_select_diverse_candidates.py`, `test_sweep_result_signal_diversity.py`, `test_export_diverse_candidates_from_results.py` |

Run all:

```bash
python -m pytest -q
```

## Local smoke commands (light)

Run after substantive changes; **no** full sweeps, **no** IBKR pull:

```bash
python -m compileall -q src
python src/strategies/loader.py --list
python src/data/read_bars.py --asset equity --symbol QQQ --start 2020-01-01 --end 2020-01-31 --head 3
python src/features/build_features.py --asset equity --symbol QQQ --start 2020-01-01 --end 2020-01-31 --orb-open-minutes 15
python src/research/check_strategy_fast_parity.py --strategy failed_orb --asset equity --symbol QQQ --start 2020-01-01 --end 2020-01-31 --testing-config src/strategies/testing_parameters/failed_orb_focused.yaml --max-combos 2
python src/combiner/run.py --candidate-root src/research/results/layer1_all10_qqq_2020_20260430_v1/selected_candidates --config src/combiner/configs/layer2_qqq_2020_20260430_v2_relaxed.yaml --asset equity --symbol QQQ --start 2020-01-01 --end 2020-01-31 --candidate-set trap_family --top-per-strategy 1 --tag smoke --no-save
```

## Configuration

See root **`pytest.ini`**:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
```
