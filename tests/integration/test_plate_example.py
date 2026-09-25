"""Check the runnable plate example against an independent linear profile."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_plate_example():
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, str(root / "examples/steady_plate.py")],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(result.stdout)
    assert report["temperatures_k"] == pytest.approx(
        [905 / 3, 920 / 3, 315] * 2, rel=0, abs=2e-12
    )
    assert report["face_order"] == ["west", "east", "south", "north"]
    assert report["west_outward_power_w"] == pytest.approx(4, rel=0, abs=5e-11)
    assert report["east_outward_power_w"] == pytest.approx(-4, rel=0, abs=5e-11)
    for cell, q in enumerate([1, 1, 1, 3, 3, 3]):
        assert report["outward_face_powers_w"][cell] == pytest.approx(
            [q, -q, 0, 0], rel=0, abs=5e-11
        )
