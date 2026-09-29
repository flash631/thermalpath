"""Print synthetic mixed-boundary and unresolved small-heater diagnostics."""

import json
import os
from dataclasses import asdict

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from thermalpath import (  # noqa: E402
    Convection,
    RectangularGrid,
    RectangularHeater,
    solve_plate,
)


def main() -> None:
    """Report physical balances and matrix residuals as separate quantities."""
    mixed = solve_plate(
        RectangularGrid((0, 1), (0, 2), 0.5),
        3,
        heaters=[RectangularHeater(0, 1, 0, 2, 10)],
        edge_flux_w_m2={"west": 2},
        face_convection=Convection(2, 300),
    )
    tiny = solve_plate(
        RectangularGrid((0, 1), (0, 1), 1),
        1,
        west_k=300,
        heaters=[RectangularHeater(0, 1, 0, 1, 1e-20)],
    )
    print(
        json.dumps(
            {"mixed": asdict(mixed), "tiny_heater": asdict(tiny)},
            indent=2,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
