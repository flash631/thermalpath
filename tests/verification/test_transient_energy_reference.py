"""Exact rational step ledgers and independent continuous-time references."""

import math
from decimal import Decimal, localcontext
from fractions import Fraction as F

import pytest

from thermalpath import Link, Network, Node, solve_transient, transient_energy_balance


@pytest.mark.parametrize("reverse", [False, True])
def test_piecewise_rational_energy_ledger(reverse):
    network = Network(
        (Node("a"), Node("b"), Node("sink", fixed_temperature_k=300)),
        tuple(
            Link(name, b if reverse else a, a if reverse else b, g)
            for name, a, b, g in [
                ("ab", "a", "b", 1),
                ("a0", "a", "sink", 2),
                ("b0", "b", "sink", 1),
            ]
        ),
    )
    steps = [F(1), F(2), F(1, 2)]
    powers = [(10, 0), (0, 6), (-2, 1)]
    loads = [{"a": p, "b": q} for p, q in powers]
    result = solve_transient(
        network, {"a": 2, "b": 3}, {"a": 300, "b": 300}, [0, 1, 3, 3.5], loads
    )
    x, y = F(0), F(0)
    for i, (h, (p, q)) in enumerate(zip(steps, powers, strict=True)):
        aa, bb = 2 / h + 3, 3 / h + 2
        u, v = 2 * x / h + p, 3 * y / h + q
        xn, yn = (bb * u + v) / (aa * bb - 1), (u + aa * v) / (aa * bb - 1)
        expected_storage = {"a": 2 * (xn - x), "b": 3 * (yn - y)}
        reservoir = -h * (2 * xn + yn)
        assert sum(expected_storage.values()) == h * (p + q) + reservoir
        report = transient_energy_balance(
            network,
            {"a": 2, "b": 3},
            result.temperatures_k[i],
            result.temperatures_k[i + 1],
            float(h),
            loads[i],
        )
        assert report.storage_j == pytest.approx(
            {k: float(v) for k, v in expected_storage.items()}, rel=0, abs=1.2e-11
        )
        assert report.source_j == {"a": float(h * p), "b": float(h * q)}
        assert report.boundary_j["sink"] == pytest.approx(
            float(reservoir), rel=0, abs=1.2e-11
        )
        assert report.total_storage_j == pytest.approx(
            float(sum(expected_storage.values())), rel=0, abs=2e-11
        )
        assert report.total_source_j == float(h * (p + q))
        assert report.total_boundary_j == pytest.approx(
            float(reservoir), rel=0, abs=1.2e-11
        )
        assert max(abs(v) for v in report.node_residual_j.values()) < 3e-11
        assert abs(report.imbalance_j) < 4e-11
        x, y = xn, yn


@pytest.mark.parametrize("coupled", [False, True])
def test_four_step_sizes_against_decimal_exponential(coupled):
    # Both fixtures have lambda*t_final=1 and initial modal amplitude 10 K.
    # Scalar heating: tau=20 s, equilibrium 310 K, start 300 K.
    # Insulated pair: C=2 J/K, G=1 W/K, difference mode rate=1/s.
    if coupled:
        network = Network((Node("a"), Node("b")), (Link("ab", "a", "b", 1),))
        capacities, initial, end = {"a": 2, "b": 2}, {"a": 310, "b": 290}, 1
    else:
        network = Network(
            (Node("a", power_w=5), Node("bath", fixed_temperature_k=300)),
            (Link("ab", "a", "bath", 0.5),),
        )
        capacities, initial, end = {"a": 10}, {"a": 300}, 20
    with localcontext() as ctx:
        ctx.prec = 70
        mode = Decimal(10) * Decimal(-1).exp()
        exact = float(Decimal(300) + mode if coupled else Decimal(310) - mode)
    errors = []
    for count in (5, 10, 20, 40):
        dt = end / count
        result = solve_transient(
            network, capacities, initial, [i * dt for i in range(count + 1)]
        )
        numerical = result.temperatures_k[-1]["a"]
        discrete_mode = 10 * F(count, count + 1) ** count
        expected = float(300 + discrete_mode if coupled else 310 - discrete_mode)
        assert numerical == pytest.approx(expected, rel=0, abs=2e-11)
        errors.append(abs(numerical - exact))
        for old, new in zip(
            result.temperatures_k, result.temperatures_k[1:], strict=False
        ):
            report = transient_energy_balance(network, capacities, old, new, dt)
            assert abs(report.imbalance_j) < 5e-11
            assert max(abs(v) for v in report.node_residual_j.values()) < 5e-11
        if coupled:
            assert sum(result.temperatures_k[-1].values()) == pytest.approx(
                600, rel=0, abs=4e-11
            )
    orders = [math.log2(a / b) for a, b in zip(errors, errors[1:], strict=False)]
    assert all(0.93 < p < 1.01 for p in orders)
    assert orders == sorted(orders)
    assert errors[-1] > 0.04  # Conservation does not remove temporal error.
