"""Run the two-material example against the independent continuum solution."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_layered_plate_example():
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, str(root / "examples/layered_plate.py")],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(result.stdout)
    assert report["temperatures_k"] == pytest.approx(
        [355, 335, 950 / 3, 920 / 3] * 2, rel=0, abs=2e-12
    )
    for name in ("interface_from_left_k", "interface_from_right_k"):
        assert report[name] == pytest.approx(320, rel=0, abs=1e-10)
    assert report["eastward_heat_flux_w_m2"] == pytest.approx(40, rel=0, abs=2e-10)
    assert report["east_outward_power_w"] == pytest.approx(30, rel=0, abs=1e-10)
