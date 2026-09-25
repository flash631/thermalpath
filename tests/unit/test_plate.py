"""Plate input domains, limiting cases and outward-flow conventions."""

import math
from dataclasses import FrozenInstanceError

import pytest

from thermalpath import PlateResult, RectangularGrid, solve_plate


@pytest.fixture
def grid():
    return RectangularGrid((0, 1, 3), (0, 2, 3), 0.5)


@pytest.mark.parametrize("value", [True, "6", None, 0, -1, float("nan"), float("inf")])
def test_invalid_conductivity(grid, value):
    with pytest.raises(ValueError, match="conductivity"):
        solve_plate(grid, value, west_k=300)


@pytest.mark.parametrize("side", ["west_k", "east_k", "south_k", "north_k"])
@pytest.mark.parametrize("value", [True, "300", 0, -1, float("nan"), float("inf")])
def test_invalid_edge_temperature(grid, side, value):
    with pytest.raises(ValueError, match="temperature"):
        solve_plate(grid, 6, **{side: value})


def test_invalid_grid():
    with pytest.raises(ValueError, match="RectangularGrid"):
        solve_plate(None, 6, west_k=300)


def test_all_insulated_has_no_unique_temperature(grid):
    with pytest.raises(ValueError, match="at least one fixed"):
        solve_plate(grid, 6)


@pytest.mark.parametrize("side", ["west_k", "east_k", "south_k", "north_k"])
def test_one_anchor_recovers_constant_field(grid, side):
    result = solve_plate(grid, 6, **{side: 321})
    assert result.temperatures_k == pytest.approx([321] * 4, rel=0, abs=2e-12)
    for cell in result.face_powers_w:
        assert cell == pytest.approx([0] * 4, rel=0, abs=5e-11)
    for i in range(4):
        for face, neighbor in enumerate(grid.neighbors(i)):
            if neighbor is None and face != [
                "west_k",
                "east_k",
                "south_k",
                "north_k",
            ].index(side):
                assert result.face_powers_w[i][face] == 0


def test_single_cell_weighted_edges_and_corner_faces():
    grid = RectangularGrid((0, 2), (0, 1), 0.5)
    result = solve_plate(grid, 4, west_k=300, east_k=320, south_k=280, north_k=340)
    # Conductances 2, 2, 8, 8 W/K give the weighted mean 310 K.
    assert result.temperatures_k == pytest.approx((310,), rel=0, abs=2e-12)
    assert result.face_powers_w[0] == pytest.approx(
        (20, -20, 240, -240), rel=0, abs=5e-11
    )
    assert isinstance(result, PlateResult)
    with pytest.raises(FrozenInstanceError):
        result.temperatures_k = (1,)


@pytest.mark.parametrize("conductivity", [1e308, 5e-324])
def test_conductance_range_failure(conductivity):
    # 2 m2 face: first overflows; 0.125 m2 face: second rounds to zero.
    thickness = 2 if conductivity > 1 else 0.125
    grid = RectangularGrid((0, 1), (0, 1), thickness)
    with pytest.raises(ValueError, match="face conductance"):
        solve_plate(grid, conductivity, west_k=300)


def test_underlying_matrix_overflow_remains_an_error():
    grid = RectangularGrid((0, 1), (0, 1), 1)
    with pytest.raises(ValueError, match="steady system"):
        solve_plate(grid, 1e307, west_k=300)


def test_tiny_boundary_difference_can_lose_cell_temperature_change():
    grid = RectangularGrid((0, 1), (0, 1), 1)
    warmer = math.nextafter(300.0, math.inf)
    result = solve_plate(grid, 1, west_k=300, east_k=warmer)
    assert result.temperatures_k == (300.0,)
    assert result.face_powers_w[0] == (0.0, -2 * (warmer - 300), 0.0, 0.0)
    assert math.fsum(result.face_powers_w[0]) != 0
