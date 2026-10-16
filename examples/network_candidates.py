"""Compare synthetic conductance alternatives under one common load case."""

import json
import os
from dataclasses import asdict

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from thermalpath import Link, Node  # noqa: E402
from thermalpath.design import (  # noqa: E402
    NetworkCandidate,
    TemperatureRequirement,
    compare_network_candidates,
)


def main() -> None:
    """Print all alternatives, including a tie, a limit case and a failed solve."""
    nodes = (Node("body", power_w=10), Node("sink", fixed_temperature_k=300))
    candidates = tuple(
        NetworkCandidate(name, (Link("path", "body", "sink", conductance),))
        for name, conductance in (
            ("weak_path", 1),
            ("at_limit", 2),
            ("strong_path", 4),
            ("equal_alternative", 4),
        )
    ) + (NetworkCandidate("disconnected", ()),)
    result = compare_network_candidates(
        nodes,
        candidates,
        (TemperatureRequirement("body", 305),),
        comparison_tolerance_k=1e-9,
    )
    print(json.dumps(asdict(result), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
