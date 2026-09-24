"""Execute the synthetic geometry example against dimensional references."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_grid_example():
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, str(root / "examples/rectangular_grid.py")],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(result.stdout)
    assert report["cell_count"] == 6
    for key in ("domain_area_m2", "sum_cell_areas_m2"):
        assert report[key] == pytest.approx(0.0024, rel=5e-15, abs=0)
    for key in ("domain_volume_m3", "sum_cell_volumes_m3"):
        assert report[key] == pytest.approx(0.0000048, rel=5e-15, abs=0)
    first = report["cells"][0]
    assert first["center_m"] == [0.005, 0.005]
    assert first["neighbors_wesn"] == [None, 1, None, 3]
    assert first["face_areas_wesn_m2"] == pytest.approx([0.00002] * 4, rel=5e-15, abs=0)
    assert report["cells"][5]["indices_xy"] == [2, 1]
    assert report["cells"][5]["area_m2"] == pytest.approx(0.0009, rel=5e-15, abs=0)
