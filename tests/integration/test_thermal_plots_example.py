"""Export in fresh headless processes and check figures against their source data."""

import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image


def test_headless_example_is_replayable_and_does_not_clobber(tmp_path):
    script = Path(__file__).resolve().parents[2] / "examples/thermal_plots.py"
    environment = dict(os.environ, MPLBACKEND="Agg", DISPLAY="", PYTHONHASHSEED="0")
    manifests = []
    for index in range(2):
        output = tmp_path / f"run{index}"
        result = subprocess.run(
            [sys.executable, str(script), str(output)],
            cwd=tmp_path,
            env=environment,
            capture_output=True,
            text=True,
            check=True,
        )
        manifest = json.loads(result.stdout)
        assert manifest == json.loads((output / "manifest.json").read_text("utf-8"))
        assert set(manifest["sha256"]) == {
            "inputs.json",
            "temperature.png",
            "transient.png",
            "errors.png",
        }
        for name, expected in manifest["sha256"].items():
            assert hashlib.sha256((output / name).read_bytes()).hexdigest() == expected
            if name.endswith(".png"):
                with Image.open(output / name) as image:
                    image.verify()
        manifests.append(manifest)
    assert manifests[0] == manifests[1]
    data = json.loads((tmp_path / "run0/inputs.json").read_text("utf-8"))
    transient = data["transient"]
    assert transient["times_s"] == list(range(21))
    numeric, exact = transient["temperatures_k"].values()
    # Independent scalar BE recurrence and exponential, not production helpers.
    for i, (actual, reference) in enumerate(zip(numeric, exact, strict=True)):
        assert actual == pytest.approx(310 - 10 * (20 / 21) ** i, abs=2e-11, rel=0)
        assert reference == pytest.approx(
            310 - 10 * math.exp(-i / 20), abs=2e-12, rel=0
        )
    assert data["errors"]["spacings_m"] == [0.015, 0.0075, 0.00375]
    assert data["errors"]["errors_k"]["Maximum"] == pytest.approx(
        [1.344988828040755, 0.443620351229, 0.125126977406], abs=2e-10, rel=0
    )
    plate = data["temperature"]
    assert len(plate["x_edges_m"]) == 17
    assert len(plate["y_edges_m"]) == 13
    computed, continuum = plate["fields_k"].values()
    assert len(computed) == len(continuum) == 192
    max_error = max(abs(a - b) for a, b in zip(computed, continuum, strict=True))
    assert max_error == data["errors"]["errors_k"]["Maximum"][-1]
    repeated = subprocess.run(
        [sys.executable, str(script), str(tmp_path / "run0")],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert repeated.returncode != 0
    for name, expected in manifests[0]["sha256"].items():
        assert (
            hashlib.sha256((tmp_path / "run0" / name).read_bytes()).hexdigest()
            == expected
        )
