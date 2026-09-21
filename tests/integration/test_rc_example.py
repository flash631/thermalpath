"""Check the documented synthetic RC example through a separate process."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_rc_example() -> None:
    result = subprocess.run(
        [sys.executable, "examples/rc_step.py"],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=True,
    )
    output = json.loads(result.stdout)
    assert output["temperature_k"] == pytest.approx(306.3212055882856, abs=2e-13, rel=0)
    assert output["stored_energy_change_j"] == pytest.approx(
        63.2120558828558, abs=2e-12, rel=0
    )
    assert output["time_constant_s"] == 20
    assert output["boundary_power_w"] + output["storage_power_w"] == 5
    assert result.stderr == ""
