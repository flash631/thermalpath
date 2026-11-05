"""Plate backend selection and propagation of numerical/domain failures."""

from types import SimpleNamespace

import numpy as np
import pytest

from thermalpath import (
    Convection,
    RectangularGrid,
    RectangularHeater,
    networks,
    solve_plate,
)


@pytest.mark.parametrize("backend", [None, "", "auto", "Sparse", 1, [], {}])
def test_invalid_backend(backend):
    with pytest.raises(ValueError, match="backend must be"):
        solve_plate(RectangularGrid((0, 1), (0, 1), 1), 1, west_k=300, backend=backend)


def test_dense_default_does_not_use_sparse_factorization(monkeypatch):
    def forbidden(matrix):
        raise AssertionError("Dense plate requested sparse factorization")

    monkeypatch.setattr(networks, "splu", forbidden)
    grid = RectangularGrid((0, 1, 3), (0, 2), 0.5)
    assert solve_plate(grid, 2, west_k=300) == solve_plate(
        grid, 2, west_k=300, backend="dense"
    )


@pytest.mark.parametrize(
    "conductivity, boundaries, message",
    [
        (0, {"west_k": 300}, "conductivity"),
        (1, {}, "nonunique"),
        (1, {"heaters": [RectangularHeater(0, 1, 0, 1, 1)]}, "incompatible"),
        (1, {"west_k": 0}, "temperature"),
        (1, {"west_k": 300, "edge_flux_w_m2": {"west": 0}}, "boundary type"),
        (1, {"face_convection": Convection(0, 300)}, "nonunique"),
        (1e307, {"west_k": 300}, "steady system"),
    ],
)
def test_sparse_plate_retains_domain_errors(conductivity, boundaries, message):
    with pytest.raises(ValueError, match=message):
        solve_plate(
            RectangularGrid((0, 1), (0, 1), 1),
            conductivity,
            backend="sparse",
            **boundaries,
        )


def test_sparse_factorization_failure_propagates(monkeypatch):
    def singular(matrix):
        raise RuntimeError("Synthetic factorization failure")

    monkeypatch.setattr(networks, "splu", singular)
    with pytest.raises(ValueError, match="steady system"):
        solve_plate(RectangularGrid((0, 1), (0, 1), 1), 1, west_k=300, backend="sparse")


def test_sparse_plate_preserves_opposite_local_errors(monkeypatch):
    # This is intentionally inaccurate: global balance cancels both local errors.
    monkeypatch.setattr(
        networks,
        "splu",
        lambda matrix: SimpleNamespace(solve=lambda rhs: np.array([302.0, 300.0])),
    )
    result = solve_plate(
        RectangularGrid((0, 1, 3), (0, 2), 0.5),
        3,
        west_k=300,
        east_k=300,
        heaters=[RectangularHeater(0.5, 2, 0.5, 1.5, 12)],
        backend="sparse",
    )
    assert result.balance.cell_residual_w == (-12, 12)
    assert result.balance.linear_residual_w == (-12, 12)
    assert result.balance.imbalance_w == 0
