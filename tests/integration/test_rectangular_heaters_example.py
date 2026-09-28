"""Run the heater example and check independent power/temperature references."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_rectangular_heaters_example():
    root = Path(__file__).resolve().parents[2]
    process = subprocess.run(
        [sys.executable, str(root / "examples/rectangular_heaters.py")],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(process.stdout)
    assert [row["cell_count"] for row in report["mappings"]] == [4, 9, 20]
    for row in report["mappings"]:
        assert row["total_power_w"] == pytest.approx(12, rel=0, abs=5e-14)
    plate = report["heated_plate"]
    assert plate["cell_powers_w"] == pytest.approx([4, 8], rel=0, abs=2e-14)
    assert plate["temperatures_k"] == pytest.approx([301, 302], rel=0, abs=2e-12)
    assert plate["total_outward_power_w"] == pytest.approx(12, rel=0, abs=1e-10)
