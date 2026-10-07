"""Export plots and their numerical inputs from existing synthetic benchmarks."""

import os

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
from pathlib import Path  # noqa: E402

import matplotlib  # noqa: E402

from thermalpath import (  # noqa: E402
    Link,
    Network,
    Node,
    RectangularGrid,
    rc_step,
    solve_transient,
)
from thermalpath.plotting import (  # noqa: E402
    plot_errors,
    plot_temperatures,
    plot_transient,
    save_png,
)

if __package__:
    from .plate_refinement import refinement_report
else:
    from plate_refinement import refinement_report


def export_plots(directory: Path) -> dict:
    """Create a new output directory; preserve any existing directory unchanged."""
    directory.mkdir(parents=True, exist_ok=False)
    study = refinement_report()
    finest = study["grids"][-1]
    nx, ny = finest["grid_shape"]
    grid = RectangularGrid(
        tuple(study["length_x_m"] * i / nx for i in range(nx + 1)),
        tuple(study["length_y_m"] * j / ny for j in range(ny + 1)),
        study["thickness_m"],
    )
    fields = {
        "Finite volume, 16 x 12": [c["computed_k"] for c in finest["cells"]],
        "Continuum at cell centres": [c["continuum_center_k"] for c in finest["cells"]],
    }
    network = Network(
        (Node("body", power_w=5), Node("bath", fixed_temperature_k=300)),
        (Link("loss", "body", "bath", 0.5),),
    )
    times = list(range(21))
    transient = solve_transient(network, {"body": 10}, {"body": 300}, times)
    histories = {
        "Backward Euler, step 1 s": [row["body"] for row in transient.temperatures_k],
        "Analytical RC": [
            rc_step(
                time_s=t,
                initial_temperature_k=300,
                boundary_temperature_k=300,
                resistance_k_w=2,
                heat_capacity_j_k=10,
                power_w=5,
            ).temperature_k
            for t in times
        ],
    }
    spacings = [row["dx_m"] for row in study["grids"]]
    errors = {
        label: [row["errors"][key] for row in study["grids"]]
        for label, key in (
            ("Mean absolute", "l1_k"),
            ("RMS", "l2_k"),
            ("Maximum", "linf_k"),
        )
    }
    figures = {
        "temperature.png": plot_temperatures(grid, fields),
        "transient.png": plot_transient(times, histories),
        "errors.png": plot_errors(spacings, errors),
    }
    inputs = {
        "description": "Synthetic manufactured plate and constant-load RC benchmarks",
        "temperature": {
            "x_edges_m": grid.x_edges_m,
            "y_edges_m": grid.y_edges_m,
            "thickness_m": grid.thickness_m,
            "fields_k": fields,
        },
        "transient": {"times_s": times, "temperatures_k": histories},
        "errors": {"spacings_m": spacings, "errors_k": errors},
    }
    (directory / "inputs.json").write_text(
        json.dumps(inputs, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    for name, figure in figures.items():
        save_png(figure, directory / name)
        figure.clear()
    manifest = {
        "matplotlib_version": matplotlib.__version__,
        "sha256": {
            name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
            for name in ("inputs.json", *figures)
        },
    }
    (directory / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    """Export actual computed data; require an explicit new destination."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_directory", type=Path)
    arguments = parser.parse_args()
    print(json.dumps(export_plots(arguments.output_directory), indent=2))


if __name__ == "__main__":
    main()
