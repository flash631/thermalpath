"""Domains, limiting states, signs, and range behavior for the RC API."""

import math
from dataclasses import FrozenInstanceError

import pytest

from thermalpath import RCResult, rc_step


def response(**changes: float) -> RCResult:
    """Use one synthetic baseline with explicit SI inputs."""
    inputs = dict(
        time_s=20.0,
        initial_temperature_k=300.0,
        boundary_temperature_k=300.0,
        resistance_k_w=2.0,
        heat_capacity_j_k=10.0,
        power_w=5.0,
    )
    inputs.update(changes)
    return rc_step(**inputs)


@pytest.mark.parametrize(
    "name",
    [
        "time_s",
        "initial_temperature_k",
        "boundary_temperature_k",
        "resistance_k_w",
        "heat_capacity_j_k",
        "power_w",
    ],
)
@pytest.mark.parametrize("value", [True, "1", None, 1j, math.nan, math.inf])
def test_reject_invalid_scalars(name: str, value: object) -> None:
    with pytest.raises(ValueError, match=name):
        response(**{name: value})


@pytest.mark.parametrize(
    "name",
    [
        "initial_temperature_k",
        "boundary_temperature_k",
        "resistance_k_w",
        "heat_capacity_j_k",
    ],
)
@pytest.mark.parametrize("value", [0.0, -1.0])
def test_positive_domains(name: str, value: float) -> None:
    with pytest.raises(ValueError, match=name):
        response(**{name: value})


def test_negative_time() -> None:
    with pytest.raises(ValueError, match="time_s"):
        response(time_s=-1)


@pytest.mark.parametrize("power", [-150.0, -151.0])
def test_entire_step_must_remain_positive(power: float) -> None:
    with pytest.raises(ValueError, match="equilibrium"):
        response(time_s=0, power_w=power)


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"resistance_k_w": 1e308}, "time constant"),
        ({"resistance_k_w": 1e-300, "heat_capacity_j_k": 1e-300}, "time constant"),
        ({"power_w": 1e308}, "intermediate"),
        ({"boundary_temperature_k": 1e308, "power_w": 5e307}, "range"),
        ({"initial_temperature_k": 1e308}, "intermediate"),
        ({"resistance_k_w": 1e-308, "initial_temperature_k": 310.0}, "intermediate"),
    ],
)
def test_unrepresentable_arithmetic(changes: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        response(**changes)


def test_initial_energy_and_instantaneous_power_are_distinct() -> None:
    result = response(time_s=0, initial_temperature_k=310)
    assert result == RCResult(310, 20, 0, 5, 0)
    result = response(time_s=0, initial_temperature_k=320)
    assert result == RCResult(320, 20, 0, 10, -5)


def test_equilibrium_is_constant_and_result_is_immutable() -> None:
    result = response(initial_temperature_k=310)
    assert result == RCResult(310, 20, 0, 5, 0)
    with pytest.raises(FrozenInstanceError):
        result.temperature_k = 1


def test_long_time_heating_limit() -> None:
    assert response(time_s=20000) == RCResult(310, 20, 100, 5, 0)


def test_large_time_ratio_has_valid_equilibrium_limit() -> None:
    result = response(time_s=1e308, resistance_k_w=0.01, heat_capacity_j_k=0.01)
    assert result.temperature_k == 300.05
    assert result.boundary_power_w == 5
    assert result.storage_power_w == 0


def test_tiny_step_keeps_energy_when_temperature_rounds_away() -> None:
    result = response(time_s=1e-16)
    assert result.temperature_k == 300
    assert result.stored_energy_change_j == pytest.approx(5e-16, rel=1e-15, abs=0)
    assert result.boundary_power_w == pytest.approx(2.5e-17, rel=1e-15, abs=0)
    assert result.storage_power_w == 5


def test_tiny_load_keeps_energy_when_equilibrium_rise_rounds_away() -> None:
    result = response(power_w=1e-20)
    assert result.temperature_k == 300
    assert result.stored_energy_change_j > 0
    assert result.boundary_power_w > 0
    assert result.storage_power_w > 0
    assert result.boundary_power_w + result.storage_power_w == pytest.approx(
        1e-20, rel=1e-15, abs=0
    )


def test_late_cooling_does_not_subtract_two_large_temperatures() -> None:
    result = response(
        time_s=1000,
        initial_temperature_k=1e100,
        boundary_temperature_k=1,
        resistance_k_w=1,
        heat_capacity_j_k=1,
        power_w=0,
    )
    assert result.temperature_k == 1
    assert result.stored_energy_change_j == -1e100


def test_very_small_time_ratio_can_underflow() -> None:
    result = response(time_s=5e-324)
    assert result.temperature_k == 300
    assert result.stored_energy_change_j == 0
    assert result.storage_power_w == 5
