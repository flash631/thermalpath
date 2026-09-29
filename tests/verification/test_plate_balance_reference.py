"""Independent balance references and deliberately inaccurate temperatures."""

import math
from fractions import Fraction as F

import numpy as np
import pytest

from thermalpath import Convection, RectangularGrid, RectangularHeater, solve_plate


@pytest.mark.parametrize("transpose", [False, True])
@pytest.mark.parametrize("factor", [0.25, 1, 8])
def test_two_cell_balance_and_actual_matrix_residual(transpose, factor):
    # Hand-derived A=[[8,-2],[-2,5]], det=36, inverse=[[5,2],[2,8]]/36.
    matrix = ((F(8), F(-2)), (F(-2), F(5)))
    theta = (F(1), F(2))
    assert tuple(
        sum(a * t for a, t in zip(row, theta, strict=True)) for row in matrix
    ) == (4, 8)
    x, y = ((0, 2), (0, 1, 3)) if transpose else ((0, 1, 3), (0, 2))
    bounds = (0.5, 1.5, 0.5, 2) if transpose else (0.5, 2, 0.5, 1.5)
    boundary = (
        dict(south_k=300, north_k=300) if transpose else dict(west_k=300, east_k=300)
    )
    result = solve_plate(
        RectangularGrid(x, y, 0.5),
        3,
        heaters=[RectangularHeater(*bounds, 12 * factor)],
        **boundary,
    )
    balance = result.balance
    assert balance.heater_input_w == pytest.approx(12 * factor, rel=0, abs=5e-14)
    expected = (
        (0, 0, 6 * factor, 6 * factor) if transpose else (6 * factor, 6 * factor, 0, 0)
    )
    assert balance.edge_outflow_w == pytest.approx(expected, rel=0, abs=5e-11)
    assert balance.broad_face_outflow_w == 0
    assert balance.cell_residual_w == pytest.approx((0, 0), rel=0, abs=5e-11)
    assert balance.imbalance_w == pytest.approx(0, rel=0, abs=1e-10)
    # Reconstruct the rounded system independently, including absolute reservoirs.
    a = np.array([[8.0, -2.0], [-2.0, 5.0]])
    b = np.array([1800 + 4 * factor, 900 + 8 * factor])
    assert balance.linear_residual_w == tuple(b - a @ result.temperatures_k)
    assert balance.linear_residual_w == pytest.approx((0, 0), rel=0, abs=5e-11)


def test_opposite_local_errors_survive_zero_global_balance(monkeypatch):
    # e=(1,-2) K gives -A*e=(-12,12) W. Global balance alone misses both.
    monkeypatch.setattr(np.linalg, "solve", lambda a, b: np.array([302.0, 300.0]))
    result = solve_plate(
        RectangularGrid((0, 1, 3), (0, 2), 0.5),
        3,
        west_k=300,
        east_k=300,
        heaters=[RectangularHeater(0.5, 2, 0.5, 1.5, 12)],
    )
    assert result.balance.cell_residual_w == (-12, 12)
    assert result.balance.linear_residual_w == (-12, 12)
    assert result.balance.edge_outflow_w == (12, 0, 0, 0)
    assert result.balance.imbalance_w == 0


@pytest.mark.parametrize("power", [1e-20, 5e-324])
def test_zero_matrix_residual_does_not_hide_physical_heating(power):
    result = solve_plate(
        RectangularGrid((0, 1), (0, 1), 1),
        1,
        west_k=300,
        heaters=[RectangularHeater(0, 1, 0, 1, power)],
    )
    assert result.temperatures_k == (300,)
    assert result.balance.linear_residual_w == (0,)
    assert result.balance.cell_residual_w == (power,)
    assert result.balance.imbalance_w == power


@pytest.mark.parametrize("flux", [-2, 2])
def test_signed_edge_and_broad_exchange(flux):
    result = solve_plate(
        RectangularGrid((0, 1), (0, 2), 0.5),
        3,
        heaters=[RectangularHeater(0, 1, 0, 2, 10)],
        edge_flux_w_m2={"west": flux},
        face_convection=Convection(2, 300),
    )
    assert result.temperatures_k == (300 + (10 - flux) / 4,)
    assert result.balance.edge_outflow_w == (flux, 0, 0, 0)
    assert result.balance.broad_face_outflow_w == 10 - flux
    assert result.balance.cell_residual_w == (0,)
    assert result.balance.linear_residual_w == (0,)
    assert result.balance.imbalance_w == 0


def test_cooling_broad_faces_have_negative_outflow():
    result = solve_plate(
        RectangularGrid((0, 1), (0, 1), 1),
        1,
        west_k=300,
        face_convection=Convection(2, 320),
    )
    assert result.temperatures_k == (310,)
    assert result.balance.edge_outflow_w == (20, 0, 0, 0)
    assert result.balance.broad_face_outflow_w == -20
    assert result.balance.imbalance_w == 0


def test_boundary_rounding_residual_is_preserved():
    warmer = math.nextafter(300.0, math.inf)
    result = solve_plate(
        RectangularGrid((0, 1), (0, 1), 1),
        1,
        west_k=300,
        east_k=warmer,
    )
    assert result.balance.linear_residual_w == (0,)
    assert result.balance.imbalance_w == 2 * (warmer - 300)
    assert result.balance.cell_residual_w == (result.balance.imbalance_w,)
