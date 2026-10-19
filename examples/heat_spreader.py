"""Reproduce a frozen synthetic electronics heat-spreader study."""

import json
import os

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from thermalpath import RectangularGrid, RectangularHeater, solve_plate  # noqa: E402

LENGTH_M = 0.06
WIDTH_M = 0.04
CONDUCTIVITY_W_M_K = 150.0
DENSITY_KG_M3 = 2700.0
THICKNESSES_M = (0.0005, 0.001, 0.002)
GRID_SHAPES = ((6, 4), (12, 8), (24, 16))
SCENARIOS = (("nominal", 10.0, 300.0), ("stress", 12.0, 310.0))
LIMIT_K = 325.0
DECISION_BAND_K = 0.25
BALANCE_TOLERANCE_W = 1e-8
GRID_CHANGE_TOLERANCE_K = 0.5


def study() -> dict:
    """Return every input, cell prediction, failure and comparison in fixed order.

    Notes
    -----
    All inputs are assigned design assumptions. The peak is the largest cell
    temperature, not a certified continuum maximum or a device junction value.
    The stress case is a second specified load, not a probability distribution.
    """
    candidates = []
    for thickness in THICKNESSES_M:
        scenarios = []
        for name, power, sink in SCENARIOS:
            grids = []
            for nx, ny in GRID_SHAPES:
                grid = RectangularGrid(
                    tuple(LENGTH_M * i / nx for i in range(nx + 1)),
                    tuple(WIDTH_M * j / ny for j in range(ny + 1)),
                    thickness,
                )
                row = dict(shape=[nx, ny], status="failed", error=None)
                try:
                    result = solve_plate(
                        grid,
                        CONDUCTIVITY_W_M_K,
                        west_k=sink,
                        east_k=sink,
                        heaters=[RectangularHeater(0.02, 0.04, 0.01, 0.03, power)],
                    )
                except ValueError as exc:
                    row["error"] = str(exc)
                else:
                    balance = result.balance
                    diagnostics = dict(
                        heater_input_w=balance.heater_input_w,
                        edge_outflow_w=balance.edge_outflow_w,
                        broad_face_outflow_w=balance.broad_face_outflow_w,
                        imbalance_w=balance.imbalance_w,
                        max_cell_residual_w=max(map(abs, balance.cell_residual_w)),
                        max_linear_residual_w=max(map(abs, balance.linear_residual_w)),
                    )
                    checks = (
                        abs(balance.heater_input_w - power),
                        abs(balance.imbalance_w),
                        diagnostics["max_cell_residual_w"],
                        diagnostics["max_linear_residual_w"],
                    )
                    row.update(
                        status="ok",
                        x_edges_m=grid.x_edges_m,
                        y_edges_m=grid.y_edges_m,
                        temperatures_k=result.temperatures_k,
                        peak_cell_k=max(result.temperatures_k),
                        diagnostics=diagnostics,
                        balance_checks_passed=all(
                            value <= BALANCE_TOLERANCE_W for value in checks
                        ),
                    )
                grids.append(row)
            complete = all(row["status"] == "ok" for row in grids)
            change = (
                abs(grids[-1]["peak_cell_k"] - grids[-2]["peak_cell_k"])
                if complete
                else None
            )
            credible = (
                complete
                and all(row["balance_checks_passed"] for row in grids)
                and change <= GRID_CHANGE_TOLERANCE_K
            )
            margin = LIMIT_K - grids[-1]["peak_cell_k"] if complete else None
            classification = "unknown"
            if credible:
                classification = "borderline"
                if margin > DECISION_BAND_K:
                    classification = "meets"
                elif margin < -DECISION_BAND_K:
                    classification = "exceeds"
            scenarios.append(
                dict(
                    name=name,
                    power_w=power,
                    sink_k=sink,
                    grids=grids,
                    last_peak_change_k=change,
                    numerical_checks_passed=credible,
                    finest_margin_k=margin,
                    classification=classification,
                )
            )
        candidates.append(
            dict(
                thickness_m=thickness,
                mass_kg=DENSITY_KG_M3 * LENGTH_M * WIDTH_M * thickness,
                scenarios=scenarios,
            )
        )
    rows = [g for c in candidates for s in c["scenarios"] for g in s["grids"]]
    return dict(
        study="synthetic electronics heat spreader",
        length_m=LENGTH_M,
        width_m=WIDTH_M,
        conductivity_w_m_k=CONDUCTIVITY_W_M_K,
        density_kg_m3=DENSITY_KG_M3,
        heater_bounds_m=[0.02, 0.04, 0.01, 0.03],
        boundaries="west/east fixed at sink; all other faces insulated",
        temperature_limit_k=LIMIT_K,
        decision_band_k=DECISION_BAND_K,
        balance_tolerance_w=BALANCE_TOLERANCE_W,
        grid_change_tolerance_k=GRID_CHANGE_TOLERANCE_K,
        edge_order=["west", "east", "south", "north"],
        cell_order="x-first",
        attempted_count=len(rows),
        completed_count=sum(g["status"] == "ok" for g in rows),
        failed_count=sum(g["status"] == "failed" for g in rows),
        candidates=candidates,
    )


def main() -> None:
    """Print the fixed study as JSON without writing result files."""
    print(json.dumps(study(), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
