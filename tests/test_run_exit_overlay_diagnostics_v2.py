"""Smoke tests for exit overlay diagnostics v2 runner (no heavy data)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from src.research.run_exit_overlay_diagnostics_v2 import main


def test_main_alignment_dry_run() -> None:
    with tempfile.TemporaryDirectory() as td:
        panel = Path(td) / "panel.csv"
        panel.write_text("profile_id,window\nx,early_oow\n", encoding="utf-8")
        out = Path(td) / "out"
        code = main(
            [
                "--local-panel",
                str(panel),
                "--output-root",
                str(out),
                "--mode",
                "alignment",
                "--dry-run",
            ]
        )
        assert code == 0
        assert (out / "alignment_dry_run_plan.csv").is_file()
