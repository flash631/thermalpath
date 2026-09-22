"""Execute the network example and compare its table with exact references."""

import csv
import io
import subprocess
import sys
from pathlib import Path

import pytest


def test_transient_example():
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, str(root / "examples/transient_network.py")],
        capture_output=True,
        text=True,
        check=True,
        cwd=root,
    )
    rows = list(csv.DictReader(io.StringIO(result.stdout)))
    assert len(rows) == 3
    assert [float(row["time_s"]) for row in rows] == [0, 1, 3]
    expected = [(300, 300), (3625 / 12, 3605 / 12), (46967 / 156, 47143 / 156)]
    for row, (a, b) in zip(rows, expected, strict=True):
        assert float(row["a_K"]) == pytest.approx(a, rel=0, abs=2e-12)
        assert float(row["b_K"]) == pytest.approx(b, rel=0, abs=2e-12)
        assert float(row["sink_K"]) == 300
    assert not result.stderr
