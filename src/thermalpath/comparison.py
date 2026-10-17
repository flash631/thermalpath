"""Import bounded temperature reference tables with declared provenance."""

import csv
import hashlib
import io
import json
import math
import re
from dataclasses import dataclass
from typing import Literal

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
