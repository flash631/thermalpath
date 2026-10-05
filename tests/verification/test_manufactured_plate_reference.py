"""Exact polynomial calculus and a separate rational finite-volume system."""

import sys
from fractions import Fraction as F

import pytest

from examples import manufactured_plate as example
from thermalpath import RectangularGrid, RectangularHeater, map_heaters, solve_plate

LX, LY, KT = F(3, 50), F(1, 25), F(1, 50)
# Expanded in physical x and y, independently of the factored example field.
POLYNOMIAL = {
    (0, 0): F(300),
    (1, 1): 320 / (LX * LY),
    (2, 1): -320 / (LX**2 * LY),
    (1, 2): -320 / (LX * LY**2),
    (2, 2): 320 / (LX**2 * LY**2),
}


def derivative(polynomial, axis):
    result = {}
    for powers, coefficient in polynomial.items():
        degree = powers[axis]
        if degree:
            new = list(powers)
            new[axis] -= 1
            result[tuple(new)] = coefficient * degree
    return result


def evaluate(polynomial, x, y):
    return sum(c * x**i * y**j for (i, j), c in polynomial.items())


def integral(polynomial, x0, x1, y0, y1):
    return sum(
        c
        * (x1 ** (i + 1) - x0 ** (i + 1))
        / (i + 1)
        * (y1 ** (j + 1) - y0 ** (j + 1))
        / (j + 1)
        for (i, j), c in polynomial.items()
    )


def forcing():
    result = {}
    for axis in (0, 1):
        for powers, c in derivative(derivative(POLYNOMIAL, axis), axis).items():
            result[powers] = result.get(powers, F(0)) - KT * c
    return result


@pytest.mark.parametrize("x", [F(0), LX / 3, LX / 2, LX])
@pytest.mark.parametrize("y", [F(0), LY / 4, LY / 2, LY])
def test_independent_derivatives_source_and_boundary_values(x, y):
    exact = evaluate(POLYNOMIAL, x, y)
    source = evaluate(forcing(), x, y)
    assert example.temperature_k(float(x), float(y)) == pytest.approx(
        float(exact), rel=0, abs=2e-12
    )
    assert example.source_w_m2(float(x), float(y)) == pytest.approx(
        float(source), rel=2e-14, abs=2e-11
    )
    assert source >= 0
    if x in (0, LX) or y in (0, LY):
        assert exact == 300
    if x in (0, LX) and y in (0, LY):
        # Both edge traces agree and the smooth gradient vanishes at the corner.
        assert source == 0
        assert evaluate(derivative(POLYNOMIAL, 0), x, y) == 0
        assert evaluate(derivative(POLYNOMIAL, 1), x, y) == 0


def test_exact_integrated_source_and_continuum_fluxes():
    # A separate unequal partition checks integrals without a second solve/grid study.
    xs, ys = (F(0), LX / 5, LX), (F(0), LY / 3, LY)
    total = F(0)
    for y0, y1 in zip(ys[:-1], ys[1:], strict=True):
        for x0, x1 in zip(xs[:-1], xs[1:], strict=True):
            power = integral(forcing(), x0, x1, y0, y1)
            total += power
            assert example.cell_power_w(*map(float, (x0, x1, y0, y1))) == pytest.approx(
                float(power), rel=2e-14, abs=0
            )
            # Integrate q dot n * t on each face, using differentiated polynomials.
            outflow = F(0)
            for axis, low, high in ((0, x0, x1), (1, y0, y1)):
                gradient = derivative(POLYNOMIAL, axis)
                for coordinate, sign in ((low, 1), (high, -1)):
                    if axis == 0:
                        face = sum(
                            c
                            * coordinate**i
                            * (y1 ** (j + 1) - y0 ** (j + 1))
                            / (j + 1)
                            for (i, j), c in gradient.items()
                        )
                    else:
                        face = sum(
                            c
                            * coordinate**j
                            * (x1 ** (i + 1) - x0 ** (i + 1))
                            / (i + 1)
                            for (i, j), c in gradient.items()
                        )
                    outflow += sign * KT * face
            assert outflow == power
    assert total == F(208, 45)
    assert example.cell_power_w(0, float(LX), 0, float(LY)) == pytest.approx(
        float(total), rel=2e-14
    )


def inverse(matrix):
    """Gauss-Jordan elimination in exact rationals; no numerical solver calls."""
    n = len(matrix)
    augmented = [row[:] + [F(i == j) for j in range(n)] for i, row in enumerate(matrix)]
    for i in range(n):
        pivot = augmented[i][i]
        assert pivot > 0
        augmented[i] = [v / pivot for v in augmented[i]]
        for j in range(n):
            if i != j:
                scale = augmented[j][i]
                augmented[j] = [
                    a - scale * b
                    for a, b in zip(augmented[j], augmented[i], strict=True)
                ]
    assert [row[:n] for row in augmented] == [
        [F(i == j) for j in range(n)] for i in range(n)
    ]
    return [row[n:] for row in augmented]


def test_frozen_4_by_3_discrete_reference_and_corner_faces():
    nx, ny = 4, 3
    dx, dy = LX / nx, LY / ny
    gx, gy = KT * dy / dx, KT * dx / dy
    n = nx * ny
    matrix = [[F(0) for _ in range(n)] for _ in range(n)]
    heaters, powers, centers = [], [], []
    faces = []
    for j in range(ny):
        for i in range(nx):
            cell = j * nx + i
            bounds = (i * dx, (i + 1) * dx, j * dy, (j + 1) * dy)
            power = integral(forcing(), *bounds)
            powers.append(power)
            centers.append(((i + F(1, 2)) * dx, (j + F(1, 2)) * dy))
            heaters.append(RectangularHeater(*map(float, bounds), float(power)))
            neighbors = (
                cell - 1 if i else None,
                cell + 1 if i + 1 < nx else None,
                cell - nx if j else None,
                cell + nx if j + 1 < ny else None,
            )
            cell_faces = []
            for neighbor, conductance in zip(neighbors, (gx, gx, gy, gy), strict=True):
                # Boundary distance is half a cell; each corner has TWO faces.
                g = conductance * (2 if neighbor is None else 1)
                matrix[cell][cell] += g
                if neighbor is not None:
                    matrix[cell][neighbor] -= g
                cell_faces.append((neighbor, g))
            faces.append(cell_faces)
    inv = inverse(matrix)
    rise = [sum(a * b for a, b in zip(row, powers, strict=True)) for row in inv]
    norm_a = max(sum(abs(v) for v in row) for row in matrix)
    norm_inv = max(sum(abs(v) for v in row) for row in inv)
    condition = norm_a * norm_inv
    assert all(v >= 0 for row in inv for v in row)
    assert condition < 12
    # Conservative regression budget for this small, moderately conditioned system.
    tolerance_k = 512 * n * sys.float_info.epsilon * float(condition) * 320
    grid = RectangularGrid(
        tuple(float(i * dx) for i in range(nx + 1)),
        tuple(float(j * dy) for j in range(ny + 1)),
        float(F(1, 500)),
    )
    assert map_heaters(grid, heaters) == pytest.approx(
        list(map(float, powers)), rel=2e-14
    )
    result = solve_plate(
        grid, 10, west_k=300, east_k=300, south_k=300, north_k=300, heaters=heaters
    )
    assert result.temperatures_k == pytest.approx(
        [float(300 + v) for v in rise], rel=0, abs=tolerance_k
    )
    exterior = [F(0)] * 4
    for cell, cell_faces in enumerate(faces):
        exact_faces = []
        for side, (neighbor, g) in enumerate(cell_faces):
            flux = g * (rise[cell] - (rise[neighbor] if neighbor is not None else 0))
            exact_faces.append(flux)
            if neighbor is None:
                exterior[side] += flux
        assert sum(exact_faces) == powers[cell]
        assert result.face_powers_w[cell] == pytest.approx(
            list(map(float, exact_faces)),
            rel=0,
            abs=float(4 * max(gx, gy)) * tolerance_k,
        )
    assert sum(exterior) == F(208, 45)
    assert result.balance.edge_outflow_w == pytest.approx(
        list(map(float, exterior)), rel=0, abs=float(16 * max(gx, gy)) * tolerance_k
    )
    assert abs(result.balance.imbalance_w) < float(32 * max(gx, gy)) * tolerance_k
    errors = [
        300 + v - evaluate(POLYNOMIAL, x, y)
        for v, (x, y) in zip(rise, centers, strict=True)
    ]
    assert min(errors) > 0
    assert max(errors) > F(1, 10)
    # Discrete exterior partition differs from the exact continuum partition.
    assert exterior != [F(32, 45), F(32, 45), F(8, 5), F(8, 5)]
