"""Physical power accounting kept separate from the assembled plate equations."""

import math
from dataclasses import dataclass

from thermalpath.grid import RectangularGrid


@dataclass(frozen=True)
class PlateBalance:
    """Store immutable plate diagnostics, with every power in watts.

    Attributes
    ----------
    cell_residual_w : tuple of float
        Heater input minus all lateral and broad-face outward powers, x-first.
        Positive means excess heat input. Inspect every cell, not just the sum.
    linear_residual_w : tuple of float
        b - A*T from the actual rounded system, in the same cell order.
        It may be zero even when the physical cell residual is nonzero.
    heater_input_w : float
        Sum of mapped heater powers.
    edge_outflow_w : tuple of float
        Exterior-only signed outward powers in west/east/south/north order.
    broad_face_outflow_w : float
        Signed outward power through both broad faces combined.
    imbalance_w : float
        Direct signed sum of mapped heaters minus exterior and broad-face
        powers. Evaluated from individual terms, not rounded subtotals.

    Notes
    -----
    No automatic tolerance or accuracy certificate is supplied. Arithmetic
    residuals do not establish spatial convergence or physical model validity.
    """

    cell_residual_w: tuple[float, ...]
    linear_residual_w: tuple[float, ...]
    heater_input_w: float
    edge_outflow_w: tuple[float, ...]
    broad_face_outflow_w: float
    imbalance_w: float


def _plate_balance(
    grid: RectangularGrid,
    heaters: tuple[float, ...],
    faces: list[list[float]],
    broad: list[float],
    linear: tuple[float, ...],
) -> PlateBalance:
    """Account for validated solver powers without cancelling local errors."""
    exterior: list[list[float]] = [[] for _ in range(4)]
    for cell in range(grid.cell_count):
        for side, neighbor in enumerate(grid.neighbors(cell)):
            if neighbor is None:
                exterior[side].append(faces[cell][side])
    try:
        return PlateBalance(
            tuple(
                math.fsum([heaters[i], -broad[i], *(-q for q in faces[i])])
                for i in range(grid.cell_count)
            ),
            linear,
            math.fsum(heaters),
            tuple(math.fsum(values) for values in exterior),
            math.fsum(broad),
            math.fsum(
                [
                    *heaters,
                    *(-q for side in exterior for q in side),
                    *(-q for q in broad),
                ]
            ),
        )
    except OverflowError as exc:
        raise ValueError("plate balance sum is outside float range") from exc
