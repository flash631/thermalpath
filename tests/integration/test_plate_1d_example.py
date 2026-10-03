"""Keep continuum error visible in the runnable one-dimensional report."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_plate_1d_example():
    root = Path(__file__).resolve().parents[2]
    process = subprocess.run(
        [sys.executable, str(root / "examples/plate_1d.py")],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(process.stdout)
    assert report["heater_input_w"] == 24
    assert abs(report["imbalance_w"]) < 2e-11
    for row, values in zip(
        report["cells"],
        [(0.5, 303, 302.625, 0.375), (2.5, 309, 305.625, 3.375)],
        strict=True,
    ):
        x, computed, continuum, error = values
        assert row["x_m"] == x
        assert row["computed_k"] == pytest.approx(computed, rel=0, abs=2e-12)
        assert row["continuum_center_k"] == continuum
        assert row["predicted_offset_k"] == error
        assert row["temperature_error_k"] == pytest.approx(error, rel=0, abs=2e-12)
    assert report["cells"][0]["outward_face_powers_w"] == pytest.approx(
        [12, -6, 0, 0], rel=0, abs=1e-11
    )
    assert report["cells"][1]["outward_face_powers_w"] == pytest.approx(
        [6, 12, 0, 0], rel=0, abs=1e-11
    )
