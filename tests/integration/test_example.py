"""Run the headless public example as an installed-package consumer."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_headless_example():
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, str(root / "examples" / "series_stack.py")],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    assert not result.stderr
    assert data["interface_resistance"]["value"] == pytest.approx(0.05)
    assert data["interface_resistance"]["unit"] == "K/W"
    assert data["temperature"]["value"] == pytest.approx(363.90)
    assert data["temperature"]["unit"] == "K"
    assert data["temperature_celsius"]["value"] == pytest.approx(90.75)
