"""Run the refinement report and check it with rational discrete temperatures."""

import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest


def test_refinement_example():
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, str(root / "examples/transient_refinement.py")],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(result.stdout)
    assert report["final_time_s"] == 20
    assert report["exact_temperature_k"] == pytest.approx(
        306.3212055882856, rel=0, abs=1e-13
    )
    assert len(report["grids"]) == 4
    for count, row in zip((5, 10, 20, 40), report["grids"], strict=True):
        expected = float(310 - 10 * Fraction(count, count + 1) ** count)
        assert row["step_s"] == 20 / count
        assert row["final_temperature_k"] == pytest.approx(expected, rel=0, abs=2e-11)
        assert row["source_j"] == 100
        assert row["storage_j"] == pytest.approx(
            10 * (expected - 300), rel=0, abs=2e-10
        )
        assert row["boundary_j"] == pytest.approx(
            row["storage_j"] - 100, rel=0, abs=2e-10
        )
        assert row["max_step_imbalance_j"] < 5e-11
    assert report["grids"][0]["observed_order"] is None
    assert all(0.93 < r["observed_order"] < 1.01 for r in report["grids"][1:])
    assert not result.stderr
