"""CLI process behavior and independently derived SI results."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from thermalpath.cli import main

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "examples/cases/heater.json"


def invoke(*arguments):
    return subprocess.run(
        [sys.executable, "-m", "thermalpath.cli", *map(str, arguments)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_process_reference():
    result = invoke("run-network", CASE)
    assert result.returncode == 0
    assert result.stderr == ""
    data = json.loads(result.stdout)
    assert data["schema_version"] == 1
    assert data["kind"] == "steady_network_result"
    # P/G = 10/2 = 5 K, so T = 300 + 5 K; q = 2*5 = 10 W.
    assert data["temperatures_k"] == {"heater": 305.0, "bath": 300.0}
    assert data["link_powers_w"] == {"strap": 10.0}
    balance = data["heat_balance"]
    assert balance["node_residual_w"] == {"heater": 0.0}
    assert balance["boundary_power_w"] == {"bath": -10.0}
    assert balance["total_input_w"] == 10.0
    assert balance["total_output_w"] == 10.0
    assert balance["imbalance_w"] == 0.0


def test_main_direct_matches_process(capsys):
    assert main(["run-network", str(CASE)]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == invoke("run-network", CASE).stdout


def test_rational_reference_through_json(tmp_path):
    # Elimination: 3*Ta-Tb=610, -Ta+4*Tb=930, hence Ta=3370/11, Tb=3400/11.
    case = {
        "schema_version": 1,
        "nodes": [
            {"id": "a", "power_w": 10},
            {"id": "b", "power_w": -30},
            {"id": "cold", "fixed_temperature_k": 300},
            {"id": "warm", "fixed_temperature_k": 320},
        ],
        "links": [
            {"id": "ac", "node_a": "a", "node_b": "cold", "conductance_w_k": 2},
            {"id": "ab", "node_a": "a", "node_b": "b", "conductance_w_k": 1},
            {"id": "bw", "node_a": "b", "node_b": "warm", "conductance_w_k": 3},
        ],
    }
    path = tmp_path / "rational.json"
    path.write_text(json.dumps(case), encoding="utf-8")
    result = invoke("run-network", path)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["temperatures_k"]["a"] == pytest.approx(3370 / 11, abs=1e-11, rel=0)
    assert data["temperatures_k"]["b"] == pytest.approx(3400 / 11, abs=1e-11, rel=0)
    assert data["link_powers_w"] == pytest.approx(
        {"ac": 140 / 11, "ab": -30 / 11, "bw": -360 / 11}, abs=1e-10, rel=0
    )
    balance = data["heat_balance"]
    assert balance["total_input_w"] == pytest.approx(470 / 11, abs=2e-10, rel=0)
    assert balance["total_output_w"] == pytest.approx(470 / 11, abs=2e-10, rel=0)
    assert balance["imbalance_w"] == pytest.approx(0, abs=4e-10, rel=0)


def test_small_load_residual_is_visible(tmp_path):
    case = json.loads(CASE.read_text("utf-8"))
    case["nodes"][0]["power_w"] = 1e-20
    path = tmp_path / "small.json"
    path.write_text(json.dumps(case), encoding="utf-8")
    result = invoke("run-network", path)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["temperatures_k"]["heater"] == 300.0
    assert data["link_powers_w"]["strap"] == 0.0
    assert data["heat_balance"]["node_residual_w"]["heater"] == 1e-20
    assert data["heat_balance"]["imbalance_w"] == 1e-20


@pytest.mark.parametrize(
    "args", [[], ["wrong"], ["run-network"], ["run-network", str(CASE), "--bad"]]
)
def test_usage_exit_two(args):
    result = invoke(*args)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "usage:" in result.stderr


def test_help():
    result = invoke("--help")
    assert result.returncode == 0
    assert "run-network" in result.stdout
    assert not result.stderr


@pytest.mark.parametrize(
    "content",
    [
        b"{",
        b"\xff",
        b'{"schema_version":2,"nodes":[],"links":[]}',
        b'{"schema_version":1,"nodes":[{"id":"a","power_w":1}],"links":[]}',
    ],
)
def test_case_errors_no_success_output(tmp_path, capsys, content):
    path = tmp_path / "bad.json"
    path.write_bytes(content)
    assert main(["run-network", str(path)]) == 1
    output = capsys.readouterr()
    assert not output.out
    assert output.err.startswith("thermalpath:")
    result = invoke("run-network", path)
    assert result.returncode == 1
    assert not result.stdout
    assert "Traceback" not in result.stderr


def test_missing_file(tmp_path, capsys):
    path = tmp_path / "absent.json"
    assert main(["run-network", str(path)]) == 1
    assert not capsys.readouterr().out
    assert not path.exists()


def test_output_failure(monkeypatch, capsys):
    def failed_write(*args, **kwargs):
        raise OSError("output unavailable")

    monkeypatch.setattr(sys.stdout, "write", failed_write)
    assert main(["run-network", str(CASE)]) == 1
    assert "output unavailable" in capsys.readouterr().err
