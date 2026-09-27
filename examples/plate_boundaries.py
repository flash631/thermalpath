"""Print a synthetic unequal-cell plate with heating flux and edge convection."""

import json
import math
import os

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from thermalpath import Convection, RectangularGrid, solve_plate  # noqa: E402


def main() -> None:
    """Compare a boundary-heated strip to its linear continuum solution."""
    grid = RectangularGrid((0, 1, 3), (0, 1, 4), 0.25)
    result = solve_plate(
        grid,
        2,
        edge_flux_w_m2={"west": -10},
        edge_convection={"east": Convection(5, 300)},
    )
    print(
        json.dumps(
            {
                "temperatures_k": result.temperatures_k,
                "west_outward_power_w": math.fsum(
                    result.face_powers_w[grid.index(0, iy)][0] for iy in range(grid.ny)
                ),
                "east_outward_power_w": math.fsum(
                    result.face_powers_w[grid.index(1, iy)][1] for iy in range(grid.ny)
                ),
                "east_surface_temperature_k": result.temperatures_k[1]
                - result.face_powers_w[1][1] / (2 * 0.25),
                "broad_face_powers_w": result.broad_face_powers_w,
            },
            indent=2,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
