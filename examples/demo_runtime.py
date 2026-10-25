"""Check and time five fresh processes running the documented series demo."""

import json
import math
import os
import statistics
import subprocess
import sys
from pathlib import Path
from time import perf_counter


def check_result(data: dict) -> None:
    """Compare demo output to independent decimal-reference values and units."""
    if data["case"] != "synthetic_series_stack":
        raise ValueError("Unexpected demo case")
    for name, expected, unit in (
        ("interface_resistance", 0.05, "K/W"),
        ("temperature", 363.9, "K"),
        ("temperature_celsius", 90.75, "degC"),
        ("power", 15.0, "W"),
    ):
        result = data[name]
        if result["unit"] != unit or not math.isclose(
            result["value"], expected, rel_tol=0.0, abs_tol=1e-12
        ):
            raise ValueError(f"Demo reference failed: {name}")


def main() -> None:
    """Print observed process times only after every output passes its checks."""
    environment = os.environ.copy()
    for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        environment[variable] = "1"
    samples = []
    demo = Path(__file__).with_name("series_stack.py")
    for _ in range(5):
        start = perf_counter()
        completed = subprocess.run(
            [sys.executable, "-I", str(demo)],
            env=environment,
            capture_output=True,
            text=True,
            check=True,
        )
        samples.append(perf_counter() - start)
        check_result(json.loads(completed.stdout))
    print(
        json.dumps(
            {
                "case": "synthetic_series_stack",
                "reference_checks": "passed",
                "timing_scope": "process_start_import_calculation_json_exit",
                "unit": "s",
                "samples": samples,
                "median": statistics.median(samples),
                "minimum": min(samples),
                "maximum": max(samples),
                "numerical_threads": 1,
            },
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
