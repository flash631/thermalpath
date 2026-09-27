"""Execute the strip example and compare its output to continuum arithmetic."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_plate_boundaries_example():
    root = Path(__file__).resolve().parents[2]
    process = subprocess.run(
        [sys.executable, str(root / "examples/plate_boundaries.py")],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(process.stdout)
    assert report["temperatures_k"] == pytest.approx([314.5, 307] * 2, rel=0, abs=2e-12)
    assert report["west_outward_power_w"] == -10
    assert report["east_outward_power_w"] == pytest.approx(10, rel=0, abs=5e-11)
    assert report["east_surface_temperature_k"] == pytest.approx(302, rel=0, abs=5e-11)
    assert report["broad_face_powers_w"] == [0] * 4
