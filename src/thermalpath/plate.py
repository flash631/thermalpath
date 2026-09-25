"""Source-free, constant-conductivity finite-volume plate solutions."""

from dataclasses import dataclass

from thermalpath.grid import RectangularGrid
from thermalpath.models import Link, Network, Node, _scalar
from thermalpath.networks import solve_steady


@dataclass(frozen=True)
class PlateResult:
    """Store cell temperatures and outward lateral-face powers.

    Attributes
    ----------
    temperatures_k : tuple of float
        Cell temperatures [K], in the grid's x-first flat order.
    face_powers_w : tuple of tuple of float
        Outward heat flow [W] for each cell, in west/east/south/north order.
        Positive means heat leaves that cell. Shared faces have opposite signs;
        insulated outer faces have exactly zero flow.
    """

    temperatures_k: tuple[float, ...]
    face_powers_w: tuple[tuple[float, ...], ...]


def solve_plate(
    grid: RectangularGrid,
    conductivity_w_m_k: float,
    *,
    west_k: float | None = None,
    east_k: float | None = None,
    south_k: float | None = None,
    north_k: float | None = None,
) -> PlateResult:
    """Solve a small steady plate with fixed-temperature or insulated edges.

    Parameters
    ----------
    grid : RectangularGrid
        Orthogonal cells with constant positive thickness [m].
    conductivity_w_m_k : float
        Finite positive, uniform isotropic conductivity [W/(m K)].
    west_k, east_k, south_k, north_k : float or None, optional
        Constant positive temperature [K] on the named geometric edge.
        None means insulated (zero outward power). At least one fixed edge
        is required. Adjacent fixed edges may have different temperatures.

    Returns
    -------
    PlateResult
        Temperatures at cell centers and signed outward face powers.

    Raises
    ------
    ValueError
        Inputs are invalid, all edges are insulated, a conductance is outside
        positive finite float range, or the underlying steady solve fails.

    Notes
    -----
    Solves sum_faces G * (T_cell - T_other) = 0, with G = k * A / d.
    A includes thickness. Internal d is the sum of adjacent half widths;
    boundary d is the cell half width, not the full width. The two broad
    faces are insulated and there is no heat generation or storage.
    Reuses the dense network solver: memory grows quadratically with cell
    count. Intended for small grids. Finite results do not certify accuracy,
    mesh convergence or physical validity. See docs/plate.md.
    """
    if not isinstance(grid, RectangularGrid):
        raise ValueError("grid must be a RectangularGrid")
    conductivity = _scalar(conductivity_w_m_k, "conductivity_w_m_k", positive=True)
    edges = (west_k, east_k, south_k, north_k)
    names = ("west", "east", "south", "north")
    nodes = [Node(str(cell)) for cell in range(grid.cell_count)]
    for name, temperature in zip(names, edges, strict=True):
        if temperature is not None:
            nodes.append(Node(name, fixed_temperature_k=temperature))
    if all(temperature is None for temperature in edges):
        raise ValueError("at least one fixed-temperature edge is required")

    widths = tuple(
        b - a for a, b in zip(grid.x_edges_m[:-1], grid.x_edges_m[1:], strict=True)
    )
    heights = tuple(
        b - a for a, b in zip(grid.y_edges_m[:-1], grid.y_edges_m[1:], strict=True)
    )
    links = []
    faces = []
    for cell in range(grid.cell_count):
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
                if edges[side] is None:
                    continue
                distance = distances[side]
                endpoint = names[side]
            distance = _scalar(distance, "face distance", positive=True)
            conductance = _scalar(
                conductivity * grid.face_areas_m2(cell)[side] / distance,
                "face conductance",
                positive=True,
            )
            link_id = str(len(links))
            links.append(Link(link_id, str(cell), endpoint, conductance))
            faces.append((link_id, cell, side, neighbor))

    result = solve_steady(Network(tuple(nodes), tuple(links)))
    powers = [[0.0] * 4 for _ in range(grid.cell_count)]
    for link_id, cell, side, neighbor in faces:
        power = result.link_powers_w[link_id]
        powers[cell][side] = power
        if neighbor is not None:
            powers[neighbor][side - 1] = -power
    return PlateResult(
        tuple(result.temperatures_k[str(cell)] for cell in range(grid.cell_count)),
        tuple(tuple(cell_powers) for cell_powers in powers),
    )
