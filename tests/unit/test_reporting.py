"""Exact export contracts, invalid inputs, and inert Markdown text."""

import json
import math
from dataclasses import FrozenInstanceError

import pytest

from thermalpath.reporting import EngineeringReport, Evidence, NumericalCheck


def arguments():
    return dict(
        title="Synthetic network",
        source_revision="unknown",
        inputs={"power_w": 10.0, "sink_k": 300.0, "conductance_w_k": 2.0},
        units={"power": "W", "temperature": "K", "conductance": "W/K"},
        results={"temperature_k": 305.0, "unrun": None, "rows": [2, 1, 1]},
        checks=(NumericalCheck("balance", "W", 0, 1e-9, "Discrete balance only."),),
        provenance=(
            Evidence("synthetic", "Assigned case", "case 1", "MIT", "No measurements."),
        ),
        limitations=("Constant conductance.",),
    )


def test_snapshot_is_deterministic_and_isolated():
    args = arguments()
    report = EngineeringReport(**args)
    expected = json.loads(report.to_json())
    assert expected["inputs"] == args["inputs"]
    assert expected["results"] == args["results"]
    assert expected["units"] == args["units"]
    assert expected["source_revision"] == "unknown"
    assert expected["provenance_status"] == "caller_declared"
    assert expected["checks"][0]["status"] == "passed"
    reordered = arguments()
    reordered["inputs"] = dict(reversed(list(args["inputs"].items())))
    assert report.to_json() == EngineeringReport(**reordered).to_json()
    assert report.to_markdown() == EngineeringReport(**reordered).to_markdown()
    args["inputs"]["power_w"] = 99
    args["results"]["rows"].append(5)
    assert json.loads(report.to_json()) == expected
    with pytest.raises(FrozenInstanceError):
        report._json = "{}"


@pytest.mark.parametrize(
    ("value", "tolerance", "status"),
    [
        (None, 0, "not_run"),
        (0, 0, "passed"),
        (-2, 2, "passed"),
        (2, 2, "passed"),
        (math.nextafter(2, math.inf), 2, "failed"),
        (-3, 2, "failed"),
        (5e-324, 0, "failed"),
    ],
)
def test_absolute_screen_boundary(value, tolerance, status):
    check = NumericalCheck("residual", "W", value, tolerance, "Supplied residual.")
    assert check.status == status
    args = arguments()
    args["checks"] = (check,)
    report = EngineeringReport(**args)
    assert json.loads(report.to_json())["checks"][0]["value"] == value
    assert status.replace("_", "&#95;") in report.to_markdown()


@pytest.mark.parametrize("field", ["value", "tolerance"])
@pytest.mark.parametrize("value", [True, "1", float("nan"), float("inf"), 10**400])
def test_invalid_check_numbers(field, value):
    args = dict(name="balance", unit="W", value=0, tolerance=0, note="Explanation.")
    args[field] = value
    with pytest.raises(ValueError):
        NumericalCheck(**args)


def test_negative_tolerance():
    with pytest.raises(ValueError, match="nonnegative"):
        NumericalCheck("residual", "W", 0, -1, "Explanation.")


@pytest.mark.parametrize(
    "text", ["", " ", "line\nbreak", "null\0", "\ud800", "x" * 4097, 3]
)
def test_invalid_text(text):
    args = arguments()
    args["title"] = text
    with pytest.raises(ValueError):
        EngineeringReport(**args)


@pytest.mark.parametrize(
    "kind", ["synthetic", "analytical", "numerical", "experimental"]
)
def test_evidence_labels(kind):
    assert Evidence(kind, "Source", "Table 1", "declared rights", "Scope").kind == kind


def test_invalid_evidence():
    with pytest.raises(ValueError, match="kind"):
        Evidence("verified", "Source", "1", "MIT", "Scope")
    with pytest.raises(ValueError):
        Evidence("synthetic", "", "1", "MIT", "Scope")


@pytest.mark.parametrize("revision", [None, 123, "HEAD", "a" * 39, "A" * 40, "g" * 40])
def test_invalid_source_revision(revision):
    args = arguments()
    args["source_revision"] = revision
    with pytest.raises(ValueError, match="source_revision"):
        EngineeringReport(**args)


@pytest.mark.parametrize("field", ["inputs", "results", "units"])
@pytest.mark.parametrize("value", [{}, [], None])
def test_required_mappings(field, value):
    args = arguments()
    args[field] = value
    with pytest.raises(ValueError):
        EngineeringReport(**args)


@pytest.mark.parametrize("field", ["checks", "provenance", "limitations"])
@pytest.mark.parametrize("value", [(), [], (1,), ("x",) * 257])
def test_required_sequences(field, value):
    args = arguments()
    args[field] = value
    with pytest.raises(ValueError):
        EngineeringReport(**args)


def test_duplicate_checks_and_bad_unit():
    args = arguments()
    args["checks"] *= 2
    with pytest.raises(ValueError, match="unique"):
        EngineeringReport(**args)
    args = arguments()
    args["units"]["power"] = None
    with pytest.raises(ValueError):
        EngineeringReport(**args)


@pytest.mark.parametrize(
    "value", [float("nan"), float("inf"), 2**63, -(2**63) - 1, {1: 2}, object(), {1, 2}]
)
def test_invalid_payload(value):
    args = arguments()
    args["results"] = {"invalid": value}
    with pytest.raises(ValueError):
        EngineeringReport(**args)


def test_valid_scalar_limits_and_tuple_order():
    args = arguments()
    args["results"] = {"values": (-(2**63), 2**63 - 1, 5e-324, -0.0, True, False)}
    values = json.loads(EngineeringReport(**args).to_json())["results"]["values"]
    assert values == list(args["results"]["values"])
    assert math.copysign(1, values[3]) == -1


def test_depth_cycles_count_and_size():
    args = arguments()
    recursive = []
    recursive.append(recursive)
    args["results"] = {"cycle": recursive}
    with pytest.raises(ValueError, match="nesting"):
        EngineeringReport(**args)
    args["results"] = {"many": [None] * 100001}
    with pytest.raises(ValueError, match="values"):
        EngineeringReport(**args)
    args["results"] = {"large": ["x" * 4096] * 257}
    with pytest.raises(ValueError, match="MiB"):
        EngineeringReport(**args)
    # Plain text fits; JSON indentation expands past the encoded output cap.
    args["results"] = {"large": ["x" * 4000] * 262}
    with pytest.raises(ValueError, match="MiB"):
        EngineeringReport(**args)


def test_markdown_keeps_complete_evidence_and_contains_markup():
    args = arguments()
    hostile = "<img src=x> | [link](https://example.invalid) ```"
    args["title"] = hostile
    args["limitations"] = (hostile,)
    args["checks"] = (NumericalCheck(hostile, "W", None, 0, hostile),)
    args["results"] = {"markup": hostile}
    report = EngineeringReport(**args)
    markdown = report.to_markdown()
    before, payload = markdown.split("````json\n")
    assert "<img" not in before and "[link]" not in before
    assert "&#124;" in before
    assert payload.endswith("\n````\n")
    assert json.loads(payload[:-6]) == json.loads(report.to_json())
    assert markdown.endswith("\n") and not markdown.endswith("\n\n")


def test_no_environment_or_working_directory_collection(monkeypatch, tmp_path):
    baseline = EngineeringReport(**arguments())
    monkeypatch.setenv("REPORT_PRIVATE_MARKER", "private-marker-not-for-export")
    monkeypatch.chdir(tmp_path)
    changed = EngineeringReport(**arguments())
    assert changed.to_json() == baseline.to_json()
    assert changed.to_markdown() == baseline.to_markdown()
    assert "private-marker" not in changed.to_json()


def test_caller_text_is_not_silently_redacted():
    args = arguments()
    args["results"]["note"] = "caller supplied private-marker"
    assert "caller supplied private-marker" in EngineeringReport(**args).to_json()
