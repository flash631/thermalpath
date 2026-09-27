"""Boundary domains, exclusive edge definitions and floating-point limits."""

import math
from dataclasses import FrozenInstanceError

import pytest

from thermalpath import Convection, PlateResult, RectangularGrid, solve_plate


@pytest.fixture
def grid():
    return RectangularGrid((0, 1, 3), (0, 2, 3), 0.5)


@pytest.mark.parametrize("value", [True, "2", None, -1, math.nan, math.inf])
def test_invalid_coefficient(value):
    with pytest.raises(ValueError, match="coefficient"):
        Convection(value, 300)


@pytest.mark.parametrize("value", [True, "300", None, 0, -1, math.nan, math.inf])
def test_invalid_ambient_even_when_disabled(value):
    with pytest.raises(ValueError, match="temperature"):
        Convection(0, value)


def test_convection_is_immutable_and_normalized():
    boundary = Convection(2, 300)
    assert type(boundary.coefficient_w_m2_k) is float
    assert type(boundary.ambient_temperature_k) is float
    with pytest.raises(FrozenInstanceError):
        boundary.coefficient_w_m2_k = 3
    assert PlateResult((300,), ((0, 0, 0, 0),)).broad_face_powers_w == ()


@pytest.mark.parametrize("argument", ["edge_flux_w_m2", "edge_convection"])
@pytest.mark.parametrize("value", [[], "west", {"West": 2}, {1: 2}])
def test_invalid_mapping(grid, argument, value):
    with pytest.raises(ValueError, match="must map"):
        solve_plate(grid, 2, east_k=300, **{argument: value})


@pytest.mark.parametrize("value", [None, 2, (2, 300), {"h": 2}])
def test_invalid_edge_convection(grid, value):
    with pytest.raises(ValueError, match="Convection"):
        solve_plate(grid, 2, east_k=300, edge_convection={"west": value})


@pytest.mark.parametrize("value", [2, (2, 300), {"h": 2}])
def test_invalid_face_convection(grid, value):
    with pytest.raises(ValueError, match="Convection"):
        solve_plate(grid, 2, east_k=300, face_convection=value)


@pytest.mark.parametrize("value", [True, "2", None, math.nan, math.inf])
def test_invalid_flux(grid, value):
    with pytest.raises(ValueError, match="edge flux"):
        solve_plate(grid, 2, east_k=300, edge_flux_w_m2={"west": value})


@pytest.mark.parametrize("side", ["west", "east", "south", "north"])
@pytest.mark.parametrize("kind", ["fixed_flux", "fixed_film", "flux_film"])
def test_conflicting_edges_even_at_zero(grid, side, kind):
    arguments = {}
    if kind.startswith("fixed"):
        arguments[side + "_k"] = 300
    if "flux" in kind:
        arguments["edge_flux_w_m2"] = {side: 0}
    if "film" in kind:
        arguments["edge_convection"] = {side: Convection(0, 300)}
    with pytest.raises(ValueError, match="more than one"):
        solve_plate(grid, 2, **arguments)


@pytest.mark.parametrize("flux", [0, 10, -10])
def test_flux_and_disabled_films_do_not_anchor(grid, flux):
    with pytest.raises(ValueError, match="anchor"):
        solve_plate(
            grid,
            2,
            edge_flux_w_m2={"west": flux},
            edge_convection={"east": Convection(0, 300)},
            face_convection=Convection(0, 300),
        )


def test_zero_coefficients_and_zero_flux_match_insulation(grid):
    reference = solve_plate(grid, 2, east_k=300)
    result = solve_plate(
        grid,
        2,
        east_k=300,
        edge_flux_w_m2={"west": 0},
        edge_convection={"north": Convection(0, 350)},
        face_convection=Convection(0, 250),
    )
    assert result == reference
    assert result.broad_face_powers_w == (0,) * 4


@pytest.mark.parametrize("flux,thickness", [(1e308, 2), (5e-324, 0.125)])
def test_flux_product_range(flux, thickness):
    grid = RectangularGrid((0, 1), (0, 1), thickness)
    with pytest.raises(ValueError, match="flux power"):
        solve_plate(grid, 1, east_k=300, edge_flux_w_m2={"west": flux})


def test_flux_sum_range():
    grid = RectangularGrid((0, 1), (0, 1), 1)
    with pytest.raises(ValueError, match="summed flux"):
        solve_plate(
            grid, 1, east_k=300, edge_flux_w_m2={"west": -1e308, "north": -1e308}
        )


@pytest.mark.parametrize("coefficient,width", [(1e308, 2), (5e-324, 0.125)])
def test_broad_conductance_range(coefficient, width):
    grid = RectangularGrid((0, width), (0, 1), 1)
    with pytest.raises(ValueError, match="broad-face conductance"):
        solve_plate(grid, 1, face_convection=Convection(coefficient, 300))


@pytest.mark.parametrize("conductivity,h", [(5e-324, 1), (1e308, 5e-324)])
def test_edge_resistance_range(conductivity, h):
    grid = RectangularGrid((0, 2), (0, 1), 1)
    with pytest.raises(ValueError, match="resistance factor"):
        solve_plate(grid, conductivity, edge_convection={"west": Convection(h, 300)})


def test_extraction_cannot_return_nonpositive_temperature():
    grid = RectangularGrid((0, 1), (0, 1), 1)
    with pytest.raises(ValueError, match="positive"):
        solve_plate(
            grid, 1, edge_flux_w_m2={"west": 1000}, face_convection=Convection(1, 300)
        )


def test_tiny_flux_retains_unresolved_balance():
    grid = RectangularGrid((0, 1), (0, 1), 1)
    result = solve_plate(
        grid, 1, edge_flux_w_m2={"west": -1e-20}, face_convection=Convection(1, 300)
    )
    assert result.temperatures_k == (300,)
    assert result.face_powers_w[0][0] == -1e-20
    assert result.broad_face_powers_w == (0,)
    assert math.fsum(result.face_powers_w[0]) == -1e-20
