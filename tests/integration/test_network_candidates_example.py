"""Run the public comparison example and check its independent scalar values."""

import csv
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def test_candidate_example_is_repeatable_and_retains_all_outcomes():
    root = Path(__file__).resolve().parents[2]
    env = dict(
        os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1"
    )
    command = [sys.executable, str(root / "examples/network_candidates.py")]
    first = subprocess.run(command, check=True, capture_output=True, text=True, env=env)
    second = subprocess.run(
        command, check=True, capture_output=True, text=True, env=env
    )
    assert first.stdout == second.stdout
    result = json.loads(first.stdout)
    assert [a["status"] for a in result["assessments"]] == [
        "exceeds",
        "borderline",
        "meets",
        "meets",
        "failed",
    ]
    assert [a["minimum_margin_k"] for a in result["assessments"]] == [
        -5,
        0,
        2.5,
        2.5,
        None,
    ]
    rows = list(csv.DictReader(io.StringIO(result["cases_csv"])))
    for row, conductance in zip(rows[:4], [1, 2, 4, 4], strict=True):
        assert json.loads(row["temperatures_k_json"])["body"] == pytest.approx(
            300 + 10 / conductance, abs=2e-12, rel=0
        )
    assert rows[4]["status"] == "failed" and rows[4]["error"]
