"""Endpoint energy accounting for a backward-Euler network step."""

import math
from collections.abc import Mapping
from dataclasses import dataclass

from thermalpath.models import Network, _scalar
from thermalpath.transient_networks import _node_values


@dataclass(frozen=True)
class TransientEnergyBalance:
    """Store signed step energies in joules in independent dictionaries.

    Attributes
    ----------
    storage_j : dict of str to float
        C*(T_new-T_old) at each nonfixed node; positive for warming.
    source_j : dict of str to float
        Duration times applied load at each nonfixed node; positive for input.
    boundary_j : dict of str to float
        Reservoir input at each fixed node, positive into the network.
        Includes exchange between fixed nodes, which cancels in the total.
    node_residual_j : dict of str to float
        Source minus endpoint outward link energy minus storage, per nonfixed
        node. Every residual matters even if their global sum is zero.
    total_storage_j : float
        Signed sum of nonfixed-node storage changes.
    total_source_j : float
        Signed sum of applied source energies, including extraction.
    total_boundary_j : float
        Signed sum of reservoir inputs, including heat removal.
    imbalance_j : float
        Source plus reservoir input minus storage, summed directly from terms
        rather than subtracting rounded totals. No pass/fail tolerance is used.
    """

    storage_j: dict[str, float]
    source_j: dict[str, float]
    boundary_j: dict[str, float]
    node_residual_j: dict[str, float]
    total_storage_j: float
    total_source_j: float
    total_boundary_j: float
    imbalance_j: float


def _product(a: float, b: float) -> float:
    """Reject overflow or a nonzero energy/power product rounded to zero."""
    value = a * b
    if not math.isfinite(value) or (value == 0 and a != 0 and b != 0):
        raise ValueError("energy calculation is outside float range")
    return value


def transient_energy_balance(
    network: Network,
    heat_capacities_j_k: Mapping[str, float],
    old_temperatures_k: Mapping[str, float],
    new_temperatures_k: Mapping[str, float],
    duration_s: float,
    powers_w: Mapping[str, float] | None = None,
) -> TransientEnergyBalance:
    """Account for one step using supplied temperatures and endpoint fluxes.

    Parameters
    ----------
    network : Network
        Constant conductances [W/K] and fixed reservoir temperatures [K].
        Insulated, disconnected and all-fixed networks are allowed.
    heat_capacities_j_k : mapping of str to float
        Positive finite capacities [J/K], exactly the nonfixed node IDs.
    old_temperatures_k, new_temperatures_k : mapping of str to float
        Positive finite temperatures [K], exactly all node IDs. Fixed-node
        values must equal their prescribed temperatures in both maps.
    duration_s : float
        Positive finite duration [s] of this step.
    powers_w : mapping of str to float, optional
        Complete nonfixed-node loads [W] for this interval, positive for input.
        None uses Node.power_w. Pass the same override used by the solver.

    Returns
    -------
    TransientEnergyBalance
        Per-node and total energies [J], including signed residuals.

    Raises
    ------
    ValueError
        Invalid network, maps, scalars or fixed temperatures; nonfinite
        intermediate products/sums or a nonzero product rounded to zero.

    Notes
    -----
    Oriented link energy is duration*G*(T_new_a-T_new_b). This is backward
    Euler's endpoint quadrature, not the exact continuous-time heat integral.
    Arbitrary valid temperature snapshots are accepted to expose residuals.
    Small temperature changes can already be lost in the supplied floats.
    Residuals assess discrete conservation, not time accuracy or physical validity.
    """
    if not isinstance(network, Network):
        raise ValueError("network must be a Network")
    ids = {n.id for n in network.nodes}
    unknown = [n for n in network.nodes if n.fixed_temperature_k is None]
    capacity = _node_values(
        heat_capacities_j_k, {n.id for n in unknown}, "heat capacities", positive=True
    )
    rows = []
    for values in (old_temperatures_k, new_temperatures_k):
        if not isinstance(values, Mapping) or set(values) != ids:
            raise ValueError("temperatures must contain exactly all node IDs")
        row = {
            n.id: _scalar(values[n.id], "temperature", positive=True)
            for n in network.nodes
        }
        if any(
            n.fixed_temperature_k is not None and row[n.id] != n.fixed_temperature_k
            for n in network.nodes
        ):
            raise ValueError("fixed temperatures must match the network")
        rows.append(row)
    old, new = rows
    dt = _scalar(duration_s, "duration_s", positive=True)
    loads = (
        {n.id: n.power_w for n in unknown}
        if powers_w is None
        else _node_values(powers_w, set(capacity), "powers_w", positive=False)
    )
    storage = {n.id: _product(capacity[n.id], new[n.id] - old[n.id]) for n in unknown}
    source = {n.id: _product(dt, loads[n.id]) for n in unknown}
    outgoing: dict[str, list[float]] = {n.id: [] for n in network.nodes}
    for link in network.links:
        power = _product(link.conductance_w_k, new[link.node_a] - new[link.node_b])
        energy = _product(dt, power)
        outgoing[link.node_a].append(energy)
        outgoing[link.node_b].append(-energy)
    fixed = [n for n in network.nodes if n.fixed_temperature_k is not None]
    boundary_terms = [q for n in fixed for q in outgoing[n.id]]
    try:
        boundaries = {n.id: math.fsum(outgoing[n.id]) for n in fixed}
        residuals = {
            n.id: math.fsum(
                [source[n.id], -storage[n.id], *(-q for q in outgoing[n.id])]
            )
            for n in unknown
        }
        return TransientEnergyBalance(
            storage,
            source,
            boundaries,
            residuals,
            math.fsum(storage.values()),
            math.fsum(source.values()),
            math.fsum(boundary_terms),
            math.fsum(
                [*source.values(), *boundary_terms, *(-v for v in storage.values())]
            ),
        )
    except OverflowError as exc:
        raise ValueError("energy sum is outside float range") from exc
