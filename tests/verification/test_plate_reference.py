"""Continuum linear profiles and an independently assembled rational 2D case."""

import math
from fractions import Fraction as F

import pytest

from thermalpath import RectangularGrid, solve_plate


@pytest.mark.parametrize("axis", ["x", "y"])
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("cross_edges", [(0, 2), (0, 0.5, 2)])
def test_unequal_cell_linear_continuum_solution(axis, reverse, cross_edges):
    edges = (-1, -0.5, 1, 3)
    grid = RectangularGrid(
        edges if axis == "x" else cross_edges,
        cross_edges if axis == "x" else edges,
        0.25,
    )
    low, high = (380, 300) if reverse else (300, 380)
    boundary = (
        {"west_k": low, "east_k": high}
        if axis == "x"
        else {"south_k": low, "north_k": high}
    )
    result = solve_plate(grid, 8, **boundary)
    # dT/ds=(high-low)/4; outward flow through the positive face is -k*A*dT/ds.
    positive, negative = (1, 0) if axis == "x" else (3, 2)
    for cell in range(grid.cell_count):
        coordinate = grid.center_m(cell)[0 if axis == "x" else 1]
        expected = low + (high - low) * (coordinate + 1) / 4
        assert result.temperatures_k[cell] == pytest.approx(expected, rel=0, abs=2e-12)
        # Cross widths are specified independently of the face-area method.
        cross_index = grid.indices(cell)[1 if axis == "x" else 0]
        width = cross_edges[cross_index + 1] - cross_edges[cross_index]
        q = -8 * 0.25 * width * (high - low) / 4
        assert result.face_powers_w[cell][positive] == pytest.approx(
            q, rel=0, abs=5e-11
        )
        assert result.face_powers_w[cell][negative] == pytest.approx(
            -q, rel=0, abs=5e-11
        )
        for side in set(range(4)) - {positive, negative}:
            assert result.face_powers_w[cell][side] == pytest.approx(
                0, rel=0, abs=5e-11
            )


def test_independent_rational_two_dimensional_reference():
    grid = RectangularGrid((0, 1, 3), (0, 2, 3), 0.5)
    result = solve_plate(grid, 6, west_k=300, east_k=360, south_k=280, north_k=340)
    # Explicit matrix and RHS are derived by hand, independent of grid methods.
    matrix = ((21, -4, -2, 0), (-4, 20, 0, -4), (-2, 0, 16, -2), (0, -4, -2, 21))
    rhs = (4440, 3840, 3840, 5160)
    t = (F(2120, 7), F(320), F(320), F(2360, 7))
    for row, b in zip(matrix, rhs, strict=True):
        assert sum(c * v for c, v in zip(row, t, strict=True)) == b
    powers = (
        (12 * (t[0] - 300), 4 * (t[0] - t[1]), 3 * (t[0] - 280), 2 * (t[0] - t[2])),
        (4 * (t[1] - t[0]), 6 * (t[1] - 360), 6 * (t[1] - 280), 4 * (t[1] - t[3])),
        (6 * (t[2] - 300), 2 * (t[2] - t[3]), 2 * (t[2] - t[0]), 6 * (t[2] - 340)),
        (2 * (t[3] - t[2]), 3 * (t[3] - 360), 4 * (t[3] - t[1]), 12 * (t[3] - 340)),
    )
    assert result.temperatures_k == pytest.approx(
        tuple(map(float, t)), rel=0, abs=2e-12
    )
    for cell, exact in enumerate(powers):
        assert sum(exact) == 0
        assert result.face_powers_w[cell] == pytest.approx(
            tuple(map(float, exact)), rel=0, abs=5e-11
        )
        assert abs(math.fsum(result.face_powers_w[cell])) < 1e-10
        assert 280 <= result.temperatures_k[cell] <= 360
    for left, right, side, opposite in (
        (0, 1, 1, 0),
        (2, 3, 1, 0),
        (0, 2, 3, 2),
        (1, 3, 3, 2),
    ):
        assert (
            result.face_powers_w[left][side] == -result.face_powers_w[right][opposite]
        )


@pytest.mark.parametrize("k_scale,t_scale", [(3, 1), (1, 4), (3, 4)])
def test_conductivity_thickness_scaling(k_scale, t_scale):
    boundary = dict(west_k=300, east_k=360, south_k=280, north_k=340)
    base = solve_plate(RectangularGrid((0, 1, 3), (0, 2, 3), 0.5), 6, **boundary)
    scaled = solve_plate(
        RectangularGrid((0, 1, 3), (0, 2, 3), 0.5 * t_scale), 6 * k_scale, **boundary
    )
    assert scaled.temperatures_k == pytest.approx(base.temperatures_k, rel=0, abs=2e-12)
    for actual, original in zip(scaled.face_powers_w, base.face_powers_w, strict=True):
        assert actual == pytest.approx(
            tuple(k_scale * t_scale * q for q in original), rel=0, abs=6e-10
        )


def test_uniform_fixed_edges_and_translation():
    grid = RectangularGrid((7, 7.5, 9), (-4, -3, 0), 0.125)
    result = solve_plate(grid, 5, west_k=315, east_k=315, south_k=315, north_k=315)
    assert result.temperatures_k == pytest.approx([315] * 4, rel=0, abs=2e-12)
    for powers in result.face_powers_w:
        assert powers == pytest.approx([0] * 4, rel=0, abs=5e-11)
