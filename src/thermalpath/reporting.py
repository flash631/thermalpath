"""Deterministic, bounded reports of supplied engineering evidence."""

import json
import math
import re
from dataclasses import asdict, dataclass

MAX_REPORT_BYTES = 1_048_576


def _text(value: str) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > 4096
        or any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in value)
    ):
        raise ValueError("text must contain 1 to 4096 characters without controls")


def _number(value: float) -> None:
    if type(value) not in (int, float):
        raise ValueError("check values must be finite numbers, not booleans")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError("check values must be finite numbers, not booleans")


@dataclass(frozen=True)
class NumericalCheck:
    """A supplied signed residual and an absolute tolerance in matching units.

    Attributes
    ----------
    name, unit, note : str
        Unique name, explicit unit, and explanation of the check or missing value.
    value : float or None
        Signed residual or error; None means not run, never zero or passed.
    tolerance : float
        Finite nonnegative absolute acceptance limit in the same unit.

    Notes
    -----
    Passing means only abs(value) <= tolerance for the supplied numbers.
    This record does not execute or independently verify a calculation.
    """

    name: str
    unit: str
    value: float | None
    tolerance: float
    note: str

    def __post_init__(self) -> None:
        for text in (self.name, self.unit, self.note):
            _text(text)
        _number(self.tolerance)
        if self.tolerance < 0:
            raise ValueError("tolerance must be nonnegative")
        if self.value is not None:
            _number(self.value)

    @property
    def status(self) -> str:
        """Return passed, failed, or not_run without changing the evidence."""
        if self.value is None:
            return "not_run"
        return "passed" if abs(self.value) <= self.tolerance else "failed"


@dataclass(frozen=True)
class Evidence:
    """Caller-declared provenance; declarations are not authenticated.

    Attributes
    ----------
    kind : str
        synthetic, analytical, numerical, or experimental.
    source, locator, license, note : str
        Source declaration, location within it, rights declaration, and scope.
        These fields are plain text and are never opened as paths or URLs.
    """

    kind: str
    source: str
    locator: str
    license: str
    note: str

    def __post_init__(self) -> None:
        if self.kind not in ("synthetic", "analytical", "numerical", "experimental"):
            raise ValueError("unknown evidence kind")
        for text in (self.source, self.locator, self.license, self.note):
            _text(text)


def _validate_json(value: object, budget: list[int], depth: int = 0) -> None:
    """Bound traversal, including cyclic objects, before serialization."""
    budget[0] -= 1
    if budget[0] < 0 or depth > 16:
        raise ValueError("report exceeds 100000 values or 16 nesting levels")
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        _text(value)
        budget[1] -= len(value.encode("utf-8"))
        if budget[1] < 0:
            raise ValueError("report exceeds 1 MiB")
    elif type(value) is int:
        if not -(2**63) <= value < 2**63:
            raise ValueError("report integers must fit signed 64 bits")
    elif type(value) is float:
        _number(value)
    elif type(value) in (list, tuple, dict):
        if type(value) is dict:
            for key, item in value.items():
                _text(key)
                _validate_json(key, budget, depth + 1)
                _validate_json(item, budget, depth + 1)
        else:
            for item in value:
                _validate_json(item, budget, depth + 1)
    else:
        raise ValueError("report values must be plain JSON-compatible data")


def _markdown_text(text: str) -> str:
    """Encode punctuation as entities so caller text cannot introduce markup."""
    return "".join(c if c.isalnum() or c == " " else f"&#{ord(c)};" for c in text)


@dataclass(frozen=True, init=False)
class EngineeringReport:
    """Immutable snapshot with JSON and Markdown representations.

    Parameters
    ----------
    title : str
        Plain report title.
    source_revision : str
        Caller-declared lowercase 40-hex Git SHA, or 'unknown'. It must identify
        the code used, not an anticipated commit. No Git inspection is performed.
    inputs, results : dict
        Nonempty plain JSON-compatible evidence, preserving list order and nulls.
    units : dict of str to str
        Nonempty field/quantity-to-unit declarations, including dimensionless
        quantities where needed. Completeness is the caller's responsibility.
    checks : tuple of NumericalCheck
        One to 256 checks with unique names; unavailable checks use value=None.
    provenance : tuple of Evidence
        One to 64 source records.
    limitations : tuple of str
        One to 64 explicit limitations.

    Notes
    -----
    No calculations are rerun and no environment, files, clock, or network are
    read. This is a formatter, not a physics or provenance validator. Caller
    text is retained; review it for private information before sharing.
    Payloads are limited to 1 MiB of UTF-8 JSON, 100000 values, and depth 16.
    """

    _json: str

    def __init__(
        self,
        *,
        title: str,
        source_revision: str,
        inputs: dict,
        units: dict[str, str],
        results: dict,
        checks: tuple[NumericalCheck, ...],
        provenance: tuple[Evidence, ...],
        limitations: tuple[str, ...],
    ) -> None:
        _text(title)
        if not isinstance(source_revision, str) or not re.fullmatch(
            r"(?:[0-9a-f]{40}|unknown)", source_revision
        ):
            raise ValueError("source_revision must be a full lowercase SHA or unknown")
        for mapping in (inputs, units, results):
            if type(mapping) is not dict or not mapping:
                raise ValueError(
                    "inputs, units and results must be nonempty dictionaries"
                )
        for unit in units.values():
            _text(unit)
        for sequence, item_type, limit in (
            (checks, NumericalCheck, 256),
            (provenance, Evidence, 64),
            (limitations, str, 64),
        ):
            if (
                type(sequence) is not tuple
                or not 1 <= len(sequence) <= limit
                or not all(isinstance(item, item_type) for item in sequence)
            ):
                raise ValueError("invalid report sequence, item type or count")
        if len({check.name for check in checks}) != len(checks):
            raise ValueError("check names must be unique")
        payload = dict(
            schema_version=1,
            title=title,
            source_revision=source_revision,
            provenance_status="caller_declared",
            scope=(
                "Formatting and numerical screens do not establish physical validation."
            ),
            inputs=inputs,
            units=units,
            results=results,
            checks=[dict(**asdict(check), status=check.status) for check in checks],
            provenance=[asdict(item) for item in provenance],
            limitations=limitations,
        )
        _validate_json(payload, [100000, MAX_REPORT_BYTES])
        encoded = json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n"
        if len(encoded.encode("utf-8")) > MAX_REPORT_BYTES:
            raise ValueError("report exceeds 1 MiB")
        object.__setattr__(self, "_json", encoded)

    def to_json(self) -> str:
        """Return the complete snapshot as sorted JSON with one final newline."""
        return self._json

    def to_markdown(self) -> str:
        """Return a check table, limitations, and the complete JSON evidence.

        The fenced evidence block preserves all inputs, results and provenance.
        Its fence is longer than every backtick run in the payload. User text
        outside that block is escaped. No HTML, images or links are generated.
        """
        payload = json.loads(self._json)
        lines = [
            "# " + _markdown_text(payload["title"]),
            "",
            "Source revision: " + payload["source_revision"],
            "",
            "Provenance: caller declared; source and revision are not authenticated.",
            "",
            payload["scope"],
            "",
            "## Numerical checks",
            "",
            "| Check | Value | Absolute tolerance | Unit | Status | Note |",
            "| --- | ---: | ---: | --- | --- | --- |",
        ]
        for check in payload["checks"]:
            cells = [
                check["name"],
                "not run" if check["value"] is None else str(check["value"]),
                str(check["tolerance"]),
                check["unit"],
                check["status"],
                check["note"],
            ]
            lines.append("| " + " | ".join(map(_markdown_text, cells)) + " |")
        lines.extend(["", "## Limitations", ""])
        lines.extend("- " + _markdown_text(text) for text in payload["limitations"])
        fence = "`" * max(
            3, 1 + max(map(len, re.findall(r"`+", self._json)), default=0)
        )
        lines.extend(
            ["", "## Complete evidence", "", fence + "json", self._json.rstrip(), fence]
        )
        return "\n".join(lines) + "\n"
