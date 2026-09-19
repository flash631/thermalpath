"""Independent rational references for finite steady thermal networks."""

from fractions import Fraction

import pytest

from thermalpath import Link, Network, Node, solve_steady


@pytest.mark.parametrize("reverse", [False, True])
def test_two_unknown_nodes_with_two_boundaries(reverse):
    # Independent elimination: 3*Ta - Tb = 610, -Ta + 4*Tb = 930.
    # Substitution gives 11*Ta=3370 and Tb=3*Ta-610.
    ta = Fraction(3370, 11)
    tb = 3 * ta - 610
    nodes = [
        Node("a", power_w=10),
        Node("b", power_w=-30),
        Node("cold", fixed_temperature_k=300),
        Node("warm", fixed_temperature_k=320),
    ]
    links = [
        Link("ac", "a", "cold", 2),
        Link("ab", "a", "b", 1),
        Link("bw", "b", "warm", 3),
    ]
    if reverse:
        nodes.reverse()
        links = [
            Link(link.id, link.node_b, link.node_a, link.conductance_w_k)
            for link in reversed(links)
        ]
    result = solve_steady(Network(nodes, links))
    assert result.temperatures_k["a"] == pytest.approx(float(ta), rel=0, abs=1e-11)
    assert result.temperatures_k["b"] == pytest.approx(float(tb), rel=0, abs=1e-11)
    expected = {"ac": 2 * (ta - 300), "ab": ta - tb, "bw": 3 * (tb - 320)}
    sign = -1 if reverse else 1
    for name, power in expected.items():
        assert result.link_powers_w[name] == pytest.approx(
            sign * float(power), rel=0, abs=1e-10
        )
    # Independently sum outgoing powers, without assembling the solver matrix.
    assert sign * (
        result.link_powers_w["ac"] + result.link_powers_w["ab"]
    ) == pytest.approx(10, abs=2e-10, rel=0)
    assert sign * (
        result.link_powers_w["bw"] - result.link_powers_w["ab"]
    ) == pytest.approx(-30, abs=2e-10, rel=0)


@pytest.mark.parametrize("scale", [0.5, 1, 8])
def test_series_limiting_case(scale):
    # 15 W through R=(1, 1/20, 2) K/W from a 318.15 K reservoir.
    # Scaling every conductance and load equally leaves temperatures unchanged.
    sink = Fraction(31815, 100)
    power = Fraction(15)
    expected = {
        "source": sink + power * (1 + Fraction(1, 20) + 2),
        "interface": sink + power * (Fraction(1, 20) + 2),
        "base": sink + power * 2,
        "sink": sink,
    }
    result = solve_steady(
        Network(
            [
                Node("source", power_w=15 * scale),
                Node("interface"),
                Node("base"),
                Node("sink", fixed_temperature_k=float(sink)),
            ],
            [
                Link("one", "source", "interface", scale),
                Link("tim", "interface", "base", 20 * scale),
                Link("two", "base", "sink", 0.5 * scale),
            ],
        )
    )
    for name, temperature in expected.items():
        assert result.temperatures_k[name] == pytest.approx(
            float(temperature), rel=0, abs=1e-9
        )
    for value in result.link_powers_w.values():
        assert value == pytest.approx(15 * scale, rel=0, abs=5e-7)
