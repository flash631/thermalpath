"""Export the fixed study to stdout; source revision is explicitly supplied."""

import argparse
import os

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from heat_spreader import study  # noqa: E402

from thermalpath.reporting import (  # noqa: E402
    EngineeringReport,
    Evidence,
    NumericalCheck,
)


def report(source_revision: str = "unknown") -> EngineeringReport:
    """Snapshot the unchanged synthetic study, retaining every attempted grid."""
    data = study()
    candidates = data.pop("candidates")
    checks = []
    for candidate in candidates:
        for scenario in candidate["scenarios"]:
            name = f"{candidate['thickness_m']} m {scenario['name']}"
            for grid in scenario["grids"]:
                prefix = f"{name} {grid['shape']}"
                diagnostics = grid.get("diagnostics")
                for key in (
                    "imbalance_w",
                    "max_cell_residual_w",
                    "max_linear_residual_w",
                ):
                    checks.append(
                        NumericalCheck(
                            f"{prefix} {key}",
                            "W",
                            diagnostics[key] if diagnostics else None,
                            data["balance_tolerance_w"],
                            "Supplied discrete diagnostic; "
                            "unavailable after failed solve.",
                        )
                    )
                checks.append(
                    NumericalCheck(
                        f"{prefix} heater integration",
                        "W",
                        diagnostics["heater_input_w"] - scenario["power_w"]
                        if diagnostics
                        else None,
                        data["balance_tolerance_w"],
                        "Integrated heater input minus assigned power.",
                    )
                )
            checks.append(
                NumericalCheck(
                    f"{name} last peak change",
                    "K",
                    scenario["last_peak_change_k"],
                    data["grid_change_tolerance_k"],
                    "Last two grids only; not a continuum error bound.",
                )
            )
    counts = {
        key: data.pop(key)
        for key in ("attempted_count", "completed_count", "failed_count")
    }
    return EngineeringReport(
        title="Synthetic heat-spreader study",
        source_revision=source_revision,
        inputs=data,
        units={
            "lengths, thickness, heater bounds and coordinates": "m",
            "conductivity": "W/(m K)",
            "density": "kg/m^3",
            "mass": "kg",
            "temperature, margin, decision band and grid change": "K",
            "power, heat flow and residual": "W",
            "counts, grid shapes and classification": "dimensionless",
        },
        results=dict(**counts, candidates=candidates),
        checks=tuple(checks),
        provenance=(
            Evidence(
                "synthetic",
                "ThermalPath heat-spreader example",
                "examples/heat_spreader.py; docs/case_study.md",
                "MIT; see LICENSE",
                "Assigned inputs; no measurements or device ratings.",
            ),
            Evidence(
                "numerical",
                "ThermalPath steady plate solver",
                "src/thermalpath/plate.py; src/thermalpath/plate_diagnostics.py",
                "MIT; see LICENSE",
                "Cell-centred finite-volume predictions.",
            ),
        ),
        limitations=(
            "Fixed edge temperatures idealize cooling; "
            "contact and package drops are absent.",
            "Cell peaks and grid changes do not bound the continuum maximum.",
            "The stress case is assigned and has no probability interpretation.",
            "Only further evaluation of the 2 mm candidate is supported "
            "when all screens pass.",
            "Source revision is caller supplied; "
            "unknown means it has not been identified.",
        ),
    )


def main() -> None:
    """Print JSON or Markdown without reading Git or writing output files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--source-revision", default="unknown")
    args = parser.parse_args()
    result = report(args.source_revision)
    print(result.to_json() if args.format == "json" else result.to_markdown(), end="")


if __name__ == "__main__":
    main()
