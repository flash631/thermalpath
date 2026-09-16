"""Domain, scaling, and representability tests for both public functions."""

import math

import pytest

from thermalpath import conduction_resistance, series_temperature


@pytest.mark.parametrize("index", range(3))
@pytest.mark.parametrize(
    "invalid", [0, -1, math.nan, math.inf, -math.inf, None, "2", True, 1j]
)
def test_conduction_rejects_invalid_input(index, invalid):
    values = [1.0, 1.0, 1.0]
    values[index] = invalid
    with pytest.raises(ValueError):
        conduction_resistance(*values)


def test_conduction_scaling():
    baseline = conduction_resistance(0.01, 10, 0.02)
    assert conduction_resistance(0.02, 10, 0.02) == pytest.approx(2 * baseline)
    assert conduction_resistance(0.01, 20, 0.02) == pytest.approx(baseline / 2)
    assert conduction_resistance(0.01, 10, 0.04) == pytest.approx(baseline / 2)


@pytest.mark.parametrize("values", [(1e308, 1e-308, 1), (1e-308, 1e308, 1e308)])
def test_conduction_rejects_unrepresentable_result(values):
    with pytest.raises(ValueError, match="calculated resistance"):
        conduction_resistance(*values)


def test_conduction_avoids_intermediate_range_errors():
    assert conduction_resistance(1e308, 1e308, 1e308) == pytest.approx(1e-308, abs=0)
    assert conduction_resistance(1e-308, 1e-308, 1e-308) == pytest.approx(1e308)


@pytest.mark.parametrize("ambient", [0, -2, math.nan, math.inf, -math.inf, "300", None])
def test_invalid_ambient(ambient):
    with pytest.raises(ValueError):
        series_temperature(ambient, 1, [1])


@pytest.mark.parametrize("power", [-1, math.nan, math.inf, -math.inf, True])
def test_invalid_power(power):
    with pytest.raises(ValueError):
        series_temperature(300, power, [1])


@pytest.mark.parametrize(
    "resistances", [[], [-1], [math.nan], [math.inf], [-math.inf], [None], "12", None]
)
def test_invalid_resistances_even_at_zero_power(resistances):
    with pytest.raises(ValueError):
        series_temperature(300, 0, resistances)


def test_zero_cases_and_monotonicity():
    assert series_temperature(300, 0, [1e308, 1e308]) == 300
    assert series_temperature(300, 5, [0, 0]) == 300
    assert series_temperature(300, 5, (0, 2)) == 310
    assert series_temperature(300, 6, [2]) > series_temperature(300, 5, [2])
    assert series_temperature(300, 5, [3]) > series_temperature(300, 5, [2])
    assert series_temperature(301, 5, [2]) - series_temperature(300, 5, [2]) == 1


@pytest.mark.parametrize("power,resistances", [(1, [1e308, 1e308]), (1e308, [2])])
def test_temperature_overflow(power, resistances):
    with pytest.raises(ValueError, match="calculated"):
        series_temperature(300, power, resistances)


def test_huge_integer_is_invalid_numeric_input():
    with pytest.raises(ValueError):
        series_temperature(10**1000, 1, [1])
