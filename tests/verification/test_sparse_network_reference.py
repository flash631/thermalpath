"""Exact synthetic references and bounded sparse storage verification."""

from fractions import Fraction

import numpy as np
import pytest
from scipy.sparse import csc_array, dok_array

from thermalpath import Link, Network, Node, heat_balance, networks, solve_steady


@pytest.mark.parametrize("backend", ["dense", "sparse"])
@pytest.mark.parametrize("reverse", [False, True])
def test_branched_rational_manufactured_network(backend, reverse):
    # Prescribed rational temperatures determine loads through exact individual
    # link laws, independently of either production matrix or linear solver.
    exact = {
        "a": Fraction(907, 3),
        "b": Fraction(1527, 5),
        "c": Fraction(2095, 7),
        "cold": Fraction(300),
        "warm": Fraction(320),
        "d": Fraction(312),
        "other": Fraction(310),
    }
    edges = [
        ("ac", "a", "cold", Fraction(2)),
        ("ab", "a", "b", Fraction(1, 8)),
        ("ab2", "b", "a", Fraction(3, 4)),
        ("bc", "b", "c", Fraction(16)),
        ("ca", "c", "a", Fraction(1, 32)),
        ("bw", "b", "warm", Fraction(4)),
        ("cw", "c", "warm", Fraction(1, 2)),
        ("fixed", "cold", "warm", Fraction(3)),
        ("do", "d", "other", Fraction(5, 2)),
    ]
    powers = {name: Fraction(0) for name in ("a", "b", "c", "d")}
    for _, a, b, conductance in edges:
        power = conductance * (exact[a] - exact[b])
        if a in powers:
            powers[a] += power
        if b in powers:
            powers[b] -= power
    assert min(powers.values()) < 0 < max(powers.values())
    nodes = [
        Node(name, power_w=float(powers[name]))
        if name in powers
        else Node(name, fixed_temperature_k=float(temperature))
        for name, temperature in exact.items()
    ]
    if reverse:
        nodes.reverse()
        edges = [(name, b, a, g) for name, a, b, g in reversed(edges)]
    network = Network(nodes, [Link(name, a, b, float(g)) for name, a, b, g in edges])
    result = solve_steady(network, backend=backend)
    assert list(result.temperatures_k) == [node.id for node in nodes]
    for name, temperature in exact.items():
        assert abs(Fraction(result.temperatures_k[name]) - temperature) <= Fraction(
            2e-10
        )
    for name, a, b, conductance in edges:
        expected = conductance * (exact[a] - exact[b])
        assert abs(Fraction(result.link_powers_w[name]) - expected) <= Fraction(2e-9)
    balance = heat_balance(network, result.link_powers_w)
    assert max(abs(x) for x in balance.node_residual_w.values()) <= 2e-9
    assert abs(balance.imbalance_w) <= 2e-9


def _chain(size):
    nodes = [Node(str(i), power_w=0.125 if i == 0 else 0) for i in range(size)]
    nodes.append(Node(str(size), fixed_temperature_k=300))
    return Network(nodes, [Link(str(i), str(i), str(i + 1), 1) for i in range(size)])


def _check_chain(result, size, temperature_tolerance):
    # Every link carries 1/8 W toward the sink, so each adds exactly 1/8 K.
    for i in range(size + 1):
        assert (
            abs(result.temperatures_k[str(i)] - (300 + (size - i) / 8))
            <= temperature_tolerance
        )
    assert max(abs(q - 0.125) for q in result.link_powers_w.values()) <= 2e-9
    assert max(abs(r) for r in result.linear_residual_w.values()) <= 2e-9


@pytest.mark.parametrize("size", [32, 128])
def test_chain_exact_reference_and_dense_agreement(size):
    network = _chain(size)
    dense = solve_steady(network)
    sparse = solve_steady(network, backend="sparse")
    for result in (dense, sparse):
        _check_chain(result, size, 2e-9)
        balance = heat_balance(network, result.link_powers_w)
        assert max(abs(r) for r in balance.node_residual_w.values()) <= 2e-9
    assert sparse.temperatures_k == pytest.approx(dense.temperatures_k, abs=2e-9, rel=0)


def test_large_chain_has_sparse_storage_and_exact_reference(monkeypatch):
    size = 4096
    captured = []
    original_factor = networks.splu

    def factor(matrix):
        assert matrix.format == "csc"
        assert matrix.nnz == 3 * size - 2
        storage = matrix.data.nbytes + matrix.indices.nbytes + matrix.indptr.nbytes
        assert storage <= 64 * size
        captured.append((matrix.nnz, storage))
        return original_factor(matrix)

    def forbidden(*args, **kwargs):
        raise AssertionError("Sparse solve attempted a dense solve or conversion")

    def guard_allocation(original):
        def checked(shape, *args, **kwargs):
            if isinstance(shape, (tuple, list)) and len(shape) == 2:
                assert min(shape) < size, "Large dense matrix allocation"
            return original(shape, *args, **kwargs)

        return checked

    monkeypatch.setattr(networks, "splu", factor)
    monkeypatch.setattr(np.linalg, "solve", forbidden)
    for array_type in (csc_array, dok_array):
        monkeypatch.setattr(array_type, "toarray", forbidden)
        monkeypatch.setattr(array_type, "todense", forbidden)
    for allocator in ("zeros", "ones", "empty", "full"):
        monkeypatch.setattr(np, allocator, guard_allocation(getattr(np, allocator)))
    network = _chain(size)
    result = solve_steady(network, backend="sparse")
    assert len(captured) == 1
    _check_chain(result, size, 2e-6)
    balance = heat_balance(network, result.link_powers_w)
    assert max(abs(r) for r in balance.node_residual_w.values()) <= 2e-9
    assert abs(balance.imbalance_w) <= 2e-9
