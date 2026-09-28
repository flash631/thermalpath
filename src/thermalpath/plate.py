"""Finite-volume plates with cellwise conductivity and prescribed heaters."""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from thermalpath.boundaries import Convection
from thermalpath.grid import RectangularGrid
from thermalpath.models import Link, Network, Node, _scalar
from thermalpath.networks import solve_steady
from thermalpath.sources import RectangularHeater, map_heaters


@dataclass(frozen=True)
class PlateResult:
    """Store cell temperatures and outward lateral and broad-face powers.

    Attributes
    ----------
    temperatures_k : tuple of float
        Cell temperatures [K], in the grid's x-first flat order.
    face_powers_w : tuple of tuple of float
        Outward heat flow [W] for each cell, in west/east/south/north order.
        Positive means heat leaves that cell. Shared faces have opposite signs;
        insulated outer faces have exactly zero flow.
    broad_face_powers_w : tuple of float
        Combined outward power [W] through both broad faces, one value per
        cell. Solver results contain zeros when broad faces are insulated.
    """

    temperatures_k: tuple[float, ...]
    face_powers_w: tuple[tuple[float, ...], ...]
    broad_face_powers_w: tuple[float, ...] = ()


def solve_plate(
    grid: RectangularGrid,
    conductivity_w_m_k: float | Sequence[float],
    *,
    west_k: float | None = None,
    east_k: float | None = None,
    south_k: float | None = None,
    north_k: float | None = None,
    edge_flux_w_m2: Mapping[str, float] | None = None,
    edge_convection: Mapping[str, Convection] | None = None,
    face_convection: Convection | None = None,
    heaters: Sequence[RectangularHeater] = (),
) -> PlateResult:
    """Solve a small steady plate with prescribed or convective boundaries.

    Parameters
    ----------
    grid : RectangularGrid
        Orthogonal cells with constant positive thickness [m].
    conductivity_w_m_k : float or sequence of float
        Finite positive isotropic conductivity [W/(m K)]. A scalar applies
        everywhere; a flat sequence supplies one value per cell in x-first
        order. Material interfaces must follow cell faces, with perfect contact.
    west_k, east_k, south_k, north_k : float or None, optional
        Constant positive temperature [K] on the named geometric edge.
        None leaves the edge available for flux or convection; if neither is
        supplied, it is insulated. Adjacent edges may differ.
    edge_flux_w_m2 : mapping of str to float or None, optional
        Constant outward-positive flux [W/m2] on any of west/east/south/north.
        Negative values heat the plate. Uses lateral area including thickness.
    edge_convection : mapping of str to Convection or None, optional
        Constant film data on named lateral edges. Includes the adjacent
        half-cell conduction resistance. Each edge permits only one boundary
        type, including explicitly supplied zero flux or zero coefficient.
    face_convection : Convection or None, optional
        Combined broad-face coefficient times projected cell area. The
        coefficient is the sum for both faces, with a shared ambient and no
        extra factor of two. Temperature is uniform through the thickness.
    heaters : sequence of RectangularHeater, optional
        Uniform nonnegative heat inputs integrated over cell/footprint overlaps.
        Every footprint must lie fully inside the plate; overlapping inputs add.

    Returns
    -------
    PlateResult
        Cell temperatures, lateral powers and combined broad-face powers.

    Raises
    ------
    ValueError
        Inputs are invalid, no fixed or positive-convection anchor exists,
        a conductance is outside positive finite float range, or the
        underlying steady solve fails.

    Notes
    -----
    Solves sum_lateral Q_out + Q_broad_out = mapped_heater_power. Conductance is
    A / (d_cell/k_cell + d_other/k_other), using the two half widths.
    A includes thickness. A fixed boundary uses G = k_cell*A/d_cell,
    with the cell half width, not the full width. Edge convection uses
    G = A/(d_cell/k_cell + 1/h). Broad-face exchange uses G = h_sum*dx*dy,
    without a through-thickness resistance. Heater watts have no extra
    thickness factor. There is no storage. See docs/sources.md and
    docs/plate_boundaries.md for conventions and limits.
    Reuses the dense network solver: memory grows quadratically with cell
    count. Intended for small grids. Finite results do not certify accuracy,
    mesh convergence or physical validity. See docs/plate.md.
    """
    if not isinstance(grid, RectangularGrid):
        raise ValueError("grid must be a RectangularGrid")
    heater_powers = map_heaters(grid, heaters)
    if isinstance(conductivity_w_m_k, Sequence) and not isinstance(
        conductivity_w_m_k, (str, bytes)
    ):
        if len(conductivity_w_m_k) != grid.cell_count:
            raise ValueError("conductivity sequence must contain one value per cell")
        conductivities = tuple(
            _scalar(value, f"conductivity_w_m_k[{cell}]", positive=True)
            for cell, value in enumerate(conductivity_w_m_k)
        )
    else:
        conductivity = _scalar(conductivity_w_m_k, "conductivity_w_m_k", positive=True)
        conductivities = (conductivity,) * grid.cell_count
    edges = (west_k, east_k, south_k, north_k)
    names = ("west", "east", "south", "north")
    fluxes = _edge_mapping(edge_flux_w_m2, "edge_flux_w_m2", names)
    convection = _edge_mapping(edge_convection, "edge_convection", names)
    fluxes = {name: _scalar(value, "edge flux") for name, value in fluxes.items()}
    for boundary in (*convection.values(), face_convection):
        if boundary is not None and not isinstance(boundary, Convection):
            raise ValueError("convection data must be Convection")
    if any(value is None for value in convection.values()):
        raise ValueError("edge_convection entries must be Convection")
    nodes = []
    for name, temperature in zip(names, edges, strict=True):
        if sum((temperature is not None, name in fluxes, name in convection)) > 1:
            raise ValueError(f"{name} has more than one boundary type")
        if temperature is not None:
            nodes.append(Node(name, fixed_temperature_k=temperature))
        elif name in convection and convection[name].coefficient_w_m2_k > 0:
            nodes.append(
                Node(name, fixed_temperature_k=convection[name].ambient_temperature_k)
            )
    if face_convection is not None and face_convection.coefficient_w_m2_k > 0:
        nodes.append(
            Node("broad", fixed_temperature_k=face_convection.ambient_temperature_k)
        )
    if not nodes:
        raise ValueError(
            "at least one fixed-temperature or positive-convection anchor is required"
        )

    widths = tuple(
        b - a for a, b in zip(grid.x_edges_m[:-1], grid.x_edges_m[1:], strict=True)
    )
    heights = tuple(
        b - a for a, b in zip(grid.y_edges_m[:-1], grid.y_edges_m[1:], strict=True)
    )
    links = []
    faces = []
    broad_links = []
    powers = [[0.0] * 4 for _ in range(grid.cell_count)]
    for cell in range(grid.cell_count):
        conductivity = conductivities[cell]
        ix, iy = grid.indices(cell)
        distances = (widths[ix] / 2,) * 2 + (heights[iy] / 2,) * 2
        for side, neighbor in enumerate(grid.neighbors(cell)):
            if neighbor is not None:
                if side in (0, 2):
                    continue  # Each internal face is constructed once.
                jx, jy = grid.indices(neighbor)
                other_half = widths[jx] / 2 if side == 1 else heights[jy] / 2
                distance = distances[side] + other_half
                endpoint = str(neighbor)
            else:
                name = names[side]
                if name in fluxes:
                    power = _scalar(
                        fluxes[name] * grid.face_areas_m2(cell)[side], "flux power"
                    )
                    if power == 0 and fluxes[name] != 0:
                        raise ValueError(
                            "flux power has nonzero magnitude below the float range"
                        )
                    powers[cell][side] = power
                    continue
                if edges[side] is None:
                    if (
                        name not in convection
                        or convection[name].coefficient_w_m2_k == 0
                    ):
                        continue
                distance = distances[side]
                endpoint = names[side]
            distance = _scalar(distance, "face distance", positive=True)
            area = grid.face_areas_m2(cell)[side]
            if neighbor is None and names[side] in convection:
                film = convection[names[side]].coefficient_w_m2_k
                half_resistance = _scalar(
                    distance / conductivity, "edge resistance factor", positive=True
                )
                film_resistance = _scalar(
                    1 / film, "film resistance factor", positive=True
                )
                resistance_factor = _scalar(
                    half_resistance + film_resistance,
                    "edge resistance factor",
                    positive=True,
                )
                conductance = area / resistance_factor
            elif neighbor is not None and conductivity != conductivities[neighbor]:
                # Series half-cell resistances, multiplied by the common area.
                left = _scalar(
                    distances[side] / conductivity,
                    "face resistance factor",
                    positive=True,
                )
                right = _scalar(
                    other_half / conductivities[neighbor],
                    "face resistance factor",
                    positive=True,
                )
                resistance_factor = _scalar(
                    left + right, "face resistance factor", positive=True
                )
                conductance = area / resistance_factor
            else:
                conductance = conductivity * area / distance
            conductance = _scalar(conductance, "face conductance", positive=True)
            link_id = str(len(links))
            links.append(Link(link_id, str(cell), endpoint, conductance))
            faces.append((link_id, cell, side, neighbor))

        try:
            load = math.fsum([heater_powers[cell], *(-power for power in powers[cell])])
        except OverflowError as exc:
            raise ValueError("summed flux and heater power must be finite") from exc
        nodes.append(Node(str(cell), power_w=load))
        if face_convection is not None and face_convection.coefficient_w_m2_k > 0:
            conductance = _scalar(
                face_convection.coefficient_w_m2_k * grid.cell_area_m2(cell),
                "broad-face conductance",
                positive=True,
            )
            link_id = str(len(links))
            links.append(Link(link_id, str(cell), "broad", conductance))
            broad_links.append((link_id, cell))

    result = solve_steady(Network(tuple(nodes), tuple(links)))
    for link_id, cell, side, neighbor in faces:
        power = result.link_powers_w[link_id]
        powers[cell][side] = power
        if neighbor is not None:
            powers[neighbor][side - 1] = -power
    broad_powers = [0.0] * grid.cell_count
    for link_id, cell in broad_links:
        broad_powers[cell] = result.link_powers_w[link_id]
    return PlateResult(
        tuple(result.temperatures_k[str(cell)] for cell in range(grid.cell_count)),
        tuple(tuple(cell_powers) for cell_powers in powers),
        tuple(broad_powers),
    )


def _edge_mapping[T](
    value: Mapping[str, T] | None, label: str, names: tuple[str, ...]
) -> dict[str, T]:
    """Copy a mapping and reject misspelled edge names."""
    if value is None:
        return {}
    if not isinstance(value, Mapping) or any(name not in names for name in value):
        raise ValueError(f"{label} must map west/east/south/north names to values")
    return dict(value)
