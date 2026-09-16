"""Exercise SI domains, boundary definitions, and structural input contracts."""

import math
from dataclasses import FrozenInstanceError
from fractions import Fraction

import pytest

from thermalpath import Link, Network, Node


@pytest.mark.parametrize("invalid", ["", " ", " a", "a\n", None, 1, True])
@pytest.mark.parametrize("field", ["node", "link", "node_a", "node_b"])
def test_invalid_identifier(field, invalid):
    with pytest.raises(ValueError, match="nonempty string"):
        if field == "node":
            Node(invalid)
        else:
            values = {"id": "path", "node_a": "a", "node_b": "b"}
            values["id" if field == "link" else field] = invalid
            Link(**values, conductance_w_k=1)


@pytest.mark.parametrize("invalid", [math.nan, math.inf, -math.inf, 10**1000])
@pytest.mark.parametrize("field", ["power_w", "fixed_temperature_k", "conductance"])
def test_nonfinite_scalars(field, invalid):
    with pytest.raises(ValueError, match="finite"):
        if field == "conductance":
            Link("ab", "a", "b", invalid)
        else:
            Node("a", **{field: invalid})


@pytest.mark.parametrize("invalid", [True, False, "3", b"3", 1j, [], object()])
@pytest.mark.parametrize("field", ["power_w", "fixed_temperature_k", "conductance"])
def test_nonreal_scalars(field, invalid):
    with pytest.raises(ValueError, match="real scalar"):
        if field == "conductance":
            Link("ab", "a", "b", invalid)
        else:
            Node("a", **{field: invalid})


@pytest.mark.parametrize("invalid", [0, -0.0, -1])
def test_positive_temperature_and_conductance(invalid):
    with pytest.raises(ValueError, match="positive"):
        Node("a", fixed_temperature_k=invalid)
    with pytest.raises(ValueError, match="positive"):
        Link("ab", "a", "b", invalid)


@pytest.mark.parametrize("power", [1, -1, 1e-300, -1e-300])
def test_fixed_node_cannot_also_prescribe_power(power):
    with pytest.raises(ValueError, match="zero power_w"):
        Node("a", power, 300)


def test_scalar_normalization_and_limits():
    assert Node("heater", Fraction(1, 2)).power_w == 0.5
    assert Node("cooler", -4).power_w == -4.0
    assert Node("unknown").fixed_temperature_k is None
    assert isinstance(Node("sink", fixed_temperature_k=300).fixed_temperature_k, float)
    assert isinstance(Link("ab", "a", "b", 2).conductance_w_k, float)
    for value in (math.ulp(0.0), 1e308):
        assert Node("sink", -0.0, value).fixed_temperature_k == value
        assert Link("ab", "a", "b", value).conductance_w_k == value
        assert Node("source", -value).power_w == -value


def test_none_is_only_valid_for_unspecified_temperature():
    with pytest.raises(ValueError):
        Node("a", power_w=None)
    with pytest.raises(ValueError):
        Link("ab", "a", "b", None)


@pytest.mark.parametrize("sign", [-1, 1])
def test_nonzero_power_cannot_underflow_to_a_zero_boundary_load(sign):
    tiny = Fraction(sign, 10**1000)
    with pytest.raises(ValueError, match="below the float range"):
        Node("sink", power_w=tiny, fixed_temperature_k=300)


def test_self_link_is_rejected():
    with pytest.raises(ValueError, match="distinct"):
        Link("loop", "a", "a", 2)


@pytest.mark.parametrize("collection", [None, "a", {}, ["a"], (1,)])
def test_wrong_collections_or_members(collection):
    with pytest.raises(ValueError, match="tuple or list"):
        Network(collection)
    with pytest.raises(ValueError, match="tuple or list"):
        Network((Node("a"),), collection)


def test_empty_network_is_rejected():
    with pytest.raises(ValueError, match="nonempty"):
        Network(())


def test_duplicate_nodes_including_conflicting_boundaries():
    with pytest.raises(ValueError, match="duplicate IDs in nodes"):
        Network((Node("a"), Node("a")))
    with pytest.raises(ValueError, match="duplicate IDs in nodes"):
        Network((Node("sink", fixed_temperature_k=300), Node("sink", 0, 310)))


def test_duplicate_links_including_reversed_endpoints():
    with pytest.raises(ValueError, match="duplicate IDs in links"):
        Network(
            (Node("a"), Node("b")),
            (Link("ab", "a", "b", 1), Link("ab", "b", "a", 2)),
        )


@pytest.mark.parametrize("endpoints", [("missing", "b"), ("a", "missing")])
def test_missing_endpoints(endpoints):
    with pytest.raises(ValueError, match="missing node"):
        Network((Node("a"), Node("b")), (Link("ab", *endpoints, 1),))


def test_parallel_paths_and_separate_case_sensitive_id_namespaces():
    network = Network(
        (Node("a", 5), Node("A", 0, 300)),
        (Link("a", "a", "A", 2), Link("parallel", "A", "a", 3)),
    )
    assert [link.conductance_w_k for link in network.links] == [2.0, 3.0]
    assert [node.id for node in network.nodes] == ["a", "A"]


def test_collections_are_copied_and_records_are_frozen():
    nodes = [Node("a"), Node("b")]
    links = [Link("ab", "a", "b", 1)]
    network = Network(nodes, links)
    nodes.clear()
    links.clear()
    assert len(network.nodes) == 2
    assert len(network.links) == 1
    assert isinstance(network.nodes, tuple)
    assert isinstance(network.links, tuple)
    for record, field, replacement in (
        (network, "nodes", ()),
        (network.nodes[0], "power_w", 2),
        (network.links[0], "conductance_w_k", -1),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(record, field, replacement)


def test_unanchored_and_isolated_records_do_not_claim_solvability():
    network = Network((Node("isolated", 5), Node("other", -5)))
    assert network.links == ()
    assert all(node.fixed_temperature_k is None for node in network.nodes)
