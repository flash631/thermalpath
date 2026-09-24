"""Rectangular cell geometry for a plate of constant thickness."""

from dataclasses import dataclass, field
from numbers import Integral

from thermalpath.models import _scalar


def _axis(
    edges: tuple[float, ...], name: str
) -> tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]:
    """Normalize edges and require representable widths and interior centers."""
    if not isinstance(edges, (tuple, list)) or len(edges) < 2:
        raise ValueError(f"{name} must be a tuple or list with at least two edges")
    values = tuple(_scalar(value, name) for value in edges)
    widths = tuple(
        _scalar(b - a, f"{name} width", positive=True)
        for a, b in zip(values[:-1], values[1:], strict=True)
    )
    centers = tuple(a + width / 2 for a, width in zip(values[:-1], widths, strict=True))
    if any(
        not a < center < b
        for a, center, b in zip(values[:-1], centers, values[1:], strict=True)
    ):
        raise ValueError(f"{name} centers must lie strictly inside their cells")
    return values, widths, centers


def _index(value: int, size: int, name: str) -> int:
    """Validate an integer index; negative indexing is not supported."""
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an integer")
    if not 0 <= value < size:
        raise ValueError(f"{name} is outside the grid")
    return int(value)


@dataclass(frozen=True)
class RectangularGrid:
    """Define axis-aligned rectangular cells extruded through one thickness.

    Parameters
    ----------
    x_edges_m, y_edges_m : tuple of float
        Finite, strictly increasing edge coordinates [m], at least two per
        axis. Lists are copied to tuples. Unequal widths and negative origins
        are allowed. Each computed center must lie strictly inside its cell.
    thickness_m : float
        Finite positive uniform thickness [m].

    Raises
    ------
    ValueError
        Edges or thickness are invalid, or a width, area, volume or center
        cannot be represented with the required finite positive geometry.

    Notes
    -----
    Flat indices increase in x first: index = iy * nx + ix. Neighbor and
    lateral-face tuples use west, east, south, north order. Missing neighbors
    are None, which identifies geometry only, not a thermal boundary condition.
    Top and bottom face areas equal cell_area_m2; lateral faces include thickness.
    No temperature, material, load or thermal boundary data are stored.
    """

    x_edges_m: tuple[float, ...]
    y_edges_m: tuple[float, ...]
    thickness_m: float
    _widths: tuple[float, ...] = field(init=False, repr=False)
    _heights: tuple[float, ...] = field(init=False, repr=False)
    _x_centers: tuple[float, ...] = field(init=False, repr=False)
    _y_centers: tuple[float, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Validate geometry without allocating a full cell array."""
        for name, widths_name, centers_name in (
            ("x_edges_m", "_widths", "_x_centers"),
            ("y_edges_m", "_heights", "_y_centers"),
        ):
            edges, widths, centers = _axis(getattr(self, name), name)
            object.__setattr__(self, name, edges)
            object.__setattr__(self, widths_name, widths)
            object.__setattr__(self, centers_name, centers)
        thickness = _scalar(self.thickness_m, "thickness_m", positive=True)
        object.__setattr__(self, "thickness_m", thickness)
        # Positive products are monotone: extrema bound every cell and face.
        for width in (min(self._widths), max(self._widths)):
            _scalar(width * thickness, "south/north face area", positive=True)
            for height in (min(self._heights), max(self._heights)):
                area = _scalar(width * height, "cell area", positive=True)
                _scalar(area * thickness, "cell volume", positive=True)
        for height in (min(self._heights), max(self._heights)):
            _scalar(height * thickness, "west/east face area", positive=True)
        _scalar(self.area_m2, "domain area", positive=True)
        _scalar(self.volume_m3, "domain volume", positive=True)

    @property
    def nx(self) -> int:
        """Number of cells along x."""
        return len(self._widths)

    @property
    def ny(self) -> int:
        """Number of cells along y."""
        return len(self._heights)

    @property
    def cell_count(self) -> int:
        """Total number of rectangular cells."""
        return self.nx * self.ny

    @property
    def area_m2(self) -> float:
        """Total planar domain area [m^2], from the outer edges."""
        return (self.x_edges_m[-1] - self.x_edges_m[0]) * (
            self.y_edges_m[-1] - self.y_edges_m[0]
        )

    @property
    def volume_m3(self) -> float:
        """Total extruded domain volume [m^3]."""
        return self.area_m2 * self.thickness_m

    def index(self, ix: int, iy: int) -> int:
        """Return the flat index for zero-based integer (ix, iy)."""
        return _index(iy, self.ny, "iy") * self.nx + _index(ix, self.nx, "ix")

    def indices(self, index: int) -> tuple[int, int]:
        """Return zero-based (ix, iy) for a flat integer index."""
        iy, ix = divmod(_index(index, self.cell_count, "index"), self.nx)
        return ix, iy

    def center_m(self, index: int) -> tuple[float, float]:
        """Return a cell's (x, y) center coordinates [m]."""
        ix, iy = self.indices(index)
        return self._x_centers[ix], self._y_centers[iy]

    def cell_area_m2(self, index: int) -> float:
        """Return planar cell area (also each top/bottom face area) [m^2]."""
        ix, iy = self.indices(index)
        return self._widths[ix] * self._heights[iy]

    def cell_volume_m3(self, index: int) -> float:
        """Return cell area times the uniform thickness [m^3]."""
        return self.cell_area_m2(index) * self.thickness_m

    def face_areas_m2(self, index: int) -> tuple[float, float, float, float]:
        """Return positive lateral areas [m^2] in west/east/south/north order."""
        ix, iy = self.indices(index)
        vertical = self._heights[iy] * self.thickness_m
        horizontal = self._widths[ix] * self.thickness_m
        return vertical, vertical, horizontal, horizontal

    def neighbors(self, index: int) -> tuple[int | None, ...]:
        """Return west/east/south/north indices, with None at outer edges."""
        ix, iy = self.indices(index)
        index = self.index(ix, iy)
        return (
            index - 1 if ix > 0 else None,
            index + 1 if ix + 1 < self.nx else None,
            index - self.nx if iy > 0 else None,
            index + self.nx if iy + 1 < self.ny else None,
        )
