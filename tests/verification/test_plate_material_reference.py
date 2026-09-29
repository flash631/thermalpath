"""Independent continuum layer solutions and a rational heterogeneous matrix."""

import math
from fractions import Fraction as F

import pytest

from thermalpath import RectangularGrid, solve_plate


@pytest.mark.parametrize("left_k,right_k", [(1, 1000000), (1000000, 1)])
def test_large_contrast_against_exact_series_solution(left_k, right_k):
    grid = RectangularGrid((0, 1, 4), (0, 1), 1)
    result = solve_plate(grid, (left_k, right_k), west_k=360, east_k=300)
    q = F(60) / (F(1, left_k) + F(3, right_k))
    expected = (360 - q * F(1, 2 * left_k), 300 + q * F(3, 2 * right_k))
    assert result.temperatures_k == pytest.approx(
        tuple(map(float, expected)), rel=0, abs=2e-12
    )
    # Large boundary G amplifies temperature roundoff: use the derived G budget.
    for cell, k in enumerate((left_k, right_k)):
        for side in (0, 1):
            budget = 2 * k * 2e-12 + 1e-10
            assert result.face_powers_w[cell][side] == pytest.approx(
                float(q) * (-1 if side == 0 else 1), rel=0, abs=budget
            )


@pytest.mark.parametrize("axis", ["x", "y"])
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("cross_edges", [(0, 3), (0, 1, 3)])
def test_two_layer_unequal_cells_flux_and_interface(axis, reverse, cross_edges):
    edges = (0, 0.5, 2, 3, 5)
    grid = RectangularGrid(
        edges if axis == "x" else cross_edges,
        cross_edges if axis == "x" else edges,
        0.25,
    )
    low, high = (300, 360) if reverse else (360, 300)
    boundaries = (
        dict(west_k=low, east_k=high)
        if axis == "x"
        else dict(south_k=low, north_k=high)
    )
    along = 0 if axis == "x" else 1
    values = tuple(
        2 if grid.indices(i)[along] < 2 else 6 for i in range(grid.cell_count)
    )
    result = solve_plate(grid, values, **boundaries)
    # Integrate dT/ds=-q''/k across lengths 2 and 3, independently of faces.
    flux = F(low - high) / (F(2, 2) + F(3, 6))
    interface = F(low) - flux * F(2, 2)
    centers = (F(1, 4), F(5, 4), F(5, 2), F(4))
    positive, negative = (1, 0) if axis == "x" else (3, 2)
    for cell in range(grid.cell_count):
        index = grid.indices(cell)[along]
        s = centers[index]
        resistance = s / 2 if s < 2 else F(2, 2) + (s - 2) / 6
        expected = F(low) - flux * resistance
        assert result.temperatures_k[cell] == pytest.approx(
            float(expected), rel=0, abs=2e-12
        )
        cross = grid.indices(cell)[1 - along]
        area = F(1, 4) * (cross_edges[cross + 1] - cross_edges[cross])
        power = float(flux * area)
        assert result.face_powers_w[cell][positive] == pytest.approx(
            power, rel=0, abs=5e-11
        )
        assert result.face_powers_w[cell][negative] == pytest.approx(
            -power, rel=0, abs=5e-11
        )
        assert abs(math.fsum(result.face_powers_w[cell])) < 1e-10
        for side in set(range(4)) - {positive, negative}:
            assert result.face_powers_w[cell][side] == pytest.approx(
                0, rel=0, abs=5e-11
            )
        if index in (1, 2):
            # Reconstruct the same perfect-contact interface from either side.
            signed_distance = F(3, 4) if index == 1 else F(-1, 2)
            reconstructed = result.temperatures_k[cell] - (
                result.face_powers_w[cell][positive]
                * float(signed_distance)
                / (values[cell] * float(area))
            )
            assert reconstructed == pytest.approx(float(interface), rel=0, abs=1e-10)


def test_independent_heterogeneous_2d_matrix():
    grid = RectangularGrid((0, 1, 3), (0, 2, 3), 0.5)
    result = solve_plate(
        grid, (2, 4, 8, 16), west_k=300, east_k=360, south_k=280, north_k=340
    )
    # Nine times the hand-assembled matrix and RHS: all entries are integers.
    matrix = (
        (71, -18, -8, 0),
        (-18, 122, 0, -32),
        (-8, 0, 188, -36),
        (0, -32, -36, 428),
    )
    rhs = (13320, 23040, 46080, 123840)
    # Exact Gaussian elimination is independent of the floating network solve.
    rows = [[F(v) for v in (*row, b)] for row, b in zip(matrix, rhs, strict=True)]
    for i in range(4):
        pivot = rows[i][i]
        rows[i] = [v / pivot for v in rows[i]]
        for j in range(4):
            if j != i:
                multiplier = rows[j][i]
                rows[j] = [
                    a - multiplier * b for a, b in zip(rows[j], rows[i], strict=True)
                ]
    t = tuple(row[-1] for row in rows)
    for row, b in zip(matrix, rhs, strict=True):
        assert sum(c * v for c, v in zip(row, t, strict=True)) == b
    powers = (
        (4 * (t[0] - 300), 2 * (t[0] - t[1]), t[0] - 280, F(8, 9) * (t[0] - t[2])),
        (
            2 * (t[1] - t[0]),
            4 * (t[1] - 360),
            4 * (t[1] - 280),
            F(32, 9) * (t[1] - t[3]),
        ),
        (
            8 * (t[2] - 300),
            4 * (t[2] - t[3]),
            F(8, 9) * (t[2] - t[0]),
            8 * (t[2] - 340),
        ),
        (
            4 * (t[3] - t[2]),
            8 * (t[3] - 360),
            F(32, 9) * (t[3] - t[1]),
            32 * (t[3] - 340),
        ),
    )
    assert result.temperatures_k == pytest.approx(
        tuple(map(float, t)), rel=0, abs=2e-12
    )
    for cell, exact in enumerate(powers):
        assert sum(exact) == 0
        assert result.face_powers_w[cell] == pytest.approx(
            tuple(map(float, exact)), rel=0, abs=2e-10
        )
        assert abs(math.fsum(result.face_powers_w[cell])) < 3e-10
        assert 280 <= result.temperatures_k[cell] <= 360
        for side, neighbor in enumerate(grid.neighbors(cell)):
            if neighbor is not None:
                assert (
                    result.face_powers_w[cell][side]
                    == -result.face_powers_w[neighbor][side ^ 1]
                )
    expected_edges = (
        powers[0][0] + powers[2][0],
        powers[1][1] + powers[3][1],
        powers[0][2] + powers[1][2],
        powers[2][3] + powers[3][3],
    )
    assert sum(expected_edges) == 0
    assert result.balance.edge_outflow_w == pytest.approx(
        tuple(map(float, expected_edges)), rel=0, abs=4e-10
    )
    assert result.balance.cell_residual_w == pytest.approx((0,) * 4, rel=0, abs=3e-10)
    assert result.balance.linear_residual_w == pytest.approx((0,) * 4, rel=0, abs=3e-10)
    assert abs(result.balance.imbalance_w) < 1.2e-9


@pytest.mark.parametrize("k_scale,thickness_scale", [(3, 1), (1, 4), (3, 4)])
def test_heterogeneous_scaling(k_scale, thickness_scale):
    boundaries = dict(west_k=300, east_k=360, south_k=280, north_k=340)
    values = (2, 4, 8, 16)
    base = solve_plate(RectangularGrid((0, 1, 3), (0, 2, 3), 0.5), values, **boundaries)
    scaled = solve_plate(
        RectangularGrid((0, 1, 3), (0, 2, 3), 0.5 * thickness_scale),
        tuple(k * k_scale for k in values),
        **boundaries,
    )
    assert scaled.temperatures_k == pytest.approx(base.temperatures_k, rel=0, abs=2e-12)
    for actual, original in zip(scaled.face_powers_w, base.face_powers_w, strict=True):
        assert actual == pytest.approx(
            tuple(k_scale * thickness_scale * q for q in original), rel=0, abs=2.4e-9
        )
