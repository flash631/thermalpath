# Temperature reference import

`thermalpath.comparison.loads_reference(csv_data, metadata_data)` reads two
UTF-8 byte strings: a temperature CSV and a JSON metadata sidecar. Use
`Path.read_bytes()` to preserve the original file identities. It returns a frozen
`ReferenceData` with ordered `ReferenceSample` rows and the declared provenance.

```python
from pathlib import Path
from thermalpath.comparison import loads_reference

base = Path("data/reference/synthetic_temperature")
reference = loads_reference(
    base.with_suffix(".csv").read_bytes(),
    base.with_suffix(".json").read_bytes(),
)
print(reference.kind)  # synthetic
print([sample.temperature_k for sample in reference.samples])
# [300.0, 300.625, 302.5, 300.625]
```

Run `python examples/reference_import.py` for the same data and both file hashes.
The example can run from another working directory. The CSV and metadata are
distributed in the source archive; the wheel contains the importer.

## CSV contract

The header must be exactly:

```csv
sample_id,location_id,time_s,temperature_k,source_record
```

| Column | Meaning |
| --- | --- |
| `sample_id` | Unique, nonempty row identifier. |
| `location_id` | Key in the metadata's location descriptions. |
| `time_s` | Nonnegative elapsed time for transient data; blank for steady data. |
| `temperature_k` | Positive finite absolute temperature in kelvin. |
| `source_record` | Locator for this value within the declared source, such as a table row and channel, or a synthetic recipe evaluation. |

Quoted commas and quoted quotation marks are accepted. Empty rows, missing or
extra columns, duplicate IDs, undeclared locations, blank values and malformed
CSV are rejected. Replicates with distinct sample IDs are preserved, including
repeated location/time pairs. Rows need not be sorted; the importer never sorts,
averages, interpolates or drops observations. A single rejected row prevents a
partial import. Missing observations require a separate accounting record and
are not supported as blank temperature cells in this format.

Numeric tokens use ASCII decimal notation with an optional sign and exponent.
They round to binary64. Nonfinite values, overflow and nonzero values rounded to
zero are rejected. Very small positive representable temperatures are accepted;
that numerical domain does not imply physical credibility. No unit conversion,
solver call, coordinate/time matching, residual or RMSE calculation occurs.

## Required metadata

Every listed field is mandatory; unknown or duplicate JSON keys are rejected.

| Field | Required value or declaration |
| --- | --- |
| `schema_version` | Integer `1`. |
| `kind` | Exactly `synthetic` or `experimental`. |
| `mode` | Exactly `steady` or `transient`; applies to every row. |
| `source` | Recoverable dataset/document identifier, version and location, or a reproducible synthetic recipe location. |
| `license` | Stated data license or documented permission, with its source. |
| `description` | What the dataset represents, including conditions needed to interpret it. |
| `method` | Generation recipe, or acquisition/processing method and records needed to interpret measurements. |
| `locations` | Object mapping each location ID to its meaning in the source: body, sensor/channel, or coordinates and their frame/units. |
| `units` | Exactly `{"temperature": "K", "time": "s"}`, including for steady data. |
| `csv_sha256` | Lowercase SHA-256 hex digest of the exact CSV bytes. |

Source and row locators must let a reviewer trace each value back to the stated
record. For experimental work, the declarations should identify the assembly,
sensor mapping, acquisition conditions, calibration and uncertainty records,
and any transformations. These details must come from the actual source.
Converting a source to SI requires a documented transformation and a new CSV
hash; changing a unit label without converting the values is not acceptable.

Text fields must be trimmed, nonempty and at most 2048 characters, without ASCII
control characters. Bare placeholders `unknown`, `n/a`, `none` and `unspecified`
are rejected without regard to case. The CSV is limited to 1 MiB and 1 to 10000
data rows; metadata is limited to 64 KiB and 1 to 10000 location descriptions.
The byte bound may be reached before the row or location bound. UTF-8 BOMs and
LF or CRLF endings are accepted. Both affect the exact-byte SHA-256 hashes.

## What an accepted import establishes

The importer checks structure, units, numeric domains, supplied traceability
fields and the CSV/sidecar hash agreement. The returned `csv_sha256` and
`metadata_sha256` identify the received bytes. A hash mismatch rejects the pair;
an updated hash and edited data form a different pair, not proof of authenticity.
Keep the original files with these hashes when retaining evidence.

The importer does not access sources, verify a license, authenticate provenance,
or determine whether a sensor measures the same quantity as a model output.
A fabricated but structurally complete declaration cannot be detected by this
parser. An `experimental` label is the supplier's declaration, not a validation
result. External evidence still needs source, acquisition and comparability
review before it can support a physical claim. Constructing the output
dataclasses directly also does not run the import checks.
