"""Sample synthetic power and conductance ranges with complete replay inputs."""

import json
import os
from dataclasses import asdict

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from thermalpath import Link, Network, Node  # noqa: E402
from thermalpath.uncertainty import UniformInput, monte_carlo_network  # noqa: E402


def main() -> None:
    """Print all samples and explicitly qualified temperature percentiles."""
    network = Network(
        (Node("body", power_w=10), Node("sink", fixed_temperature_k=300)),
        (Link("path", "body", "sink", 2),),
    )
    study = monte_carlo_network(
        network,
        (
            UniformInput("power_w", "body", 8, 12),
            UniformInput("conductance_w_k", "path", 1, 3),
        ),
        count=64,
        seed=2026,
    )
    adverse = monte_carlo_network(
        network,
        (UniformInput("power_w", "body", -800, 0),),
        count=16,
        seed=2026,
    )
    print(
        json.dumps(
            {
                "study": asdict(study),
                "adverse_study": asdict(adverse),
                "distribution": "independent_uniform",
                "percentile_method": "linear",
                "interpretation": "conditional model outputs, not safety bounds",
                "physical_validation": False,
            },
            indent=2,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
