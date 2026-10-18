"""Exercise the public comparison example from an unrelated directory."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def test_example_retains_missing_excluded_and_unused_values(tmp_path):
    root = Path(__file__).resolve().parents[2]
    env = dict(
        os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1"
    )
    command = [sys.executable, str(root / "examples/reference_comparison.py")]
    first = subprocess.run(
        command, cwd=tmp_path, env=env, capture_output=True, text=True, check=True
    )
    second = subprocess.run(
        command, cwd=tmp_path, env=env, capture_output=True, text=True, check=True
    )
    assert first.stdout == second.stdout
    result = json.loads(first.stdout)
    assert result["kind"] == "synthetic"
    assert [r["status"] for r in result["rows"]] == [
        "matched",
        "matched",
        "missing",
        "excluded",
    ]
    assert [r["residual_k"] for r in result["rows"]] == [3, -4, None, None]
    assert (
        result["matched_count"],
        result["missing_count"],
        result["excluded_count"],
    ) == (2, 1, 1)
    assert result["rmse_k"] == pytest.approx(3.5355339059327378, abs=1e-14, rel=0)
    assert result["unused_predictions"][0]["time_s"] == 20
    assert len(result["csv_sha256"]) == len(result["metadata_sha256"]) == 64
