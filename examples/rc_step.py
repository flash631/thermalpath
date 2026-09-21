"""Print a synthetic one-node step with explicit SI units."""

import json
import os
from dataclasses import asdict

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from thermalpath import rc_step  # noqa: E402

result = rc_step(20.0, 300.0, 300.0, 2.0, 10.0, 5.0)
print(json.dumps(asdict(result), indent=2, allow_nan=False))
