"""Check the frozen study by separation of variables on the discrete grid."""

import math

import numpy as np
import pytest

from examples import heat_spreader as case


@pytest.fixture(scope="module")
def report():
    return case.study()


def modal_reference(nx, ny, thickness, power, sink):
    """Invert scalar eigenvalues, without the production mesh or matrix builder.

    The x sine modes impose zero edge rise at half-cell distances. The y
    cosine modes impose insulated ends. Their tensor products diagonalize
    the uniform finite-volume operator. The source occupies the middle
    third in x and the middle half in y on every frozen grid.
    """
    dx, dy = 0.06 / nx, 0.04 / ny
    gx = 150 * thickness * dy / dx
    gy = 150 * thickness * dx / dy
    source = np.zeros((ny, nx))
    source[ny // 4 : 3 * ny // 4, nx // 3 : 2 * nx // 3] = power / (
        (nx // 3) * (ny // 2)
    )
    rise = np.zeros_like(source)
    for m in range(1, nx + 1):
        x = np.sin(math.pi * m * (np.arange(nx) + 0.5) / nx)
        for n in range(ny):
            y = np.cos(math.pi * n * (np.arange(ny) + 0.5) / ny)
            mode = y[:, None] * x[None, :]
            eigenvalue = 4 * (
                gx * math.sin(math.pi * m / (2 * nx)) ** 2
                + gy * math.sin(math.pi * n / (2 * ny)) ** 2
            )
            norm = (nx if m == nx else nx / 2) * (ny if n == 0 else ny / 2)
            rise += mode * np.sum(source * mode) / (norm * eigenvalue)
    return sink + rise


@pytest.mark.parametrize("candidate", range(3))
@pytest.mark.parametrize("scenario", range(2))
@pytest.mark.parametrize("level", range(3))
def test_independent_modal_temperatures_and_balances(
    report, candidate, scenario, level
):
    c = report["candidates"][candidate]
    s = c["scenarios"][scenario]
    row = s["grids"][level]
    nx, ny = row["shape"]
    expected = modal_reference(nx, ny, c["thickness_m"], s["power_w"], s["sink_k"])
    actual = np.array(row["temperatures_k"]).reshape(ny, nx)
    assert actual == pytest.approx(expected, abs=2e-9, rel=0)
    assert actual == pytest.approx(actual[:, ::-1], abs=2e-9, rel=0)
    assert actual == pytest.approx(actual[::-1, :], abs=2e-9, rel=0)
    assert actual.min() > s["sink_k"]
    d = row["diagnostics"]
    assert d["heater_input_w"] == pytest.approx(s["power_w"], abs=1e-8, rel=0)
    assert d["edge_outflow_w"] == pytest.approx(
        [s["power_w"] / 2, s["power_w"] / 2, 0, 0], abs=1e-8, rel=0
    )
    assert d["broad_face_outflow_w"] == 0
    assert abs(d["imbalance_w"]) <= 1e-8
    assert d["max_cell_residual_w"] <= 1e-8
    assert d["max_linear_residual_w"] <= 1e-8


def test_frozen_inputs_and_numerical_screen(report):
    assert case.THICKNESSES_M == (0.0005, 0.001, 0.002)
    assert case.GRID_SHAPES == ((6, 4), (12, 8), (24, 16))
    assert case.SCENARIOS == (("nominal", 10.0, 300.0), ("stress", 12.0, 310.0))
    assert case.LIMIT_K == 325
    assert case.DECISION_BAND_K == 0.25
    assert case.GRID_CHANGE_TOLERANCE_K == 0.5
    assert case.BALANCE_TOLERANCE_W == 1e-8
    assert (
        report["attempted_count"],
        report["completed_count"],
        report["failed_count"],
    ) == (
        18,
        18,
        0,
    )
    assert [c["mass_kg"] for c in report["candidates"]] == pytest.approx(
        [0.00324, 0.00648, 0.01296], abs=1e-16, rel=0
    )
    assert [
        [s["classification"] for s in c["scenarios"]] for c in report["candidates"]
    ] == [
        ["exceeds", "exceeds"],
        ["meets", "exceeds"],
        ["meets", "meets"],
    ]
    for c in report["candidates"]:
        for s in c["scenarios"]:
            assert s["numerical_checks_passed"]
            assert s["last_peak_change_k"] <= 0.5
            peaks = [g["peak_cell_k"] for g in s["grids"]]
            # A decreasing change is evidence for this grid family only.
            assert 0 < peaks[2] - peaks[1] < peaks[1] - peaks[0]


def test_thickness_power_and_sink_scaling(report):
    baseline = report["candidates"][0]["scenarios"][0]
    for c in report["candidates"]:
        for s in c["scenarios"]:
            for base, row in zip(baseline["grids"], s["grids"], strict=True):
                expected = s["sink_k"] + (np.array(base["temperatures_k"]) - 300) * (
                    s["power_w"] / 10 * 0.0005 / c["thickness_m"]
                )
                assert row["temperatures_k"] == pytest.approx(expected, abs=2e-9, rel=0)
