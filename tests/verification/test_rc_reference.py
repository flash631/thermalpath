"""Independent decimal references and thermal energy identities."""

from decimal import Decimal, localcontext

import pytest

from thermalpath import rc_step


@pytest.mark.parametrize("initial,power", [(300, 5), (330, 0), (300, -5), (280, 5)])
@pytest.mark.parametrize("time", [0, 1e-8, 5, 20, 100, 2000])
def test_decimal_solution_and_integrated_boundary_energy(
    initial: int, power: int, time: float
) -> None:
    # Solve for the offset from the reservoir using 70-digit decimal arithmetic.
    # Integral of boundary power = P*t + (T0-Tinf)*C*(1-exp(-t/RC)).
    with localcontext() as context:
        context.prec = 70
        t = Decimal.from_float(float(time))
        c, r, tb, t0, p = map(Decimal, (10, 2, 300, initial, power))
        exponential = (-t / (r * c)).exp()
        offset = p * r + (t0 - tb - p * r) * exponential
        temperature = tb + offset
        energy = c * (temperature - t0)
        boundary = offset / r
        storage = p - boundary
        boundary_energy = p * t + c * (t0 - tb - p * r) * (1 - exponential)
        assert abs(p * t - energy - boundary_energy) < Decimal("1e-60")
    result = rc_step(time, initial, 300, 2, 10, power)
    assert result.temperature_k == pytest.approx(float(temperature), rel=0, abs=2e-13)
    assert result.stored_energy_change_j == pytest.approx(
        float(energy), rel=0, abs=2e-12
    )
    assert result.boundary_power_w == pytest.approx(float(boundary), rel=0, abs=2e-14)
    assert result.storage_power_w == pytest.approx(float(storage), rel=0, abs=2e-14)
    assert result.storage_power_w + result.boundary_power_w == pytest.approx(
        power, rel=0, abs=4e-14
    )
    assert result.stored_energy_change_j + float(boundary_energy) == pytest.approx(
        power * time, rel=0, abs=4e-12
    )


def test_initial_slope_and_capacity_time_scaling() -> None:
    # Initially the 300 K body loses no heat to its 300 K reservoir: slope=P/C.
    result = rc_step(1e-5, 300, 300, 2, 10, 5)
    assert (result.temperature_k - 300) / 1e-5 == pytest.approx(0.5, rel=3e-7)
    # Scaling C and elapsed time together preserves temperature and power;
    # stored energy changes in proportion to C.
    reference = rc_step(20, 300, 300, 2, 10, 5)
    scaled = rc_step(80, 300, 300, 2, 40, 5)
    assert scaled.temperature_k == reference.temperature_k
    assert scaled.boundary_power_w == reference.boundary_power_w
    assert scaled.storage_power_w == reference.storage_power_w
    assert scaled.stored_energy_change_j == 4 * reference.stored_energy_change_j


def test_monotone_heating_and_cooling_without_overshoot() -> None:
    times = [0, 1, 5, 20, 100, 2000]
    heating = [rc_step(t, 300, 300, 2, 10, 5).temperature_k for t in times]
    cooling = [rc_step(t, 330, 300, 2, 10, 0).temperature_k for t in times]
    assert heating == sorted(heating)
    assert cooling == sorted(cooling, reverse=True)
    assert all(300 <= t <= 310 for t in heating)
    assert all(300 <= t <= 330 for t in cooling)
