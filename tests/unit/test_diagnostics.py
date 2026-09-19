"""Connectivity, input-domain, and adverse heat-accounting cases."""

from types import MappingProxyType

import pytest

from thermalpath import (
    Link,
    Network,
    Node,
    check_connectivity,
    heat_balance,
    solve_steady,
)


def pair():
    return Network(
        [Node("load", power_w=10), Node("bath", fixed_temperature_k=300)],
        [Link("path", "load", "bath", 2)],
    )


def test_component_order_parallel_links_and_isolated_fixed_node():
    network = Network(
        [
            Node("b"),
            Node("isolated", fixed_temperature_k=280),
            Node("a", fixed_temperature_k=300),
            Node("c"),
            Node("d", fixed_temperature_k=310),
        ],
        [
            Link("ab", "a", "b", 1),
            Link("ba", "b", "a", 2),
            Link("cd", "c", "d", 3),
        ],
    )
    assert check_connectivity(network) == (("b", "a"), ("isolated",), ("c", "d"))


@pytest.mark.parametrize("load", [0, 2])
def test_errors_identify_all_floating_components(load):
    network = Network(
        [
            Node("anchored", fixed_temperature_k=300),
            Node("loose", power_w=load),
            Node("a", power_w=1),
            Node("b", power_w=-1),
        ],
        [Link("ab", "a", "b", 1)],
    )
    for operation in (check_connectivity, solve_steady):
        with pytest.raises(ValueError, match="unanchored components") as error:
            operation(network)
        assert "[('loose',), ('a', 'b')]" in str(error.value)
    with pytest.raises(ValueError, match="unanchored components"):
        heat_balance(network, {"ab": 1})


def test_cycle_is_traversed_once():
    network = Network(
        [Node("a"), Node("b"), Node("c", fixed_temperature_k=300)],
        [Link("ab", "a", "b", 1), Link("bc", "b", "c", 1), Link("ca", "c", "a", 1)],
    )
    assert check_connectivity(network) == (("a", "b", "c"),)


@pytest.mark.parametrize("bad", [None, {}, [], 1])
def test_wrong_network_type(bad):
    with pytest.raises(ValueError, match="must be a Network"):
        check_connectivity(bad)
    with pytest.raises(ValueError, match="must be a Network"):
        heat_balance(bad, {})


@pytest.mark.parametrize(
    "powers", [None, [], {"wrong": 10}, {}, {"path": 10, "extra": 0}]
)
def test_link_mapping_requires_exact_ids(powers):
    with pytest.raises(ValueError, match="exactly the network link IDs"):
        heat_balance(pair(), powers)


@pytest.mark.parametrize("power", [True, "10", None, 1j, float("nan"), float("inf")])
def test_invalid_powers_rejected(power):
    with pytest.raises(ValueError, match="link power"):
        heat_balance(pair(), {"path": power})


def test_mapping_is_not_mutated_and_report_is_an_independent_copy():
    powers = {"path": 10}
    report = heat_balance(pair(), MappingProxyType(powers))
    assert powers == {"path": 10}
    report.boundary_power_w["bath"] = 99
    assert heat_balance(pair(), powers).boundary_power_w == {"bath": -10}


def test_zero_links_at_fixed_nodes():
    network = Network(
        [Node("one", fixed_temperature_k=300), Node("two", fixed_temperature_k=310)]
    )
    report = heat_balance(network, {})
    assert report.node_outflow_w == {"one": 0, "two": 0}
    assert report.node_residual_w == {}
    assert report.boundary_power_w == {"one": 0, "two": 0}
    assert report.total_input_w == report.total_output_w == report.imbalance_w == 0


def test_imbalance_survives_rounding_of_source_and_sink_totals():
    network = Network(
        [
            Node("large", power_w=1e16),
            Node("small", power_w=1),
            Node("extract", power_w=-1e16),
            Node("bath", fixed_temperature_k=300),
        ],
        [Link(name, name, "bath", 1) for name in ("large", "small", "extract")],
    )
    report = heat_balance(network, {"large": 0, "small": 0, "extract": 0})
    assert report.total_input_w == report.total_output_w == 1e16
    assert report.imbalance_w == 1
    assert report.node_residual_w == {"large": 1e16, "small": 1, "extract": -1e16}


def test_nodal_residual_uses_original_power_terms():
    network = Network(
        [Node("a", power_w=1), Node("bath", fixed_temperature_k=300)],
        [Link(name, "a", "bath", 1) for name in ("big", "small", "return")],
    )
    report = heat_balance(network, {"big": 1e16, "small": 1, "return": -1e16})
    assert report.node_outflow_w == {"a": 1, "bath": -1}
    assert report.node_residual_w == {"a": 0}
    assert report.imbalance_w == 0


@pytest.mark.parametrize("sign", [-1, 1])
def test_external_total_overflow(sign):
    network = Network(
        [
            Node("a", power_w=sign * 1e308),
            Node("b", power_w=sign * 1e308),
            Node("bath", fixed_temperature_k=300),
        ],
        [Link("a", "a", "bath", 1), Link("b", "b", "bath", 1)],
    )
    with pytest.raises(ValueError, match="heat-balance sum is outside float range"):
        heat_balance(network, {"a": 0, "b": 0})


def test_nodal_outflow_overflow():
    network = Network(
        [Node("a"), Node("bath", fixed_temperature_k=300)],
        [Link("one", "a", "bath", 1), Link("two", "a", "bath", 1)],
    )
    with pytest.raises(ValueError, match="heat-balance sum is outside float range"):
        heat_balance(network, {"one": 1e308, "two": 1e308})


def test_nodal_residual_overflow():
    network = Network(
        [Node("a", power_w=1e308), Node("bath", fixed_temperature_k=300)],
        [Link("one", "a", "bath", 1)],
    )
    with pytest.raises(ValueError, match="heat-balance sum is outside float range"):
        heat_balance(network, {"one": -1e308})
