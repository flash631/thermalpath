"""Manufactured transient paths with bounded sparse assembly and factor reuse."""

from types import SimpleNamespace

import numpy as np
import pytest
from scipy.sparse import csc_array, dok_array

from thermalpath import (
    Link,
    Network,
    Node,
    solve_transient,
    transient_energy_balance,
    transient_networks,
)


@pytest.mark.parametrize("size", [32, 128, 1024])
def test_manufactured_ramp_sparse_storage_and_reuse(monkeypatch, size):
    # T_i(t)=300+i/8+t/4 K, C=2 J/K, G=1 W/K, h=1/2 s.
    # Internal second differences vanish. End nodes need outward-flow
    # adjustments -1/8,+1/8 W in addition to the uniform C*dT/dt=1/2 W.
    network = Network(
        [
            Node(
                str(i),
                power_w=0.5 + (-0.125 if i == 0 else 0.125 if i == size - 1 else 0),
            )
            for i in range(size)
        ],
        [Link(str(i), str(i), str(i + 1), 1) for i in range(size - 1)],
    )
    capacities = {str(i): 2 for i in range(size)}
    initial = {str(i): 300 + i / 8 for i in range(size)}
    captured = []
    solves = []
    original_factor = transient_networks.splu

    def factor(matrix):
        assert matrix.format == "csc"
        assert matrix.nnz == 3 * size - 2
        payload = matrix.data.nbytes + matrix.indices.nbytes + matrix.indptr.nbytes
        assert payload <= 64 * size
        captured.append((matrix.nnz, payload))
        lu = original_factor(matrix)

        def solve(rhs):
            solves.append(1)
            return lu.solve(rhs)

        return SimpleNamespace(solve=solve)

    def forbidden(*args, **kwargs):
        raise AssertionError("Sparse integration attempted dense allocation or solve")

    def guard_allocation(original):
        def checked(shape, *args, **kwargs):
            if isinstance(shape, (tuple, list)) and len(shape) == 2:
                assert min(shape) < size, "Large dense matrix allocation"
            return original(shape, *args, **kwargs)

        return checked

    with monkeypatch.context() as patch:
        patch.setattr(transient_networks, "splu", factor)
        patch.setattr(np.linalg, "solve", forbidden)
        patch.setattr(np, "diag", forbidden)
        for array_type in (csc_array, dok_array):
            patch.setattr(array_type, "toarray", forbidden)
            patch.setattr(array_type, "todense", forbidden)
        for allocator in ("zeros", "ones", "empty", "full"):
            patch.setattr(np, allocator, guard_allocation(getattr(np, allocator)))
        result = solve_transient(
            network, capacities, initial, [i / 2 for i in range(9)], backend="sparse"
        )
    assert len(captured) == 1
    assert len(solves) == 8
    for time, row in zip(result.times_s, result.temperatures_k, strict=True):
        for i in range(size):
            assert abs(row[str(i)] - (300 + i / 8 + time / 4)) <= 2e-10
    for old, new in zip(result.temperatures_k, result.temperatures_k[1:], strict=False):
        report = transient_energy_balance(network, capacities, old, new, 0.5)
        assert max(abs(r) for r in report.node_residual_j.values()) <= 2e-9
        assert abs(report.imbalance_j) <= 2e-6
        assert abs(report.total_storage_j - size / 4) <= 2e-6
    if size <= 128:
        dense = solve_transient(network, capacities, initial, result.times_s)
        for a, b in zip(dense.temperatures_k, result.temperatures_k, strict=True):
            assert a == pytest.approx(b, rel=0, abs=2e-10)
