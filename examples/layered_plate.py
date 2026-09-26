"""Print a synthetic two-material plate and its reconstructed interface."""

import json
import os

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from thermalpath import RectangularGrid, solve_plate  # noqa: E402


def main() -> None:
    """Solve unequal cells spanning two perfectly bonded materials."""
    grid = RectangularGrid((0, 0.5, 2, 3, 5), (0, 1, 3), 0.25)
    result = solve_plate(grid, (2, 2, 6, 6) * 2, west_k=360, east_k=300)
    # First row: interface at x=2 m, area=0.25 m2, centers at 1.25 and 2.5 m.
    q = result.face_powers_w[1][1]
    print(
        json.dumps(
            {
                "temperatures_k": result.temperatures_k,
                "interface_from_left_k": result.temperatures_k[1]
                - q * 0.75 / (2 * 0.25),
                "interface_from_right_k": result.temperatures_k[2]
                + q * 0.5 / (6 * 0.25),
                "eastward_heat_flux_w_m2": q / 0.25,
                "east_outward_power_w": sum(
                    result.face_powers_w[grid.index(3, iy)][1] for iy in range(grid.ny)
                ),
            },
            indent=2,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
