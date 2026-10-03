"""Report a uniformly heated 1D plate and its cell-centre temperature error."""

import json
import os

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from thermalpath import RectangularGrid, RectangularHeater, solve_plate  # noqa: E402


def main() -> None:
    """Compare two unequal cells with an integrated quadratic profile."""
    grid = RectangularGrid((0, 1, 4), (0, 2), 0.5)
    result = solve_plate(
        grid, 2, west_k=300, east_k=300, heaters=[RectangularHeater(0, 4, 0, 2, 24)]
    )
    rows = []
    for cell, temperature in enumerate(result.temperatures_k):
        x = grid.center_m(cell)[0]
        width = grid.x_edges_m[cell + 1] - grid.x_edges_m[cell]
        continuum = 300 + 1.5 * x * (4 - x)
        rows.append(
            {
                "x_m": x,
                "computed_k": temperature,
                "continuum_center_k": continuum,
                "temperature_error_k": temperature - continuum,
                "predicted_offset_k": 3 * width**2 / 8,
                "outward_face_powers_w": result.face_powers_w[cell],
            }
        )
    print(
        json.dumps(
            {
                "case": "uniform heating with fixed ends and insulated other faces",
                "cells": rows,
                "heater_input_w": result.balance.heater_input_w,
                "imbalance_w": result.balance.imbalance_w,
            },
            indent=2,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
