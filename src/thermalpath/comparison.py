"""Import temperature references and compare explicitly corresponding predictions."""

import csv
import hashlib
import io
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from thermalpath.models import _scalar

_COLUMNS = ("sample_id", "location_id", "time_s", "temperature_k", "source_record")
_NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
_FIELDS = {
    "schema_version",
    "kind",
    "mode",
    "source",
    "license",
    "description",
    "method",
    "locations",
    "units",
    "csv_sha256",
}


@dataclass(frozen=True)
class ReferenceSample:
    """One imported row; time is None for a steady reference.

    Attributes
    ----------
    sample_id, location_id, source_record : str
        Unique row ID, declared location ID, and locator within the source.
    time_s : float or None
        Nonnegative elapsed time in seconds for transient data.
    temperature_k : float
        Positive absolute temperature in kelvin.
    """

    sample_id: str
    location_id: str
    time_s: float | None
    temperature_k: float
    source_record: str


@dataclass(frozen=True)
class ReferenceData:
    """Imported values and declarations; construction alone does not validate.

    Attributes
    ----------
    kind : {"synthetic", "experimental"}
        Supplier's data label, retained without an authenticity claim.
    mode : {"steady", "transient"}
        Whether every row has a blank time or a nonnegative elapsed time.
    source, license, description, method : str
        Source locator, stated license/permission, dataset description, and
        generation or acquisition method. These declarations are not verified.
    locations : tuple of (str, str)
        Location IDs and their source-specific descriptions, in declared order.
    samples : tuple of ReferenceSample
        Validated rows in original order, including repeated locations/times.
    csv_sha256, metadata_sha256 : str
        SHA-256 identities of the exact supplied bytes, including line endings.
    """

    kind: Literal["synthetic", "experimental"]
    mode: Literal["steady", "transient"]
    source: str
    license: str
    description: str
    method: str
    locations: tuple[tuple[str, str], ...]
    samples: tuple[ReferenceSample, ...]
    csv_sha256: str
    metadata_sha256: str


def _text(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > 2048
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
        or value.casefold() in {"unknown", "n/a", "none", "unspecified"}
    ):
        raise ValueError(f"{field} requires a nonempty, trimmed declaration")
    return value


def _object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate metadata field: {key}")
        result[key] = value
    return result


def _decode(data: bytes, limit: int, name: str) -> str:
    if not isinstance(data, bytes) or not 0 < len(data) <= limit:
        raise ValueError(f"{name} must contain 1 to {limit} bytes")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{name} must be UTF-8") from exc


def _number(token: str, field: str, positive: bool) -> float:
    if not _NUMBER.fullmatch(token):
        raise ValueError(f"{field} requires a decimal number")
    value = float(token)
    nonzero = any(c in "123456789" for c in token.lower().split("e")[0])
    if (
        not math.isfinite(value)
        or (value == 0 and nonzero)
        or value < 0
        or (positive and value == 0)
    ):
        raise ValueError(f"{field} is outside its physical or finite float domain")
    return value


def loads_reference(csv_data: bytes, metadata_data: bytes) -> ReferenceData:
    """Import a version-1 reference CSV and its hash-bound JSON sidecar.

    Parameters
    ----------
    csv_data : bytes
        UTF-8 CSV, at most 1 MiB, with the exact ordered header sample_id,
        location_id,time_s,temperature_k,source_record and 1 to 10000 rows.
    metadata_data : bytes
        UTF-8 JSON, at most 64 KiB. Required fields and provenance conventions
        are specified in docs/comparison.md. Only kelvin and seconds are accepted.

    Returns
    -------
    ReferenceData
        Immutable imported rows, provenance declarations and byte hashes.

    Raises
    ------
    ValueError
        Encoding, size, schema, units, hash, provenance or row checks fail.
        No partial result is returned and no row is silently excluded.

    Notes
    -----
    Optional UTF-8 BOMs are accepted and included in the hashes. Ordinary
    decimal values round to binary64; overflow and nonzero underflow to zero
    are rejected. No files or URLs are opened. Supplied provenance is checked
    for structure, not truth, source availability, license rights, calibration,
    uncertainty or physical comparability. See docs/comparison.md before use.
    """
    csv_text = _decode(csv_data, 1048576, "CSV")
    metadata_text = _decode(metadata_data, 65536, "metadata")
    try:
        meta = json.loads(metadata_text, object_pairs_hook=_object)
    except RecursionError as exc:
        raise ValueError("metadata nesting is too deep") from exc
    if not isinstance(meta, dict) or meta.keys() != _FIELDS:
        raise ValueError("metadata must contain exactly the version-1 fields")
    if type(meta["schema_version"]) is not int or meta["schema_version"] != 1:
        raise ValueError("schema_version must be integer 1")
    if meta["kind"] not in ("synthetic", "experimental"):
        raise ValueError("kind must be synthetic or experimental")
    if meta["mode"] not in ("steady", "transient"):
        raise ValueError("mode must be steady or transient")
    if meta["units"] != {"temperature": "K", "time": "s"}:
        raise ValueError("units must be exactly temperature K and time s")
    for field in ("source", "license", "description", "method"):
        _text(meta[field], field)
    locations = meta["locations"]
    if not isinstance(locations, dict) or not 1 <= len(locations) <= 10000:
        raise ValueError("locations must contain 1 to 10000 descriptions")
    for key, description in locations.items():
        _text(key, "location_id")
        _text(description, "location description")
    checksum = hashlib.sha256(csv_data).hexdigest()
    if meta["csv_sha256"] != checksum:
        raise ValueError("csv_sha256 does not match the supplied CSV bytes")
    reader = csv.reader(io.StringIO(csv_text, newline=""), strict=True)
    samples = []
    ids = set()
    try:
        if tuple(next(reader, ())) != _COLUMNS:
            raise ValueError("CSV header must match the version-1 columns in order")
        for row in reader:
            if len(samples) >= 10000:
                raise ValueError("CSV exceeds 10000 data rows")
            if len(row) != len(_COLUMNS):
                raise ValueError("every CSV row must contain exactly five fields")
            sample_id, location_id, time, temperature, record = row
            _text(sample_id, "sample_id")
            _text(location_id, "location_id")
            _text(record, "source_record")
            if sample_id in ids:
                raise ValueError("sample_id must be unique")
            if location_id not in locations:
                raise ValueError("location_id has no declared description")
            if meta["mode"] == "steady":
                if time:
                    raise ValueError("steady rows must have blank time_s")
                time_s = None
            else:
                time_s = _number(time, "time_s", positive=False)
            temperature_k = _number(temperature, "temperature_k", positive=True)
            samples.append(
                ReferenceSample(sample_id, location_id, time_s, temperature_k, record)
            )
            ids.add(sample_id)
    except csv.Error as exc:
        raise ValueError("malformed CSV") from exc
    if not samples:
        raise ValueError("CSV must contain at least one data row")
    return ReferenceData(
        meta["kind"],
        meta["mode"],
        meta["source"],
        meta["license"],
        meta["description"],
        meta["method"],
        tuple(locations.items()),
        tuple(samples),
        checksum,
        hashlib.sha256(metadata_data).hexdigest(),
    )


@dataclass(frozen=True)
class TemperaturePrediction:
    """One model value at a declared reference location and elapsed time.

    Parameters
    ----------
    location_id : str
        Exact reference location ID; coordinate correspondence is caller supplied.
    time_s : float or None
        Nonnegative elapsed seconds, or None for a steady prediction.
    temperature_k : float
        Finite positive absolute temperature in kelvin.
    """

    location_id: str
    time_s: float | None
    temperature_k: float

    def __post_init__(self) -> None:
        """Validate and convert scalar fields to binary64."""
        _text(self.location_id, "prediction location_id")
        if self.time_s is not None:
            time = _scalar(self.time_s, "prediction time_s")
            if time < 0:
                raise ValueError("prediction time_s must be nonnegative")
            object.__setattr__(self, "time_s", time)
        object.__setattr__(
            self,
            "temperature_k",
            _scalar(self.temperature_k, "prediction temperature_k", positive=True),
        )


@dataclass(frozen=True)
class TemperatureResidual:
    """One reference row, retained even when absent from the RMSE denominator.

    Attributes
    ----------
    sample : ReferenceSample
        Original row, including its source locator.
    prediction : TemperaturePrediction or None
        Exact-key prediction, if supplied, including for an excluded row.
    status : {"matched", "missing", "excluded"}
        Only matched rows contribute to RMSE. Explicit exclusion takes priority.
    residual_k : float or None
        Predicted minus reference temperature [K], only for matched rows.
    reason : str or None
        Exclusion reason or missing-prediction explanation; None when matched.
    """

    sample: ReferenceSample
    prediction: TemperaturePrediction | None
    status: Literal["matched", "missing", "excluded"]
    residual_k: float | None
    reason: str | None


@dataclass(frozen=True)
class ReferenceComparison:
    """Comparison evidence with a conditional, equal-row RMSE in kelvin.

    Attributes
    ----------
    reference : ReferenceData
        Input dataset with its original declarations and hashes.
    matching_note : str
        Caller declaration of coordinate/sensor, time-origin and quantity mapping.
    predictions : tuple of TemperaturePrediction
        All supplied predictions in input order.
    rows : tuple of TemperatureResidual
        Every reference row in original order, including replicates.
    unused_predictions : tuple of TemperaturePrediction
        Predictions used by no matched row, in input order.
    matched_count, missing_count, excluded_count : int
        Disjoint counts whose sum is the number of reference rows.
    rmse_k : float or None
        Square root of the mean squared matched residual [K]. None if empty.
        This is not a full-dataset metric when any rows are missing or excluded.
    """

    reference: ReferenceData
    matching_note: str
    predictions: tuple[TemperaturePrediction, ...]
    rows: tuple[TemperatureResidual, ...]
    unused_predictions: tuple[TemperaturePrediction, ...]
    matched_count: int
    missing_count: int
    excluded_count: int
    rmse_k: float | None


def compare_reference(
    reference: ReferenceData,
    predictions: Sequence[TemperaturePrediction],
    *,
    matching_note: str,
    exclusions: Mapping[str, str] | None = None,
) -> ReferenceComparison:
    """Calculate exact-key signed residuals and an equal-row RMSE.

    Parameters
    ----------
    reference : ReferenceData
        Dataset from loads_reference. Relevant row domains are checked again;
        this operation does not reauthenticate the original bytes or provenance.
    predictions : sequence of TemperaturePrediction
        Zero to 10000 values with unique (location_id, time_s) keys. Times must
        agree with the reference's steady/transient mode. Unused values survive.
    matching_note : str
        Required correspondence declaration; see docs/comparison.md. Declaring
        a mapping does not establish its physical correctness.
    exclusions : mapping of str to str, optional
        Reference sample IDs and nonempty reasons. Unknown IDs are rejected.

    Returns
    -------
    ReferenceComparison
        Matched, missing and excluded rows; counts; unused predictions; RMSE.

    Raises
    ------
    ValueError
        Invalid row domains, duplicate prediction keys, mode mismatch, size
        limits or invalid exclusions. Invalid numbers are never silently dropped.

    Notes
    -----
    Keys match exactly after binary64 conversion. There is no interpolation,
    nearest-neighbor search, time tolerance, fitting or unit conversion. Each
    nonexcluded replicate contributes separately with equal weight. RMSE uses
    scaled squares to avoid intermediate overflow and loss of uniformly tiny
    residuals. Rounding remains; no uncertainty or physical validation is inferred.
    """
    _text(matching_note, "matching_note")
    if not isinstance(reference, ReferenceData) or reference.mode not in (
        "steady",
        "transient",
    ):
        raise ValueError("reference must have a steady or transient mode")
    if (
        not isinstance(reference.samples, tuple)
        or not 1 <= len(reference.samples) <= 10000
    ):
        raise ValueError("reference must contain 1 to 10000 immutable rows")
    if (
        not isinstance(predictions, Sequence)
        or isinstance(predictions, (str, bytes))
        or len(predictions) > 10000
    ):
        raise ValueError("predictions must be a sequence of at most 10000 values")
    predictions = tuple(predictions)
    lookup = {}
    for prediction in predictions:
        if not isinstance(prediction, TemperaturePrediction):
            raise ValueError("predictions must contain TemperaturePrediction values")
        if (prediction.time_s is None) != (reference.mode == "steady"):
            raise ValueError("prediction time must agree with reference mode")
        key = (prediction.location_id, prediction.time_s)
        if key in lookup:
            raise ValueError("prediction location/time keys must be unique")
        lookup[key] = prediction
    ids = set()
    locations = dict(reference.locations)
    for sample in reference.samples:
        if not isinstance(sample, ReferenceSample):
            raise ValueError("reference rows must be ReferenceSample values")
        _text(sample.sample_id, "sample_id")
        _text(sample.location_id, "location_id")
        _text(sample.source_record, "source_record")
        if sample.sample_id in ids or sample.location_id not in locations:
            raise ValueError("reference IDs must be unique and locations declared")
        ids.add(sample.sample_id)
        _scalar(sample.temperature_k, "reference temperature_k", positive=True)
        if (sample.time_s is None) != (reference.mode == "steady"):
            raise ValueError("reference time must agree with reference mode")
        if sample.time_s is not None and _scalar(sample.time_s, "reference time_s") < 0:
            raise ValueError("reference time_s must be nonnegative")
    if exclusions is None:
        exclusions = {}
    if not isinstance(exclusions, Mapping):
        raise ValueError("exclusions must map sample IDs to reasons")
    exclusions = dict(exclusions)
    for sample_id, reason in exclusions.items():
        if sample_id not in ids:
            raise ValueError("exclusion sample_id is absent from reference")
        _text(reason, "exclusion reason")
    rows = []
    residuals = []
    used = set()
    missing = 0
    for sample in reference.samples:
        key = (
            sample.location_id,
            None if sample.time_s is None else float(sample.time_s),
        )
        prediction = lookup.get(key)
        if sample.sample_id in exclusions:
            status, reason, residual = "excluded", exclusions[sample.sample_id], None
        elif prediction is None:
            status, reason, residual = (
                "missing",
                "No exact location/time prediction",
                None,
            )
            missing += 1
        else:
            status, reason = "matched", None
            residual = prediction.temperature_k - float(sample.temperature_k)
            residuals.append(residual)
            used.add(key)
        rows.append(TemperatureResidual(sample, prediction, status, residual, reason))
    rmse = None
    if residuals:
        scale = max(abs(r) for r in residuals)
        rmse = (
            scale
            * math.sqrt(math.fsum((r / scale) ** 2 for r in residuals) / len(residuals))
            if scale
            else 0.0
        )
    return ReferenceComparison(
        reference,
        matching_note,
        predictions,
        tuple(rows),
        tuple(p for p in predictions if (p.location_id, p.time_s) not in used),
        len(residuals),
        missing,
        len(exclusions),
        rmse,
    )
