"""Report centre-temperature errors on the three frozen manufactured grids."""

import json
import os
from math import fsum, log2, sqrt

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from thermalpath import RectangularGrid, RectangularHeater, solve_plate  # noqa: E402

if __package__:
    from . import manufactured_plate as benchmark
else:
    import manufactured_plate as benchmark


def refinement_report() -> dict:
    """Return the fixed synthetic study, with area-normalized error norms in K.

    Notes
    -----
    The report compares cell-centre values, not cell averages. Each finer grid
    halves both spacings and reintegrates the same continuum forcing. Orders
    are measured separately for the two grid pairs; the first has no order.
    """
    records = []
    previous = None
    for nx, ny in ((4, 3), (8, 6), (16, 12)):
        grid = RectangularGrid(
            tuple(benchmark.LENGTH_X_M * i / nx for i in range(nx + 1)),
            tuple(benchmark.LENGTH_Y_M * j / ny for j in range(ny + 1)),
            benchmark.THICKNESS_M,
        )
        heaters = [
            RectangularHeater(x0, x1, y0, y1, benchmark.cell_power_w(x0, x1, y0, y1))
            for y0, y1 in zip(grid.y_edges_m[:-1], grid.y_edges_m[1:], strict=True)
            for x0, x1 in zip(grid.x_edges_m[:-1], grid.x_edges_m[1:], strict=True)
        ]
        result = solve_plate(
            grid,
            benchmark.CONDUCTIVITY_W_MK,
            west_k=benchmark.BOUNDARY_K,
            east_k=benchmark.BOUNDARY_K,
            south_k=benchmark.BOUNDARY_K,
            north_k=benchmark.BOUNDARY_K,
            heaters=heaters,
        )
        cells = []
        for cell, computed in enumerate(result.temperatures_k):
            x, y = grid.center_m(cell)
            reference = benchmark.temperature_k(x, y)
            cells.append(
                dict(
                    x_m=x,
                    y_m=y,
                    computed_k=computed,
                    continuum_center_k=reference,
                    error_k=computed - reference,
                    cell_input_w=heaters[cell].power_w,
                )
            )
        # All cells have equal area in each frozen grid, so weights are 1/N.
        errors = [row["error_k"] for row in cells]
        norms = dict(
            l1_k=fsum(abs(e) for e in errors) / len(errors),
            l2_k=sqrt(fsum(e * e for e in errors) / len(errors)),
            linf_k=max(abs(e) for e in errors),
        )
        records.append(
            dict(
                grid_shape=[nx, ny],
                dx_m=benchmark.LENGTH_X_M / nx,
                dy_m=benchmark.LENGTH_Y_M / ny,
                cells=cells,
                errors=norms,
                observed_order=None
                if previous is None
                else {
                    name: log2(previous[name] / value) for name, value in norms.items()
                },
                heater_input_w=result.balance.heater_input_w,
                edge_outflow_w=result.balance.edge_outflow_w,
                imbalance_w=result.balance.imbalance_w,
                relative_imbalance=abs(result.balance.imbalance_w)
                / result.balance.heater_input_w,
                max_cell_residual_w=max(map(abs, result.balance.cell_residual_w)),
                max_linear_residual_w=max(map(abs, result.balance.linear_residual_w)),
            )
        )
        previous = norms
    return dict(
        case="frozen manufactured polynomial plate",
        length_x_m=benchmark.LENGTH_X_M,
        length_y_m=benchmark.LENGTH_Y_M,
        thickness_m=benchmark.THICKNESS_M,
        conductivity_w_mk=benchmark.CONDUCTIVITY_W_MK,
        boundary_k=benchmark.BOUNDARY_K,
        peak_continuum_rise_k=benchmark.PEAK_RISE_K,
        edge_order=["west", "east", "south", "north"],
        continuum_edge_outflow_w=[32 / 45, 32 / 45, 8 / 5, 8 / 5],
        grids=records,
    )


def main() -> None:
    """Print reproducible inputs, every cell, error norms and power diagnostics."""
    print(json.dumps(refinement_report(), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
