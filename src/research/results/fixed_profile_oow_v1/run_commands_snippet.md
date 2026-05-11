# Example combiner runs (legacy snippet)

**Prefer:** `run_commands_multiline.md`, `run_commands_powershell.ps1`, or `python -m src.research.fixed_profile_oow run …` (see `execution_runbook.md`). The blocks below use backslash continuation and can be awkward in PowerShell.

Adjust `--end` to your latest available QQQ date after running `inspect-data`.

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_vwap_mtp2.yaml --asset equity --symbol QQQ \
  --start 2020-01-01 --end 2022-12-31 --candidate-set vwap_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\vwap_mtp2\early_oow

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_vwap_mtp2.yaml --asset equity --symbol QQQ \
  --start 2023-01-01 --end 2024-12-31 --candidate-set vwap_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\vwap_mtp2\insample_ref

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_vwap_mtp2.yaml --asset equity --symbol QQQ \
  --start 2025-01-01 --end 2026-04-30 --candidate-set vwap_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\vwap_mtp2\late_oow

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_vwap_mtp2.yaml --asset equity --symbol QQQ \
  --start 2020-01-01 --end 2026-04-30 --candidate-set vwap_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\vwap_mtp2\full_available

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_vwap_mtp1.yaml --asset equity --symbol QQQ \
  --start 2020-01-01 --end 2022-12-31 --candidate-set vwap_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\vwap_mtp1\early_oow

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_vwap_mtp1.yaml --asset equity --symbol QQQ \
  --start 2023-01-01 --end 2024-12-31 --candidate-set vwap_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\vwap_mtp1\insample_ref

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_vwap_mtp1.yaml --asset equity --symbol QQQ \
  --start 2025-01-01 --end 2026-04-30 --candidate-set vwap_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\vwap_mtp1\late_oow

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_vwap_mtp1.yaml --asset equity --symbol QQQ \
  --start 2020-01-01 --end 2026-04-30 --candidate-set vwap_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\vwap_mtp1\full_available

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp1.yaml --asset equity --symbol QQQ \
  --start 2020-01-01 --end 2022-12-31 --candidate-set indicator_completion_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp1\early_oow

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp1.yaml --asset equity --symbol QQQ \
  --start 2023-01-01 --end 2024-12-31 --candidate-set indicator_completion_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp1\insample_ref

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp1.yaml --asset equity --symbol QQQ \
  --start 2025-01-01 --end 2026-04-30 --candidate-set indicator_completion_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp1\late_oow

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp1.yaml --asset equity --symbol QQQ \
  --start 2020-01-01 --end 2026-04-30 --candidate-set indicator_completion_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp1\full_available

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp2.yaml --asset equity --symbol QQQ \
  --start 2020-01-01 --end 2022-12-31 --candidate-set indicator_completion_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp2\early_oow

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp2.yaml --asset equity --symbol QQQ \
  --start 2023-01-01 --end 2024-12-31 --candidate-set indicator_completion_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp2\insample_ref

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp2.yaml --asset equity --symbol QQQ \
  --start 2025-01-01 --end 2026-04-30 --candidate-set indicator_completion_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp2\late_oow

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp2.yaml --asset equity --symbol QQQ \
  --start 2020-01-01 --end 2026-04-30 --candidate-set indicator_completion_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp2\full_available

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp3.yaml --asset equity --symbol QQQ \
  --start 2020-01-01 --end 2022-12-31 --candidate-set indicator_completion_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp3\early_oow

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp3.yaml --asset equity --symbol QQQ \
  --start 2023-01-01 --end 2024-12-31 --candidate-set indicator_completion_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp3\insample_ref

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp3.yaml --asset equity --symbol QQQ \
  --start 2025-01-01 --end 2026-04-30 --candidate-set indicator_completion_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp3\late_oow

python -m src.combiner.run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates \
  --config src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp3.yaml --asset equity --symbol QQQ \
  --start 2020-01-01 --end 2026-04-30 --candidate-set indicator_completion_core \
  --output-root src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp3\full_available

