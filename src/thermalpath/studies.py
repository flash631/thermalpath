"""Bounded steady-network sweeps with self-contained CSV case records."""

import csv
import io
import json
import math
from dataclasses import dataclass
from itertools import product

from thermalpath.diagnostics import heat_balance
from thermalpath.io import dumps_case, loads_case
from thermalpath.models import Network, _scalar
from thermalpath.networks import solve_steady

_FIELDS = {
    "power_w": "nodes",
    "fixed_temperature_k": "nodes",
    "conductance_w_k": "links",
}
_HEADER = (
    "sweep_schema_version",
    "case_index",
    "case_json",
    "status",
    "error",
    "temperatures_k_json",
    "link_powers_w_json",
    "linear_residual_w_json",
    "imbalance_w",
)
_MAX_CASES = 256
_MAX_CASE_CHARS = 32768


@dataclass(frozen=True)
class SweepAxis:
    """Specify one ordered finite parameter axis without changing topology.

    Parameters
    ----------
    field : str
        power_w [W], fixed_temperature_k [K], or conductance_w_k [W/K].
    target_id : str
        Existing node or link ID, according to field.
    values : tuple of float
        One to 256 finite real values; lists are copied to tuples. Repeated
        values remain repeated cases. Nonpositive conductances/temperatures
        are retained as failed cases when evaluated, never silently filtered.

    Raises
    ------
    ValueError
        Field, ID, collection, or scalar representation is invalid.
    """

    field: str
    target_id: str
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.field, str) or self.field not in _FIELDS:
            raise ValueError("unsupported sweep field")
        if not isinstance(self.target_id, str) or not self.target_id:
            raise ValueError("target_id must be a nonempty string")
        if not isinstance(self.values, (tuple, list)) or not (
            1 <= len(self.values) <= _MAX_CASES
        ):
            raise ValueError("axis values must contain 1 to 256 entries")
        object.__setattr__(
            self, "values", tuple(_scalar(v, "axis value") for v in self.values)
        )


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":"))


def _bounded(network: Network) -> None:
    if len(network.nodes) > 64 or len(network.links) > 128:
        raise ValueError("sweep networks are limited to 64 nodes and 128 links")


def _evaluate(cases: list[str]) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(_HEADER)
    for index, case in enumerate(cases):
        # Case-size limits apply to the specification, before the solver runs.
        if len(case) > _MAX_CASE_CHARS:
            raise ValueError("case_json exceeds 32768 characters")
        try:
            network = loads_case(case)
            _bounded(network)
            result = solve_steady(network)
            balance = heat_balance(network, result.link_powers_w)
        except ValueError as exc:
            writer.writerow((1, index, case, "failed", str(exc), "", "", "", ""))
        else:
            writer.writerow(
                (
                    1,
                    index,
                    case,
                    "ok",
                    "",
                    _json(result.temperatures_k),
                    _json(result.link_powers_w),
                    _json(result.linear_residual_w),
                    repr(balance.imbalance_w),
                )
            )
    return output.getvalue()


def sweep_network(network: Network, axes: tuple[SweepAxis, ...]) -> str:
    """Evaluate a Cartesian parameter sweep and return version-1 CSV text.

    Parameters
    ----------
    network : Network
        Immutable base input, at most 64 nodes and 128 links. Every row carries
        its complete version-1 network JSON, with explicit defaults and SI units
        in field names. Each case specification is at most 32768 characters.
    axes : tuple of SweepAxis
        Tuple or list of at most eight distinct (field, target_id) axes. The
        last axis varies fastest; input value order and duplicates are kept.
        No axes evaluates the base once. At most 256 combinations are allowed.
        Power axes target unknown nodes; temperature axes target fixed nodes.

    Returns
    -------
    str
        CSV with zero-based case_index, full inputs, status/error, and JSON
        temperature, oriented link-power and linear-residual maps. Global
        imbalance_w is separate from the linear residual. Failed cases have
        empty result fields. Write with UTF-8 and newline="".

    Raises
    ------
    ValueError
        Sweep structure, resource bound or target is invalid. Physical-domain
        and numerical ValueError failures inside a case become failed rows;
        unexpected exceptions propagate. No partial CSV is returned.

    Notes
    -----
    Uses the existing constant-conductance steady solver without changing its
    equations or accuracy limits. CSV replay requires this solver and schema;
    numerical results need not be bit-identical across platforms or versions.
    Numerical verification does not establish physical validation.
    """
    if not isinstance(network, Network):
        raise ValueError("network must be a Network")
    _bounded(network)
    if not isinstance(axes, (tuple, list)) or len(axes) > 8:
        raise ValueError("axes must be a tuple or list of at most eight axes")
    if any(not isinstance(axis, SweepAxis) for axis in axes):
        raise ValueError("axes must contain SweepAxis objects")
    if len({(axis.field, axis.target_id) for axis in axes}) != len(axes):
        raise ValueError("duplicate sweep target")
    if math.prod(len(axis.values) for axis in axes) > _MAX_CASES:
        raise ValueError("sweep exceeds 256 cases")
    base = json.loads(dumps_case(network))
    targets = []
    for axis in axes:
        group = _FIELDS[axis.field]
        indices = {item["id"]: i for i, item in enumerate(base[group])}
        if axis.target_id not in indices:
            raise ValueError("sweep target does not exist")
        index = indices[axis.target_id]
        if group == "nodes":
            fixed = base[group][index]["fixed_temperature_k"] is not None
            if fixed != (axis.field == "fixed_temperature_k"):
                raise ValueError("axis must preserve the node boundary type")
        targets.append((group, index, axis.field))
    cases = []
    for values in product(*(axis.values for axis in axes)):
        for (group, index, field), value in zip(targets, values, strict=True):
            base[group][index][field] = value
        cases.append(_json(base))
    return _evaluate(cases)


def replay_network_sweep(text: str) -> str:
    """Recompute a sweep from the complete case_json in each CSV row.

    Parameters
    ----------
    text : str
        Version-1 CSV, at most 32 MiB of characters, with the exact header and
        one to 256 consecutively indexed rows. Inputs are independent of the
        original base/axes. All old output fields are ignored and recomputed.

    Returns
    -------
    str
        Fresh CSV in original row order, including failures. Compare input
        records and outputs yourself when assessing another solver revision.

    Raises
    ------
    ValueError
        CSV syntax, header, envelope, row count, or case size is invalid.
        Invalid network specifications are preserved as failed case rows.

    Notes
    -----
    This reads data, never code. CSV quoting is not spreadsheet formula
    protection; import text fields as text when inspecting a CSV in a spreadsheet.
    """
    if not isinstance(text, str) or len(text) > 32 * 1024 * 1024:
        raise ValueError("CSV text must be a string of at most 32 MiB characters")
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    cases = []
    try:
        if next(reader, None) != list(_HEADER):
            raise ValueError("unsupported sweep CSV header")
        for index, row in enumerate(reader):
            if index >= _MAX_CASES:
                raise ValueError("sweep exceeds 256 cases")
            if len(row) != len(_HEADER) or row[:2] != ["1", str(index)]:
                raise ValueError("invalid sweep version, index or row width")
            cases.append(row[2])
    except csv.Error as exc:
        raise ValueError("invalid sweep CSV syntax") from exc
    if not cases:
        raise ValueError("sweep CSV has no cases")
    return _evaluate(cases)
