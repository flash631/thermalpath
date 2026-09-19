"""Connectivity and signed steady heat accounting for thermal networks."""

import math
from collections.abc import Mapping
from dataclasses import dataclass

from thermalpath.models import Network, _scalar


def check_connectivity(network: Network) -> tuple[tuple[str, ...], ...]:
    """Return anchored components in input order, or identify floating ones.

    Parameters
    ----------
    network : Network
        Validated nodes and positive-conductance links.

    Returns
    -------
    tuple of tuple of str
        Node IDs grouped by connected component. Components follow their first
        node's input position; nodes within each component retain input order.
        Separate anchored components and isolated fixed nodes are allowed.

    Raises
    ------
    ValueError
        The input is not a Network or a component has no fixed temperature.
        The error lists every unanchored component, including isolated nodes.

    Notes
    -----
    A component without a fixed temperature cannot have a unique absolute
    steady temperature, even if its prescribed loads sum to zero. This check
    establishes graph anchoring only, not numerical conditioning or accuracy.
    """
    if not isinstance(network, Network):
        raise ValueError("network must be a Network")
    neighbors: dict[str, list[str]] = {node.id: [] for node in network.nodes}
    order = {node.id: i for i, node in enumerate(network.nodes)}
    fixed = {node.id for node in network.nodes if node.fixed_temperature_k is not None}
    for link in network.links:
        neighbors[link.node_a].append(link.node_b)
        neighbors[link.node_b].append(link.node_a)
    reached: set[str] = set()
    components = []
    unanchored = []
    for node in network.nodes:
        if node.id in reached:
            continue
        pending = [node.id]
        reached.add(node.id)
        members = []
        while pending:
            current = pending.pop()
            members.append(current)
            for neighbor in neighbors[current]:
                if neighbor not in reached:
                    reached.add(neighbor)
                    pending.append(neighbor)
        component = tuple(sorted(members, key=order.__getitem__))
        components.append(component)
        if fixed.isdisjoint(component):
            unanchored.append(component)
    if unanchored:
        raise ValueError(
            "every unknown node needs a path to a fixed temperature; "
            f"unanchored components: {unanchored!r}"
        )
    return tuple(components)


@dataclass(frozen=True)
class HeatBalance:
    """Report signed power accounting in watts, with independent result copies.

    Attributes
    ----------
    node_outflow_w : dict of str to float
        Sum of outward link powers at each node, in input node order.
    node_residual_w : dict of str to float
        Applied load minus outward link powers at unknown-temperature nodes.
        Positive values mean excess heat input; negative values mean a deficit.
    boundary_power_w : dict of str to float
        Required reservoir input at fixed nodes, positive into the network.
        Negative values mean heat removed by the reservoir.
    total_input_w : float
        Sum of positive prescribed loads and positive reservoir inputs.
    total_output_w : float
        Positive magnitude of negative prescribed loads and reservoir inputs.
    imbalance_w : float
        Signed sum of all prescribed loads and reservoir inputs, evaluated
        directly rather than by subtracting the two rounded totals.
    """

    node_outflow_w: dict[str, float]
    node_residual_w: dict[str, float]
    boundary_power_w: dict[str, float]
    total_input_w: float
    total_output_w: float
    imbalance_w: float


def heat_balance(network: Network, link_powers_w: Mapping[str, float]) -> HeatBalance:
    """Account for supplied oriented powers without solving or hiding residuals.

    Parameters
    ----------
    network : Network
        Validated network with every connected component anchored.
    link_powers_w : mapping of str to float
        Exactly one finite real power [W] per link ID. Positive means node_a
        to node_b. Usually this is solve_steady(network).link_powers_w.

    Returns
    -------
    HeatBalance
        Nodal balances, inferred boundary powers, and external power totals.

    Raises
    ------
    ValueError
        Connectivity is unanchored, power IDs do not match, powers are invalid,
        or a sum exceeds floating-point range.

    Notes
    -----
    Each link contributes +q at node_a and -q at node_b to outward flow.
    Every unknown-node residual matters: opposite errors can cancel globally.
    No acceptance tolerance is imposed. These balances do not verify q=G*dT,
    temperature boundaries, solver accuracy, or physical model validity.
    """
    check_connectivity(network)
    if not isinstance(link_powers_w, Mapping) or set(link_powers_w) != {
        link.id for link in network.links
    }:
        raise ValueError("link_powers_w must map exactly the network link IDs")
    outgoing: dict[str, list[float]] = {node.id: [] for node in network.nodes}
    for link in network.links:
        power = _scalar(link_powers_w[link.id], f"link power {link.id!r}")
        outgoing[link.node_a].append(power)
        outgoing[link.node_b].append(-power)
    try:
        outflow = {name: math.fsum(values) for name, values in outgoing.items()}
        residuals = {
            node.id: math.fsum([node.power_w, *(-q for q in outgoing[node.id])])
            for node in network.nodes
            if node.fixed_temperature_k is None
        }
        boundaries = {
            node.id: outflow[node.id]
            for node in network.nodes
            if node.fixed_temperature_k is not None
        }
        external = [node.power_w for node in network.nodes] + list(boundaries.values())
        return HeatBalance(
            outflow,
            residuals,
            boundaries,
            math.fsum(power for power in external if power > 0),
            math.fsum(-power for power in external if power < 0),
            math.fsum(external),
        )
    except OverflowError as exc:
        raise ValueError("heat-balance sum is outside float range") from exc
