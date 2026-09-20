"""Version-1 JSON cases for constant-conductance networks in SI units."""

import json
import math
from dataclasses import asdict

from thermalpath.models import Link, Network, Node


def _object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject duplicate keys instead of silently replacing input values."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key!r}")
        result[key] = value
    return result


def _float(token: str) -> float:
    """Reject overflow and nonzero tokens rounded to zero during decoding."""
    value = float(token)
    nonzero = any(digit in "123456789" for digit in token.lower().split("e")[0])
    if not math.isfinite(value) or (value == 0 and nonzero):
        raise ValueError("JSON number is outside the nonzero finite float range")
    return value


def _constant(token: str) -> None:
    """Reject nonstandard NaN and infinity tokens."""
    raise ValueError(f"invalid JSON numeric constant: {token}")


def _fields(value: object, required: set[str], optional: set[str]) -> dict:
    """Require an object with only the declared fields."""
    if not isinstance(value, dict):
        raise ValueError("expected a JSON object")
    missing = required - value.keys()
    unknown = value.keys() - required - optional
    if missing or unknown:
        raise ValueError(
            f"invalid fields: missing={sorted(missing)}, unknown={sorted(unknown)}"
        )
    return value


def loads_case(text: str) -> Network:
    """Decode a version-1 JSON network case without solving it.

    Parameters
    ----------
    text : str
        JSON object with schema_version=1, nodes, and links. Powers use W,
        conductances W/K, and fixed absolute temperatures K.

    Returns
    -------
    Network
        Validated immutable inputs, preserving array order and identifiers.

    Raises
    ------
    ValueError
        JSON syntax, version, fields, numbers, or model inputs are invalid.
        Duplicate keys and unknown fields are rejected at every object level.

    Notes
    -----
    Missing node power defaults to zero; missing fixed temperature leaves it
    unknown. Ordinary decimal numbers round to binary64. Nonzero floating
    tokens that round to zero are rejected. Connectivity is checked by the
    solver, so a structurally valid case need not have a steady solution.
    """
    if not isinstance(text, str):
        raise ValueError("case text must be a string")
    case = _fields(
        json.loads(
            text,
            object_pairs_hook=_object,
            parse_float=_float,
            parse_constant=_constant,
        ),
        {"schema_version", "nodes", "links"},
        set(),
    )
    if type(case["schema_version"]) is not int or case["schema_version"] != 1:
        raise ValueError("unsupported schema_version; expected integer 1")
    for name in ("nodes", "links"):
        if not isinstance(case[name], list):
            raise ValueError(f"{name} must be a JSON array")
    nodes = tuple(
        Node(**_fields(node, {"id"}, {"power_w", "fixed_temperature_k"}))
        for node in case["nodes"]
    )
    links = tuple(
        Link(**_fields(link, {"id", "node_a", "node_b", "conductance_w_k"}, set()))
        for link in case["links"]
    )
    return Network(nodes, links)


def dumps_case(network: Network) -> str:
    """Encode validated network inputs as deterministic version-1 JSON.

    Parameters
    ----------
    network : Network
        Network inputs in SI units.

    Returns
    -------
    str
        Indented JSON ending in a newline, with explicit node defaults. Array
        order and normalized binary64 values survive decoding exactly. Original
        whitespace, numeric spelling, and omitted defaults are not retained.

    Raises
    ------
    ValueError
        The argument is not a Network.
    """
    if not isinstance(network, Network):
        raise ValueError("network must be a Network")
    return (
        json.dumps({"schema_version": 1, **asdict(network)}, indent=2, allow_nan=False)
        + "\n"
    )
