"""Export a bounded load/conductance sweep, including rejected candidates."""

import argparse
import csv
import io
import json
import os
from pathlib import Path

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from thermalpath import Link, Network, Node  # noqa: E402
from thermalpath.studies import (  # noqa: E402
    SweepAxis,
    replay_network_sweep,
    sweep_network,
)


def main() -> None:
    """Write a new CSV file and report measured case counts and closure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    base = Network(
        (Node("body"), Node("reservoir", fixed_temperature_k=300)),
        (Link("path", "body", "reservoir", 1),),
    )
    text = sweep_network(
        base,
        (
            SweepAxis("power_w", "body", (0, 10, 20)),
            SweepAxis("conductance_w_k", "path", (1, 2, 0)),
        ),
    )
    if replay_network_sweep(text) != text:
        raise RuntimeError("CSV replay differs in the current environment")
    with args.output.open("x", encoding="utf-8", newline="") as output:
        output.write(text)
    rows = list(csv.DictReader(io.StringIO(text)))
    successful = [row for row in rows if row["status"] == "ok"]
    print(
        json.dumps(
            {
                "cases": len(rows),
                "successful": len(successful),
                "failed": len(rows) - len(successful),
                "max_abs_imbalance_w": max(
                    abs(float(row["imbalance_w"])) for row in successful
                ),
                "replay_matches": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
