"""Documentation artifacts for Layer 1/2/3 connectivity."""

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1] / "docs"


def _read(name: str) -> str:
    return (_ROOT / name).read_text(encoding="utf-8")


def test_layer_flow_mentions_layers():
    text = _read("LAYER_FLOW.md").lower()
    assert "layer 1" in text
    assert "layer 2" in text
    assert "layer 3" in text


def test_design_docs_exist():
    for name in (
        "BACKTEST_SWEEP_DESIGN.md",
        "CANONICAL_COMBINER_DESIGN.md",
        "LEGACY_RESULTS_POLICY.md",
        "MAINLINE_LEGACY_SURGERY_PLAN.md",
    ):
        assert (_ROOT / name).is_file(), name


def test_layer_flow_csv_exists():
    assert (_ROOT / "LAYER_FLOW.csv").is_file()
