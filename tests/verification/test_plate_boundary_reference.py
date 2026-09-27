"""Continuum film/flux limits and an independently assembled rational system."""

import math
from fractions import Fraction as F

import pytest

from thermalpath import Convection, RectangularGrid, solve_plate


@pytest.mark.parametrize("axis", ["x", "y"])
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("flux", [10, -10])
@pytest.mark.parametrize("thickness", [0.25, 0.75])
def test_flux_to_film_continuum(axis, reverse, flux, thickness):
    axial, transverse = (0, 1, 3), (0, 1, 4)
    grid = RectangularGrid(
        axial if axis == "x" else transverse,
        transverse if axis == "x" else axial,
        thickness,
    )
    low, high = ("west", "east") if axis == "x" else ("south", "north")
    incoming, outgoing = (high, low) if reverse else (low, high)
    result = solve_plate(
        grid,
        2,
        edge_flux_w_m2={incoming: -flux},
        edge_convection={outgoing: Convection(5, 300)},
    )
    # Direct integration: T_surface = Ta + q/h; gradient magnitude = q/k.
    for cell, temperature in enumerate(result.temperatures_k):
        coordinate = grid.center_m(cell)[axis == "y"]
        distance = coordinate if reverse else 3 - coordinate
        assert temperature == pytest.approx(
            300 + flux / 5 + flux * distance / 2, rel=0, abs=2e-12
        )
        powers = result.face_powers_w[cell]
        assert math.fsum(powers) == pytest.approx(0, rel=0, abs=2e-10)
        for side, neighbor in enumerate(grid.neighbors(cell)):
            if neighbor is None and side == ("west", "east", "south", "north").index(
                outgoing
            ):
                q = powers[side] / grid.face_areas_m2(cell)[side]
                assert q == pytest.approx(flux, rel=0, abs=5e-11)
                half_width = 0.5 if reverse else 1
                surface = temperature - q * half_width / 2
                assert surface == pytest.approx(300 + flux / 5, rel=0, abs=5e-11)


@pytest.mark.parametrize("side", ["west", "east", "south", "north"])
def test_each_film_alone_anchors_constant_field(side):
    grid = RectangularGrid((0, 1, 3), (0, 2, 3), 0.5)
    result = solve_plate(
        grid, (2, 4, 8, 16), edge_convection={side: Convection(7, 321)}
    )
    assert result.temperatures_k == pytest.approx([321] * 4, rel=0, abs=2e-12)
    assert max(abs(q) for p in result.face_powers_w for q in p) < 2e-10


def test_broad_faces_alone_anchor_unequal_grid():
    grid = RectangularGrid((0, 1, 3), (0, 2, 3), 0.5)
    result = solve_plate(grid, (2, 4, 8, 16), face_convection=Convection(3, 315))
    assert result.temperatures_k == pytest.approx([315] * 4, rel=0, abs=2e-12)
    assert result.broad_face_powers_w == pytest.approx([0] * 4, rel=0, abs=5e-11)


def test_two_films_with_unequal_material_layers():
    grid = RectangularGrid((0, 0.5, 2, 3, 5), (0, 1, 3), 0.25)
    # Series continuum resistance per unit area: 1/2 + 2/2 + 3/6 + 1/4.
    flux = F(60) / (F(1, 2) + 1 + F(1, 2) + F(1, 4))
    left_surface = F(360) - flux / 2
    interface = left_surface - flux
    centers = (
        left_surface - flux * F(1, 8),
        left_surface - flux * F(5, 8),
        interface - flux * F(1, 12),
        interface - flux / 3,
    )
    assert interface == 320
    result = solve_plate(
        grid,
        (2, 2, 6, 6) * 2,
        edge_convection={"west": Convection(2, 360), "east": Convection(4, 300)},
    )
    assert result.temperatures_k == pytest.approx(
        tuple(map(float, centers)) * 2, rel=0, abs=2e-12
    )
    east_power = math.fsum(
        result.face_powers_w[grid.index(3, iy)][1] for iy in range(2)
    )
    assert east_power == pytest.approx(float(flux * F(3, 4)), rel=0, abs=5e-11)


@pytest.mark.parametrize("thickness", [0.25, 0.5, 1])
def test_broad_coefficient_uses_plan_area_without_factor_two(thickness):
    grid = RectangularGrid((0, 2), (0, 3), thickness)
    result = solve_plate(
        grid, 4, edge_flux_w_m2={"west": -20}, face_convection=Convection(5, 300)
    )
    # Input 20*(3*t) W, projected area 6 m2, h_sum=5 -> G=30 W/K.
    assert result.temperatures_k == pytest.approx(
        (300 + 2 * thickness,), rel=0, abs=2e-12
    )
    assert result.broad_face_powers_w == pytest.approx(
        (60 * thickness,), rel=0, abs=1e-10
    )


def test_large_edge_coefficient_tends_to_fixed_geometric_edge():
    grid = RectangularGrid((0, 1, 3), (0, 2), 0.5)
    fixed = solve_plate(grid, 2, west_k=360, east_k=300)
    for h in (1e3, 1e6, 1e12, 1e300):
        result = solve_plate(
            grid, 2, west_k=360, edge_convection={"east": Convection(h, 300)}
        )
        # q=60/(3/2+1/h), so |T_h-T_fixed| <= q/h <= 40/h.
        for actual, reference in zip(
            result.temperatures_k, fixed.temperatures_k, strict=True
        ):
            assert abs(actual - reference) <= 40 / h + 2e-12


def test_small_edge_coefficient_tends_to_insulation():
    grid = RectangularGrid((0, 1, 3), (0, 2), 0.5)
    for h in (1e-3, 1e-6, 1e-12):
        result = solve_plate(
            grid, 2, west_k=360, edge_convection={"east": Convection(h, 300)}
        )
        # q <= 60*h; largest center distance from the fixed edge is 2 m.
        assert max(abs(t - 360) for t in result.temperatures_k) <= 60 * h + 2e-12


def test_large_broad_coefficient_tends_to_ambient():
    grid = RectangularGrid((0, 2), (0, 3), 0.5)
    for h in (1, 1e3, 1e6, 1e12):
        result = solve_plate(
            grid, 4, edge_flux_w_m2={"west": -20}, face_convection=Convection(h, 300)
        )
        assert result.temperatures_k[0] == pytest.approx(300 + 5 / h, rel=0, abs=2e-12)
    # No power accuracy claim at enormous h: subtracting near-equal K loses digits.


def test_mixed_two_cell_exact_rational_balance():
    grid = RectangularGrid((0, 1, 3), (0, 3), 0.5)
    temperatures = (F(138548, 467), F(138887, 467))
    matrix = ((29, -9), (-9, 35))
    rhs = (5927, 7739)
    assert (
        tuple(
            sum(F(a) * t for a, t in zip(row, temperatures, strict=True))
            for row in matrix
        )
        == rhs
    )
    a, b = temperatures
    lateral = (
        (3 * (a - 300), 3 * (a - b), F(2, 3) * (a - 310), F(1)),
        (3 * (b - a), F(-15), F(8, 3) * (b - 310), F(2)),
    )
    broad = (3 * (a - 290), 6 * (b - 290))
    assert all(sum(p) + q == 0 for p, q in zip(lateral, broad, strict=True))
    result = solve_plate(
        grid,
        (2, 4),
        south_k=310,
        edge_convection={"west": Convection(4, 300)},
        edge_flux_w_m2={"east": -10, "north": 2},
        face_convection=Convection(1, 290),
    )
    assert result.temperatures_k == pytest.approx(
        tuple(map(float, temperatures)), rel=0, abs=2e-12
    )
    for cell in range(2):
        assert result.face_powers_w[cell] == pytest.approx(
            tuple(map(float, lateral[cell])), rel=0, abs=5e-11
        )
        assert result.broad_face_powers_w[cell] == pytest.approx(
            float(broad[cell]), rel=0, abs=5e-11
        )
        assert math.fsum(
            (*result.face_powers_w[cell], result.broad_face_powers_w[cell])
        ) == pytest.approx(0, rel=0, abs=1e-10)
