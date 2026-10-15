"""Admission, reproducibility and failure retention for uniform input studies."""

import csv
import io
import json
from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from thermalpath import Link, Network, Node
from thermalpath.studies import replay_network_sweep
from thermalpath.uncertainty import UniformInput, monte_carlo_network


def network():
    return Network(
        (Node("body", power_w=10), Node("sink", fixed_temperature_k=300)),
        (Link("path", "body", "sink", 2),),
    )


def draw(inputs=None, **kwargs):
    if inputs is None:
        inputs = (UniformInput("power_w", "body", 8, 12),)
    return monte_carlo_network(network(), inputs, **{"count": 8, "seed": 0, **kwargs})


@pytest.mark.parametrize(
    "field,target", [("normal", "body"), (None, "body"), ("power_w", "")]
)
def test_invalid_field_or_target(field, target):
    with pytest.raises(ValueError):
        UniformInput(field, target, 0, 1)


@pytest.mark.parametrize(
    "lower,upper",
    [
        (2, 1),
        (-1e308, 1e308),
        (float("nan"), 1),
        (0, float("inf")),
        (True, 2),
        (0, "2"),
    ],
)
def test_invalid_bounds(lower, upper):
    with pytest.raises(ValueError):
        UniformInput("power_w", "body", lower, upper)


@pytest.mark.parametrize(
    "field,target", [("fixed_temperature_k", "sink"), ("conductance_w_k", "path")]
)
@pytest.mark.parametrize("lower", [-1, 0])
def test_positive_support_required(field, target, lower):
    with pytest.raises(ValueError, match="positive"):
        UniformInput(field, target, lower, 1)


def test_uniform_input_immutable_and_normalized():
    item = UniformInput("power_w", "body", -2, 3)
    assert type(item.lower) is type(item.upper) is float
    with pytest.raises(FrozenInstanceError):
        item.upper = 4


@pytest.mark.parametrize(
    "inputs", [(), "uniform", (None,), (UniformInput("power_w", "body", 0, 1),) * 9]
)
def test_invalid_collection(inputs):
    with pytest.raises(ValueError, match="inputs"):
        draw(inputs)


@pytest.mark.parametrize("count", [0, -1, 257, True, 1.0, np.int64(2), None])
def test_invalid_count(count):
    with pytest.raises(ValueError, match="count"):
        draw(count=count)


@pytest.mark.parametrize("seed", [-1, 2**64, True, 1.0, np.int64(2), None])
def test_explicit_bounded_seed(seed):
    with pytest.raises(ValueError, match="seed"):
        draw(seed=seed)


@pytest.mark.parametrize(
    "field,target,match",
    [
        ("power_w", "absent", "exist"),
        ("conductance_w_k", "absent", "exist"),
        ("power_w", "sink", "boundary"),
        ("fixed_temperature_k", "body", "boundary"),
    ],
)
def test_invalid_target(field, target, match):
    with pytest.raises(ValueError, match=match):
        draw((UniformInput(field, target, 1, 2),))


def test_duplicate_target():
    item = UniformInput("power_w", "body", 1, 2)
    with pytest.raises(ValueError, match="duplicate"):
        draw((item, item))


def test_network_limits():
    item = (UniformInput("power_w", "body", 1, 2),)
    for base, match in [
        (None, "Network"),
        (Network(tuple(Node(str(i)) for i in range(65))), "64 nodes"),
    ]:
        with pytest.raises(ValueError, match=match):
            monte_carlo_network(base, item, count=1, seed=1)


def test_same_seed_replay_and_global_rng_untouched():
    np.random.seed(18)
    before = np.random.get_state()
    inputs = [
        UniformInput("power_w", "body", 8, 12),
        UniformInput("conductance_w_k", "path", 1, 3),
    ]
    result = draw(inputs)
    after = np.random.get_state()
    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]
    assert result == draw(inputs)
    assert result.samples != draw(inputs, seed=1).samples
    assert result.inputs == tuple(inputs)
    inputs.clear()
    assert len(result.inputs) == 2
    assert result.bit_generator == "PCG64"
    assert result.distribution == "independent_uniform"
    assert result.percentile_method == "linear"
    assert result.numpy_version == np.__version__
    assert result.count == len(result.samples) == 8
    assert replay_network_sweep(result.cases_csv) == result.cases_csv
    assert network().nodes[0].power_w == 10


def test_constant_single_sample_and_largest_seed():
    result = draw((UniformInput("power_w", "body", 0, 0),), count=1, seed=2**64 - 1)
    assert result.samples == ((0.0,),)
    assert result.percentiles_k == {"body": (300, 300, 300), "sink": (300, 300, 300)}
    assert result.failed_count == 0


def test_maximum_count_and_eight_inputs():
    base = Network(tuple(Node(str(i), fixed_temperature_k=300) for i in range(8)))
    inputs = tuple(
        UniformInput("fixed_temperature_k", str(i), 290, 310) for i in range(8)
    )
    result = monte_carlo_network(base, inputs, count=256, seed=0)
    assert len(result.samples) == 256
    assert all(
        len(row) == 8 and all(290 <= value <= 310 for value in row)
        for row in result.samples
    )
    assert result.failed_count == 0
    assert len(result.percentiles_k) == 8


def test_mixed_failures_retained_without_success_only_percentiles():
    result = draw((UniformInput("power_w", "body", -800, 0),), count=16, seed=2026)
    rows = list(csv.DictReader(io.StringIO(result.cases_csv)))
    failed = [row for row in rows if row["status"] == "failed"]
    assert 0 < len(failed) < 16
    assert result.failed_count == len(failed)
    assert result.percentiles_k == {}
    assert len(rows) == result.count == len(result.samples)
    assert replay_network_sweep(result.cases_csv) == result.cases_csv
    for sample, row in zip(result.samples, rows, strict=True):
        assert json.loads(row["case_json"])["nodes"][0]["power_w"] == sample[0]
        assert (row["status"] == "ok") == (300 + sample[0] / 2 > 0)
    assert all(row["error"] and not row["temperatures_k_json"] for row in failed)


def test_all_failed_unanchored_network_is_preserved():
    result = monte_carlo_network(
        Network((Node("body"),)),
        (UniformInput("power_w", "body", 0, 1),),
        count=3,
        seed=0,
    )
    assert result.failed_count == 3
    assert result.percentiles_k == {}


def test_large_finite_and_narrow_support():
    lower = 1e308
    upper = np.nextafter(lower, np.inf)
    base = Network((Node("sink", fixed_temperature_k=lower),))
    result = monte_carlo_network(
        base,
        (UniformInput("fixed_temperature_k", "sink", lower, upper),),
        count=16,
        seed=0,
    )
    assert all(lower <= row[0] <= upper for row in result.samples)
    assert all(np.isfinite(result.percentiles_k["sink"]))


def test_bad_generator_draw_is_rejected(monkeypatch):
    class BadGenerator:
        def uniform(self, lower, upper, size):
            return np.full(size, np.inf)

    monkeypatch.setattr(np.random, "Generator", lambda _: BadGenerator())
    with pytest.raises(ValueError, match="sample"):
        draw()


def test_unexpected_solver_error_propagates(monkeypatch):
    def broken(_):
        raise RuntimeError("unexpected implementation failure")

    monkeypatch.setattr("thermalpath.studies.solve_steady", broken)
    with pytest.raises(RuntimeError, match="implementation"):
        draw()
