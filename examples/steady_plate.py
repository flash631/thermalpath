"""Print a synthetic source-free plate with a linear temperature profile."""

import json
import os

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from thermalpath import RectangularGrid, solve_plate  # noqa: E402


def main() -> None:
    """Solve a 60 mm by 40 mm plate with a 20 K edge difference."""
    grid = RectangularGrid((0, 0.01, 0.03, 0.06), (0, 0.01, 0.04), 0.002)
    result = solve_plate(grid, 150, west_k=300, east_k=320)
    print(
        json.dumps(
            {
                "temperatures_k": result.temperatures_k,
                "face_order": ["west", "east", "south", "north"],
                "outward_face_powers_w": result.face_powers_w,
                "west_outward_power_w": sum(
                    result.face_powers_w[grid.index(0, iy)][0] for iy in range(grid.ny)
                ),
                "east_outward_power_w": sum(
                    result.face_powers_w[grid.index(grid.nx - 1, iy)][1]
                    for iy in range(grid.ny)
                ),
            },
            indent=2,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
