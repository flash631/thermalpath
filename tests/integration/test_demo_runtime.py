"""Check the timing example's reference gate and installed-package execution."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from examples.demo_runtime import check_result


@pytest.mark.parametrize("change", ["value", "unit", "case"])
def test_rejects_wrong_demo(change):
    data = {
        "case": "synthetic_series_stack",
        "interface_resistance": {"value": 0.05, "unit": "K/W"},
        "temperature": {"value": 363.9, "unit": "K"},
        "temperature_celsius": {"value": 90.75, "unit": "degC"},
        "power": {"value": 15.0, "unit": "W"},
    }
    if change == "case":
        data["case"] = "another_case"
    else:
        data["temperature"][change] = 300.0 if change == "value" else "degC"
    with pytest.raises(ValueError):
        check_result(data)


def test_runtime_example_from_unrelated_directory(tmp_path):
    script = Path(__file__).resolve().parents[2] / "examples/demo_runtime.py"
    completed = subprocess.run(
        [sys.executable, "-I", str(script)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    result = json.loads(completed.stdout)
    assert result["reference_checks"] == "passed"
    assert result["timing_scope"] == "process_start_import_calculation_json_exit"
    assert result["unit"] == "s"
    assert result["numerical_threads"] == 1
    assert len(result["samples"]) == 5
    ordered = sorted(result["samples"])
    assert 0 < result["minimum"] == ordered[0]
    assert result["median"] == ordered[2]
    assert result["maximum"] == ordered[-1]
