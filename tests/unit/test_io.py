"""Strict case decoding and normalized input round trips."""

import json
import math

import pytest

from thermalpath import Link, Network, Node, dumps_case, loads_case


def case_text(**changes):
    case = {"schema_version": 1, "nodes": [{"id": "a"}], "links": []}
    case.update(changes)
    return json.dumps(case)


def test_defaults_and_unanchored_input():
    assert loads_case(case_text()) == Network((Node("a"),))


def test_round_trip_preserves_normalized_inputs_and_order():
    network = Network(
        (
            Node("source", math.nextafter(10.0, math.inf)),
            Node("sink", -2.0),
            Node("bath-\u03b1", fixed_temperature_k=300.1),
        ),
        (
            Link("z", "source", "sink", 0.1),
            Link("a", "bath-\u03b1", "sink", 2.0),
            Link("parallel", "source", "sink", 3.0),
        ),
    )
    encoded = dumps_case(network)
    assert encoded.endswith("\n")
    assert loads_case(encoded) == network
    assert dumps_case(loads_case(encoded)) == encoded
    assert json.loads(encoded)["nodes"][2]["power_w"] == 0.0


@pytest.mark.parametrize("version", [0, 2, -1, "1", None, True, 1.0, [], {}])
def test_reject_version(version):
    with pytest.raises(ValueError, match="schema_version"):
        loads_case(case_text(schema_version=version))


@pytest.mark.parametrize(
    "text",
    [
        "",
        "{",
        "{} trailing",
        "[]",
        "null",
        "true",
        "3",
        "{}",
        '{"schema_version":1,"nodes":[],"links":[],"extra":0}',
        '{"schema_version":1,"schema_version":1,"nodes":[],"links":[]}',
        '{"schema_version":1,"nodes":[{"id":"a","id":"b"}],"links":[]}',
    ],
)
def test_reject_malformed_json(text):
    with pytest.raises(ValueError):
        loads_case(text)


@pytest.mark.parametrize("field", ["nodes", "links"])
@pytest.mark.parametrize("value", [None, {}, 1, "[]", True])
def test_reject_non_arrays(field, value):
    with pytest.raises(ValueError, match="array"):
        loads_case(case_text(**{field: value}))


@pytest.mark.parametrize(
    "nodes",
    [
        [],
        [None],
        [[]],
        [{}],
        [{"id": "a", "power": 1}],
        [{"id": "a", "power_w": True}],
        [{"id": "a", "power_w": "10"}],
        [{"id": "a", "fixed_temperature_k": 0}],
        [{"id": " a"}],
        [{"id": "a"}, {"id": "a"}],
        [{"id": "a", "power_w": 1, "fixed_temperature_k": 300}],
    ],
)
def test_reject_node_inputs(nodes):
    with pytest.raises(ValueError):
        loads_case(case_text(nodes=nodes))


@pytest.mark.parametrize(
    "link",
    [
        None,
        [],
        {},
        {"id": "g", "node_a": "a", "node_b": "b", "conductance_w_k": 1},
        {"id": "g", "node_a": "a", "node_b": "a", "conductance_w_k": 1},
        {"id": "g", "node_a": "a", "node_b": "b", "conductance_w_k": 0},
        {"id": "g", "node_a": "a", "node_b": "b", "conductance_w_k": 1, "unit": "W/K"},
    ],
)
def test_reject_link_inputs(link):
    with pytest.raises(ValueError):
        loads_case(case_text(links=[link]))


@pytest.mark.parametrize(
    "token", ["NaN", "Infinity", "-Infinity", "1e400", "1e-400", "-1e-400", "9" * 400]
)
def test_reject_unrepresentable_numbers(token):
    text = case_text(nodes=[{"id": "a", "power_w": "TOKEN"}])
    with pytest.raises(ValueError):
        loads_case(text.replace('"TOKEN"', token))


@pytest.mark.parametrize("token", ["0.0", "-0.0", "0e-400", "5e-324", "-5e-324"])
def test_zero_and_representable_small_numbers(token):
    text = case_text(nodes=[{"id": "a", "power_w": "TOKEN"}])
    network = loads_case(text.replace('"TOKEN"', token))
    assert network.nodes[0].power_w == float(token)
    assert loads_case(dumps_case(network)) == network


def test_api_wrong_types():
    with pytest.raises(ValueError, match="string"):
        loads_case(b"{}")
    with pytest.raises(ValueError, match="Network"):
        dumps_case({})
