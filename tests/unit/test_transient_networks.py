"""Domain, interval semantics, boundaries, and numerical failure tests."""

from fractions import Fraction
from types import SimpleNamespace

import numpy as np
import pytest

from thermalpath import Link, Network, Node, solve_transient, transient_networks

pytestmark = pytest.mark.parametrize("backend", ["dense", "sparse"])


def isolated(**overrides):
    arguments = dict(
        network=Network((Node("a", power_w=2),)),
        heat_capacities_j_k={"a": 2},
        initial_temperatures_k={"a": 300},
        times_s=[0, 1, 3],
    )
    arguments.update(overrides)
    return solve_transient(**arguments)


def test_constant_and_piecewise_isolated_loads(backend):
    assert [r["a"] for r in isolated(backend=backend).temperatures_k] == [300, 301, 303]
    result = isolated(interval_powers_w=[{"a": 4}, {"a": -2}], backend=backend)
    assert result.times_s == (0, 1, 3)
    assert [r["a"] for r in result.temperatures_k] == [300, 302, 300]


@pytest.mark.parametrize("name", ["heat_capacities_j_k", "initial_temperatures_k"])
@pytest.mark.parametrize(
    "value",
    [
        None,
        [],
        {},
        {"extra": 2},
        {"a": 2, "extra": 3},
        {"a": 0},
        {"a": -1},
        {"a": True},
        {"a": float("nan")},
        {"a": float("inf")},
        {"a": "2"},
        {"a": Fraction(1, 10**400)},
    ],
)
def test_invalid_node_maps(backend, name, value):
    with pytest.raises(ValueError):
        isolated(**{name: value}, backend=backend)


@pytest.mark.parametrize(
    "times",
    [
        None,
        1,
        [],
        [0],
        [0, 0],
        [2, 1],
        [-1, 1],
        [0, True],
        [0, float("nan")],
        [0, float("inf")],
        [0, "1"],
        [0, 1, 1],
    ],
)
def test_invalid_times(backend, times):
    with pytest.raises(ValueError):
        isolated(times_s=times, backend=backend)


@pytest.mark.parametrize(
    "loads",
    [
        2,
        {},
        [],
        [{"a": 2}],
        [{"a": 2}] * 3,
        [{}, {"a": 2}],
        [{"a": 2}, {"b": 1}],
        [{"a": 2}, {"a": float("nan")}],
        [{"a": 2}, {"a": True}],
        [{"a": 2}, {"a": float("inf")}],
    ],
)
def test_invalid_interval_loads(backend, loads):
    with pytest.raises(ValueError):
        isolated(interval_powers_w=loads, backend=backend)


def test_invalid_network(backend):
    with pytest.raises(ValueError, match="Network"):
        isolated(network=None, backend=backend)


def test_inputs_and_rows_are_independent(backend):
    capacities = {"a": 2}
    initial = {"a": 300}
    loads = [{"a": 4}, {"a": -2}]
    result = isolated(
        heat_capacities_j_k=capacities,
        initial_temperatures_k=initial,
        interval_powers_w=loads,
        backend=backend,
    )
    result.temperatures_k[1]["a"] = 1
    assert result.temperatures_k[0] == initial == {"a": 300}
    assert result.temperatures_k[2] == {"a": 300}
    assert capacities == {"a": 2} and loads == [{"a": 4}, {"a": -2}]


def test_fixed_nodes_and_all_fixed_network(backend):
    network = Network(
        (Node("hot", fixed_temperature_k=400), Node("cold", fixed_temperature_k=300)),
        (Link("q", "hot", "cold", 2),),
    )
    result = solve_transient(network, {}, {}, [0, 1, 2], [{}, {}], backend=backend)
    assert result.temperatures_k == ({"hot": 400, "cold": 300},) * 3
    with pytest.raises(ValueError, match="nonfixed"):
        solve_transient(network, {"hot": 1}, {}, [0, 1], backend=backend)


def test_disconnected_nodes_are_allowed(backend):
    network = Network(
        (Node("a", power_w=2), Node("b"), Node("fixed", fixed_temperature_k=280))
    )
    result = solve_transient(
        network, {"a": 2, "b": 1}, {"a": 300, "b": 310}, [5, 7], backend=backend
    )
    assert result.temperatures_k[-1] == {"a": 302, "b": 310, "fixed": 280}


@pytest.mark.parametrize("power", [-600, -1000])
def test_nonpositive_temperature_rejected(backend, power):
    with pytest.raises(ValueError, match="positive"):
        isolated(interval_powers_w=[{"a": power}, {"a": 0}], backend=backend)


@pytest.mark.parametrize(
    "capacities,times",
    [({"a": 1e308}, [0, 1e-300]), ({"a": 1e-300}, [0, 1e300]), ({"a": 1e308}, [0, 1])],
)
def test_storage_arithmetic_range(backend, capacities, times):
    with pytest.raises(ValueError, match="float range"):
        isolated(heat_capacities_j_k=capacities, times_s=times, backend=backend)


def test_boundary_arithmetic_range(backend):
    network = Network(
        (Node("a"), Node("b", fixed_temperature_k=300)), (Link("ab", "a", "b", 1e308),)
    )
    with pytest.raises(ValueError, match="float range"):
        isolated(network=network, backend=backend)


def test_lost_capacity_can_make_insulated_matrix_singular(backend):
    network = Network((Node("a"), Node("b")), (Link("ab", "a", "b", 1e20),))
    with pytest.raises(ValueError, match="singular"):
        solve_transient(
            network, {"a": 1, "b": 1}, {"a": 300, "b": 300}, [0, 1], backend=backend
        )


def test_nonfinite_solver_output_is_rejected(backend, monkeypatch):
    monkeypatch.setattr(np.linalg, "solve", lambda a, b: np.array([np.nan]))
    monkeypatch.setattr(
        transient_networks,
        "splu",
        lambda matrix: SimpleNamespace(solve=lambda rhs: np.array([np.nan])),
    )
    with pytest.raises(ValueError, match="finite"):
        isolated(backend=backend)


def test_rounded_away_temperature_rise_is_not_an_accuracy_claim(backend):
    result = isolated(interval_powers_w=[{"a": 1e-20}, {"a": 1e-20}], backend=backend)
    assert result.temperatures_k[-1]["a"] == 300
