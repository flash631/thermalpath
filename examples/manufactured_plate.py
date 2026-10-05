"""Compare one fixed grid with a smooth manufactured two-dimensional field."""

import json
import os
from math import fsum

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from thermalpath import RectangularGrid, RectangularHeater, solve_plate  # noqa: E402

LENGTH_X_M = 0.06
LENGTH_Y_M = 0.04
THICKNESS_M = 0.002
CONDUCTIVITY_W_MK = 10.0
BOUNDARY_K = 300.0
PEAK_RISE_K = 20.0


def temperature_k(x_m: float, y_m: float) -> float:
    """Evaluate the prescribed continuum field inside the benchmark rectangle."""
    x, y = x_m / LENGTH_X_M, y_m / LENGTH_Y_M
    return BOUNDARY_K + 16 * PEAK_RISE_K * x * (1 - x) * y * (1 - y)


def source_w_m2(x_m: float, y_m: float) -> float:
    """Evaluate -k*t*Laplacian(T), positive for heat input per projected area."""
    x, y = x_m / LENGTH_X_M, y_m / LENGTH_Y_M
    return (
        32
        * CONDUCTIVITY_W_MK
        * THICKNESS_M
        * PEAK_RISE_K
        * (y * (1 - y) / LENGTH_X_M**2 + x * (1 - x) / LENGTH_Y_M**2)
    )


def cell_power_w(x0: float, x1: float, y0: float, y1: float) -> float:
    """Integrate the fixed polynomial source over one cell, in watts.

    Parameters
    ----------
    x0, x1, y0, y1 : float
        Ordered cell bounds in metres within the benchmark rectangle.

    Notes
    -----
    The mean of z*(1-z) on an interval is m*(1-m) - width**2/12.
    These example helpers assume the declared benchmark domain; they are not
    general source or geometry APIs.
    """
    x, y = (x0 + x1) / (2 * LENGTH_X_M), (y0 + y1) / (2 * LENGTH_Y_M)
    dx, dy = (x1 - x0) / LENGTH_X_M, (y1 - y0) / LENGTH_Y_M
    mean_x = x * (1 - x) - dx**2 / 12
    mean_y = y * (1 - y) - dy**2 / 12
    return (
        32
        * CONDUCTIVITY_W_MK
        * THICKNESS_M
        * PEAK_RISE_K
        * (mean_y / LENGTH_X_M**2 + mean_x / LENGTH_Y_M**2)
        * (x1 - x0)
        * (y1 - y0)
    )


def main() -> None:
    """Print the frozen 4 by 3 comparison without a refinement/order claim."""
    grid = RectangularGrid(
        tuple(LENGTH_X_M * i / 4 for i in range(5)),
        tuple(LENGTH_Y_M * j / 3 for j in range(4)),
        THICKNESS_M,
    )
    heaters = [
        RectangularHeater(x0, x1, y0, y1, cell_power_w(x0, x1, y0, y1))
        for y0, y1 in zip(grid.y_edges_m[:-1], grid.y_edges_m[1:], strict=True)
        for x0, x1 in zip(grid.x_edges_m[:-1], grid.x_edges_m[1:], strict=True)
    ]
    result = solve_plate(
        grid,
        CONDUCTIVITY_W_MK,
        west_k=BOUNDARY_K,
        east_k=BOUNDARY_K,
        south_k=BOUNDARY_K,
        north_k=BOUNDARY_K,
        heaters=heaters,
    )
    rows = []
    for cell, computed in enumerate(result.temperatures_k):
        x, y = grid.center_m(cell)
        reference = temperature_k(x, y)
        rows.append(
            {
                "x_m": x,
                "y_m": y,
                "computed_k": computed,
                "continuum_center_k": reference,
                "temperature_error_k": computed - reference,
                "cell_input_w": heaters[cell].power_w,
            }
        )
    edge_factor = 8 * CONDUCTIVITY_W_MK * THICKNESS_M * PEAK_RISE_K / 3
    continuum_edges = [
        edge_factor * LENGTH_Y_M / LENGTH_X_M,
        edge_factor * LENGTH_Y_M / LENGTH_X_M,
        edge_factor * LENGTH_X_M / LENGTH_Y_M,
        edge_factor * LENGTH_X_M / LENGTH_Y_M,
    ]
    print(
        json.dumps(
            {
                "case": "manufactured polynomial plate, constant fixed edges",
                "grid_shape": [grid.nx, grid.ny],
                "cells": rows,
                "heater_input_w": result.balance.heater_input_w,
                "edge_order": ["west", "east", "south", "north"],
                "computed_edge_outflow_w": result.balance.edge_outflow_w,
                "continuum_edge_outflow_w": continuum_edges,
                "continuum_total_outflow_w": fsum(continuum_edges),
                "imbalance_w": result.balance.imbalance_w,
                "max_abs_temperature_error_k": max(
                    abs(row["temperature_error_k"]) for row in rows
                ),
            },
            indent=2,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
