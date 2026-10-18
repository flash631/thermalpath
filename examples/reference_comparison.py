"""Compare the bundled arithmetic fixture with declared synthetic predictions."""

import json
import os
from pathlib import Path

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from thermalpath.comparison import (  # noqa: E402
    TemperaturePrediction,
    compare_reference,
    loads_reference,
)


def main() -> None:
    """Print all rows, counts and the conditional RMSE without fitting."""
    base = Path(__file__).resolve().parents[1] / "data/reference/synthetic_temperature"
    reference = loads_reference(
        base.with_suffix(".csv").read_bytes(),
        base.with_suffix(".json").read_bytes(),
    )
    location = reference.samples[0].location_id
    comparison = compare_reference(
        reference,
        (
            TemperaturePrediction(location, 0, 303),
            TemperaturePrediction(location, 2.5, 296.625),
            TemperaturePrediction(location, 20, 305),
        ),
        matching_note=(
            "Same synthetic body and elapsed-time origin as the reference recipe. "
            "Predictions are assigned arithmetic values, not a thermal solver output."
        ),
        exclusions={
            reference.samples[3].sample_id: "Repeat omitted for this declared example"
        },
    )
    print(
        json.dumps(
            {
                "kind": reference.kind,
                "csv_sha256": reference.csv_sha256,
                "metadata_sha256": reference.metadata_sha256,
                "matching_note": comparison.matching_note,
                "rows": [
                    {
                        "sample_id": row.sample.sample_id,
                        "location_id": row.sample.location_id,
                        "time_s": row.sample.time_s,
                        "reference_k": row.sample.temperature_k,
                        "prediction_k": row.prediction.temperature_k
                        if row.prediction
                        else None,
                        "status": row.status,
                        "residual_k": row.residual_k,
                        "reason": row.reason,
                    }
                    for row in comparison.rows
                ],
                "matched_count": comparison.matched_count,
                "missing_count": comparison.missing_count,
                "excluded_count": comparison.excluded_count,
                "unused_predictions": [
                    {
                        "location_id": p.location_id,
                        "time_s": p.time_s,
                        "temperature_k": p.temperature_k,
                    }
                    for p in comparison.unused_predictions
                ],
                "rmse_k": comparison.rmse_k,
                "scope": (
                    "Equal-row RMSE for the two matched rows only; "
                    "synthetic arithmetic."
                ),
            },
            indent=2,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
