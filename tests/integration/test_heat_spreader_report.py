"""Run both report formats and compare them with the unchanged study."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(*arguments):
    return subprocess.run(
        [sys.executable, str(ROOT / "examples/heat_spreader_report.py"), *arguments],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def test_both_formats_retain_the_complete_study():
    first = run("--format", "json")
    assert first == run("--format", "json")
    data = json.loads(first)
    raw = subprocess.run(
        [sys.executable, str(ROOT / "examples/heat_spreader.py")],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    original = json.loads(raw)
    assert data["results"]["candidates"] == original.pop("candidates")
    for key in ("attempted_count", "completed_count", "failed_count"):
        assert data["results"][key] == original.pop(key)
    assert data["inputs"] == original
    assert len(data["checks"]) == 78
    assert all(check["status"] == "passed" for check in data["checks"])
    markdown = run()
    assert markdown == run()
    payload = markdown.split("```json\n", 1)[1].removesuffix("```\n")
    assert json.loads(payload) == data
    assert data["source_revision"] == "unknown"
    sha = "abcde" * 8
    assert (
        json.loads(run("--format", "json", "--source-revision", sha))["source_revision"]
        == sha
    )


def test_failed_study_evidence_is_not_dropped(monkeypatch):
    # Match the example's direct-script import without changing the library.
    monkeypatch.syspath_prepend(str(ROOT / "examples"))
    import heat_spreader
    import heat_spreader_report as example

    original = heat_spreader.solve_plate
    calls = 0

    def fail_once(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ValueError("synthetic failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(heat_spreader, "solve_plate", fail_once)
    data = json.loads(example.report().to_json())
    assert data["results"]["failed_count"] == 1
    assert sum(c["status"] == "not_run" for c in data["checks"]) == 5
    assert (
        data["results"]["candidates"][0]["scenarios"][0]["classification"] == "unknown"
    )
