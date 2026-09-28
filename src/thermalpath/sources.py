"""Conservative overlap mapping for uniform rectangular heaters."""

import math
from collections.abc import Sequence
from dataclasses import dataclass

from thermalpath.grid import RectangularGrid
from thermalpath.models import _scalar


@dataclass(frozen=True)
class RectangularHeater:
    """Prescribe total heat input uniformly over a rectangular footprint.

    Parameters
    ----------
    x_min_m, x_max_m, y_min_m, y_max_m : float
        Finite footprint edges [m], with strictly positive width and height.
        The footprint must lie fully inside the grid when mapped.
    power_w : float
        Finite nonnegative total input [W]. Zero disables the heat input,
        but geometry is still validated. Overlapping heaters add their powers.

    Notes
    -----
    The projected footprint area must be finite and positive in float
    arithmetic. Power is already integrated through the thickness; mapping
    does not multiply by thickness or by the number of broad faces.
    """

    x_min_m: float
    x_max_m: float
    y_min_m: float
    y_max_m: float
    power_w: float

    def __post_init__(self) -> None:
        """Normalize SI values and reject invalid geometry and power."""
        for name in ("x_min_m", "x_max_m", "y_min_m", "y_max_m", "power_w"):
            object.__setattr__(self, name, _scalar(getattr(self, name), name))
        width = _scalar(self.x_max_m - self.x_min_m, "heater width", positive=True)
        height = _scalar(self.y_max_m - self.y_min_m, "heater height", positive=True)
        _scalar(width * height, "heater area", positive=True)
        if self.power_w < 0:
            raise ValueError("heater power_w must be nonnegative")


def map_heaters(
    grid: RectangularGrid, heaters: Sequence[RectangularHeater]
) -> tuple[float, ...]:
    """Integrate uniform heater inputs over cells in x-first flat order.

    Parameters
    ----------
    grid : RectangularGrid
        Grid covering every heater footprint completely.
    heaters : sequence of RectangularHeater
        Uniform rectangular inputs, including an empty sequence for no heat.

    Returns
    -------
    tuple of float
        Total prescribed input [W] for each cell. Positive heats the plate.

    Raises
    ------
    ValueError
        Inputs are invalid, a footprint extends outside the domain, or a
        positive contribution or summed power is outside finite float range.

    Notes
    -----
    Each contribution is P*(overlap_width/heater_width)*
    (overlap_height/heater_height). It is zero for an empty intersection.
    Shared footprint boundaries have zero area. No clipping or correction
    to force the rounded sum is applied. Conservation holds in exact
    arithmetic; floating-point limits are documented in docs/sources.md.
    """
    if not isinstance(grid, RectangularGrid):
        raise ValueError("grid must be a RectangularGrid")
    if not isinstance(heaters, Sequence) or isinstance(heaters, (str, bytes)):
        raise ValueError("heaters must be a sequence of RectangularHeater")
    heaters = tuple(heaters)
    for heater in heaters:
        if not isinstance(heater, RectangularHeater):
            raise ValueError("heaters must contain only RectangularHeater")
        if not (
            grid.x_edges_m[0] <= heater.x_min_m < heater.x_max_m <= grid.x_edges_m[-1]
            and grid.y_edges_m[0]
            <= heater.y_min_m
            < heater.y_max_m
            <= grid.y_edges_m[-1]
        ):
            raise ValueError("heater footprint must lie fully inside the grid")
    powers = []
    for cell in range(grid.cell_count):
        ix, iy = grid.indices(cell)
        contributions = []
        for heater in heaters:
            dx = min(grid.x_edges_m[ix + 1], heater.x_max_m) - max(
                grid.x_edges_m[ix], heater.x_min_m
            )
            dy = min(grid.y_edges_m[iy + 1], heater.y_max_m) - max(
                grid.y_edges_m[iy], heater.y_min_m
            )
            if dx <= 0 or dy <= 0 or heater.power_w == 0:
                continue
            contribution = (
                heater.power_w
                * (dx / (heater.x_max_m - heater.x_min_m))
                * (dy / (heater.y_max_m - heater.y_min_m))
            )
            contributions.append(_scalar(contribution, "mapped power", positive=True))
        try:
            power = math.fsum(contributions)
        except OverflowError as exc:
            raise ValueError("summed heater power must be finite") from exc
        powers.append(_scalar(power, "summed heater power"))
    return tuple(powers)
