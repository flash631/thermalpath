"""Transient plate API, physical domains and inherited solver behavior."""

from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import numpy as np
import pytest

from thermalpath import (
    Convection,
    RectangularGrid,
    RectangularHeater,
    TransientPlateResult,
    solve_plate,
    solve_transient_plate,
    transient_networks,
)


@pytest.fixture(params=["dense", "sparse"])
def backend(request):
    return request.param


def test_scalar_inputs_and_positive_initial_time(backend):
    grid = RectangularGrid((0, 1, 3), (0, 2), 0.5)
    result = solve_transient_plate(grid, 2, 4, 310, [2, 2.25, 3], backend=backend)
    assert isinstance(result, TransientPlateResult)
    assert result.times_s == (2, 2.25, 3)
    for row in result.temperatures_k:
        assert row == pytest.approx((310, 310), abs=2e-10, rel=0)
    assert len(result.energy_balances) == 2
    assert tuple(result.energy_balances[0].storage_j) == ("0", "1")
    assert result.energy_balances[0].boundary_j == {}
    with pytest.raises(FrozenInstanceError):
        result.times_s = (0, 1)


def test_inputs_are_copied_and_energy_rows_are_independent(backend):
    grid = RectangularGrid((0, 1, 3), (0, 2, 3), 0.5)
    capacity = [2, 3, 4, 5]
    initial = [301, 302, 303, 304]
    times = [0, 0.25, 0.5]
    result = solve_transient_plate(
        grid, [1, 2, 3, 4], capacity, initial, times, backend=backend
    )
    assert result.temperatures_k[0] == tuple(initial)
    assert tuple(result.energy_balances[0].storage_j) == ("0", "1", "2", "3")
    assert capacity == [2, 3, 4, 5]
    assert initial == [301, 302, 303, 304]
    capacity[0] = initial[0] = times[0] = -1
    assert result.times_s[0] == 0
    assert result.temperatures_k[0][0] == 301
    result.energy_balances[0].storage_j["0"] = -999
    assert result.energy_balances[1].storage_j["0"] != -999


@pytest.mark.parametrize("name", ["capacity", "initial"])
@pytest.mark.parametrize(
    "value",
    [
        0,
        -1,
        True,
        None,
        "300",
        b"300",
        {},
        [],
        [1],
        [1, 0],
        [1, float("nan")],
        float("inf"),
        float("nan"),
        np.array([1, 2]),
    ],
)
def test_invalid_cell_values(backend, name, value):
    grid = RectangularGrid((0, 1, 2), (0, 1), 1)
    capacity = value if name == "capacity" else 10
    initial = value if name == "initial" else 300
    with pytest.raises(ValueError, match="volumetric|initial"):
        solve_transient_plate(grid, 1, capacity, initial, [0, 1], backend=backend)


@pytest.mark.parametrize("thickness,capacity", [(2, 1e308), (1e-200, 1e-200)])
def test_unrepresentable_cell_heat_capacity(backend, thickness, capacity):
    grid = RectangularGrid((0, 1), (0, 1), thickness)
    with pytest.raises(ValueError, match="cell heat capacity"):
        solve_transient_plate(grid, 1, capacity, 300, [0, 1], backend=backend)


@pytest.mark.parametrize(
    "times",
    [
        [],
        [0],
        [1, 0],
        [0, 0],
        [-1, 1],
        [0, float("inf")],
        [0, float("nan")],
        [0, True],
        "01",
        None,
    ],
)
def test_invalid_times(backend, times):
    with pytest.raises(ValueError, match="times_s"):
        solve_transient_plate(
            RectangularGrid((0, 1), (0, 1), 1), 1, 1, 300, times, backend=backend
        )


@pytest.mark.parametrize("backend", [None, "auto", "Sparse", [], 1])
def test_invalid_backend(backend):
    with pytest.raises(ValueError, match="backend"):
        solve_transient_plate(
            RectangularGrid((0, 1), (0, 1), 1), 1, 1, 300, [0, 1], backend=backend
        )


@pytest.mark.parametrize(
    "conductivity,boundaries,message",
    [
        (0, {}, "conductivity"),
        ([1, 2], {}, "conductivity sequence"),
        (1, {"west_k": 0}, "temperature"),
        (1, {"west_k": 300, "edge_flux_w_m2": {"west": 0}}, "boundary type"),
        (1, {"edge_convection": {"west": None}}, "Convection"),
        (1, {"edge_flux_w_m2": {"typo": 0}}, "map west"),
        (1, {"face_convection": 3}, "Convection"),
        (1, {"heaters": [RectangularHeater(0, 2, 0, 1, 1)]}, "inside"),
    ],
)
def test_shared_plate_domains(backend, conductivity, boundaries, message):
    with pytest.raises(ValueError, match=message):
        solve_transient_plate(
            RectangularGrid((0, 1), (0, 1), 1),
            conductivity,
            1,
            300,
            [0, 1],
            backend=backend,
            **boundaries,
        )


def test_invalid_grid(backend):
    with pytest.raises(ValueError, match="RectangularGrid"):
        solve_transient_plate(None, 1, 1, 300, [0, 1], backend=backend)


def test_extraction_can_make_temperature_invalid(backend):
    with pytest.raises(ValueError, match="temperatures must be"):
        solve_transient_plate(
            RectangularGrid((0, 1), (0, 1), 1),
            1,
            1,
            1,
            [0, 1],
            edge_flux_w_m2={"west": 2},
            backend=backend,
        )


def test_zero_convection_matches_insulation(backend):
    grid = RectangularGrid((0, 1, 2), (0, 1), 0.5)
    args = (grid, 1, (2, 3), (300, 320), (0, 0.25, 0.5))
    assert solve_transient_plate(*args, backend=backend) == solve_transient_plate(
        *args,
        edge_convection={"north": Convection(0, 900)},
        face_convection=Convection(0, 800),
        backend=backend,
    )


def test_dense_is_default(monkeypatch):
    def forbidden(matrix):
        raise AssertionError("Default integration requested sparse factorization")

    monkeypatch.setattr(transient_networks, "splu", forbidden)
    args = (RectangularGrid((0, 1, 2), (0, 1), 0.5), 1, 2, (300, 320), (0, 0.5))
    assert solve_transient_plate(*args) == solve_transient_plate(*args, backend="dense")


def test_steady_solution_stays_fixed(backend):
    grid = RectangularGrid((0, 1, 3), (0, 1, 2), 0.5)
    boundary = {
        "west_k": 300,
        "east_k": 310,
        "face_convection": Convection(0.25, 295),
        "heaters": [RectangularHeater(0.5, 2, 0.25, 1.5, 6)],
    }
    steady = solve_plate(grid, (2, 4, 3, 6), backend=backend, **boundary)
    result = solve_transient_plate(
        grid,
        (2, 4, 3, 6),
        (8, 6, 4, 10),
        steady.temperatures_k,
        (0, 0.125, 1, 10),
        backend=backend,
        **boundary,
    )
    for row in result.temperatures_k:
        assert row == pytest.approx(steady.temperatures_k, abs=2e-10, rel=0)


def test_sparse_factor_reuse_and_changed_step(monkeypatch):
    original = transient_networks.splu
    factors, solves = [], []

    def factor(matrix):
        factors.append(1)
        lu = original(matrix)

        def solve(rhs):
            solves.append(1)
            return lu.solve(rhs)

        return SimpleNamespace(solve=solve)

    monkeypatch.setattr(transient_networks, "splu", factor)
    args = (RectangularGrid((0, 1, 3), (0, 1), 0.5), 2, (3, 4), (300, 310))
    times = (0, 0.25, 0.5, 1, 1.25)
    solve_transient_plate(*args, times, backend="sparse")
    assert len(factors) == 3
    assert len(solves) == 4
    solve_transient_plate(*args, times, backend="sparse")
    assert len(factors) == 6  # No factor survives a new call.


def test_sparse_factor_failure_is_reported(monkeypatch):
    def fail(matrix):
        raise RuntimeError("Synthetic factorization failure")

    monkeypatch.setattr(transient_networks, "splu", fail)
    with pytest.raises(ValueError, match="transient system"):
        solve_transient_plate(
            RectangularGrid((0, 1), (0, 1), 1), 1, 1, 300, [0, 1], backend="sparse"
        )


def test_energy_range_failure_is_reported(backend):
    # Integration has a representable 302 K field, but dt*heater overflows.
    with pytest.raises(ValueError, match="energy calculation"):
        solve_transient_plate(
            RectangularGrid((0, 1), (0, 1), 1),
            1,
            1,
            302,
            [0, 1e150],
            face_convection=Convection(1e160, 300),
            heaters=[RectangularHeater(0, 1, 0, 1, 2e160)],
            backend=backend,
        )
