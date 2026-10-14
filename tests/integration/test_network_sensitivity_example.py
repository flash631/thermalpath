"""Check the standalone sensitivity report and replay its exported inputs."""

import csv
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from thermalpath.studies import replay_network_sweep


def test_example_reproduces_and_contains_full_case_evidence(tmp_path):
    script = Path(__file__).resolve().parents[2] / "examples/network_sensitivity.py"
    outputs = [
        subprocess.run(
            [sys.executable, str(script)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        for _ in range(2)
    ]
    assert outputs[0] == outputs[1]
    report = json.loads(outputs[0])
    assert report["physical_validation"] is False
    assert report["reference_derivative_k2_w"] == -3
    assert report["absolute_errors_k2_w"][:3] == pytest.approx(
        [1 / 5, 1 / 21, 1 / 85], rel=0, abs=3e-12
    )
    assert report["absolute_errors_k2_w"][3] is None
    study = report["study"]
    estimates = study["estimates"]
    assert [row["status"] for row in estimates] == ["ok", "ok", "ok", "failed"]
    for text in [study["base_case_csv"], *(row["cases_csv"] for row in estimates)]:
        assert replay_network_sweep(text) == text
        for row in csv.DictReader(io.StringIO(text)):
            case = json.loads(row["case_json"])
            g = case["links"][0]["conductance_w_k"]
            if not g:
                assert row["status"] == "failed"
                continue
            assert json.loads(row["temperatures_k_json"]) == pytest.approx(
                {"a": 304 + 12 / g, "b": 304, "sink": 300}, rel=0, abs=2e-12
            )
            assert abs(float(row["imbalance_w"])) < 2e-12
            residuals = json.loads(row["linear_residual_w_json"])
            assert max(map(abs, residuals.values())) < 2e-12
