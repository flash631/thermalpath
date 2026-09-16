"""The quality driver must stop at a failed subprocess and retain all gates."""

from types import SimpleNamespace

import pytest

from scripts import check


@pytest.mark.parametrize("failure", range(4))
def test_gate_failure_stops_execution(monkeypatch, failure):
    calls = []

    def run(arguments, **kwargs):
        assert kwargs["env"]["OMP_NUM_THREADS"] == "1"
        calls.append(arguments)
        return SimpleNamespace(returncode=7 if len(calls) - 1 == failure else 0)

    monkeypatch.setattr(check.subprocess, "run", run)
    assert check.main() == 7
    assert len(calls) == failure + 1
    assert all(call[0] == check.sys.executable for call in calls)


def test_complete_quality_gate(monkeypatch):
    calls = []
    monkeypatch.setattr(
        check.subprocess,
        "run",
        lambda args, **kwargs: calls.append(args) or SimpleNamespace(returncode=0),
    )
    assert check.main() == 0
    assert len(calls) == 4
    assert "--cov=thermalpath" in calls[2]
    assert "--cov-branch" in calls[2]
    assert "--cov-fail-under=90" in calls[2]
    assert calls[3][-1] == "build"
