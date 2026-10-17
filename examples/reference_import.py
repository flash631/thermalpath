"""Read the bundled synthetic temperature reference and its provenance."""

import json
from pathlib import Path

from thermalpath.comparison import loads_reference


def main() -> None:
    """Print imported values and byte identities without fitting or comparison."""
    base = Path(__file__).resolve().parents[1] / "data/reference/synthetic_temperature"
    result = loads_reference(
        base.with_suffix(".csv").read_bytes(),
        base.with_suffix(".json").read_bytes(),
    )
    print(
        json.dumps(
            {
                "kind": result.kind,
                "mode": result.mode,
                "source": result.source,
                "license": result.license,
                "count": len(result.samples),
                "times_s": [sample.time_s for sample in result.samples],
                "temperatures_k": [sample.temperature_k for sample in result.samples],
                "csv_sha256": result.csv_sha256,
                "metadata_sha256": result.metadata_sha256,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
