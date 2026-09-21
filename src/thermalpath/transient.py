"""Closed-form response of one thermal capacitance to a constant heat step."""

import math
from dataclasses import dataclass

from thermalpath.models import _scalar


@dataclass(frozen=True)
class RCResult:
    """One-node response at an elapsed time, with signed energy and powers.

    Attributes
    ----------
    temperature_k : float
        Absolute node temperature [K].
    time_constant_s : float
        Resistance times heat capacity [s].
    stored_energy_change_j : float
        Energy relative to the initial state [J], positive for warming.
    boundary_power_w : float
        Instantaneous heat flow from node to fixed boundary [W].
    storage_power_w : float
        Instantaneous rate of energy storage [W], positive for warming.
    """

    temperature_k: float
    time_constant_s: float
    stored_energy_change_j: float
    boundary_power_w: float
    storage_power_w: float


def rc_step(
    time_s: float,
    initial_temperature_k: float,
    boundary_temperature_k: float,
    resistance_k_w: float,
    heat_capacity_j_k: float,
    power_w: float,
) -> RCResult:
    """Evaluate a constant-power one-node RC step without time integration.

    Parameters
    ----------
    time_s : float
        Finite nonnegative elapsed time after the step [s].
    initial_temperature_k : float
        Finite positive node temperature at time zero [K].
    boundary_temperature_k : float
        Finite positive constant reservoir temperature [K].
    resistance_k_w : float
        Finite positive constant node-to-reservoir resistance [K/W].
    heat_capacity_j_k : float
        Finite positive constant lumped heat capacity [J/K].
    power_w : float
        Constant applied power for times at or after zero [W], signed into
        the node. Negative values describe heat extraction.

    Returns
    -------
    RCResult
        Temperature, time constant, stored energy change, boundary power,
        and storage rate. Storage rate plus boundary power equals applied
        power in exact arithmetic; stored energy is measured in joules.

    Raises
    ------
    ValueError
        Inputs violate their domains, the equilibrium temperature is not
        positive, the time constant is unrepresentable, or an intermediate
        or output exceeds finite floating-point range.

    Notes
    -----
    Solves C*dT/dt = P - (T-Tb)/R with one uniform node temperature.
    The positive equilibrium requirement applies even for a short requested
    time, keeping the entire step trajectory in the physical domain.
    Small temperature changes are retained separately for energy accounting.
    Binary64 rounding and underflow still limit very small changes and powers;
    the function is not an accuracy certificate or physical validation.
    """
    time = _scalar(time_s, "time_s")
    if time < 0:
        raise ValueError("time_s must be nonnegative")
    initial = _scalar(initial_temperature_k, "initial_temperature_k", positive=True)
    boundary = _scalar(boundary_temperature_k, "boundary_temperature_k", positive=True)
    resistance = _scalar(resistance_k_w, "resistance_k_w", positive=True)
    capacity = _scalar(heat_capacity_j_k, "heat_capacity_j_k", positive=True)
    power = _scalar(power_w, "power_w")
    tau = resistance * capacity
    if not math.isfinite(tau) or tau <= 0:
        raise ValueError("time constant must fit in a finite positive float")
    try:
        load_rise = power * resistance
        equilibrium = math.fsum((boundary, load_rise))
        amplitude = math.fsum((boundary, -initial, load_rise))
        initial_outflow = (initial - boundary) / resistance
        initial_storage = amplitude / resistance
        energy_scale = capacity * amplitude
        if not all(
            math.isfinite(value)
            for value in (
                equilibrium,
                amplitude,
                initial_outflow,
                initial_storage,
                energy_scale,
            )
        ):
            raise ValueError("RC intermediate exceeds finite float range")
        if equilibrium <= 0:
            raise ValueError("equilibrium temperature must be positive")
        scaled_time = time / tau
        decay = math.exp(-scaled_time)
        fraction = -math.expm1(-scaled_time)
        # Use the nearer endpoint to avoid cancellation in late cooling.
        temperature = (
            math.fsum((initial, amplitude * fraction))
            if scaled_time <= math.log(2.0)
            else math.fsum((equilibrium, -amplitude * decay))
        )
        energy = energy_scale * fraction
        outflow = math.fsum((initial_outflow * decay, power * fraction))
        storage = initial_storage * decay
    except OverflowError as exc:
        raise ValueError("RC calculation exceeds finite float range") from exc
    if not all(math.isfinite(v) for v in (temperature, energy, outflow, storage)):
        raise ValueError("RC output exceeds finite float range")
    if temperature <= 0:
        raise ValueError("calculated temperature must be positive")
    return RCResult(temperature, tau, energy, outflow, storage)
