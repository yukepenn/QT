"""Tests for export_diverse_candidates_from_results."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[1]


def test_export_writes_yaml_and_csv():
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        ct = td_path / "ct.csv"
        cx = td_path / "cx.csv"
        base = (
            "strategy,asset,symbol,root,contract,start,end,params_json,trades,profit_factor,total_r,"
            "max_drawdown_r,avg_bars_held,eod_count,end_of_data_count,win_rate,total_net_pnl,avg_r,"
            "avg_net_pnl,max_drawdown_pnl,stop_count,target_count,max_hold_count\n"
        )
        ct.write_text(
            base
            + "pa_buy_sell_close_trend,equity,QQQ,,,2023-01-01,2024-12-31,{},40,1.2,5,-5,10,0,0,0.5,1,0.1,0.1,-1,10,10,0\n",
            encoding="utf-8",
        )
        cx.write_text(
            base
            + "pa_climax_reversal,equity,QQQ,,,2023-01-01,2024-12-31,{},40,1.2,3,-4,8,0,0,0.5,1,0.1,0.1,-1,5,5,0\n",
            encoding="utf-8",
        )
        div = td_path / "div"
        div.mkdir()
        pd.DataFrame(
            [
                {
                    "source_row_index": 0,
                    "candidate_score": 1.5,
                    "hash_pick_rank": 1,
                    "pure_signal_hash": "aaa",
                    "pure_signal_hash_key": "aaa",
                },
                {
                    "source_row_index": 0,
                    "candidate_score": 1.4,
                    "hash_pick_rank": 2,
                    "pure_signal_hash": "aaa",
                    "pure_signal_hash_key": "aaa",
                },
            ]
        ).to_csv(div / "unique_signal_hash_candidates_pa_buy_sell_close_trend.csv", index=False)
        pd.DataFrame(
            [
                {
                    "source_row_index": 0,
                    "candidate_score": 1.2,
                    "hash_pick_rank": 1,
                    "pure_signal_hash": "bbb",
                    "pure_signal_hash_key": "bbb",
                },
            ]
        ).to_csv(div / "unique_signal_hash_candidates_pa_climax_reversal.csv", index=False)

        out = td_path / "repaired"
        r = subprocess.run(
            [
                sys.executable,
                str(_ROOT / "src/research/export_diverse_candidates_from_results.py"),
                "--close-trend-results-csv",
                str(ct),
                "--climax-results-csv",
                str(cx),
                "--raw-diversity-dir",
                str(div),
                "--output-root",
                str(out),
                "--top-close-trend",
                "1",
                "--top-climax",
                "1",
            ],
            cwd=str(_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert r.returncode == 0, r.stderr
        yfiles = list((out / "selected_candidates").glob("*.yaml"))
        assert len(yfiles) == 2
        doc = yaml.safe_load((out / "selected_candidates" / yfiles[0].name).read_text(encoding="utf-8"))
        assert "candidate_id" in doc
        sc = pd.read_csv(out / "selected_candidates.csv")
        assert len(sc) == 2
        assert (out / "CLIMAX_CAPPED_ONE_PATH.md").is_file()
