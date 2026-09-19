"""Dense steady solutions for small constant-conductance thermal networks."""

import math
from dataclasses import dataclass

import numpy as np

from thermalpath.models import Network


@dataclass(frozen=True)
class SteadyResult:
    """Report temperatures [K] and oriented link powers [W] by input ID.

    Attributes
    ----------
    temperatures_k : dict of str to float
        All node temperatures, in input node order.
    link_powers_w : dict of str to float
        All link powers, in input link order; positive from node_a to node_b.

    Notes
    -----
    Dictionaries are independent result copies and may be edited by the caller.
    No reservoir reaction or heat-balance diagnostic is included.
    """

    temperatures_k: dict[str, float]
    link_powers_w: dict[str, float]


def solve_steady(network: Network) -> SteadyResult:
    """Solve steady node balances with prescribed temperature boundaries.

    Parameters
    ----------
    network : Network
        Validated constant positive conductances [W/K], signed nodal loads [W],
        and fixed boundary temperatures [K]. Every unknown node must have a
        path to at least one fixed-temperature node.

    Returns
    -------
    SteadyResult
        Positive absolute temperatures and powers G * (T_a - T_b).

    Raises
    ------
    ValueError
        The input is not a Network, an unknown node lacks a fixed boundary,
        the assembled system is singular or exceeds floating-point range,
        a temperature is nonfinite/nonpositive, or a nonzero link power
        overflows or underflows to zero.

    Notes
    -----
    Solves L_uu T_u = P_u - L_uf T_f using a dense binary64 linear solve.
    There is no storage, radiation, or temperature-dependent conductance.
    This direct solve has no mesh, iteration, or time-step convergence parameter.
    Extreme conductance ratios or small temperature differences can lose
    accuracy; finite results are not an accuracy certificate. See docs/networks.md.
    """
    if not isinstance(network, Network):
        raise ValueError("network must be a Network")
    temperatures = {
        node.id: node.fixed_temperature_k
        for node in network.nodes
        if node.fixed_temperature_k is not None
    }
    neighbors: dict[str, list[str]] = {node.id: [] for node in network.nodes}
    for link in network.links:
        neighbors[link.node_a].append(link.node_b)
        neighbors[link.node_b].append(link.node_a)
    reached = set(temperatures)
    pending = list(reached)
    while pending:
        for neighbor in neighbors[pending.pop()]:
            if neighbor not in reached:
                reached.add(neighbor)
                pending.append(neighbor)
    if len(reached) != len(network.nodes):
        raise ValueError("every unknown node needs a path to a fixed temperature")

    unknown = [node for node in network.nodes if node.fixed_temperature_k is None]
    indices = {node.id: i for i, node in enumerate(unknown)}
    if unknown:
        matrix = np.zeros((len(unknown), len(unknown)), dtype=float)
        rhs = np.array([node.power_w for node in unknown], dtype=float)
        try:
            with np.errstate(over="raise", invalid="raise", under="raise"):
                for link in network.links:
                    for a, b in (
                        (link.node_a, link.node_b),
                        (link.node_b, link.node_a),
                    ):
                        if a in indices:
                            i = indices[a]
                            matrix[i, i] += link.conductance_w_k
                            if b in indices:
                                matrix[i, indices[b]] -= link.conductance_w_k
                            else:
                                rhs[i] += (
                                    np.float64(link.conductance_w_k) * temperatures[b]
                                )
                solution = np.linalg.solve(matrix, rhs)
        except (FloatingPointError, np.linalg.LinAlgError) as exc:
            raise ValueError(
                "steady system is singular or outside float range"
            ) from exc
        if not np.all(np.isfinite(solution)) or np.any(solution <= 0):
            raise ValueError("calculated temperatures must be finite and positive")
        temperatures.update(
            (node.id, float(solution[i])) for i, node in enumerate(unknown)
        )

    powers = {}
    for link in network.links:
        difference = temperatures[link.node_a] - temperatures[link.node_b]
        power = link.conductance_w_k * difference
        if not math.isfinite(power) or (power == 0 and difference != 0):
            raise ValueError("calculated link power is outside float range")
        powers[link.id] = power
    return SteadyResult(
        {node.id: temperatures[node.id] for node in network.nodes}, powers
    )
