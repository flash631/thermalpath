"""Immutable inputs for constant-conductance thermal networks in SI units."""

import math
from dataclasses import dataclass
from numbers import Real


def _identifier(value: str, name: str) -> None:
    """Require a nonempty identifier without surrounding whitespace."""
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{name} must be a nonempty string without outer whitespace")


def _scalar(value: float, name: str, *, positive: bool = False) -> float:
    """Normalize a finite real scalar, optionally requiring strict positivity."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a real scalar")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} must fit in a finite float") from exc
    if result == 0 and value != 0:
        raise ValueError(f"{name} has nonzero magnitude below the float range")
    if not math.isfinite(result) or (positive and result <= 0):
        domain = "finite and positive" if positive else "finite"
        raise ValueError(f"{name} must be {domain}")
    return result


@dataclass(frozen=True)
class Node:
    """Define a thermal node with a load or a prescribed temperature.

    Parameters
    ----------
    id : str
        Case-sensitive node identifier, unique within a network.
    power_w : float, optional
        Finite heat input [W], positive into the node, negative for extraction.
        Defaults to zero. Must be zero when a temperature is prescribed.
    fixed_temperature_k : float or None, optional
        Finite positive prescribed absolute temperature [K]. None leaves the
        temperature unknown. A fixed boundary supplies or removes whatever
        power is required; this model does not also prescribe that power.

    Raises
    ------
    ValueError
        An identifier, scalar domain, or boundary definition is invalid.
    """

    id: str
    power_w: float = 0.0
    fixed_temperature_k: float | None = None

    def __post_init__(self) -> None:
        """Validate and normalize immutable node fields."""
        _identifier(self.id, "node id")
        power = _scalar(self.power_w, "power_w")
        object.__setattr__(self, "power_w", power)
        if self.fixed_temperature_k is not None:
            temperature = _scalar(
                self.fixed_temperature_k, "fixed_temperature_k", positive=True
            )
            object.__setattr__(self, "fixed_temperature_k", temperature)
            if power != 0:
                raise ValueError("a fixed-temperature node must have zero power_w")


@dataclass(frozen=True)
class Link:
    """Define a passive thermal conductance between distinct nodes.

    Parameters
    ----------
    id : str
        Case-sensitive link identifier, unique within a network.
    node_a : str
        Identifier of the first endpoint; positive link power flows from a to b.
    node_b : str
        Identifier of the second endpoint.
    conductance_w_k : float
        Finite positive constant conductance [W/K]. The constitutive relation
        is q_ab = conductance_w_k * (T_a - T_b) [W]. Omit an insulated link;
        infinite conductance (an ideal short) is not represented here.

    Raises
    ------
    ValueError
        An identifier or conductance is invalid, or both endpoints are equal.
    """

    id: str
    node_a: str
    node_b: str
    conductance_w_k: float

    def __post_init__(self) -> None:
        """Validate endpoints and normalize immutable conductance."""
        _identifier(self.id, "link id")
        _identifier(self.node_a, "node_a")
        _identifier(self.node_b, "node_b")
        if self.node_a == self.node_b:
            raise ValueError("link endpoints must be distinct")
        object.__setattr__(
            self,
            "conductance_w_k",
            _scalar(self.conductance_w_k, "conductance_w_k", positive=True),
        )


@dataclass(frozen=True)
class Network:
    """Collect nodes and links with unique IDs and existing endpoints.

    Parameters
    ----------
    nodes : tuple of Node
        Nonempty node collection. Lists are also accepted and copied to tuples.
    links : tuple of Link, optional
        Link collection, empty by default. Lists are copied to tuples. Parallel
        links are allowed when their IDs differ. Node and link ID namespaces
        are separate.

    Raises
    ------
    ValueError
        Collections or members have wrong types, nodes are empty, IDs repeat,
        or a link references a missing node.

    Notes
    -----
    Structural validation does not guarantee a unique steady solution. Isolated
    nodes and networks without fixed boundaries remain valid input records.
    No connectivity diagnosis or temperature solution is performed here.
    """

    nodes: tuple[Node, ...]
    links: tuple[Link, ...] = ()

    def __post_init__(self) -> None:
        """Copy collections and check references without changing their order."""
        for name, item_type in (("nodes", Node), ("links", Link)):
            items = getattr(self, name)
            if not isinstance(items, (tuple, list)) or any(
                not isinstance(item, item_type) for item in items
            ):
                raise ValueError(
                    f"{name} must be a tuple or list of {item_type.__name__}"
                )
            object.__setattr__(self, name, tuple(items))
            if len({item.id for item in items}) != len(items):
                raise ValueError(f"duplicate IDs in {name}")
        if not self.nodes:
            raise ValueError("nodes must be nonempty")
        node_ids = {node.id for node in self.nodes}
        for link in self.links:
            if link.node_a not in node_ids or link.node_b not in node_ids:
                raise ValueError(f"link {link.id!r} references a missing node")
