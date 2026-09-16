"""Independent rational references; no reference result calls the solver."""

from fractions import Fraction

import pytest

from thermalpath import conduction_resistance, series_temperature


def test_exact_rational_reference_and_signed_balance():
    interface = Fraction(50, 1_000_000) / (5 * Fraction(2, 10_000))
    assert interface == Fraction(1, 20)
    source = Fraction(31815, 100) + 15 * (1 + interface + 2)
    assert source == Fraction(3639, 10)
    assert source - Fraction(27315, 100) == Fraction(363, 4)
    computed_r = conduction_resistance(50e-6, 5, 2e-4)
    computed_t = series_temperature(318.15, 15, [1, computed_r, 2])
    assert computed_r == pytest.approx(float(interface), rel=1e-14, abs=0)
    assert computed_t == pytest.approx(float(source), rel=0, abs=1e-12)
    # Positive heat is toward the sink; injected minus rejected power is zero.
    rejected = (computed_t - 318.15) / float(Fraction(61, 20))
    assert 15 - rejected == pytest.approx(0, abs=1e-12)


def test_path_subdivision_invariance():
    total = conduction_resistance(0.01, 5, 2e-4)
    half = conduction_resistance(0.005, 5, 2e-4)
    assert series_temperature(300, 2, [total]) == pytest.approx(
        series_temperature(300, 2, [half, half]), rel=1e-14
    )
