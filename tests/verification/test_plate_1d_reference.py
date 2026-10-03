"""Integrated 1D profiles and exact rational discrete balances."""

import math
import sys
from fractions import Fraction as F

import pytest

from thermalpath import Convection, RectangularGrid, RectangularHeater, solve_plate


@pytest.mark.parametrize("axis", [0, 1])
@pytest.mark.parametrize("edges", [(0, 4), (0, 1, 2, 3, 4), (0, 0.5, 2, 4)])
@pytest.mark.parametrize("thickness", [F(1, 4), F(1, 2)])
@pytest.mark.parametrize("source", [F(0), F(3)])
@pytest.mark.parametrize("boundary", ["fixed", "insulated-fixed", "flux-film"])
def test_heated_profiles_and_every_face(axis, edges, thickness, source, boundary):
    # Derive q=-k*T' and q'=s/t without using the solver's matrix or residuals.
    length, conductivity, film = F(4), F(2), F(4)
    left, right, west_outward = F(320), F(300), F(-4)
    points = tuple(map(F, edges))
    widths = tuple(b - a for a, b in zip(points[:-1], points[1:], strict=True))
    centers = tuple((a + b) / 2 for a, b in zip(points[:-1], points[1:], strict=True))
    if boundary == "fixed":
        q0 = conductivity * (left - right) / length - source * length / (2 * thickness)
        constant = left
    else:
        q0 = -west_outward if boundary == "flux-film" else F(0)
        q_end = q0 + source * length / thickness
        surface = right + q_end / film if boundary == "flux-film" else right
        constant = surface + q0 * length / conductivity
        constant += source * length**2 / (2 * conductivity * thickness)
    continuum = tuple(
        constant
        - q0 * x / conductivity
        - source * x**2 / (2 * conductivity * thickness)
        for x in centers
    )
    biases = tuple(source * dx**2 / (8 * conductivity * thickness) for dx in widths)
    discrete = tuple(t + e for t, e in zip(continuum, biases, strict=True))
    flux = tuple(q0 + source * x / thickness for x in points)

    # Exact substitution into the face law, independent of floating arithmetic.
    for i in range(len(widths) - 1):
        assert (
            conductivity * (discrete[i] - discrete[i + 1])
            == flux[i + 1] * (widths[i] + widths[i + 1]) / 2
        )
    if boundary == "fixed":
        assert conductivity * (left - discrete[0]) / (widths[0] / 2) == flux[0]
    if boundary == "flux-film":
        assert (discrete[-1] - right) / (
            widths[-1] / (2 * conductivity) + 1 / film
        ) == flux[-1]
    else:
        assert conductivity * (discrete[-1] - right) / (widths[-1] / 2) == flux[-1]
    assert thickness * (flux[-1] - flux[0]) == source * length

    transverse = (0, 0.5, 2)
    grid = RectangularGrid(
        edges if axis == 0 else transverse,
        transverse if axis == 0 else edges,
        float(thickness),
    )
    low, high = ("west", "east") if axis == 0 else ("south", "north")
    if boundary == "fixed":
        boundaries = {f"{low}_k": float(left), f"{high}_k": float(right)}
    elif boundary == "insulated-fixed":
        boundaries = {f"{high}_k": float(right)}
    else:
        boundaries = {
            "edge_flux_w_m2": {low: float(west_outward)},
            "edge_convection": {high: Convection(float(film), float(right))},
        }
    heater = RectangularHeater(
        grid.x_edges_m[0],
        grid.x_edges_m[-1],
        grid.y_edges_m[0],
        grid.y_edges_m[-1],
        float(source * 8),
    )
    result = solve_plate(grid, float(conductivity), heaters=[heater], **boundaries)

    # Nonnegative inverse: a uniform-source barrier bounds ||A^-1||_infinity.
    # Each cell receives at least one watt for source 1/(min(dx)*min(dy)).
    inverse_bound = (
        length**2 / (2 * conductivity * thickness)
        + length / (film * thickness)
        + max(widths) ** 2 / (8 * conductivity * thickness)
    ) / (min(widths) / 2)
    # At most two axial and two transverse neighbors; boundary G <= 2*k*A/dx.
    row_norm_bound = (
        8 * conductivity * thickness * (F(3, 2) / min(widths) + max(widths) / F(1, 2))
    )
    condition_budget = float(inverse_bound * row_norm_bound)
    temperature_budget = (
        64
        * sys.float_info.epsilon
        * grid.cell_count
        * condition_budget
        * max(map(float, discrete))
    )
    assert temperature_budget < 1e-6  # Far below the smallest nonzero offset.
    power_budget = float(row_norm_bound) * temperature_budget
    for cell, actual in enumerate(result.temperatures_k):
        axial = grid.indices(cell)[axis]
        cross = grid.indices(cell)[1 - axis]
        area = thickness * (F(1, 2) if cross == 0 else F(3, 2))
        assert actual == pytest.approx(
            float(discrete[axial]), rel=0, abs=temperature_budget
        )
        assert actual - float(continuum[axial]) == pytest.approx(
            float(biases[axial]), rel=0, abs=temperature_budget
        )
        expected = [F(0)] * 4
        expected[2 * axis] = -flux[axial] * area
        expected[2 * axis + 1] = flux[axial + 1] * area
        assert result.face_powers_w[cell] == pytest.approx(
            tuple(map(float, expected)), rel=0, abs=power_budget
        )
        assert sum(expected) == source * widths[axial] * area / thickness
        assert result.broad_face_powers_w[cell] == 0
    assert result.balance.heater_input_w == pytest.approx(
        float(source * 8), rel=0, abs=1e-13
    )
    assert abs(result.balance.imbalance_w) <= grid.cell_count * power_budget


def test_unequal_width_rational_system_and_nonzero_continuum_error():
    # Widths 1 and 3 m, k*t=1 W/K, breadth 2 m: A=[[5,-1],[-1,7/3]].
    theta = (F(3), F(9))
    matrix = ((F(5), F(-1)), (F(-1), F(7, 3)))
    assert tuple(
        sum(a * t for a, t in zip(row, theta, strict=True)) for row in matrix
    ) == (6, 18)
    result = solve_plate(
        RectangularGrid((0, 1, 4), (0, 2), 0.5),
        2,
        west_k=300,
        east_k=300,
        heaters=[RectangularHeater(0, 4, 0, 2, 24)],
    )
    assert result.temperatures_k == pytest.approx((303, 309), rel=0, abs=2e-12)
    continuum = (F(2421, 8), F(2445, 8))
    assert tuple(300 + t - c for t, c in zip(theta, continuum, strict=True)) == (
        F(3, 8),
        F(27, 8),
    )
    assert result.face_powers_w[0] == pytest.approx((12, -6, 0, 0), rel=0, abs=1e-11)
    assert result.face_powers_w[1] == pytest.approx((6, 12, 0, 0), rel=0, abs=1e-11)
    assert math.fsum(result.balance.cell_residual_w) == pytest.approx(
        0, rel=0, abs=2e-11
    )
