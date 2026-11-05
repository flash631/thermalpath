"""Sparse plate storage bounds, analytical fields and backend compatibility."""

import numpy as np
import pytest
from scipy.sparse import csc_array, dok_array

from thermalpath import (
    Convection,
    RectangularGrid,
    RectangularHeater,
    networks,
    solve_plate,
)


def test_mixed_plate_results_agree_between_backends():
    grid = RectangularGrid((0, 0.01, 0.03, 0.06), (0, 0.01, 0.04), 0.002)
    inputs = dict(
        west_k=300,
        edge_flux_w_m2={"south": -200},
        edge_convection={"east": Convection(12, 295)},
        face_convection=Convection(8, 290),
        heaters=[RectangularHeater(0.005, 0.045, 0.005, 0.035, 1.25)],
    )
    dense, sparse = (
        solve_plate(grid, (2, 4, 8, 16, 32, 64), backend=backend, **inputs)
        for backend in ("dense", "sparse")
    )
    assert sparse.temperatures_k == pytest.approx(
        dense.temperatures_k, rel=0, abs=2e-10
    )
    for expected, actual in zip(dense.face_powers_w, sparse.face_powers_w, strict=True):
        assert actual == pytest.approx(expected, rel=0, abs=2e-9)
    assert sparse.broad_face_powers_w == pytest.approx(
        dense.broad_face_powers_w, rel=0, abs=2e-9
    )
    for field in (
        "heater_input_w",
        "edge_outflow_w",
        "broad_face_outflow_w",
        "cell_residual_w",
        "linear_residual_w",
        "imbalance_w",
    ):
        assert getattr(sparse.balance, field) == pytest.approx(
            getattr(dense.balance, field), rel=0, abs=2e-9
        )


@pytest.mark.parametrize("nx,ny", [(8, 6), (32, 24), (64, 48)])
def test_sparse_plate_storage_and_independent_linear_field(monkeypatch, nx, ny):
    size = nx * ny
    captured = []
    original_factor = networks.splu

    def factor(matrix):
        assert matrix.format == "csc"
        assert matrix.nnz == 5 * size - 2 * nx - 2 * ny
        storage = matrix.data.nbytes + matrix.indices.nbytes + matrix.indptr.nbytes
        assert storage <= 88 * size
        captured.append((matrix.nnz, storage))
        return original_factor(matrix)

    def forbidden(*args, **kwargs):
        raise AssertionError("Sparse plate attempted a dense solve or conversion")

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
    grid = RectangularGrid(
        tuple(0.06 * i / nx for i in range(nx + 1)),
        tuple(0.04 * j / ny for j in range(ny + 1)),
        0.002,
    )
    result = solve_plate(grid, 10, west_k=300, east_k=320, backend="sparse")
    assert len(captured) == 1
    # Integrate T''=0 independently: linear T and constant -k*t*dT/dx.
    for cell, temperature in enumerate(result.temperatures_k):
        x, _ = grid.center_m(cell)
        assert abs(temperature - (300 + 20 * x / 0.06)) <= 2e-8
        power = 10 * 0.002 * (0.04 / ny) * 20 / 0.06
        assert result.face_powers_w[cell] == pytest.approx(
            (power, -power, 0, 0), rel=0, abs=2e-9
        )
    assert result.broad_face_powers_w == (0,) * size
    assert max(map(abs, result.balance.cell_residual_w)) <= 2e-9
    assert max(map(abs, result.balance.linear_residual_w)) <= 2e-9
    assert abs(result.balance.imbalance_w) <= 2e-8
