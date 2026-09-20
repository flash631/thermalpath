"""Run a versioned steady network case and print JSON results."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from thermalpath.diagnostics import heat_balance
from thermalpath.io import loads_case
from thermalpath.networks import solve_steady


def main(argv: list[str] | None = None) -> int:
    """Run the CLI, returning 0 on success and 1 for case or execution errors.

    Parameters
    ----------
    argv : list of str or None, optional
        Arguments excluding the executable name. None reads sys.argv.

    Returns
    -------
    int
        Zero after a successful solve and JSON write, one for a file, case,
        solver, or output error. Argument parsing exits with code two for
        invalid usage, or zero for help.

    Notes
    -----
    Result fields carry SI units in their names. Positive link power runs from
    node_a to node_b. A successful exit does not certify numerical accuracy;
    inspect node residuals and the solver's documented conditioning limits.
    """
    parser = argparse.ArgumentParser(prog="thermalpath")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run-network", help="solve a version-1 JSON case")
    run.add_argument("case", type=Path, help="UTF-8 JSON case file")
    arguments = parser.parse_args(argv)
    try:
        network = loads_case(arguments.case.read_text(encoding="utf-8"))
        result = solve_steady(network)
        report = {
            "schema_version": 1,
            "kind": "steady_network_result",
            **asdict(result),
            "heat_balance": asdict(heat_balance(network, result.link_powers_w)),
        }
        print(json.dumps(report, indent=2, allow_nan=False))
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"thermalpath: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
