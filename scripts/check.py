"""Run the same complete quality gate locally and in public CI."""

import os
import subprocess
import sys
from pathlib import Path

COMMANDS = (
    ("ruff", "check", "."),
    ("ruff", "format", "--check", "."),
    (
        "pytest",
        "--cov=thermalpath",
        "--cov-branch",
        "--cov-report=term-missing",
        "--cov-fail-under=90",
    ),
    ("build",),
)


def main() -> int:
    """Stop at the first failure; never reinterpret a failed check as success."""
    environment = os.environ.copy()
    for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        environment[variable] = "1"
    environment["MPLBACKEND"] = "Agg"
    environment["PYTHONHASHSEED"] = "0"
    for arguments in COMMANDS:
        result = subprocess.run(
            [sys.executable, "-m", *arguments],
            cwd=Path(__file__).resolve().parents[1],
            env=environment,
            check=False,
        )
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
