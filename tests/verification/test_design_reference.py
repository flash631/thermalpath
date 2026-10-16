"""Independent rational balances for comparisons with a shared load case."""

import csv
import io
import json
from fractions import Fraction as F

import pytest

from thermalpath import Link, Node
from thermalpath.design import (
    NetworkCandidate,
    TemperatureRequirement,
    compare_network_candidates,
)


@pytest.mark.parametrize("power_a,power_b", [(12, 4), (0, 0), (-2, 3)])
def test_two_unknown_nodes_against_rational_elimination(power_a, power_b):
    # Solve gA*(Ta-300)+gC*(Ta-Tb)=Pa and
    # gB*(Tb-300)+gC*(Tb-Ta)=Pb by hand elimination.
    conductances = [(1, 2, 3), (2, 4, 1), (3, 1, 2), (1, 2, 3)]
    candidates = tuple(
        NetworkCandidate(
            str(i),
            (
                Link("a-s", "a", "sink", ga),
                Link("b-s", "b", "sink", gb),
                Link("a-b", "a", "b", gc),
            ),
        )
        for i, (ga, gb, gc) in enumerate(conductances)
    )
    result = compare_network_candidates(
        (Node("a", power_a), Node("b", power_b), Node("sink", fixed_temperature_k=300)),
        candidates,
        (TemperatureRequirement("a", 304), TemperatureRequirement("b", 302)),
        comparison_tolerance_k=1e-9,
    )
    rows = list(csv.DictReader(io.StringIO(result.cases_csv)))
    for (ga, gb, gc), assessment, row in zip(
        conductances, result.assessments, rows, strict=True
    ):
        determinant = ga * gb + ga * gc + gb * gc
        ta = F(300) + F(power_a * (gb + gc) + power_b * gc, determinant)
        tb = F(300) + F(power_b * (ga + gc) + power_a * gc, determinant)
        expected = {"a": float(ta), "b": float(tb), "sink": 300.0}
        assert json.loads(row["temperatures_k_json"]) == pytest.approx(
            expected, abs=2e-12, rel=0
        )
        margins = {"a": float(304 - ta), "b": float(302 - tb)}
        assert assessment.margins_k == pytest.approx(margins, abs=2e-12, rel=0)
        assert assessment.minimum_margin_k == pytest.approx(
            min(margins.values()), abs=2e-12, rel=0
        )
        exact_minimum = min(F(304) - ta, F(302) - tb)
        band = F.from_float(1e-9)
        expected_status = (
            "exceeds"
            if exact_minimum < -band
            else "meets"
            if exact_minimum > band
            else "borderline"
        )
        assert assessment.status == expected_status
        assert float(row["imbalance_w"]) == pytest.approx(0, abs=2e-12, rel=0)
        assert (
            max(abs(v) for v in json.loads(row["linear_residual_w_json"]).values())
            <= 2e-12
        )
    assert result.assessments[0].margins_k == result.assessments[3].margins_k
