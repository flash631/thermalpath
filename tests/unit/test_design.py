"""Common-input screening, threshold decisions and retained alternatives."""

import csv
import io
import json
from dataclasses import FrozenInstanceError

import pytest

from thermalpath import Link, Node
from thermalpath.design import (
    NetworkCandidate,
    TemperatureRequirement,
    compare_network_candidates,
)
from thermalpath.studies import replay_network_sweep


def compare(**kwargs):
    inputs = {
        "nodes": (Node("body", power_w=10), Node("sink", fixed_temperature_k=300)),
        "candidates": (NetworkCandidate("base", (Link("g", "body", "sink", 2),)),),
        "requirements": (TemperatureRequirement("body", 306),),
        "comparison_tolerance_k": 0.125,
    }
    return compare_network_candidates(**(inputs | kwargs))


@pytest.mark.parametrize("name", ["", " space", None, 5])
def test_invalid_names(name):
    with pytest.raises(ValueError):
        NetworkCandidate(name, ())
    with pytest.raises(ValueError):
        TemperatureRequirement(name, 300)


@pytest.mark.parametrize("links", [None, "links", (None,), (1,) * 129])
def test_invalid_links(links):
    with pytest.raises(ValueError, match="links"):
        NetworkCandidate("a", links)


@pytest.mark.parametrize("value", [0, -1, True, "300", float("inf"), float("nan")])
def test_invalid_upper_limit(value):
    with pytest.raises(ValueError):
        TemperatureRequirement("body", value)


def test_records_copy_lists_and_are_frozen():
    links = [Link("g", "body", "sink", 2)]
    candidate = NetworkCandidate("a", links)
    links.clear()
    assert len(candidate.links) == 1
    with pytest.raises(FrozenInstanceError):
        candidate.name = "b"
    requirements = [TemperatureRequirement("body", 306)]
    study = compare(candidates=[candidate], requirements=requirements)
    requirements.clear()
    assert study.requirements == (TemperatureRequirement("body", 306),)
    assert type(study.requirements[0].maximum_k) is float
    assert type(study.comparison_tolerance_k) is float


@pytest.mark.parametrize("candidates", [(), "x", (None,), (None,) * 65])
def test_invalid_candidates(candidates):
    with pytest.raises(ValueError, match="candidates"):
        compare(candidates=candidates)


@pytest.mark.parametrize("requirements", [(), "x", (None,), (None,) * 65])
def test_invalid_requirements(requirements):
    with pytest.raises(ValueError, match="requirements"):
        compare(requirements=requirements)


@pytest.mark.parametrize("value", [-1, True, "1", float("nan"), float("inf")])
def test_invalid_comparison_band(value):
    with pytest.raises(ValueError):
        compare(comparison_tolerance_k=value)


def test_duplicate_names_and_requirement_nodes():
    candidate = NetworkCandidate("a", ())
    with pytest.raises(ValueError, match="duplicate candidate"):
        compare(candidates=(candidate, candidate))
    req = TemperatureRequirement("body", 300)
    with pytest.raises(ValueError, match="duplicate requirement"):
        compare(requirements=(req, req))
    with pytest.raises(ValueError, match="does not exist"):
        compare(requirements=(TemperatureRequirement("missing", 300),))


@pytest.mark.parametrize(
    "limit,status,margin",
    [
        (304, "exceeds", -1),
        (304.875, "borderline", -0.125),
        (305, "borderline", 0),
        (305.125, "borderline", 0.125),
        (306, "meets", 1),
    ],
)
def test_classification_including_band_endpoints(limit, status, margin):
    result = compare(requirements=(TemperatureRequirement("body", limit),))
    assert result.assessments[0].status == status
    assert result.assessments[0].minimum_margin_k == margin


def test_zero_band_still_retains_equality():
    result = compare(
        requirements=(TemperatureRequirement("body", 305),), comparison_tolerance_k=0
    )
    assert result.assessments[0].status == "borderline"


def test_all_limits_must_pass_and_fixed_nodes_can_be_checked():
    study = compare(
        requirements=(
            TemperatureRequirement("body", 306),
            TemperatureRequirement("sink", 299),
        )
    )
    result = study.assessments[0]
    assert result.margins_k == {"body": 1, "sink": -1}
    assert result.status == "exceeds"
    assert result.minimum_margin_k == -1


def test_ties_failures_and_complete_shared_inputs_survive_replay():
    links = (Link("g", "body", "sink", 2),)
    study = compare(
        candidates=(
            NetworkCandidate("first", links),
            NetworkCandidate("unanchored", ()),
            NetworkCandidate("same", links),
            NetworkCandidate("too_hot", (Link("g", "body", "sink", 1),)),
        )
    )
    assert [a.name for a in study.assessments] == [
        "first",
        "unanchored",
        "same",
        "too_hot",
    ]
    assert [a.status for a in study.assessments] == [
        "meets",
        "failed",
        "meets",
        "exceeds",
    ]
    first, failed, same, hot = study.assessments
    assert first.margins_k == same.margins_k == {"body": 1}
    assert failed.minimum_margin_k is None and failed.margins_k == {}
    assert failed.error and not first.error
    assert hot.minimum_margin_k == -4
    rows = list(csv.DictReader(io.StringIO(study.cases_csv)))
    common = json.loads(rows[0]["case_json"])["nodes"]
    assert all(json.loads(row["case_json"])["nodes"] == common for row in rows)
    assert rows[1]["temperatures_k_json"] == ""
    assert study.cases_csv == replay_network_sweep(study.cases_csv)
    assert "uncertainty is not evaluated" in study.qualification
    assert "No safety bounds" in study.qualification


def test_all_failed_does_not_claim_feasibility():
    study = compare(candidates=(NetworkCandidate("a", ()), NetworkCandidate("b", ())))
    assert all(a.status == "failed" for a in study.assessments)
    assert all(a.minimum_margin_k is None for a in study.assessments)


def test_negative_load_invalid_temperature_is_retained():
    study = compare(
        nodes=(Node("body", power_w=-1000), Node("sink", fixed_temperature_k=300))
    )
    assert study.assessments[0].status == "failed"
    assert study.assessments[0].minimum_margin_k is None


@pytest.mark.parametrize(
    "links",
    [
        (Link("missing", "body", "missing", 1),),
        (Link("g", "body", "sink", 1),) * 2,
    ],
)
def test_malformed_alternative_rejected_before_any_solve(links, monkeypatch):
    def forbidden(_):
        raise AssertionError("must validate before solving")

    monkeypatch.setattr("thermalpath.design._evaluate", forbidden)
    with pytest.raises(ValueError):
        compare(
            candidates=(NetworkCandidate("valid", ()), NetworkCandidate("bad", links))
        )


def test_resource_bounds_before_solves():
    with pytest.raises(ValueError, match="64 nodes"):
        compare(nodes=tuple(Node(str(i)) for i in range(65)))
    name = "x" * 33000
    with pytest.raises(ValueError, match="32768"):
        compare(
            nodes=(Node(name, fixed_temperature_k=300),),
            candidates=(NetworkCandidate("a", ()),),
            requirements=(TemperatureRequirement(name, 301),),
        )


def test_maximum_candidates_kept():
    study = compare(candidates=tuple(NetworkCandidate(str(i), ()) for i in range(64)))
    assert len(study.assessments) == 64


def test_unexpected_solver_exception_propagates(monkeypatch):
    def broken(_):
        raise RuntimeError("unexpected")

    monkeypatch.setattr("thermalpath.studies.solve_steady", broken)
    with pytest.raises(RuntimeError, match="unexpected"):
        compare()
