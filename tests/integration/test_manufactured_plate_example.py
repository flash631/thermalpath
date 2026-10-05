"""Run the frozen manufactured-solution report as a standalone script."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_manufactured_plate_example():
    root = Path(__file__).resolve().parents[2]
    process = subprocess.run(
        [sys.executable, str(root / "examples/manufactured_plate.py")],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(process.stdout)
    assert report["grid_shape"] == [4, 3]
    assert len(report["cells"]) == 12
    assert report["heater_input_w"] == pytest.approx(208 / 45, rel=2e-14)
    assert report["continuum_total_outflow_w"] == pytest.approx(208 / 45, rel=2e-14)
    assert report["continuum_edge_outflow_w"] == pytest.approx(
        [32 / 45, 32 / 45, 8 / 5, 8 / 5], rel=2e-14
    )
    assert abs(report["imbalance_w"]) < 2e-11
    assert report["max_abs_temperature_error_k"] == pytest.approx(
        1.3449888280407, rel=0, abs=3e-9
    )
    # Exact rational matrix results, in x-first order; see the verification test.
    temperature_numerators = [
        3589862631290,
        3661545298030,
        3661545298030,
        3589862631290,
        3636032563550,
        3754945266250,
        3754945266250,
        3636032563550,
        3589862631290,
        3661545298030,
        3661545298030,
        3589862631290,
    ]
    power_numerators = [
        629,
        1115,
        1115,
        629,
        821,
        1307,
        1307,
        821,
        629,
        1115,
        1115,
        629,
    ]
    for row, temperature, power in zip(
        report["cells"], temperature_numerators, power_numerators, strict=True
    ):
        assert row["cell_input_w"] == pytest.approx(power / 2430, rel=2e-14)
        assert row["computed_k"] == pytest.approx(
            temperature / 11744694171, rel=0, abs=3e-9
        )
        assert row["temperature_error_k"] == pytest.approx(
            row["computed_k"] - row["continuum_center_k"], rel=0, abs=1e-13
        )
