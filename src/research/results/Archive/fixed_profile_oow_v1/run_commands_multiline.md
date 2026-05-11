# Fixed-profile combiner commands

Do **not** pass `--use-signal-cache` on unsafe OneDrive roots. These lines omit it (combiner default off unless YAML enables).

## vwap_mtp2 — early_oow

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_vwap_mtp2.yaml' --asset equity --symbol QQQ --start 2020-01-01 --end 2022-12-31 --candidate-set vwap_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\vwap_mtp2\early_oow' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```

## vwap_mtp2 — insample_ref

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_vwap_mtp2.yaml' --asset equity --symbol QQQ --start 2023-01-01 --end 2024-12-31 --candidate-set vwap_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\vwap_mtp2\insample_ref' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```

## vwap_mtp2 — late_oow

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_vwap_mtp2.yaml' --asset equity --symbol QQQ --start 2025-01-01 --end 2026-04-30 --candidate-set vwap_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\vwap_mtp2\late_oow' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```

## vwap_mtp2 — full_available

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_vwap_mtp2.yaml' --asset equity --symbol QQQ --start 2020-01-01 --end 2026-04-30 --candidate-set vwap_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\vwap_mtp2\full_available' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```

## vwap_mtp1 — early_oow

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_vwap_mtp1.yaml' --asset equity --symbol QQQ --start 2020-01-01 --end 2022-12-31 --candidate-set vwap_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\vwap_mtp1\early_oow' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```

## vwap_mtp1 — insample_ref

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_vwap_mtp1.yaml' --asset equity --symbol QQQ --start 2023-01-01 --end 2024-12-31 --candidate-set vwap_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\vwap_mtp1\insample_ref' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```

## vwap_mtp1 — late_oow

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_vwap_mtp1.yaml' --asset equity --symbol QQQ --start 2025-01-01 --end 2026-04-30 --candidate-set vwap_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\vwap_mtp1\late_oow' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```

## vwap_mtp1 — full_available

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_vwap_mtp1.yaml' --asset equity --symbol QQQ --start 2020-01-01 --end 2026-04-30 --candidate-set vwap_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\vwap_mtp1\full_available' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```

## indicator_mtp1 — early_oow

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp1.yaml' --asset equity --symbol QQQ --start 2020-01-01 --end 2022-12-31 --candidate-set indicator_completion_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp1\early_oow' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```

## indicator_mtp1 — insample_ref

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp1.yaml' --asset equity --symbol QQQ --start 2023-01-01 --end 2024-12-31 --candidate-set indicator_completion_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp1\insample_ref' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```

## indicator_mtp1 — late_oow

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp1.yaml' --asset equity --symbol QQQ --start 2025-01-01 --end 2026-04-30 --candidate-set indicator_completion_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp1\late_oow' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```

## indicator_mtp1 — full_available

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp1.yaml' --asset equity --symbol QQQ --start 2020-01-01 --end 2026-04-30 --candidate-set indicator_completion_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp1\full_available' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```

## indicator_mtp2 — early_oow

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp2.yaml' --asset equity --symbol QQQ --start 2020-01-01 --end 2022-12-31 --candidate-set indicator_completion_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp2\early_oow' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```

## indicator_mtp2 — insample_ref

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp2.yaml' --asset equity --symbol QQQ --start 2023-01-01 --end 2024-12-31 --candidate-set indicator_completion_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp2\insample_ref' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```

## indicator_mtp2 — late_oow

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp2.yaml' --asset equity --symbol QQQ --start 2025-01-01 --end 2026-04-30 --candidate-set indicator_completion_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp2\late_oow' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```

## indicator_mtp2 — full_available

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp2.yaml' --asset equity --symbol QQQ --start 2020-01-01 --end 2026-04-30 --candidate-set indicator_completion_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp2\full_available' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```

## indicator_mtp3 — early_oow

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp3.yaml' --asset equity --symbol QQQ --start 2020-01-01 --end 2022-12-31 --candidate-set indicator_completion_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp3\early_oow' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```

## indicator_mtp3 — insample_ref

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp3.yaml' --asset equity --symbol QQQ --start 2023-01-01 --end 2024-12-31 --candidate-set indicator_completion_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp3\insample_ref' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```

## indicator_mtp3 — late_oow

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp3.yaml' --asset equity --symbol QQQ --start 2025-01-01 --end 2026-04-30 --candidate-set indicator_completion_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp3\late_oow' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```

## indicator_mtp3 — full_available

```powershell
'C:\Users\Yuke Zhang\AppData\Local\Programs\Python\Python311\python.exe' -m src.combiner.run --candidate-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\layer1_global_qqq_2023_2024_v2\selected_candidates_l2_core\selected_candidates' --config 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\configs\layer2_fixed_indicator_mtp3.yaml' --asset equity --symbol QQQ --start 2020-01-01 --end 2026-04-30 --candidate-set indicator_completion_core --output-root 'D:\OneDrive - Washington University in St. Louis\QT\src\research\results\fixed_profile_oow_v1\local_runs\indicator_mtp3\full_available' --tag fixed_profile --top-per-strategy 3 --data-dir data/raw/ibkr --no-detailed
```
