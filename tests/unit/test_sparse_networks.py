"""Sparse backend selection, factor reuse and numerical failure handling."""

from types import SimpleNamespace

import numpy as np
import pytest

from thermalpath import Link, Network, Node, networks, solve_steady


def _one_node():
    return Network(
        [Node("a", power_w=10), Node("sink", fixed_temperature_k=300)],
        [Link("path", "a", "sink", 2)],
    )


@pytest.mark.parametrize("backend", [None, "", "auto", "Sparse", 1, [], {}])
def test_invalid_backend(backend):
    with pytest.raises(ValueError, match="backend must be"):
        solve_steady(_one_node(), backend=backend)


def test_dense_default_does_not_factor_sparse_matrix(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Dense default requested a sparse factorization")

    monkeypatch.setattr(networks, "splu", forbidden)
    assert solve_steady(_one_node()) == solve_steady(_one_node(), backend="dense")


@pytest.mark.parametrize(
    "correction, expected",
    [
        (-1.0, 305.0),
        (-1000.0, 306.0),
        (np.nan, 306.0),
        (2.0, 306.0),
        (0.0, 306.0),
        (RuntimeError(), 306.0),
    ],
)
def test_sparse_correction_reuses_one_factor(monkeypatch, correction, expected):
    factor_calls = []
    solve_calls = []

    def factor(matrix):
        factor_calls.append(matrix)
        assert matrix.format == "csc"

        def solve(rhs):
            solve_calls.append(rhs.copy())
            if len(solve_calls) == 1:
                return np.array([306.0])
            if isinstance(correction, Exception):
                raise correction
            return np.array([correction])

        return SimpleNamespace(solve=solve)

    monkeypatch.setattr(networks, "splu", factor)
    result = solve_steady(_one_node(), backend="sparse")
    assert len(factor_calls) == 1
    assert len(solve_calls) == 2
    assert solve_calls[0] == pytest.approx([610.0])
    assert solve_calls[1] == pytest.approx([-2.0])
    assert result.temperatures_k["a"] == expected
    assert result.linear_residual_w["a"] == 610 - 2 * expected


def test_sparse_factorization_failure_is_domain_error(monkeypatch):
    def singular(matrix):
        raise RuntimeError("Synthetic singular factorization")

    monkeypatch.setattr(networks, "splu", singular)
    with pytest.raises(ValueError, match="system is singular or outside float range"):
        solve_steady(_one_node(), backend="sparse")


def test_sparse_nonfinite_linear_residual_is_rejected(monkeypatch):
    monkeypatch.setattr(
        networks, "splu", lambda a: SimpleNamespace(solve=lambda b: np.array([1e308]))
    )
    with pytest.raises(ValueError, match="linear residual is outside float range"):
        solve_steady(_one_node(), backend="sparse")


def test_all_fixed_sparse_network_needs_no_factorization(monkeypatch):
    def forbidden(matrix):
        raise AssertionError("Fixed-only network must not be factorized")

    monkeypatch.setattr(networks, "splu", forbidden)
    result = solve_steady(
        Network([Node("fixed", fixed_temperature_k=300)]), backend="sparse"
    )
    assert result.temperatures_k == {"fixed": 300.0}
    assert result.linear_residual_w == {}
