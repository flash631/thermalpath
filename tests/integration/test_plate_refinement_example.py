"""Exercise the standalone report and recompute norms from its exported cells."""

import json
import math
import subprocess
import sys
from pathlib import Path

import pytest


def test_plate_refinement_example():
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, str(root / "examples/plate_refinement.py")],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(result.stdout)
    assert [r["grid_shape"] for r in report["grids"]] == [[4, 3], [8, 6], [16, 12]]
    for row in report["grids"]:
        errors = [c["computed_k"] - c["continuum_center_k"] for c in row["cells"]]
        assert len(errors) == math.prod(row["grid_shape"])
        assert [c["error_k"] for c in row["cells"]] == errors
        assert row["errors"] == pytest.approx(
            dict(
                l1_k=math.fsum(map(abs, errors)) / len(errors),
                l2_k=math.sqrt(math.fsum(e**2 for e in errors) / len(errors)),
                linf_k=max(map(abs, errors)),
            )
        )
        assert (
            row["relative_imbalance"] == abs(row["imbalance_w"]) / row["heater_input_w"]
        )
        assert math.fsum(c["cell_input_w"] for c in row["cells"]) == pytest.approx(
            208 / 45, rel=3e-14
        )
