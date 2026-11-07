"""Sparse factor lifetime, operator changes, compatibility and failure checks."""

from fractions import Fraction as F
from types import SimpleNamespace

import numpy as np
import pytest

from thermalpath import Link, Network, Node, solve_transient, transient_networks


def _single(g=1, capacity=2, *, times=(0, 0.5, 1), loads=None, backend="sparse"):
    network = Network(
        (Node("a"), Node("bath", fixed_temperature_k=300)),
        (Link("ab", "a", "bath", g),),
    )
    return solve_transient(
        network, {"a": capacity}, {"a": 310}, times, loads, backend=backend
    )


def _track_factors(monkeypatch):
    calls = []
    original = transient_networks.splu

    def factor(matrix):
        entry = {"matrix": matrix.copy(), "solves": 0}
        calls.append(entry)
        lu = original(matrix)

        def solve(rhs):
            entry["solves"] += 1
            return lu.solve(rhs)

        return SimpleNamespace(solve=solve)

    monkeypatch.setattr(transient_networks, "splu", factor)
    return calls


def test_load_changes_reuse_one_factor_with_exact_reference(monkeypatch):
    calls = _track_factors(monkeypatch)
    powers = (4, -2, 0, 8)
    result = _single(times=(0, 0.5, 1, 1.5, 2), loads=[{"a": p} for p in powers])
    rise = F(10)
    for row, power in zip(result.temperatures_k[1:], powers, strict=True):
        rise = (4 * rise + power) / 5
        assert row["a"] == pytest.approx(float(300 + rise), rel=0, abs=2e-12)
    assert [call["solves"] for call in calls] == [4]
    assert calls[0]["matrix"][0, 0] == 5


def test_changed_step_replaces_factor_even_when_old_step_returns(monkeypatch):
    calls = _track_factors(monkeypatch)
    result = _single(times=(0, 0.5, 1, 2, 3, 3.5, 4))
    rise = F(10)
    for row, dt in zip(
        result.temperatures_k[1:],
        (F(1, 2),) * 2 + (F(1),) * 2 + (F(1, 2),) * 2,
        strict=True,
    ):
        rise /= 1 + dt / 2
        assert row["a"] == pytest.approx(float(300 + rise), rel=0, abs=2e-12)
    assert [call["solves"] for call in calls] == [2, 2, 2]
    assert [call["matrix"][0, 0] for call in calls] == [5, 3, 5]


def test_nearby_but_distinct_steps_are_not_merged(monkeypatch):
    calls = _track_factors(monkeypatch)
    times = (0, 1, float(np.nextafter(2.0, 3.0)))
    assert times[1] - times[0] != times[2] - times[1]
    _single(times=times)
    assert [call["solves"] for call in calls] == [1, 1]


def test_new_calls_rebuild_after_conductance_capacity_and_input_changes(monkeypatch):
    calls = _track_factors(monkeypatch)
    for g, capacity in ((1, 2), (2, 2), (2, 4), (1, 2)):
        result = _single(g, capacity, times=(0, 0.5))
        expected = 300 + F(10) / (1 + F(g, 2 * capacity))
        assert result.temperatures_k[-1]["a"] == pytest.approx(
            float(expected), rel=0, abs=2e-12
        )
    assert [call["solves"] for call in calls] == [1] * 4
    assert [call["matrix"][0, 0] for call in calls] == [5, 6, 10, 5]


@pytest.mark.parametrize("reverse", [False, True])
def test_new_calls_rebuild_after_topology_order_and_fixed_partition_changes(
    monkeypatch, reverse
):
    calls = _track_factors(monkeypatch)
    nodes = [Node("a"), Node("b")]
    if reverse:
        nodes.reverse()
    for linked in (False, True):
        network = Network(nodes, (Link("ab", "a", "b", 1),) if linked else ())
        result = solve_transient(
            network,
            {"a": 2, "b": 2},
            {"a": 310, "b": 290},
            [0, 1],
            backend="sparse",
        )
        assert list(result.temperatures_k[-1]) == [n.id for n in nodes]
        expected = {"a": 305, "b": 295} if linked else {"a": 310, "b": 290}
        assert result.temperatures_k[-1] == pytest.approx(expected, rel=0, abs=2e-12)
    network = Network(
        (Node("a"), Node("b", fixed_temperature_k=290)),
        (Link("ab", "a", "b", 1),),
    )
    result = solve_transient(network, {"a": 2}, {"a": 310}, [0, 1], backend="sparse")
    assert result.temperatures_k[-1]["a"] == pytest.approx(
        float(F(910, 3)), rel=0, abs=2e-12
    )
    assert [call["matrix"].shape for call in calls] == [(2, 2), (2, 2), (1, 1)]


def test_default_is_dense_and_all_fixed_sparse_needs_no_factor(monkeypatch):
    def forbidden(matrix):
        raise AssertionError("Unexpected sparse factorization")

    monkeypatch.setattr(transient_networks, "splu", forbidden)
    network = Network((Node("a"),))
    args = network, {"a": 2}, {"a": 300}, [0, 1]
    assert solve_transient(*args) == solve_transient(*args, backend="dense")
    fixed = Network((Node("bath", fixed_temperature_k=300),))
    assert solve_transient(fixed, {}, {}, [0, 1], backend="sparse").temperatures_k == (
        {"bath": 300},
        {"bath": 300},
    )


@pytest.mark.parametrize("backend", [None, True, 1, [], {}, "auto", "SPARSE"])
def test_invalid_backend(backend):
    with pytest.raises(ValueError, match="backend"):
        _single(backend=backend)


@pytest.mark.parametrize("failure_at", ["factor", "solve"])
def test_sparse_runtime_failure_becomes_value_error(monkeypatch, failure_at):
    def fail(*args):
        raise RuntimeError("synthetic numerical failure")

    monkeypatch.setattr(
        transient_networks,
        "splu",
        fail if failure_at == "factor" else lambda matrix: SimpleNamespace(solve=fail),
    )
    with pytest.raises(ValueError, match="singular or outside float range"):
        _single()


def test_sparse_diagonal_storage_sum_overflow_is_rejected():
    network = Network((Node("a"), Node("b")), (Link("ab", "a", "b", 1e308),))
    with pytest.raises(ValueError, match="float range"):
        solve_transient(
            network,
            {"a": 1e308, "b": 1e308},
            {"a": 0.5, "b": 0.5},
            [0, 1],
            backend="sparse",
        )
