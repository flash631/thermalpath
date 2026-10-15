"""Bounded independent uniform inputs for constant-conductance networks."""

import csv
import io
import json
import math
from dataclasses import dataclass

import numpy as np

from thermalpath.io import dumps_case
from thermalpath.models import Network, _scalar
from thermalpath.studies import SweepAxis, _bounded, _evaluate, _json


@dataclass(frozen=True)
class UniformInput:
    """Specify one independent uniform input in its network field's SI unit.

    Parameters
    ----------
    field, target_id : str
        power_w [W] for an unknown node, fixed_temperature_k [K] for a fixed
        node, or conductance_w_k [W/K] for a link. Boundary types stay fixed.
    lower, upper : float
        Finite ordered bounds with finite difference. Equal bounds specify a
        constant. Temperature and conductance lower bounds must be positive.
        Negative power is permitted; a resulting nonpositive temperature is a
        failed case, not a reason to redraw. Floats can include either endpoint.

    Raises
    ------
    ValueError
        The field, identifier, bounds or physical input domain is invalid.
    """

    field: str
    target_id: str
    lower: float
    upper: float

    def __post_init__(self) -> None:
        SweepAxis(self.field, self.target_id, (0,))
        positive = self.field != "power_w"
        lower = _scalar(self.lower, "lower", positive=positive)
        upper = _scalar(self.upper, "upper", positive=positive)
        if lower > upper or not math.isfinite(upper - lower):
            raise ValueError("bounds must be ordered with a finite difference")
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)


@dataclass(frozen=True)
class NetworkMonteCarlo:
    """Keep sampling metadata, every input/case and conditional percentiles.

    Attributes
    ----------
    inputs : tuple of UniformInput
        Ordered independent uniform specifications; no correlation model.
    distribution : str
        independent_uniform, including any constant inputs.
    seed, count : int
        Explicit seed and requested number of cases, including failed cases.
    bit_generator, numpy_version : str
        PCG64 and the NumPy version used to generate the samples.
    samples : tuple of tuple of float
        Row-major sampled values, with columns in inputs order. These and the
        full cases_csv are the replay evidence if a random stream changes.
    cases_csv : str
        Version-1 sweep CSV with complete SI inputs, results and failures.
        Recompute with replay_network_sweep; no random sampling is needed.
    failed_count : int
        Number of failed cases. Cases are never removed or replaced.
    percentile_levels : tuple of float
        Fixed levels (5, 50, 95), in percent, using linear sample interpolation.
    percentile_method : str
        linear, recorded explicitly for serialized results.
    percentiles_k : dict of str to tuple of float
        Per-node P5/P50/P95 in kelvin. Empty if any case failed. Conditional on
        the specified model/distributions; not confidence or safety bounds.
        The dictionary is an independent mutable copy.
    """

    inputs: tuple[UniformInput, ...]
    distribution: str
    seed: int
    count: int
    bit_generator: str
    numpy_version: str
    samples: tuple[tuple[float, ...], ...]
    cases_csv: str
    failed_count: int
    percentile_levels: tuple[float, ...]
    percentile_method: str
    percentiles_k: dict[str, tuple[float, ...]]


def monte_carlo_network(
    network: Network,
    inputs: tuple[UniformInput, ...],
    *,
    count: int,
    seed: int,
) -> NetworkMonteCarlo:
    """Draw paired independent inputs and evaluate every sampled network.

    Parameters
    ----------
    network : Network
        Base topology, at most 64 nodes and 128 links. Unspecified fields keep
        their base values. Each full case must fit the sweep CSV size limit.
    inputs : tuple of UniformInput
        Tuple or list of one to eight distinct (field, target_id) inputs.
        Only independent uniform distributions are supported, including
        constants. No fitting, truncation, correlations or rejection sampling.
    count : int
        One to 256 cases. Each row pairs one draw from every input; this is
        not a Cartesian product. Bool and non-Python-int values are rejected.
    seed : int
        Explicit Python integer from 0 through 2**64-1; bool is rejected.

    Returns
    -------
    NetworkMonteCarlo
        Sampling evidence and linear sample P5/P50/P95 for every node if all
        cases succeeded. Any failure suppresses the entire percentile map.

    Raises
    ------
    ValueError
        Invalid specification/target, resource limit, or nonfinite/out-of-bound
        draw. Solver ValueError failures remain in cases_csv; other errors
        propagate. No partial study is returned for a specification error.

    Notes
    -----
    Uses a local Generator(PCG64(seed)) and one uniform call of shape
    (count, len(inputs)), including constant columns. Global random state is
    untouched. Stream reproduction requires the same inputs, ordering, count,
    call pattern and compatible NumPy environment; seed alone is insufficient.
    Full sampled cases support replay without a stream-compatibility claim.
    Finite samples do not certify extrema, failure probabilities, model
    accuracy or physical validity. Even a one-case study has percentiles but
    contains no evidence about distribution tails.
    """
    if not isinstance(network, Network):
        raise ValueError("network must be a Network")
    _bounded(network)
    if not isinstance(inputs, (tuple, list)) or not 1 <= len(inputs) <= 8:
        raise ValueError("inputs must contain one to eight UniformInput objects")
    if any(not isinstance(item, UniformInput) for item in inputs):
        raise ValueError("inputs must contain UniformInput objects")
    inputs = tuple(inputs)
    if len({(item.field, item.target_id) for item in inputs}) != len(inputs):
        raise ValueError("duplicate uncertain target")
    if type(count) is not int or not 1 <= count <= 256:
        raise ValueError("count must be an integer from 1 to 256")
    if type(seed) is not int or not 0 <= seed < 2**64:
        raise ValueError("seed must be an integer from 0 through 2**64-1")
    base = json.loads(dumps_case(network))
    targets = []
    for item in inputs:
        group = "links" if item.field == "conductance_w_k" else "nodes"
        matches = {entry["id"]: i for i, entry in enumerate(base[group])}
        if item.target_id not in matches:
            raise ValueError("uncertain target does not exist")
        index = matches[item.target_id]
        if group == "nodes" and (
            base[group][index]["fixed_temperature_k"] is not None
        ) != (item.field == "fixed_temperature_k"):
            raise ValueError("uncertain input must preserve the node boundary type")
        targets.append((group, index, item.field))
    lower = np.array([item.lower for item in inputs])
    upper = np.array([item.upper for item in inputs])
    rng = np.random.Generator(np.random.PCG64(seed))
    values = rng.uniform(lower, upper, size=(count, len(inputs)))
    if not np.all(np.isfinite(values) & (values >= lower) & (values <= upper)):
        raise ValueError("sample exceeds its finite bounds")
    samples = tuple(tuple(float(value) for value in row) for row in values)
    cases = []
    for row in samples:
        for (group, index, field), value in zip(targets, row, strict=True):
            base[group][index][field] = value
        cases.append(_json(base))
    evidence = _evaluate(cases)
    rows = list(csv.DictReader(io.StringIO(evidence)))
    failed = sum(row["status"] != "ok" for row in rows)
    levels = (5.0, 50.0, 95.0)
    percentiles = {}
    if not failed:
        temperatures = [json.loads(row["temperatures_k_json"]) for row in rows]
        percentiles = {
            node.id: tuple(
                float(value)
                for value in np.percentile(
                    [row[node.id] for row in temperatures], levels, method="linear"
                )
            )
            for node in network.nodes
        }
    return NetworkMonteCarlo(
        inputs,
        "independent_uniform",
        seed,
        count,
        "PCG64",
        np.__version__,
        samples,
        evidence,
        failed,
        levels,
        "linear",
        percentiles,
    )
