"""Local temperature derivatives for bounded constant-conductance networks."""

import csv
import io
import json
import math
from dataclasses import dataclass

from thermalpath.io import dumps_case
from thermalpath.models import Network, _scalar
from thermalpath.studies import SweepAxis, sweep_network


@dataclass(frozen=True)
class SensitivityEstimate:
    """Keep one requested step, its evidence, and any numerical failure.

    Attributes
    ----------
    step : float
        Requested positive perturbation in the parameter's SI unit.
    lower_value, upper_value : float
        Actual rounded parameter values, in the same unit.
    status, error : str
        Status is 'ok' or 'failed'; error explains a failed estimate.
    dimensional : dict of str to float
        Temperature derivative for each node, in K per parameter unit.
        Empty on failure.
    scaled : dict of str to float
        Dimensionless (parameter_value / baseline_temperature_k) * dimensional.
        Uses absolute kelvin, including fixed nodes. Empty on failure.
    cases_csv : str
        Complete lower/upper inputs and solver diagnostics in sweep CSV format.
        Empty if the rounded perturbations cannot be represented safely.
    """

    step: float
    lower_value: float
    upper_value: float
    status: str
    error: str
    dimensional: dict[str, float]
    scaled: dict[str, float]
    cases_csv: str


@dataclass(frozen=True)
class NetworkSensitivity:
    """Report one parameter's local temperature sensitivity and retained cases.

    Attributes
    ----------
    field, target_id : str
        Network field and existing node/link ID that was perturbed.
    parameter_value : float
        Baseline value in parameter_unit.
    parameter_unit : str
        W, K, or W/K. Dimensional derivatives have units K/parameter_unit.
    base_case_csv : str
        Complete baseline input, temperatures, linear residual and heat balance.
    estimates : tuple of SensitivityEstimate
        Requested order, including failed estimates. No estimate is selected
        automatically. Result dictionaries are independent mutable copies.
    """

    field: str
    target_id: str
    parameter_value: float
    parameter_unit: str
    base_case_csv: str
    estimates: tuple[SensitivityEstimate, ...]


def _rows(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def network_sensitivity(
    network: Network, field: str, target_id: str, steps: tuple[float, ...]
) -> NetworkSensitivity:
    """Estimate temperature derivatives with a two-sided quadratic stencil.

    Parameters
    ----------
    network : Network
        Baseline admitted by sweep_network (64 nodes, 128 links at most).
        Its steady solution must exist and have positive finite temperatures.
    field : str
        power_w for an unknown node, fixed_temperature_k for a fixed node,
        or conductance_w_k for a link. Topology and boundary types stay fixed.
    target_id : str
        Existing target ID in the corresponding namespace.
    steps : tuple of float
        Tuple or list of 3 to 16 distinct finite positive absolute steps in
        the parameter's SI unit. Order is preserved. No automatic step tuning.

    Returns
    -------
    NetworkSensitivity
        Derivatives at the baseline using actual rounded lower/upper values.
        Invalid physical perturbations or nonfinite derivative arithmetic
        produce failed estimates, with empty derivative maps and an error.

    Raises
    ------
    ValueError
        Invalid specification, target, resource bound or baseline solution.
        Unexpected internal exceptions propagate.

    Notes
    -----
    With hm = p0 - lower and hp = upper - p0, the derivative is
    hm/(hm+hp)*(Tupper-T0)/hp + hp/(hm+hp)*(T0-Tlower)/hm.
    Taylor expansion gives leading truncation error hm*hp*T'''/6 for a
    smooth solution. Roundoff and cancellation grow for small steps; 'ok'
    means the stencil was evaluated, not that accuracy has been certified.
    Both perturbed cases must be valid; there is no one-sided fallback.
    Scaled values use absolute kelvin and are zero when p0 is zero, even
    when the dimensional derivative is nonzero. This is not physical validation.
    """
    SweepAxis(field, target_id, (0,))
    if not isinstance(steps, (tuple, list)) or not 3 <= len(steps) <= 16:
        raise ValueError("steps must contain 3 to 16 entries")
    sizes = tuple(_scalar(h, "step", positive=True) for h in steps)
    if len(set(sizes)) != len(sizes):
        raise ValueError("steps must be distinct")
    base_csv = sweep_network(network, ())
    group = "links" if field == "conductance_w_k" else "nodes"
    targets = {item["id"]: item for item in json.loads(dumps_case(network))[group]}
    if target_id not in targets:
        raise ValueError("sensitivity target does not exist")
    target = targets[target_id]
    if group == "nodes" and (target["fixed_temperature_k"] is not None) != (
        field == "fixed_temperature_k"
    ):
        raise ValueError("sensitivity must preserve the node boundary type")
    value = target[field]
    base = _rows(base_csv)[0]
    if base["status"] != "ok":
        raise ValueError("invalid sensitivity baseline: " + base["error"])
    temperatures = json.loads(base["temperatures_k_json"])
    estimates = []
    for step in sizes:
        lower, upper = value - step, value + step
        hm, hp = value - lower, upper - value
        evidence = ""
        dimensional, scaled = {}, {}
        try:
            if not (
                math.isfinite(lower)
                and math.isfinite(upper)
                and lower < value < upper
                and math.isfinite(hm + hp)
            ):
                raise ValueError("perturbations collapse or exceed the finite range")
            evidence = sweep_network(
                network, (SweepAxis(field, target_id, (lower, upper)),)
            )
            rows = _rows(evidence)
            failures = [row["error"] for row in rows if row["status"] != "ok"]
            if failures:
                raise ValueError("invalid two-sided stencil: " + "; ".join(failures))
            below, above = [json.loads(row["temperatures_k_json"]) for row in rows]
            for node, temperature in temperatures.items():
                derivative = (hm / (hm + hp)) * ((above[node] - temperature) / hp) + (
                    hp / (hm + hp)
                ) * ((temperature - below[node]) / hm)
                relative = (value / temperature) * derivative
                if not math.isfinite(derivative) or not math.isfinite(relative):
                    raise ValueError("sensitivity arithmetic exceeds the finite range")
                dimensional[node], scaled[node] = derivative, relative
        except ValueError as exc:
            status, error = "failed", str(exc)
            dimensional, scaled = {}, {}
        else:
            status, error = "ok", ""
        estimates.append(
            SensitivityEstimate(
                step, lower, upper, status, error, dimensional, scaled, evidence
            )
        )
    return NetworkSensitivity(
        field,
        target_id,
        value,
        {"power_w": "W", "fixed_temperature_k": "K", "conductance_w_k": "W/K"}[field],
        base_csv,
        tuple(estimates),
    )
