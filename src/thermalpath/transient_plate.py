"""Backward-Euler heat storage for constant-property depth-averaged plates."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from thermalpath.boundaries import Convection
from thermalpath.grid import RectangularGrid
from thermalpath.models import _scalar
from thermalpath.plate import _assemble_plate
from thermalpath.sources import RectangularHeater
from thermalpath.transient_energy import (
    TransientEnergyBalance,
    transient_energy_balance,
)
from thermalpath.transient_networks import solve_transient


@dataclass(frozen=True)
class TransientPlateResult:
    """Store cell temperatures and endpoint step-energy accounting.

    Attributes
    ----------
    times_s : tuple of float
        Requested times [s], including the initial time.
    temperatures_k : tuple of tuple of float
        One cell-temperature row [K] per time, in the grid's x-first order.
    energy_balances : tuple of TransientEnergyBalance
        One record [J] per interval. Cell keys are decimal flat indices.
        Source energy combines heaters and prescribed inward edge flux.
        Reservoir keys are west/east/south/north and broad, when present;
        their energy is positive into the plate. Each record has independent
        dictionaries. Residuals measure discrete conservation, not time error.
    """

    times_s: tuple[float, ...]
    temperatures_k: tuple[tuple[float, ...], ...]
    energy_balances: tuple[TransientEnergyBalance, ...]


def _cell_values(
    value: float | Sequence[float], count: int, name: str
) -> tuple[float, ...]:
    """Copy positive scalar or x-first cell data without accepting text arrays."""
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if len(value) != count:
            raise ValueError(f"{name} must contain one value per cell")
        return tuple(_scalar(item, name, positive=True) for item in value)
    return (_scalar(value, name, positive=True),) * count


def solve_transient_plate(
    grid: RectangularGrid,
    conductivity_w_m_k: float | Sequence[float],
    volumetric_heat_capacity_j_m3_k: float | Sequence[float],
    initial_temperatures_k: float | Sequence[float],
    times_s: Sequence[float],
    *,
    west_k: float | None = None,
    east_k: float | None = None,
    south_k: float | None = None,
    north_k: float | None = None,
    edge_flux_w_m2: Mapping[str, float] | None = None,
    edge_convection: Mapping[str, Convection] | None = None,
    face_convection: Convection | None = None,
    heaters: Sequence[RectangularHeater] = (),
    backend: Literal["dense", "sparse"] = "dense",
) -> TransientPlateResult:
    """Integrate a depth-averaged plate with constant properties and loads.

    Parameters
    ----------
    grid : RectangularGrid
        Orthogonal cells with positive constant thickness [m].
    conductivity_w_m_k : float or sequence of float
        Positive isotropic conductivity [W/(m K)], uniform or one per cell.
        Material interfaces follow cell faces and have perfect contact.
    volumetric_heat_capacity_j_m3_k : float or sequence of float
        Positive density times specific heat [J/(m3 K)], uniform or one per
        cell in x-first order. Cell heat capacity is this value times volume.
    initial_temperatures_k : float or sequence of float
        Positive initial cell temperature [K], uniform or in x-first order.
    times_s : sequence of float
        At least two finite, nonnegative, strictly increasing times [s].
        The supplied initial condition applies at times_s[0].
    west_k, east_k, south_k, north_k : float or None, optional
        Constant positive temperature [K] on the geometric edge. Each edge
        permits one boundary type. Unspecified edges are insulated.
    edge_flux_w_m2 : mapping of str to float or None, optional
        Constant outward-positive flux [W/m2] on named lateral edges; negative
        heats the plate. Lateral areas include thickness.
    edge_convection : mapping of str to Convection or None, optional
        Constant lateral film data. Conductance includes half-cell conduction
        in series with the film. Zero coefficient means insulation.
    face_convection : Convection or None, optional
        Sum of both broad-face coefficients [W/(m2 K)] with one ambient.
        Uses projected area once and assumes uniform through-thickness
        temperature, with no additional transverse resistance.
    heaters : sequence of RectangularHeater, optional
        Constant nonnegative power inputs integrated over footprint overlaps.
        Heater watts are not multiplied by thickness.
    backend : {"dense", "sparse"}, optional
        Dense solve by default; select sparse for assembly and single-factor
        reuse on consecutive exactly equal computed time steps within a call.

    Returns
    -------
    TransientPlateResult
        Initial and computed cell temperatures, and signed step energies.

    Raises
    ------
    ValueError
        Invalid geometry, material, initial state, boundary, load, time or
        backend; unrepresentable positive heat capacity; failed integration
        or energy accounting; nonpositive or nonfinite computed temperatures.

    Notes
    -----
    All properties, boundary data and heater loads remain constant in time.
    C_i = cvol_i*V_i [J/K] and C_i*dT_i/dt = P_i - sum_j G_ij*(T_i-T_j).
    Uses the same face laws as solve_plate and backward Euler from
    solve_transient. Positive cell capacities allow fully insulated plates.
    Step energies use endpoint fluxes and combine prescribed inward flux with
    heater input in the source term. They are not continuous-time integrals.
    Dense storage is quadratic in cell count; sparse factors can fill in and
    the full temperature/energy history grows with cells and time intervals.
    Finite positive states and small residuals do not establish spatial/time
    accuracy or physical validity. See docs/transient_plate.md.
    """
    assembly = _assemble_plate(
        grid,
        conductivity_w_m_k,
        west_k=west_k,
        east_k=east_k,
        south_k=south_k,
        north_k=north_k,
        edge_flux_w_m2=edge_flux_w_m2,
        edge_convection=edge_convection,
        face_convection=face_convection,
        heaters=heaters,
    )
    volumetric = _cell_values(
        volumetric_heat_capacity_j_m3_k,
        grid.cell_count,
        "volumetric_heat_capacity_j_m3_k",
    )
    initial = _cell_values(
        initial_temperatures_k, grid.cell_count, "initial_temperatures_k"
    )
    capacities = {
        str(cell): _scalar(
            value * grid.cell_volume_m3(cell), "cell heat capacity", positive=True
        )
        for cell, value in enumerate(volumetric)
    }
    result = solve_transient(
        assembly.network,
        capacities,
        {str(cell): value for cell, value in enumerate(initial)},
        times_s,
        backend=backend,
    )
    energies = tuple(
        transient_energy_balance(assembly.network, capacities, old, new, end - start)
        for start, end, old, new in zip(
            result.times_s[:-1],
            result.times_s[1:],
            result.temperatures_k[:-1],
            result.temperatures_k[1:],
            strict=True,
        )
    )
    return TransientPlateResult(
        result.times_s,
        tuple(
            tuple(row[str(cell)] for cell in range(grid.cell_count))
            for row in result.temperatures_k
        ),
        energies,
    )
