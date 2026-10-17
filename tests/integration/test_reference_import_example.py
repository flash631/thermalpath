"""Run the reference import example from an unrelated directory."""

import json
import os
import subprocess
import sys
from pathlib import Path


def test_reference_example(tmp_path):
    root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        env[name] = "1"
    run = subprocess.run(
        [sys.executable, str(root / "examples/reference_import.py")],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    output = json.loads(run.stdout)
    assert output["kind"] == "synthetic"
    assert output["mode"] == "transient"
    assert output["count"] == 4
    assert output["times_s"] == [0, 2.5, 10, 2.5]
    assert output["temperatures_k"] == [300, 300.625, 302.5, 300.625]
    assert output["license"] == "MIT; see LICENSE"
    assert len(output["csv_sha256"]) == len(output["metadata_sha256"]) == 64
