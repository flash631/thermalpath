"""Backward-Euler integration of small constant-conductance networks."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from thermalpath.models import Network, _scalar


@dataclass(frozen=True)
class TransientResult:
    """Store times [s] and node temperatures [K], including the initial state.

    Attributes
    ----------
    times_s : tuple of float
        Requested integration grid.
    temperatures_k : tuple of dict of str to float
        Independent dictionaries in time order, with nodes in input order.
        Callers may edit dictionaries without changing inputs or other rows.
    """

    times_s: tuple[float, ...]
    temperatures_k: tuple[dict[str, float], ...]


def _node_values(
    values: Mapping[str, float], ids: set[str], name: str, *, positive: bool
) -> dict[str, float]:
    """Copy a complete unknown-node map and validate its scalar values."""
    if not isinstance(values, Mapping) or set(values) != ids:
        raise ValueError(f"{name} must contain exactly the nonfixed node IDs")
    return {
        key: _scalar(value, name, positive=positive) for key, value in values.items()
    }


def solve_transient(
    network: Network,
    heat_capacities_j_k: Mapping[str, float],
    initial_temperatures_k: Mapping[str, float],
    times_s: Sequence[float],
    interval_powers_w: Sequence[Mapping[str, float]] | None = None,
) -> TransientResult:
    """Integrate temperatures with backward Euler and piecewise constant loads.

    Parameters
    ----------
    network : Network
        Constant positive conductances [W/K] and constant fixed boundaries [K].
        Insulated and disconnected components are allowed.
    heat_capacities_j_k : mapping of str to float
        Finite positive heat capacities [J/K], exactly one per nonfixed node.
    initial_temperatures_k : mapping of str to float
        Finite positive temperatures [K] at times_s[0], for nonfixed nodes only.
    times_s : sequence of float
        At least two finite, nonnegative, strictly increasing times [s].
        Every load change must coincide with a grid point.
    interval_powers_w : sequence of mapping, optional
        One complete nonfixed-node load map [W] per interval. Map i applies
        from times_s[i] up to times_s[i+1], replacing all Node.power_w values.
        Positive means heating; negative means extraction. None uses the
        network's constant loads on every interval. No interpolation is used.

    Returns
    -------
    TransientResult
        Initial and computed temperatures; prescribed nodes stay exactly fixed.

    Raises
    ------
    ValueError
        Invalid maps, scalars, time grid or load count; unrepresentable time
        differences or assembled system; numerical singularity; nonpositive
        or nonfinite calculated temperatures.

    Notes
    -----
    Solves (C/dt + L_uu) T_new = (C/dt) T_old + P - L_uf T_fixed.
    Positive capacity gives a unique update without a fixed boundary in exact
    arithmetic. Uses dense binary64 solves with no accuracy certificate.
    Negative loads can produce invalid temperatures. Positivity checks cover
    computed grid states only, not the underlying continuous trajectory.
    Use transient_energy_balance with the same interval loads for step accounting.
    """
    if not isinstance(network, Network):
        raise ValueError("network must be a Network")
    unknown = [n for n in network.nodes if n.fixed_temperature_k is None]
    ids = {n.id for n in unknown}
    capacity = _node_values(heat_capacities_j_k, ids, "heat capacities", positive=True)
    initial = _node_values(
        initial_temperatures_k, ids, "initial temperatures", positive=True
    )
    if not isinstance(times_s, Sequence) or len(times_s) < 2:
        raise ValueError("times_s must be a sequence with at least two times")
    times = tuple(_scalar(t, "times_s") for t in times_s)
    if times[0] < 0 or any(b <= a for a, b in zip(times, times[1:], strict=False)):
        raise ValueError("times_s must be nonnegative and strictly increasing")
    if interval_powers_w is None:
        loads = [{n.id: n.power_w for n in unknown}] * (len(times) - 1)
    else:
        if (
            not isinstance(interval_powers_w, Sequence)
            or len(interval_powers_w) != len(times) - 1
        ):
            raise ValueError("provide one load map per time interval")
        loads = [
            _node_values(p, ids, "interval powers", positive=False)
            for p in interval_powers_w
        ]
    temperatures = {
        n.id: initial[n.id] if n.id in ids else n.fixed_temperature_k
        for n in network.nodes
    }
    rows = [temperatures.copy()]
    indices = {n.id: i for i, n in enumerate(unknown)}
    matrix = np.zeros((len(unknown), len(unknown)))
    boundary = np.zeros(len(unknown))
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise", under="raise"):
            for link in network.links:
                for a, b in ((link.node_a, link.node_b), (link.node_b, link.node_a)):
                    if a in indices:
                        i = indices[a]
                        matrix[i, i] += link.conductance_w_k
                        if b in indices:
                            matrix[i, indices[b]] -= link.conductance_w_k
                        else:
                            boundary[i] += (
                                np.float64(link.conductance_w_k) * temperatures[b]
                            )
            capacities = np.array([capacity[n.id] for n in unknown])
            old = np.array([initial[n.id] for n in unknown])
            for start, end, load in zip(times, times[1:], loads, strict=False):
                dt = end - start
                if unknown:
                    storage = capacities / dt
                    system = matrix + np.diag(storage)
                    rhs = (
                        storage * old
                        + boundary
                        + np.array([load[n.id] for n in unknown])
                    )
                    old = np.linalg.solve(system, rhs)
                    if not np.all(np.isfinite(old)) or np.any(old <= 0):
                        raise ValueError(
                            "calculated temperatures must be finite and positive"
                        )
                    temperatures.update(
                        (n.id, float(old[i])) for i, n in enumerate(unknown)
                    )
                rows.append(temperatures.copy())
    except (FloatingPointError, np.linalg.LinAlgError) as exc:
        raise ValueError("transient system is singular or outside float range") from exc
    return TransientResult(times, tuple(rows))
