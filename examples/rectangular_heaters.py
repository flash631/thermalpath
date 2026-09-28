"""Print a synthetic heater mapping and a two-cell heated plate reference."""

import json
import math
import os

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from thermalpath import (  # noqa: E402
    RectangularGrid,
    RectangularHeater,
    map_heaters,
    solve_plate,
)


def main() -> None:
    """Report integrated watts separately from the computed temperatures."""
    heater = RectangularHeater(0.5, 3.5, 0.5, 2.5, 12)
    grids = (
        RectangularGrid((0, 2, 4), (0, 1.5, 3), 0.5),
        RectangularGrid((0, 1, 3, 4), (0, 1, 2, 3), 0.5),
        RectangularGrid((0, 0.75, 1.5, 2.5, 3.25, 4), (0, 0.75, 1.5, 2.25, 3), 0.5),
    )
    mappings = []
    for grid in grids:
        powers = map_heaters(grid, [heater])
        mappings.append(
            dict(
                cell_count=grid.cell_count,
                cell_powers_w=powers,
                total_power_w=math.fsum(powers),
            )
        )
    grid = RectangularGrid((0, 1, 3), (0, 2), 0.5)
    heaters = [RectangularHeater(0.5, 2, 0.5, 1.5, 12)]
    result = solve_plate(grid, 3, west_k=300, east_k=300, heaters=heaters)
    print(
        json.dumps(
            dict(
                mappings=mappings,
                heated_plate=dict(
                    cell_powers_w=map_heaters(grid, heaters),
                    temperatures_k=result.temperatures_k,
                    total_outward_power_w=math.fsum(
                        power for faces in result.face_powers_w for power in faces
                    ),
                ),
            ),
            indent=2,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
