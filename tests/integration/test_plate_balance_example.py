"""Check that the runnable report keeps an adverse balance visible."""

import json
import subprocess
import sys
from pathlib import Path


def test_plate_balance_example():
    root = Path(__file__).resolve().parents[2]
    process = subprocess.run(
        [sys.executable, str(root / "examples/plate_balance.py")],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(process.stdout)
    assert report["mixed"]["temperatures_k"] == [302]
    assert report["mixed"]["balance"]["heater_input_w"] == 10
    assert report["mixed"]["balance"]["broad_face_outflow_w"] == 8
    assert report["mixed"]["balance"]["imbalance_w"] == 0
    assert report["tiny_heater"]["balance"]["linear_residual_w"] == [0]
    assert report["tiny_heater"]["balance"]["cell_residual_w"] == [1e-20]
    assert report["tiny_heater"]["balance"]["imbalance_w"] == 1e-20
