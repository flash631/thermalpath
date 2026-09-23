"""Print scalar heating errors and discrete energy balances on four time grids."""

import os

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

import json  # noqa: E402
import math  # noqa: E402

from thermalpath import (  # noqa: E402
    Link,
    Network,
    Node,
    solve_transient,
    transient_energy_balance,
)


def main() -> None:
    """Use a fixed synthetic case and grid family; write unit-labelled JSON."""
    network = Network(
        (Node("body", power_w=5), Node("bath", fixed_temperature_k=300)),
        (Link("loss", "body", "bath", 0.5),),
    )
    exact = 310 - 10 * math.exp(-1)
    records = []
    previous_error = None
    for count in (5, 10, 20, 40):
        dt = 20 / count
        result = solve_transient(
            network, {"body": 10}, {"body": 300}, [i * dt for i in range(count + 1)]
        )
        reports = [
            transient_energy_balance(network, {"body": 10}, old, new, dt)
            for old, new in zip(
                result.temperatures_k, result.temperatures_k[1:], strict=False
            )
        ]
        error = abs(result.temperatures_k[-1]["body"] - exact)
        records.append(
            dict(
                step_s=dt,
                final_temperature_k=result.temperatures_k[-1]["body"],
                absolute_error_k=error,
                observed_order=None
                if previous_error is None
                else math.log2(previous_error / error),
                storage_j=math.fsum(r.total_storage_j for r in reports),
                source_j=math.fsum(r.total_source_j for r in reports),
                boundary_j=math.fsum(r.total_boundary_j for r in reports),
                max_step_imbalance_j=max(abs(r.imbalance_j) for r in reports),
            )
        )
        previous_error = error
    print(
        json.dumps(
            dict(final_time_s=20, exact_temperature_k=exact, grids=records),
            indent=2,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
