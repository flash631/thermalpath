"""Independent rational, scalar and modal transient plate references."""

import math
from fractions import Fraction as F
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.sparse import csc_array, dok_array

from thermalpath import (
    Convection,
    RectangularGrid,
    RectangularHeater,
    solve_transient_plate,
    transient_networks,
)

pytestmark = pytest.mark.parametrize("backend", ["dense", "sparse"])


def _eliminate(matrix, rhs):
    """Solve a small rational system by exact elimination, independent of NumPy."""
    original = [row[:] for row in matrix]
    target = rhs[:]
    rows = [row[:] + [value] for row, value in zip(matrix, rhs, strict=True)]
    for column in range(len(rows)):
        divisor = rows[column][column]
        assert divisor != 0
        rows[column] = [value / divisor for value in rows[column]]
        for index in range(len(rows)):
            if index != column:
                factor = rows[index][column]
                rows[index] = [
                    a - factor * b
                    for a, b in zip(rows[index], rows[column], strict=True)
                ]
    answer = [row[-1] for row in rows]
    assert [
        sum(a * b for a, b in zip(row, answer, strict=True)) for row in original
    ] == target
    return answer


def rational_case():
    """Assemble the frozen 2x2 problem from rational geometry and face laws."""
    # x widths 1,2; y widths 1,1; thickness 1/2. No production geometry,
    # heater mapper, plate assembly or solver is used to obtain expectations.
    widths = [F(1), F(2), F(1), F(2)]
    conductivity = [F(2), F(4), F(3), F(6)]
    capacities = [
        a * b / 2 for a, b in zip(widths, [F(8), F(6), F(4), F(10)], strict=True)
    ]
    # Full heater bounds x=[1/2,2], y=[1/4,3/2], total 6 W.
    heater = [
        F(6) * dx / F(3, 2) * dy / F(5, 4)
        for dy in [F(3, 4), F(1, 2)]
        for dx in [F(1, 2), F(1)]
    ]
    assert sum(heater) == 6
    loads = heater[:]
    loads[0] += F(3, 2)  # South q_out=-3 W/m2 times thickness*width.
    loads[1] += 3
    links = []
    for left, right, area, d_left, d_right in [
        (0, 1, F(1, 2), F(1, 2), F(1)),
        (2, 3, F(1, 2), F(1, 2), F(1)),
        (0, 2, F(1, 2), F(1, 2), F(1, 2)),
        (1, 3, F(1), F(1, 2), F(1, 2)),
    ]:
        links.append(
            (
                left,
                right,
                area / (d_left / conductivity[left] + d_right / conductivity[right]),
            )
        )
    boundaries = []
    for cell in (0, 2):
        boundaries.append((cell, "west", conductivity[cell], F(300)))
    for cell in (1, 3):
        boundaries.append(
            (cell, "east", F(1, 2) / (1 / conductivity[cell] + F(1, 2)), F(290))
        )
    for cell in range(4):
        boundaries.append((cell, "broad", widths[cell] / 4, F(295)))
    matrix = [[F(0) for _ in range(4)] for _ in range(4)]
    rhs_fixed = loads[:]
    for a, b, conductance in links:
        matrix[a][a] += conductance
        matrix[b][b] += conductance
        matrix[a][b] -= conductance
        matrix[b][a] -= conductance
    for cell, _, conductance, temperature in boundaries:
        matrix[cell][cell] += conductance
        rhs_fixed[cell] += conductance * temperature
    old = list(map(F, (310, 320, 315, 305)))
    rows = [old]
    ledger = []
    for duration in [F(1, 4), F(1, 2), F(1, 4)]:
        system = [row[:] for row in matrix]
        rhs = rhs_fixed[:]
        for cell in range(4):
            system[cell][cell] += capacities[cell] / duration
            rhs[cell] += capacities[cell] / duration * old[cell]
        new = _eliminate(system, rhs)
        storage = [c * (b - a) for c, a, b in zip(capacities, old, new, strict=True)]
        source = [duration * power for power in loads]
        boundary = {name: F(0) for name in ("west", "east", "broad")}
        outgoing = [F(0)] * 4
        for a, b, conductance in links:
            transfer = duration * conductance * (new[a] - new[b])
            outgoing[a] += transfer
            outgoing[b] -= transfer
        for cell, name, conductance, temperature in boundaries:
            incoming = duration * conductance * (temperature - new[cell])
            boundary[name] += incoming
            outgoing[cell] -= incoming
        assert [
            p - q - s for p, q, s in zip(source, outgoing, storage, strict=True)
        ] == [0] * 4
        assert sum(source) + sum(boundary.values()) == sum(storage)
        ledger.append((storage, source, boundary))
        rows.append(new)
        old = new
    return rows, ledger


def test_heterogeneous_rational_steps_and_energy(backend):
    expected, ledger = rational_case()
    result = solve_transient_plate(
        RectangularGrid((0, 1, 3), (0, 1, 2), 0.5),
        (2, 4, 3, 6),
        (8, 6, 4, 10),
        (310, 320, 315, 305),
        (0, 0.25, 0.75, 1),
        west_k=300,
        edge_convection={"east": Convection(2, 290), "north": Convection(0, 1000)},
        edge_flux_w_m2={"south": -3},
        face_convection=Convection(0.25, 295),
        heaters=[RectangularHeater(0.5, 2, 0.25, 1.5, 6)],
        backend=backend,
    )
    for actual, reference in zip(result.temperatures_k, expected, strict=True):
        assert actual == pytest.approx(tuple(map(float, reference)), abs=2e-10, rel=0)
    for actual, (storage, source, boundary) in zip(
        result.energy_balances, ledger, strict=True
    ):
        for field, reference in [
            (actual.storage_j, storage),
            (actual.source_j, source),
        ]:
            assert tuple(field.values()) == pytest.approx(
                tuple(map(float, reference)), abs=5e-9, rel=0
            )
        assert actual.boundary_j == pytest.approx(
            {name: float(value) for name, value in boundary.items()}, abs=5e-9, rel=0
        )
        assert max(map(abs, actual.node_residual_j.values())) <= 5e-9
        assert abs(actual.imbalance_j) <= 2e-8


def test_one_cell_convection_and_flux_recurrence(backend):
    # V=2*3*0.5=3 m3, C=12 J/K. West lateral area 1.5 m2,
    # half-cell/film resistance factors 1/2+1/2 => G_w=1.5 W/K.
    # Broad G=0.25*6=1.5 W/K. East outward flux=2*1.5=3 W.
    result = solve_transient_plate(
        RectangularGrid((0, 2), (0, 3), 0.5),
        2,
        4,
        320,
        (0, 0.25, 0.75, 1),
        edge_convection={"west": Convection(2, 300)},
        edge_flux_w_m2={"east": 2},
        face_convection=Convection(0.25, 290),
        heaters=[RectangularHeater(0, 2, 0, 3, 6)],
        backend=backend,
    )
    old = F(320)
    for row, duration in zip(
        result.temperatures_k[1:], [F(1, 4), F(1, 2), F(1, 4)], strict=True
    ):
        old = (12 * old / duration + 3 + F(3, 2) * (300 + 290)) / (12 / duration + 3)
        assert row == pytest.approx((float(old),), abs=2e-10, rel=0)


def test_insulated_uniform_heating_with_unequal_cells(backend):
    result = solve_transient_plate(
        RectangularGrid((0, 1, 3), (0, 1, 2), 0.5),
        2,
        4,
        300,
        (0, 0.25, 0.75, 1),
        heaters=[RectangularHeater(0, 3, 0, 2, 6)],
        backend=backend,
    )
    # Total capacity=4*3=12 J/K; power=6 W => warming at 1/2 K/s.
    for time, row in zip(result.times_s, result.temperatures_k, strict=True):
        assert row == pytest.approx((300 + time / 2,) * 4, abs=2e-10, rel=0)
    for report in result.energy_balances:
        assert report.boundary_j == {}
        assert abs(report.imbalance_j) <= 2e-8


def modal_case(nx, ny, steps, backend):
    """Run a cosine mode and derive its discrete/continuum rates independently."""
    dx, dy = 2 / nx, 1 / ny
    shape = [
        math.cos(math.pi * (ix + 0.5) / nx) * math.cos(math.pi * (iy + 0.5) / ny)
        for iy in range(ny)
        for ix in range(nx)
    ]
    rate = 0.8 * (
        (math.sin(math.pi / (2 * nx)) / dx) ** 2
        + (math.sin(math.pi / (2 * ny)) / dy) ** 2
    )
    continuum_rate = 0.2 * math.pi**2 * 1.25
    times = tuple(0.2 * index / steps for index in range(steps + 1))
    result = solve_transient_plate(
        RectangularGrid(
            tuple(dx * i for i in range(nx + 1)),
            tuple(dy * j for j in range(ny + 1)),
            0.2,
        ),
        2,
        10,
        tuple(300 + 20 * value for value in shape),
        times,
        backend=backend,
    )
    amplitude = 20
    for index, row in enumerate(result.temperatures_k):
        if index:
            amplitude /= 1 + rate * (times[index] - times[index - 1])
        assert row == pytest.approx(
            tuple(300 + amplitude * value for value in shape), abs=2e-10, rel=0
        )
    for report in result.energy_balances:
        assert abs(report.imbalance_j) <= 2e-8
        assert max(map(abs, report.node_residual_j.values())) <= 5e-9
    final = result.temperatures_k[-1]
    temporal = max(
        abs(value - (300 + 20 * math.exp(-rate * 0.2) * mode))
        for value, mode in zip(final, shape, strict=True)
    )
    continuum = max(
        abs(value - (300 + 20 * math.exp(-continuum_rate * 0.2) * mode))
        for value, mode in zip(final, shape, strict=True)
    )
    time_discrete_amplitude = 20
    for start, end in zip(times[:-1], times[1:], strict=True):
        time_discrete_amplitude /= 1 + continuum_rate * (end - start)
    spatial_errors = tuple(
        value - (300 + time_discrete_amplitude * mode)
        for value, mode in zip(final, shape, strict=True)
    )
    spatial = max(map(abs, spatial_errors))
    spatial_rms = math.sqrt(
        math.fsum(error**2 for error in spatial_errors) / len(spatial_errors)
    )
    # The cell-centered cosine has mean square 1/2 on each axis. Its 2D
    # RMS is therefore 1/2 on every grid; no solver output enters this identity.
    amplitude_error = abs(amplitude - time_discrete_amplitude)
    assert spatial_rms == pytest.approx(amplitude_error / 2, abs=2e-10, rel=0)
    sampled_peak = math.cos(math.pi / (2 * nx)) * math.cos(math.pi / (2 * ny))
    assert spatial == pytest.approx(amplitude_error * sampled_peak, abs=2e-10, rel=0)
    return {
        "temporal_error_k": temporal,
        "spatial_error_k": spatial,
        "spatial_rms_error_k": spatial_rms,
        "continuum_error_k": continuum,
    }


def test_temporal_refinement(backend):
    rows = [modal_case(8, 6, steps, backend) for steps in (10, 20, 40)]
    errors = [row["temporal_error_k"] for row in rows]
    assert errors[-1] < 0.06
    for a, b in zip(errors[:-1], errors[1:], strict=True):
        assert 0.9 < math.log2(a / b) < 1.1
    assert rows[-1]["continuum_error_k"] > errors[-1]


def test_spatial_refinement_at_fixed_time_discretization(backend):
    rows = [modal_case(nx, ny, 8, backend) for nx, ny in ((4, 3), (8, 6), (16, 12))]
    maximum_errors = [row["spatial_error_k"] for row in rows]
    rms_errors = [row["spatial_rms_error_k"] for row in rows]
    assert maximum_errors[-1] < 0.08
    for a, b in zip(rms_errors[:-1], rms_errors[1:], strict=True):
        assert 1.8 < math.log2(a / b) < 2.2
    # Retain the original coarse maximum-error result: moving sample peaks
    # produce order below 1.8 here. RMS order is the convergence criterion.
    assert math.log2(maximum_errors[0] / maximum_errors[1]) < 1.8


def test_sparse_plate_storage_and_factor_reuse(monkeypatch, backend):
    # The bounded resource test always exercises sparse; the backend parameter
    # also selects the small companion calculation below.
    factors, solves = [], []
    original = transient_networks.splu

    def factor(matrix):
        assert matrix.nnz == 4992
        payload = matrix.data.nbytes + matrix.indices.nbytes + matrix.indptr.nbytes
        assert payload <= 200000
        factors.append(payload)
        lu = original(matrix)

        def solve(rhs):
            solves.append(1)
            return lu.solve(rhs)

        return SimpleNamespace(solve=solve)

    def forbidden(*args, **kwargs):
        raise AssertionError("Sparse plate attempted dense allocation or solve")

    def guarded(original_allocator):
        def allocate(shape, *args, **kwargs):
            if isinstance(shape, (tuple, list)) and len(shape) == 2:
                assert min(shape) < 1024, "Large dense matrix allocation"
            return original_allocator(shape, *args, **kwargs)

        return allocate

    with monkeypatch.context() as patch:
        patch.setattr(transient_networks, "splu", factor)
        patch.setattr(np.linalg, "solve", forbidden)
        patch.setattr(np, "diag", forbidden)
        for array_type in (csc_array, dok_array):
            patch.setattr(array_type, "toarray", forbidden)
            patch.setattr(array_type, "todense", forbidden)
        for allocator in ("zeros", "ones", "empty", "full"):
            patch.setattr(np, allocator, guarded(getattr(np, allocator)))
        edges = tuple(i / 32 for i in range(33))
        result = solve_transient_plate(
            RectangularGrid(edges, edges, 1),
            2,
            10,
            300,
            (0, 0.125, 0.25, 0.375),
            heaters=[RectangularHeater(0, 1, 0, 1, 1)],
            backend="sparse",
        )
    assert len(factors) == 1
    assert len(solves) == 3
    for time, row in zip(result.times_s, result.temperatures_k, strict=True):
        assert max(abs(value - (300 + time / 10)) for value in row) <= 5e-10
    for report in result.energy_balances:
        assert abs(report.imbalance_j) <= 5e-8
    small = solve_transient_plate(
        RectangularGrid((0, 1), (0, 1), 1),
        2,
        10,
        300,
        (0, 0.125, 0.25, 0.375),
        heaters=[RectangularHeater(0, 1, 0, 1, 1)],
        backend=backend,
    )
    assert small.temperatures_k[-1][0] == pytest.approx(
        result.temperatures_k[-1][0], abs=5e-10, rel=0
    )
