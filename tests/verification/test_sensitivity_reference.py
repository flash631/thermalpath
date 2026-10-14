"""Exact differentiated balances and finite-step error references."""

from fractions import Fraction as F

import pytest

from thermalpath import Link, Network, Node
from thermalpath.sensitivity import network_sensitivity


def series():
    return Network(
        (
            Node("a", power_w=12),
            Node("b", power_w=4),
            Node("sink", fixed_temperature_k=300),
        ),
        (Link("ab", "a", "b", 2), Link("bs", "b", "sink", 4)),
    )


@pytest.mark.parametrize(
    "field,target,steps,expected",
    [
        ("power_w", "a", (2, 1, 0.5), {"a": 0.75, "b": 0.25, "sink": 0}),
        ("power_w", "b", (2, 1, 0.5), {"a": 0.25, "b": 0.25, "sink": 0}),
        ("fixed_temperature_k", "sink", (2, 1, 0.5), {"a": 1, "b": 1, "sink": 1}),
    ],
)
def test_differentiated_two_node_balances(field, target, steps, expected):
    # Gb*(Tb-Tsink)=Pa+Pb, Ga*(Ta-Tb)=Pa.
    result = network_sensitivity(series(), field, target, steps)
    for row in result.estimates:
        assert row.status == "ok"
        assert row.dimensional == pytest.approx(expected, rel=0, abs=3e-12)
        for node, temperature in {"a": 310, "b": 304, "sink": 300}.items():
            assert row.scaled[node] == pytest.approx(
                result.parameter_value * expected[node] / temperature, rel=0, abs=3e-12
            )


def test_conductance_error_is_known_for_three_sizes():
    result = network_sensitivity(series(), "conductance_w_k", "ab", (0.5, 0.25, 0.125))
    errors = []
    for row in result.estimates:
        # Ta=304+12/g. Central difference is exactly -12/(g*g-h*h).
        h = F(row.step)
        reference = -F(12) / (4 - h * h)
        assert row.status == "ok"
        assert row.dimensional == pytest.approx(
            {"a": float(reference), "b": 0, "sink": 0}, rel=0, abs=3e-12
        )
        exact_error = F(3) * h * h / (4 - h * h)
        measured = abs(row.dimensional["a"] + 3)
        assert measured == pytest.approx(float(exact_error), rel=0, abs=3e-12)
        errors.append(measured)
    assert errors[0] > errors[1] > errors[2]
    assert errors[0] / errors[1] == pytest.approx(4.2, rel=0, abs=1e-9)
    assert errors[1] / errors[2] == pytest.approx(85 / 21, rel=0, abs=1e-9)


def test_unequal_binary64_spacing_against_exact_interpolation():
    base = Network(
        (Node("body", power_w=0.25), Node("sink", fixed_temperature_k=1)),
        (Link("path", "body", "sink", 1),),
    )
    result = network_sensitivity(base, "conductance_w_k", "path", (0.1, 0.2, 0.3))
    assert result.estimates[0].upper_value - 1 != 1 - result.estimates[0].lower_value
    for row in result.estimates:
        lo, hi = F(row.lower_value), F(row.upper_value)
        hm, hp = 1 - lo, hi - 1
        f0, flo, fhi = F(5, 4), 1 + F(1, 4) / lo, 1 + F(1, 4) / hi
        reference = (hm * (fhi - f0) / hp + hp * (f0 - flo) / hm) / (hm + hp)
        assert row.dimensional["body"] == pytest.approx(
            float(reference), rel=0, abs=3e-14
        )


def test_negative_parameter_and_zero_response_are_not_absolute_values():
    base = Network(
        (Node("body", power_w=-10), Node("sink", fixed_temperature_k=300)),
        (Link("path", "body", "sink", 2),),
    )
    result = network_sensitivity(base, "power_w", "body", (1, 2, 4))
    for row in result.estimates:
        assert row.dimensional["body"] == 0.5
        assert row.scaled["body"] == pytest.approx(-5 / 295, rel=0, abs=1e-15)
