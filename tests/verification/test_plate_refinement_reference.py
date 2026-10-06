"""Independent sine-mode solve, rational loads and discrete error bounds."""

from fractions import Fraction as F
from math import fsum, log2, pi, sin, sqrt
from sys import float_info

import pytest

from examples.plate_refinement import refinement_report


@pytest.fixture(scope="module")
def report():
    return refinement_report()


def reference(nx, ny):
    """Solve in the separable eigenbasis without calling a matrix solver."""
    lx, ly, kt, amplitude = F(3, 50), F(1, 25), F(1, 50), F(320)
    dx, dy = lx / nx, ly / ny
    gx, gy = kt * dy / dx, kt * dx / dy
    powers, exact = [], []
    for j in range(ny):
        row, temperatures = [], []
        y = F(2 * j + 1, 2 * ny)
        for i in range(nx):
            x = F(2 * i + 1, 2 * nx)
            # Integrate the expanded quadratic in normalized coordinates.
            x0, x1, y0, y1 = F(i, nx), F(i + 1, nx), F(j, ny), F(j + 1, ny)
            ix = (x1**2 - x0**2) / 2 - (x1**3 - x0**3) / 3
            iy = (y1**2 - y0**2) / 2 - (y1**3 - y0**3) / 3
            row.append(
                2 * kt * amplitude * (dy * lx * ix / ly**2 + dx * ly * iy / lx**2)
            )
            temperatures.append(300 + amplitude * x * (1 - x) * y * (1 - y))
        powers.append(row)
        exact.extend(temperatures)
    bases = []
    eigenvalues = []
    for n, g in ((nx, gx), (ny, gy)):
        basis = [
            [
                sin(pi * p * (i + 0.5) / n) / sqrt(n if p == n else n / 2)
                for i in range(n)
            ]
            for p in range(1, n + 1)
        ]
        # Verify orthonormality, including the exceptional highest-mode norm.
        for p in range(n):
            for q in range(n):
                assert fsum(
                    a * b for a, b in zip(basis[p], basis[q], strict=True)
                ) == pytest.approx(float(p == q), rel=0, abs=2e-14)
        bases.append(basis)
        eigenvalues.append(
            [4 * float(g) * sin(pi * p / (2 * n)) ** 2 for p in range(1, n + 1)]
        )
    sx, sy = bases
    ax, ay = eigenvalues
    projected_x = [
        [fsum(float(powers[j][i]) * sx[p][i] for i in range(nx)) for p in range(nx)]
        for j in range(ny)
    ]
    coefficients = [
        [
            fsum(projected_x[j][p] * sy[q][j] for j in range(ny)) / (ax[p] + ay[q])
            for p in range(nx)
        ]
        for q in range(ny)
    ]
    rise = [
        fsum(
            coefficients[q][p] * sx[p][i] * sy[q][j]
            for q in range(ny)
            for p in range(nx)
        )
        for j in range(ny)
        for i in range(nx)
    ]
    # Positive inverse and the one-dimensional quadratic supersolution bound.
    inverse_bound = (lx**2 + dx**2) / (8 * kt * dx * dy)
    condition_bound = 4 * (gx + gy) * inverse_bound
    tolerance = 64 * nx * ny * float_info.epsilon * float(condition_bound) * 320
    residual = F(8, 3) * kt * 20 * dx * dy * (1 / (ny**2 * lx**2) + 1 / (nx**2 * ly**2))
    lower_error = -residual * inverse_bound
    upper_error = max(F(20, nx**2), F(20, ny**2))
    barrier = [
        (((F(2 * i + 1, 2) * dx) * (lx - F(2 * i + 1, 2) * dx)) + dx**2 / 4)
        / (2 * kt * dx * dy)
        for _ in range(ny)
        for i in range(nx)
    ]
    for cell in range(nx * ny):
        j, i = divmod(cell, nx)
        ax_exact, aw, boundary_sum = F(0), F(0), F(0)
        for neighbor, g in (
            (cell - 1 if i else None, gx),
            (cell + 1 if i < nx - 1 else None, gx),
            (cell - nx if j else None, gy),
            (cell + nx if j < ny - 1 else None, gy),
        ):
            if neighbor is None:
                ax_exact += 2 * g * (exact[cell] - 300)
                aw += 2 * g * barrier[cell]
                boundary_sum += 2 * g
            else:
                ax_exact += g * (exact[cell] - exact[neighbor])
                aw += g * (barrier[cell] - barrier[neighbor])
        x, y = F(2 * i + 1, 2 * nx), F(2 * j + 1, 2 * ny)
        rhs_error = -residual
        if i in (0, nx - 1):
            rhs_error += 160 * gx * y * (1 - y) / nx**2
        if j in (0, ny - 1):
            rhs_error += 160 * gy * x * (1 - x) / ny**2
        assert powers[j][i] - ax_exact == rhs_error
        assert -residual <= rhs_error <= upper_error * boundary_sum
        assert aw >= 1
        assert 0 < barrier[cell] <= inverse_bound
    return (
        powers,
        exact,
        rise,
        tolerance,
        float(lower_error),
        float(upper_error),
        float(gx),
        float(gy),
    )


@pytest.mark.parametrize("level,nx,ny", [(0, 4, 3), (1, 8, 6), (2, 16, 12)])
def test_all_cells_norms_and_balance_against_independent_modes(report, level, nx, ny):
    grid = report["grids"][level]
    powers, exact, rise, tolerance, low, high, gx, gy = reference(nx, ny)
    assert grid["grid_shape"] == [nx, ny]
    assert sum(map(sum, powers)) == F(208, 45)
    errors = []
    exterior = [[], [], [], []]
    for cell, row in enumerate(grid["cells"]):
        j, i = divmod(cell, nx)
        assert row["x_m"] == pytest.approx(float(F(3 * (2 * i + 1), 100 * nx)))
        assert row["y_m"] == pytest.approx(float(F(2 * j + 1, 50 * ny)))
        assert row["cell_input_w"] == pytest.approx(float(powers[j][i]), rel=3e-14)
        assert row["continuum_center_k"] == pytest.approx(
            float(exact[cell]), rel=0, abs=2e-12
        )
        assert row["computed_k"] == pytest.approx(
            300 + rise[cell], rel=0, abs=tolerance
        )
        error = 300 + rise[cell] - float(exact[cell])
        errors.append(error)
        assert low - tolerance <= row["error_k"] <= high + tolerance
        faces = []
        for side, neighbor, g in (
            (0, cell - 1 if i else None, gx),
            (1, cell + 1 if i < nx - 1 else None, gx),
            (2, cell - nx if j else None, gy),
            (3, cell + nx if j < ny - 1 else None, gy),
        ):
            power = (
                2 * g * rise[cell]
                if neighbor is None
                else g * (rise[cell] - rise[neighbor])
            )
            faces.append(power)
            if neighbor is None:
                exterior[side].append(power)
        # Check the eigenmode solution against every independently assembled row.
        assert fsum(faces) == pytest.approx(float(powers[j][i]), rel=0, abs=2e-12)
    expected = dict(
        l1_k=fsum(map(abs, errors)) / len(errors),
        l2_k=sqrt(fsum(e**2 for e in errors) / len(errors)),
        linf_k=max(map(abs, errors)),
    )
    for norm, value in expected.items():
        assert grid["errors"][norm] == pytest.approx(value, rel=0, abs=tolerance)
    assert grid["edge_outflow_w"] == pytest.approx(
        [fsum(side) for side in exterior],
        rel=0,
        abs=4 * max(nx, ny) * max(gx, gy) * tolerance,
    )
    assert grid["heater_input_w"] == pytest.approx(208 / 45, rel=3e-14)
    # Separate roundoff budgets for physical and linear residuals, not K errors.
    local_budget = 64 * float_info.epsilon * 320 * 4 * (gx + gy)
    assert grid["max_cell_residual_w"] < local_budget
    assert grid["max_linear_residual_w"] < local_budget
    assert abs(grid["imbalance_w"]) < nx * ny * local_budget


def test_frozen_inputs_and_both_orders(report):
    assert [
        report[k]
        for k in (
            "length_x_m",
            "length_y_m",
            "thickness_m",
            "conductivity_w_mk",
            "boundary_k",
            "peak_continuum_rise_k",
        )
    ] == [0.06, 0.04, 0.002, 10, 300, 20]
    assert report["grids"][0]["observed_order"] is None
    for old, new in zip(report["grids"], report["grids"][1:], strict=False):
        assert new["dx_m"] == old["dx_m"] / 2
        assert new["dy_m"] == old["dy_m"] / 2
        for name in ("l1_k", "l2_k", "linf_k"):
            assert 0 < new["errors"][name] < old["errors"][name]
            assert new["observed_order"][name] == pytest.approx(
                log2(old["errors"][name] / new["errors"][name]), abs=1e-12
            )
    # Preserve the lower maximum-norm orders; never replace them with two.
    assert [
        r["observed_order"]["linf_k"] for r in report["grids"][1:]
    ] == pytest.approx([1.60019673305, 1.82593268269], abs=2e-7)
