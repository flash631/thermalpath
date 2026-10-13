"""Run the example in fresh processes and independently inspect exported cases."""

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_example_reproduces_and_preserves_existing_file(tmp_path):
    script = Path(__file__).resolve().parents[2] / "examples/network_sweep.py"
    outputs = []
    for name in ("first.csv", "second.csv"):
        target = tmp_path / name
        run = subprocess.run(
            [sys.executable, str(script), str(target)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=True,
        )
        assert json.loads(run.stdout) == {
            "cases": 9,
            "successful": 6,
            "failed": 3,
            "max_abs_imbalance_w": 0.0,
            "replay_matches": True,
        }
        outputs.append(target.read_bytes())
        with target.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        for index, row in enumerate(rows):
            assert int(row["case_index"]) == index
            case = json.loads(row["case_json"])
            power = (0, 10, 20)[index // 3]
            conductance = (1, 2, 0)[index % 3]
            assert case["nodes"][0]["power_w"] == power
            assert case["links"][0]["conductance_w_k"] == conductance
            if conductance:
                temperatures = json.loads(row["temperatures_k_json"])
                assert temperatures["body"] == pytest.approx(
                    300 + power / conductance, rel=0, abs=1e-12
                )
                assert json.loads(row["link_powers_w_json"])["path"] == pytest.approx(
                    power, rel=0, abs=1e-12
                )
            else:
                assert row["status"] == "failed"
                assert row["temperatures_k_json"] == ""
    assert outputs[0] == outputs[1]
    run = subprocess.run(
        [sys.executable, str(script), str(target)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert run.returncode != 0
    assert target.read_bytes() == outputs[-1]
