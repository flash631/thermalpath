"""Boundary, orientation, and numerical-domain tests for the steady solver."""

import pytest

from thermalpath import Link, Network, Node, solve_steady


def test_one_node_heating_and_result_order():
    network = Network(
        [Node("heater", power_w=10), Node("sink", fixed_temperature_k=300)],
        [Link("path", "heater", "sink", 2)],
    )
    result = solve_steady(network)
    assert result.temperatures_k == {"heater": 305, "sink": 300}
    assert list(result.temperatures_k) == ["heater", "sink"]
    assert result.link_powers_w == {"path": 10}
    result.temperatures_k["heater"] = 1
    assert solve_steady(network).temperatures_k["heater"] == 305


@pytest.mark.parametrize("power, temperature", [(0, 300), (-20, 290)])
def test_zero_load_and_extraction(power, temperature):
    result = solve_steady(
        Network(
            [Node("a", power_w=power), Node("b", fixed_temperature_k=300)],
            [Link("ab", "a", "b", 2)],
        )
    )
    assert result.temperatures_k["a"] == temperature
    assert result.link_powers_w["ab"] == power


def test_parallel_links_and_reversed_orientation():
    result = solve_steady(
        Network(
            [Node("a", power_w=12), Node("b", fixed_temperature_k=300)],
            [Link("forward", "a", "b", 1), Link("reverse", "b", "a", 2)],
        )
    )
    assert result.temperatures_k == {"a": 304, "b": 300}
    assert result.link_powers_w == {"forward": 4, "reverse": -8}


def test_all_fixed_nodes_and_empty_links():
    nodes = [
        Node("hot", fixed_temperature_k=350),
        Node("cold", fixed_temperature_k=300),
    ]
    result = solve_steady(Network(nodes, [Link("bc", "hot", "cold", 2)]))
    assert result.temperatures_k == {"hot": 350, "cold": 300}
    assert result.link_powers_w == {"bc": 100}
    assert solve_steady(Network(nodes)).link_powers_w == {}


def test_separate_anchored_networks_are_valid():
    result = solve_steady(
        Network(
            [
                Node("a", power_w=4),
                Node("b", fixed_temperature_k=300),
                Node("c", power_w=-2),
                Node("d", fixed_temperature_k=350),
            ],
            [Link("ab", "a", "b", 2), Link("cd", "c", "d", 1)],
        )
    )
    assert result.temperatures_k == {"a": 302, "b": 300, "c": 348, "d": 350}


@pytest.mark.parametrize(
    "network",
    [
        Network([Node("a")]),
        Network([Node("a", power_w=1)]),
        Network([Node("a"), Node("b")], [Link("ab", "a", "b", 1)]),
        Network([Node("a"), Node("b", fixed_temperature_k=300)]),
        Network(
            [
                Node("a", power_w=1),
                Node("b", power_w=-1),
                Node("fixed", fixed_temperature_k=300),
            ],
            [Link("ab", "a", "b", 1)],
        ),
    ],
)
def test_unanchored_nodes_rejected_even_with_balanced_loads(network):
    with pytest.raises(ValueError, match="path to a fixed temperature"):
        solve_steady(network)


@pytest.mark.parametrize("bad", [None, {}, [], 1])
def test_wrong_input_type(bad):
    with pytest.raises(ValueError, match="must be a Network"):
        solve_steady(bad)


@pytest.mark.parametrize("power", [-600, -602, 1e308])
def test_nonpositive_or_overflowed_temperature(power):
    conductance = 1e-300 if power > 0 else 2
    with pytest.raises(ValueError, match="temperatures must be finite and positive"):
        solve_steady(
            Network(
                [Node("a", power_w=power), Node("b", fixed_temperature_k=300)],
                [Link("ab", "a", "b", conductance)],
            )
        )


@pytest.mark.parametrize(
    "conductance, fixed_temperature",
    [(1e308, 300), (1e-300, 1e-300)],
)
def test_boundary_term_outside_range(conductance, fixed_temperature):
    with pytest.raises(ValueError, match="system is singular or outside float range"):
        solve_steady(
            Network(
                [Node("a"), Node("b", fixed_temperature_k=fixed_temperature)],
                [Link("ab", "a", "b", conductance)],
            )
        )


def test_summed_conductance_overflow():
    with pytest.raises(ValueError, match="system is singular or outside float range"):
        solve_steady(
            Network(
                [Node("a"), Node("b", fixed_temperature_k=1e-300)],
                [Link("one", "a", "b", 1e308), Link("two", "a", "b", 1e308)],
            )
        )


def test_weak_anchor_lost_to_roundoff():
    with pytest.raises(ValueError, match="system is singular or outside float range"):
        solve_steady(
            Network(
                [Node("a"), Node("b"), Node("sink", fixed_temperature_k=300)],
                [Link("ab", "a", "b", 1), Link("bs", "b", "sink", 1e-30)],
            )
        )


@pytest.mark.parametrize(
    "hot, cold, conductance", [(350, 300, 1e308), (2e-100, 1e-100, 1e-300)]
)
def test_link_power_outside_range(hot, cold, conductance):
    with pytest.raises(ValueError, match="link power is outside float range"):
        solve_steady(
            Network(
                [
                    Node("a", fixed_temperature_k=hot),
                    Node("b", fixed_temperature_k=cold),
                ],
                [Link("ab", "a", "b", conductance)],
            )
        )
