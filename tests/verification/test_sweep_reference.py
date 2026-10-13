"""Independent thermal balances for every case of a frozen parameter product."""

import csv
import io
import json
from fractions import Fraction

import pytest

from thermalpath import Link, Network, Node
from thermalpath.studies import SweepAxis, replay_network_sweep, sweep_network


def test_two_unknown_series_network_against_exact_rational_balances():
    base = Network(
        (Node("a"), Node("b", power_w=3), Node("sink", fixed_temperature_k=300)),
        (Link("ab", "a", "b", 1), Link("bs", "b", "sink", 2)),
    )
    text = sweep_network(
        base,
        (
            SweepAxis("power_w", "a", (-2, 0, 7)),
            SweepAxis("conductance_w_k", "ab", (0.5, 2, 4)),
            SweepAxis("fixed_temperature_k", "sink", (280, 320)),
        ),
    )
    assert replay_network_sweep(text) == text
    rows = list(csv.DictReader(io.StringIO(text)))
    assert len(rows) == 18
    for row in rows:
        case = json.loads(row["case_json"])
        p = Fraction(case["nodes"][0]["power_w"])
        g = Fraction(case["links"][0]["conductance_w_k"])
        boundary = Fraction(case["nodes"][2]["fixed_temperature_k"])
        # Node b sends both loads to the sink; a adds its own P/G rise.
        tb = boundary + (p + 3) / 2
        ta = tb + p / g
        assert row["status"] == "ok"
        assert json.loads(row["temperatures_k_json"]) == pytest.approx(
            {"a": float(ta), "b": float(tb), "sink": float(boundary)}, abs=2e-12, rel=0
        )
        assert json.loads(row["link_powers_w_json"]) == pytest.approx(
            {"ab": float(p), "bs": float(p + 3)}, abs=2e-12, rel=0
        )
        assert max(map(abs, json.loads(row["linear_residual_w_json"]).values())) < 2e-12
        assert abs(float(row["imbalance_w"])) < 2e-12
