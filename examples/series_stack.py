"""Print a synthetic single-path calculation as JSON, without a display."""

import json
import os

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from thermalpath import conduction_resistance, series_temperature  # noqa: E402


def main() -> None:
    """Compute the documented example through the public API."""
    interface = conduction_resistance(50e-6, 5.0, 2e-4)
    temperature = series_temperature(318.15, 15.0, [1.0, interface, 2.0])
    print(
        json.dumps(
            {
                "case": "synthetic_series_stack",
                "interface_resistance": {"value": interface, "unit": "K/W"},
                "temperature": {"value": temperature, "unit": "K"},
                "temperature_celsius": {"value": temperature - 273.15, "unit": "degC"},
                "power": {"value": 15.0, "unit": "W"},
            },
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
