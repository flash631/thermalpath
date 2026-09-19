"""Independent source, sink, boundary, and link power ledgers."""

from fractions import Fraction

import pytest

from thermalpath import Link, Network, Node, heat_balance, solve_steady


def ledger_network():
    # Exact temperatures: a=310, b=320, cold=300, warm=340 K.
    # The two parallel cold paths each remove 10 W from a. The b->a path
    # supplies 10 W. The warm reservoir supplies 60 W to b, which extracts 50 W.
    return Network(
        [
            Node("a", power_w=10),
            Node("b", power_w=-50),
            Node("cold", fixed_temperature_k=300),
            Node("warm", fixed_temperature_k=340),
        ],
        [
            Link("ac", "a", "cold", 1),
            Link("ca", "cold", "a", 1),
            Link("ab", "a", "b", 1),
            Link("bw", "b", "warm", 3),
        ],
    )


@pytest.mark.parametrize("reverse", [False, True])
def test_exact_multinode_ledger_with_parallel_links(reverse):
    network = ledger_network()
    powers = {"ac": 10, "ca": -10, "ab": -10, "bw": -60}
    if reverse:
        network = Network(
            network.nodes,
            [
                Link(link.id, link.node_b, link.node_a, link.conductance_w_k)
                for link in reversed(network.links)
            ],
        )
        powers = {key: -value for key, value in powers.items()}
    report = heat_balance(network, powers)
    assert report.node_outflow_w == {"a": 10, "b": -50, "cold": -20, "warm": 60}
    assert list(report.node_outflow_w) == ["a", "b", "cold", "warm"]
    assert report.node_residual_w == {"a": 0, "b": 0}
    assert report.boundary_power_w == {"cold": -20, "warm": 60}
    assert report.total_input_w == report.total_output_w == 70
    assert report.imbalance_w == 0


def test_internal_flow_error_cancels_globally_but_not_locally():
    report = heat_balance(ledger_network(), {"ac": 10, "ca": -10, "ab": -9, "bw": -60})
    assert report.imbalance_w == 0
    assert report.node_residual_w == {"a": -1, "b": 1}


def test_boundary_flow_error_is_visible_in_global_balance():
    report = heat_balance(ledger_network(), {"ac": 11, "ca": -10, "ab": -10, "bw": -60})
    assert report.boundary_power_w == {"cold": -21, "warm": 60}
    assert report.node_residual_w == {"a": -1, "b": 0}
    assert report.total_input_w == 70
    assert report.total_output_w == 71
    assert report.imbalance_w == -1


def test_fixed_to_fixed_flow_and_separate_anchored_components():
    network = Network(
        [
            Node("hot", fixed_temperature_k=350),
            Node("cold", fixed_temperature_k=300),
            Node("load", power_w=-4),
            Node("bath", fixed_temperature_k=300),
        ],
        [Link("exchange", "hot", "cold", 2), Link("cooling", "load", "bath", 2)],
    )
    report = heat_balance(network, solve_steady(network).link_powers_w)
    assert report.node_residual_w == {"load": 0}
    assert report.boundary_power_w == {"hot": 100, "cold": -100, "bath": 4}
    assert report.total_input_w == report.total_output_w == 104
    assert report.imbalance_w == 0


def test_solved_rational_network_closes_with_power_tolerance():
    # Elimination: 3*Ta-Tb=610 and -Ta+4*Tb=930.
    # Ta=3370/11 K, Tb=3400/11 K. Cold removes 140/11 W;
    # warm supplies 360/11 W; loads add 10 W and extract 30 W.
    network = Network(
        [
            Node("a", power_w=10),
            Node("b", power_w=-30),
            Node("cold", fixed_temperature_k=300),
            Node("warm", fixed_temperature_k=320),
        ],
        [
            Link("ac", "a", "cold", 2),
            Link("ab", "a", "b", 1),
            Link("bw", "b", "warm", 3),
        ],
    )
    report = heat_balance(network, solve_steady(network).link_powers_w)
    assert report.boundary_power_w == pytest.approx(
        {"cold": float(Fraction(-140, 11)), "warm": float(Fraction(360, 11))},
        rel=0,
        abs=1e-10,
    )
    assert report.node_residual_w == pytest.approx({"a": 0, "b": 0}, rel=0, abs=2e-10)
    expected_total = float(Fraction(470, 11))
    assert report.total_input_w == pytest.approx(expected_total, rel=0, abs=2e-10)
    assert report.total_output_w == pytest.approx(expected_total, rel=0, abs=2e-10)
    assert report.imbalance_w == pytest.approx(0, rel=0, abs=4e-10)


def test_lost_temperature_difference_is_reported_as_unbalanced():
    network = Network(
        [Node("tiny", power_w=1e-20), Node("bath", fixed_temperature_k=300)],
        [Link("path", "tiny", "bath", 1)],
    )
    solution = solve_steady(network)
    assert solution.temperatures_k["tiny"] == 300
    assert solution.link_powers_w == {"path": 0}
    report = heat_balance(network, solution.link_powers_w)
    assert report.node_residual_w == {"tiny": 1e-20}
    assert report.imbalance_w == 1e-20
