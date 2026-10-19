"""Exercise reproducibility and retained failures in the fixed study."""

import json
import subprocess
import sys
from pathlib import Path

from examples import heat_spreader as case

ROOT = Path(__file__).resolve().parents[2]


def test_example_repeats_exactly():
    command = [sys.executable, str(ROOT / "examples/heat_spreader.py")]
    first = subprocess.run(command, check=True, capture_output=True, text=True).stdout
    second = subprocess.run(command, check=True, capture_output=True, text=True).stdout
    assert first == second
    report = json.loads(first)
    assert report["completed_count"] == 18
    assert (
        len(report["candidates"][-1]["scenarios"][-1]["grids"][-1]["temperatures_k"])
        == 384
    )


def test_one_failure_is_retained_and_blocks_only_its_scenario(monkeypatch):
    original = case.solve_plate
    calls = 0

    def failing_once(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ValueError("synthetic solve failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(case, "solve_plate", failing_once)
    report = case.study()
    assert calls == 18
    assert report["failed_count"] == 1
    assert report["completed_count"] == 17
    failed = report["candidates"][0]["scenarios"][0]
    assert failed["grids"][1]["error"] == "synthetic solve failure"
    assert failed["classification"] == "unknown"
    assert failed["finest_margin_k"] is None
    assert failed["last_peak_change_k"] is None
    assert not failed["numerical_checks_passed"]
    assert report["candidates"][2]["scenarios"][1]["classification"] == "meets"


def test_failed_balance_blocks_classification(monkeypatch):
    monkeypatch.setattr(case, "BALANCE_TOLERANCE_W", 0)
    report = case.study()
    assert report["completed_count"] == 18
    assert all(
        s["classification"] == "unknown"
        for c in report["candidates"]
        for s in c["scenarios"]
    )


def test_failed_grid_check_and_equality(monkeypatch):
    monkeypatch.setattr(case, "GRID_CHANGE_TOLERANCE_K", 0)
    report = case.study()
    assert report["candidates"][2]["scenarios"][1]["classification"] == "unknown"
    monkeypatch.setattr(case, "GRID_CHANGE_TOLERANCE_K", 0.5)
    peak = report["candidates"][2]["scenarios"][1]["grids"][-1]["peak_cell_k"]
    monkeypatch.setattr(case, "LIMIT_K", peak)
    assert (
        case.study()["candidates"][2]["scenarios"][1]["classification"] == "borderline"
    )
