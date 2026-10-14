"""Sensitivity admission and preserved failure evidence."""

import csv
import io
import json
import math

import pytest

from thermalpath import Link, Network, Node
from thermalpath.sensitivity import network_sensitivity
from thermalpath.studies import replay_network_sweep


def network(power=10):
    return Network(
        (Node("body", power_w=power), Node("sink", fixed_temperature_k=300)),
        (Link("path", "body", "sink", 2),),
    )


@pytest.mark.parametrize("steps", [None, (), (1, 2), (1,) * 17, "123"])
def test_step_collection(steps):
    with pytest.raises(ValueError, match="3 to 16"):
        network_sensitivity(network(), "power_w", "body", steps)


@pytest.mark.parametrize("value", [0, -1, True, None, float("nan"), float("inf")])
def test_step_domain(value):
    with pytest.raises(ValueError):
        network_sensitivity(network(), "power_w", "body", (value, 1, 2))


def test_repeated_steps():
    with pytest.raises(ValueError, match="distinct"):
        network_sensitivity(network(), "power_w", "body", (1, 2, 1))


@pytest.mark.parametrize(
    "field,target,match",
    [
        ("bad", "body", "field"),
        ("power_w", "", "target_id"),
        ("power_w", "absent", "exist"),
        ("conductance_w_k", "absent", "exist"),
        ("power_w", "sink", "boundary"),
        ("fixed_temperature_k", "body", "boundary"),
    ],
)
def test_targets(field, target, match):
    with pytest.raises(ValueError, match=match):
        network_sensitivity(network(), field, target, (1, 2, 3))


def test_invalid_network_and_baseline():
    with pytest.raises(ValueError, match="Network"):
        network_sensitivity(None, "power_w", "body", (1, 2, 3))
    with pytest.raises(ValueError, match="baseline"):
        network_sensitivity(Network((Node("body"),)), "power_w", "body", (1, 2, 3))
    with pytest.raises(ValueError, match="64 nodes"):
        network_sensitivity(
            Network(tuple(Node(str(i)) for i in range(65))), "power_w", "0", (1, 2, 3)
        )


def test_order_input_preservation_and_replay():
    base = network()
    result = network_sensitivity(base, "conductance_w_k", "path", [0.5, 2, 0.25])
    assert base == network()
    assert (result.field, result.target_id, result.parameter_unit) == (
        "conductance_w_k",
        "path",
        "W/K",
    )
    assert result.parameter_value == 2
    assert [row.step for row in result.estimates] == [0.5, 2, 0.25]
    assert [row.status for row in result.estimates] == ["ok", "failed", "ok"]
    assert replay_network_sweep(result.base_case_csv) == result.base_case_csv
    for row in result.estimates:
        assert replay_network_sweep(row.cases_csv) == row.cases_csv
    failed = result.estimates[1]
    assert failed.lower_value == 0
    assert "positive" in failed.error
    assert failed.dimensional == failed.scaled == {}
    evidence = list(csv.DictReader(io.StringIO(failed.cases_csv)))
    assert [row["status"] for row in evidence] == ["failed", "ok"]
    assert json.loads(evidence[0]["case_json"])["links"][0]["conductance_w_k"] == 0


def test_zero_parameter_scaling_and_fixed_node_derivatives():
    result = network_sensitivity(network(0), "power_w", "body", (1, 2, 4))
    for row in result.estimates:
        assert row.dimensional == {"body": 0.5, "sink": 0.0}
        assert row.scaled == {"body": 0.0, "sink": 0.0}


def test_sixteen_steps_and_all_fixed_baseline():
    base = Network((Node("sink", fixed_temperature_k=300),))
    steps = tuple(range(16, 0, -1))
    result = network_sensitivity(base, "fixed_temperature_k", "sink", steps)
    assert result.parameter_unit == "K"
    assert [row.step for row in result.estimates] == list(steps)
    assert all(row.dimensional == {"sink": 1} for row in result.estimates)
    assert all(row.scaled == {"sink": 1} for row in result.estimates)


def test_unresolved_temperature_change_is_not_an_accuracy_claim():
    # Input steps are representable about zero, but the output changes vanish
    # next to 300 K in binary64. Retain that result; do not invent accuracy.
    result = network_sensitivity(network(0), "power_w", "body", (1e-20, 2e-20, 3e-20))
    assert all(row.status == "ok" for row in result.estimates)
    assert all(row.dimensional["body"] == 0 for row in result.estimates)


def test_solution_boundary_and_temperature_boundary_are_failures():
    for field, target, steps in [
        ("power_w", "body", (610, 611, 612)),
        ("fixed_temperature_k", "sink", (300, 301, 302)),
    ]:
        result = network_sensitivity(network(), field, target, steps)
        assert all(row.status == "failed" and row.cases_csv for row in result.estimates)


def test_collapsed_perturbations_are_retained():
    result = network_sensitivity(network(), "power_w", "body", (1e-20, 2e-20, 3e-20))
    for row in result.estimates:
        assert row.lower_value == row.upper_value == 10
        assert row.status == "failed"
        assert row.cases_csv == ""
        assert "collapse" in row.error


def test_overflowing_span_and_upper_value():
    base = Network((Node("sink", fixed_temperature_k=1e308),))
    result = network_sensitivity(
        base, "fixed_temperature_k", "sink", (1e308, 9e307, 8e307)
    )
    assert all(row.status == "failed" for row in result.estimates)
    assert math.isinf(result.estimates[0].upper_value)


def test_nonfinite_derivative_preserves_solver_evidence(monkeypatch):
    from thermalpath import sensitivity

    original = sensitivity.sweep_network
    calls = 0

    def huge_output(base, axes):
        nonlocal calls
        text = original(base, axes)
        if calls:
            table = list(csv.reader(io.StringIO(text)))
            table[2][5] = json.dumps({"body": 1e308, "sink": 300})
            stream = io.StringIO(newline="")
            csv.writer(stream).writerows(table)
            text = stream.getvalue()
        calls += 1
        return text

    monkeypatch.setattr(sensitivity, "sweep_network", huge_output)
    result = network_sensitivity(network(), "power_w", "body", (0.01, 0.02, 0.04))
    assert all(row.status == "failed" and row.cases_csv for row in result.estimates)
    assert all("arithmetic" in row.error for row in result.estimates)


def test_unexpected_error_propagates(monkeypatch):
    def bug(*args):
        raise RuntimeError("unexpected")

    monkeypatch.setattr("thermalpath.sensitivity.sweep_network", bug)
    with pytest.raises(RuntimeError, match="unexpected"):
        network_sensitivity(network(), "power_w", "body", (1, 2, 4))
