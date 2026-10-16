"""Nominal comparison of network alternatives against common upper limits."""

import csv
import io
import json
from dataclasses import dataclass

from thermalpath.io import dumps_case
from thermalpath.models import Link, Network, Node, _identifier, _scalar
from thermalpath.studies import _bounded, _evaluate


@dataclass(frozen=True)
class NetworkCandidate:
    """Name a link alternative; loads and boundary nodes are supplied once.

    Parameters
    ----------
    name : str
        Nonempty identifier, unique within a comparison.
    links : tuple of Link
        Up to 128 passive links. Lists are copied. Empty/disconnected alternatives
        are allowed and retained if the steady solve fails. Endpoints are checked
        against the common nodes when comparing.
    """

    name: str
    links: tuple[Link, ...]

    def __post_init__(self) -> None:
        _identifier(self.name, "candidate name")
        if (
            not isinstance(self.links, (tuple, list))
            or len(self.links) > 128
            or any(not isinstance(link, Link) for link in self.links)
        ):
            raise ValueError("candidate links must contain at most 128 Link objects")
        object.__setattr__(self, "links", tuple(self.links))


@dataclass(frozen=True)
class TemperatureRequirement:
    """Set a finite positive upper temperature [K] for one common node.

    Parameters
    ----------
    node_id : str
        Existing node identifier, unique among requirements.
    maximum_k : float
        Finite positive upper absolute temperature [K].
    """

    node_id: str
    maximum_k: float

    def __post_init__(self) -> None:
        _identifier(self.node_id, "requirement node_id")
        object.__setattr__(
            self, "maximum_k", _scalar(self.maximum_k, "maximum_k", positive=True)
        )


@dataclass(frozen=True)
class CandidateAssessment:
    """Retain one named alternative and its nominal requirement assessment.

    Attributes
    ----------
    name : str
        Candidate name in original input order.
    status : str
        meets, exceeds, borderline, or failed. These describe only this model
        at the common nominal loads and boundaries.
    margins_k : dict of str to float
        Upper limit minus computed temperature for each required node [K].
        Empty on failure. This is an independent mutable dictionary.
    minimum_margin_k : float or None
        Smallest required-node margin [K], or None on failure.
    error : str
        Retained solver failure message; empty for a successful solve.
    """

    name: str
    status: str
    margins_k: dict[str, float]
    minimum_margin_k: float | None
    error: str


@dataclass(frozen=True)
class NetworkComparison:
    """Keep shared requirements, every alternative and reproducible evidence.

    Attributes
    ----------
    requirements : tuple of TemperatureRequirement
        Common upper limits in input order.
    comparison_tolerance_k : float
        Nonnegative absolute classification band [K], not an error bound.
    assessments : tuple of CandidateAssessment
        All alternatives in input order, including ties and failures. No ranking
        or automatic selection is performed.
    cases_csv : str
        Complete networks, temperatures, link powers, matrix residuals, global
        imbalance and failures in version-1 sweep CSV. Row i corresponds to
        assessments[i]; replay_network_sweep recomputes the solves.
    qualification : str
        Explicit nominal-only interpretation and uncertainty limitation.
    """

    requirements: tuple[TemperatureRequirement, ...]
    comparison_tolerance_k: float
    assessments: tuple[CandidateAssessment, ...]
    cases_csv: str
    qualification: str


def compare_network_candidates(
    nodes: tuple[Node, ...],
    candidates: tuple[NetworkCandidate, ...],
    requirements: tuple[TemperatureRequirement, ...],
    *,
    comparison_tolerance_k: float,
) -> NetworkComparison:
    """Compare bounded link alternatives using identical loads and boundaries.

    Parameters
    ----------
    nodes : tuple of Node
        One to 64 common nodes, including powers [W] and prescribed temperatures
        [K]. Lists are accepted. Alternatives can change only links.
    candidates : tuple of NetworkCandidate
        One to 64 uniquely named alternatives, including identical link sets.
    requirements : tuple of TemperatureRequirement
        One to 64 distinct common-node upper limits. Lists are accepted.
    comparison_tolerance_k : float
        Explicit finite nonnegative classification band [K]. A successful case
        exceeds if any margin is below minus this band; meets if every margin
        is above the band; otherwise borderline. Equality is always borderline.

    Returns
    -------
    NetworkComparison
        Full evidence and all assessments. Failed solves have no margin.

    Raises
    ------
    ValueError
        Malformed shared inputs, duplicate names/requirements, missing endpoints,
        or resource limits. All specifications are checked before solving.
        Solver ValueError failures are retained per candidate; unexpected
        exceptions propagate. No partial comparison is returned.

    Notes
    -----
    The existing steady solver and sweep case-size limit apply. A classification
    band handles chosen decision resolution; it does not bound numerical error,
    input uncertainty or model error. No uncertainty propagation is performed.
    Passing nominal requirements does not establish physical feasibility,
    manufacturability, safety, reliability or superiority on cost/mass.
    """
    common = Network(nodes)
    _bounded(common)
    if not isinstance(candidates, (tuple, list)) or not 1 <= len(candidates) <= 64:
        raise ValueError("candidates must contain one to 64 NetworkCandidate objects")
    if any(not isinstance(item, NetworkCandidate) for item in candidates):
        raise ValueError("candidates must contain NetworkCandidate objects")
    if len({item.name for item in candidates}) != len(candidates):
        raise ValueError("duplicate candidate name")
    if not isinstance(requirements, (tuple, list)) or not 1 <= len(requirements) <= 64:
        raise ValueError(
            "requirements must contain one to 64 TemperatureRequirement objects"
        )
    if any(not isinstance(item, TemperatureRequirement) for item in requirements):
        raise ValueError("requirements must contain TemperatureRequirement objects")
    requirements = tuple(requirements)
    required_ids = {item.node_id for item in requirements}
    if len(required_ids) != len(requirements):
        raise ValueError("duplicate requirement node")
    if not required_ids <= {node.id for node in common.nodes}:
        raise ValueError("requirement node does not exist")
    tolerance = _scalar(comparison_tolerance_k, "comparison_tolerance_k")
    if tolerance < 0:
        raise ValueError("comparison_tolerance_k must be nonnegative")
    cases = [dumps_case(Network(common.nodes, item.links)) for item in candidates]
    if any(len(case) > 32768 for case in cases):
        raise ValueError("case_json exceeds 32768 characters")
    evidence = _evaluate(cases)
    assessments = []
    for candidate, row in zip(
        candidates, csv.DictReader(io.StringIO(evidence)), strict=True
    ):
        margins = {}
        minimum = None
        status = "failed"
        if row["status"] == "ok":
            temperatures = json.loads(row["temperatures_k_json"])
            margins = {
                item.node_id: item.maximum_k - temperatures[item.node_id]
                for item in requirements
            }
            minimum = min(margins.values())
            if minimum < -tolerance:
                status = "exceeds"
            elif minimum > tolerance:
                status = "meets"
            else:
                status = "borderline"
        assessments.append(
            CandidateAssessment(candidate.name, status, margins, minimum, row["error"])
        )
    return NetworkComparison(
        requirements,
        tolerance,
        tuple(assessments),
        evidence,
        "Nominal model comparison only; uncertainty is not evaluated. "
        "No safety bounds or physical validation are established.",
    )
