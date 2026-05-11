from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.research.side_flip_diagnostic import main as side_flip_main


def test_side_flip_proxy_writes_csv(tmp_path: Path, monkeypatch) -> None:
    metrics = tmp_path / "m.csv"
    pd.DataFrame(
        [
            {
                "profile_id": "indicator_mtp1",
                "window_id": "early_oow",
                "total_r": -10.0,
                "trades": 1,
            }
        ]
    ).to_csv(metrics, index=False)
    outd = tmp_path / "sf"
    monkeypatch.chdir(tmp_path)
    rc = side_flip_main(["--metrics-csv", str(metrics), "--output-dir", str(outd), "--profiles", "indicator_mtp1"])
    assert rc == 0
    got = pd.read_csv(outd / "side_flip_metrics.csv")
    assert float(got.iloc[0]["side_flip_proxy_total_r"]) == 10.0
    assert "non-executable" in (outd / "side_flip_interpretation.md").read_text(encoding="utf-8").lower()
