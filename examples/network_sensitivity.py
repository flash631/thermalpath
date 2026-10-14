"""Report local conductance sensitivity, refinement and a rejected stencil."""

import json
import os
from dataclasses import asdict

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from thermalpath import Link, Network, Node  # noqa: E402
from thermalpath.sensitivity import network_sensitivity  # noqa: E402


def main() -> None:
    """Print all inputs, diagnostics and estimates as a reproducible JSON report."""
    base = Network(
        (
            Node("a", power_w=12),
            Node("b", power_w=4),
            Node("sink", fixed_temperature_k=300),
        ),
        (Link("ab", "a", "b", 2), Link("bs", "b", "sink", 4)),
    )
    study = network_sensitivity(base, "conductance_w_k", "ab", (0.5, 0.25, 0.125, 2))
    # Independently: Tb=300+(12+4)/4=304; Ta=304+12/g, dTa/dg=-12/g**2.
    reference = -3.0
    errors = [
        abs(row.dimensional["a"] - reference) if row.status == "ok" else None
        for row in study.estimates
    ]
    print(
        json.dumps(
            {
                "study": asdict(study),
                "reference_derivative_k2_w": reference,
                "absolute_errors_k2_w": errors,
                "physical_validation": False,
            },
            indent=2,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
