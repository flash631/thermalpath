"""Fresh-process reproduction, retained adverse cases and deterministic replay."""

import csv
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from thermalpath.studies import replay_network_sweep


def test_example_reproduces_and_replays(tmp_path):
    script = Path(__file__).resolve().parents[2] / "examples/network_uncertainty.py"
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
    assert report["interpretation"] == "conditional model outputs, not safety bounds"
    assert report["physical_validation"] is False
    assert report["distribution"] == "independent_uniform"
    assert report["percentile_method"] == "linear"
    for name in ("study", "adverse_study"):
        study = report[name]
        assert study["seed"] == 2026
        assert len(study["samples"]) == study["count"]
        assert replay_network_sweep(study["cases_csv"]) == study["cases_csv"]
        for row in csv.DictReader(io.StringIO(study["cases_csv"])):
            case = json.loads(row["case_json"])
            p = case["nodes"][0]["power_w"]
            g = case["links"][0]["conductance_w_k"]
            if row["status"] == "ok":
                assert json.loads(row["temperatures_k_json"])["body"] == pytest.approx(
                    300 + p / g, abs=2e-12, rel=0
                )
            else:
                assert 300 + p / g <= 0
    assert report["study"]["failed_count"] == 0
    assert 0 < report["adverse_study"]["failed_count"] < 16
    assert report["adverse_study"]["percentiles_k"] == {}
