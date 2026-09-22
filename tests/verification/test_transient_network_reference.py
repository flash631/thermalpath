"""Independent exact arithmetic references for discrete network updates."""

from fractions import Fraction as F

import pytest

from thermalpath import Link, Network, Node, solve_steady, solve_transient


@pytest.mark.parametrize("reverse", [False, True])
def test_two_node_rational_reference(reverse):
    # C=(2,3), G_ab=1, G_a0=2, G_b0=1, T0=300.
    # In rises x=T-300: A=[[2/h+3,-1],[-1,3/h+2]].
    network = Network(
        (Node("a"), Node("b"), Node("sink", fixed_temperature_k=300)),
        tuple(
            Link(name, b if reverse else a, a if reverse else b, g)
            for name, a, b, g in [
                ("ab", "a", "b", 1),
                ("a0", "a", "sink", 2),
                ("b0", "b", "sink", 1),
            ]
        ),
    )
    steps = [F(1), F(2), F(1, 2)]
    powers = [(10, 0), (0, 6), (-2, 1)]
    result = solve_transient(
        network,
        {"a": 2, "b": 3},
        {"a": 300, "b": 300},
        [0, 1, 3, 3.5],
        [{"a": a, "b": b} for a, b in powers],
    )
    x, y = F(0), F(0)
    for row, h, (p, q) in zip(result.temperatures_k[1:], steps, powers, strict=True):
        aa, bb = 2 / h + 3, 3 / h + 2
        u, v = 2 * x / h + p, 3 * y / h + q
        determinant = aa * bb - 1
        x, y = (bb * u + v) / determinant, (u + aa * v) / determinant
        assert row["a"] == pytest.approx(float(300 + x), rel=0, abs=2e-12)
        assert row["b"] == pytest.approx(float(300 + y), rel=0, abs=2e-12)
        assert row["sink"] == 300
    assert result.temperatures_k[1]["a"] == pytest.approx(
        float(F(3625, 12)), rel=0, abs=2e-12
    )
    assert result.temperatures_k[1]["b"] == pytest.approx(
        float(F(3605, 12)), rel=0, abs=2e-12
    )


def test_insulated_two_node_mode():
    # Equal unit capacities and unit conductance: average=300,
    # difference_new=difference_old/(1+2*h), h=1 -> 1/3.
    network = Network((Node("a"), Node("b")), (Link("ab", "a", "b", 1),))
    result = solve_transient(
        network, {"a": 1, "b": 1}, {"a": 310, "b": 290}, [0, 1, 2, 3]
    )
    for i, row in enumerate(result.temperatures_k):
        assert row["a"] == pytest.approx(float(300 + F(10, 3**i)), rel=0, abs=2e-12)
        assert row["b"] == pytest.approx(float(300 - F(10, 3**i)), rel=0, abs=2e-12)


def test_one_node_discrete_decay_and_multiple_boundaries():
    network = Network(
        (
            Node("a", power_w=2),
            Node("cold", fixed_temperature_k=290),
            Node("hot", fixed_temperature_k=310),
        ),
        (Link("ac", "a", "cold", 1), Link("ah", "a", "hot", 1)),
    )
    result = solve_transient(network, {"a": 2}, {"a": 301}, [0, 1, 2])
    assert all(row["a"] == 301 for row in result.temperatures_k)
    assert result.temperatures_k[-1] == solve_steady(network).temperatures_k
    decay = solve_transient(network, {"a": 2}, {"a": 305}, [0, 1, 2])
    assert [row["a"] for row in decay.temperatures_k] == [305, 303, 302]


def test_parallel_links_and_time_capacity_scaling():
    one = Network(
        (Node("a"), Node("b", fixed_temperature_k=300)), (Link("ab", "a", "b", 2),)
    )
    two = Network(one.nodes, (Link("ab1", "a", "b", 1), Link("ab2", "b", "a", 1)))
    a = solve_transient(one, {"a": 2}, {"a": 310}, [0, 1, 3])
    b = solve_transient(two, {"a": 20}, {"a": 310}, [0, 10, 30])
    assert a.temperatures_k == b.temperatures_k
    assert a.temperatures_k[-1]["a"] == pytest.approx(
        float(F(905, 3)), rel=0, abs=2e-12
    )
