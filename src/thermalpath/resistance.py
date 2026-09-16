"""Steady, single-path thermal resistances with prescribed heat input."""

import math
from collections.abc import Sequence


def _number(value: float, name: str, *, positive: bool) -> float:
    """Convert a real scalar and enforce its finite physical domain."""
    if isinstance(value, (str, bytes, bool, complex)):
        raise ValueError(f"{name} must be a real number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite real number") from exc
    if not math.isfinite(result) or (result <= 0 if positive else result < 0):
        domain = "positive" if positive else "nonnegative"
        raise ValueError(f"{name} must be finite and {domain}")
    return result


def conduction_resistance(
    thickness_m: float, conductivity_w_mk: float, area_m2: float
) -> float:
    """Return the resistance of a homogeneous layer in K/W.

    Parameters
    ----------
    thickness_m : float
        Positive layer thickness [m].
    conductivity_w_mk : float
        Positive constant isotropic conductivity [W/(m K)].
    area_m2 : float
        Positive cross-sectional area normal to heat flow [m²].

    Returns
    -------
    float
        Thickness divided by conductivity and area [K/W].

    Raises
    ------
    ValueError
        An input is nonfinite or nonpositive, or the result cannot be
        represented as a finite positive float.

    Notes
    -----
    Assumes steady one-dimensional conduction with uniform area, no internal
    heat generation, and negligible lateral loss. Contact resistance is not
    included. Mantissa/exponent arithmetic avoids intermediate overflow.
    """
    length = _number(thickness_m, "thickness_m", positive=True)
    conductivity = _number(conductivity_w_mk, "conductivity_w_mk", positive=True)
    area = _number(area_m2, "area_m2", positive=True)
    ml, el = math.frexp(length)
    mk, ek = math.frexp(conductivity)
    ma, ea = math.frexp(area)
    try:
        result = math.ldexp(ml / mk / ma, el - ek - ea)
    except OverflowError as exc:
        raise ValueError("calculated resistance exceeds finite float range") from exc
    if not math.isfinite(result) or result <= 0:
        raise ValueError("calculated resistance is not a finite positive float")
    return result


def series_temperature(
    ambient_k: float, power_w: float, resistances_k_w: Sequence[float]
) -> float:
    """Return source temperature for a steady series path in kelvin.

    Parameters
    ----------
    ambient_k : float
        Positive prescribed sink temperature [K].
    power_w : float
        Nonnegative heat flowing from source to sink [W].
    resistances_k_w : sequence of float
        Nonempty sequence of finite nonnegative thermal resistances [K/W].
        Individual zero resistances describe ideal thermal connections.

    Returns
    -------
    float
        Ambient temperature plus power times total resistance [K].

    Raises
    ------
    ValueError
        Inputs violate their domains, the sequence is empty, or the
        calculated total resistance or temperature is nonfinite.

    Notes
    -----
    Each element carries the same prescribed power. There are no parallel
    paths, storage terms, or temperature-dependent properties. This function
    neither predicts convection coefficients nor establishes a safe device
    operating temperature. Zero power returns ambient after validating inputs.
    """
    ambient = _number(ambient_k, "ambient_k", positive=True)
    power = _number(power_w, "power_w", positive=False)
    if isinstance(resistances_k_w, (str, bytes)):
        raise ValueError("resistances_k_w must be a nonempty sequence")
    try:
        values = [
            _number(value, "resistance_k_w", positive=False)
            for value in resistances_k_w
        ]
    except TypeError as exc:
        raise ValueError("resistances_k_w must be a nonempty sequence") from exc
    if not values:
        raise ValueError("resistances_k_w must be nonempty")
    if power == 0:
        return ambient
    try:
        total = math.fsum(values)
    except OverflowError as exc:
        raise ValueError("calculated total resistance exceeds float range") from exc
    result = ambient + power * total
    if not math.isfinite(result):
        raise ValueError("calculated temperature must be finite")
    return result
