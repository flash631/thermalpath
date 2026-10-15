"""Independent raw-bit sampling, exact balances and sample-quantile checks."""

import csv
import io
import json
from fractions import Fraction

import numpy as np
import pytest

from thermalpath import Link, Network, Node
from thermalpath.uncertainty import UniformInput, monte_carlo_network


def linear_percentiles(values):
    """Interpolate sorted values with exact rational weights and abscissae."""
    ordered = sorted(Fraction(value) for value in values)
    output = []
    for numerator in (5, 50, 95):
        position = Fraction((len(ordered) - 1) * numerator, 100)
        index = position.numerator // position.denominator
        weight = position - index
        output.append(
            float(
                (1 - weight) * ordered[index]
                + weight * ordered[min(index + 1, len(ordered) - 1)]
            )
        )
    return tuple(output)


def test_paired_draws_against_raw_pcg64_bits_and_exact_two_node_balances():
    base = Network(
        (
            Node("a", power_w=12),
            Node("b", power_w=4),
            Node("sink", fixed_temperature_k=300),
        ),
        (Link("ab", "a", "b", 2), Link("bs", "b", "sink", 4)),
    )
    inputs = (
        UniformInput("power_w", "a", 8, 12),
        UniformInput("conductance_w_k", "ab", 1, 3),
        UniformInput("fixed_temperature_k", "sink", 290, 310),
    )
    count, seed = 31, 2026
    result = monte_carlo_network(base, inputs, count=count, seed=seed)
    # Independent of Generator.uniform: binary64 uniforms from raw 64-bit words.
    raw = np.random.PCG64(seed).random_raw(count * 3)
    reference_draws = []
    for row in range(count):
        reference_draws.append(
            tuple(
                item.lower
                + (item.upper - item.lower)
                * ((int(raw[row * 3 + column]) >> 11) / 2**53)
                for column, item in enumerate(inputs)
            )
        )
    assert result.samples == tuple(reference_draws)
    reference_temperatures = {"a": [], "b": [], "sink": []}
    for values, row in zip(
        result.samples, csv.DictReader(io.StringIO(result.cases_csv)), strict=True
    ):
        power, conductance, sink = map(Fraction, values)
        tb = sink + (power + 4) / 4
        ta = tb + power / conductance
        exact = {"a": float(ta), "b": float(tb), "sink": float(sink)}
        assert json.loads(row["temperatures_k_json"]) == pytest.approx(
            exact, abs=2e-12, rel=0
        )
        assert json.loads(row["link_powers_w_json"]) == pytest.approx(
            {"ab": float(power), "bs": float(power + 4)}, abs=2e-12, rel=0
        )
        assert abs(float(row["imbalance_w"])) < 2e-12
        assert max(map(abs, json.loads(row["linear_residual_w_json"]).values())) < 2e-12
        for node, value in exact.items():
            reference_temperatures[node].append(value)
    for node, values in reference_temperatures.items():
        assert result.percentiles_k[node] == pytest.approx(
            linear_percentiles(values), abs=2e-12, rel=0
        )
    assert result.failed_count == 0


def test_scalar_population_quantiles_are_not_sample_or_safety_bounds():
    base = Network(
        (Node("body"), Node("sink", fixed_temperature_k=300)),
        (Link("path", "body", "sink", 2),),
    )
    result = monte_carlo_network(
        base, (UniformInput("power_w", "body", 0, 20),), count=4, seed=7
    )
    temperatures = [300 + row[0] / 2 for row in result.samples]
    assert result.percentiles_k["body"] == pytest.approx(
        linear_percentiles(temperatures), abs=2e-12, rel=0
    )
    # Population T is uniform on [300, 310]; finite sample quantiles differ.
    assert result.percentiles_k["body"] != pytest.approx(
        (300.5, 305, 309.5), abs=1e-3, rel=0
    )
    assert result.percentiles_k["body"][-1] < 310
