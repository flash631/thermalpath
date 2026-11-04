"""Boundary, orientation, and numerical-domain tests for the steady solver."""

import numpy as np
import pytest

from thermalpath import Link, Network, Node, solve_steady


@pytest.mark.parametrize("correction", [-1000.0, float("nan"), 2.0, 0.0])
def test_unhelpful_correction_keeps_direct_solution(monkeypatch, correction):
    answers = iter((np.array([306.0]), np.array([correction])))
    monkeypatch.setattr(np.linalg, "solve", lambda a, b: next(answers))
    result = solve_steady(
        Network(
            [Node("a", power_w=10), Node("sink", fixed_temperature_k=300)],
            [Link("path", "a", "sink", 2)],
        )
    )
    assert result.temperatures_k["a"] == 306.0
    assert result.linear_residual_w["a"] == -2.0


def test_correction_failure_keeps_direct_solution(monkeypatch):
    calls = 0

    def solve(matrix, rhs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise np.linalg.LinAlgError("Synthetic correction failure")
        return np.array([305.0])

    monkeypatch.setattr(np.linalg, "solve", solve)
    result = solve_steady(
        Network(
            [Node("a", power_w=10), Node("sink", fixed_temperature_k=300)],
            [Link("path", "a", "sink", 2)],
        )
    )
    assert calls == 2
    assert result.temperatures_k["a"] == 305.0


def test_improving_correction_updates_reported_matrix_residual(monkeypatch):
    answers = iter((np.array([306.0]), np.array([-1.0])))
    monkeypatch.setattr(np.linalg, "solve", lambda a, b: next(answers))
    result = solve_steady(
        Network(
            [Node("a", power_w=10), Node("sink", fixed_temperature_k=300)],
            [Link("path", "a", "sink", 2)],
        )
    )
    assert result.temperatures_k["a"] == 305.0
    assert result.linear_residual_w["a"] == 0.0


@pytest.mark.parametrize("backend", ["dense", "sparse"])
def test_one_node_heating_and_result_order(backend):
    network = Network(
        [Node("heater", power_w=10), Node("sink", fixed_temperature_k=300)],
        [Link("path", "heater", "sink", 2)],
    )
    result = solve_steady(network, backend=backend)
    assert result.temperatures_k == {"heater": 305, "sink": 300}
    assert list(result.temperatures_k) == ["heater", "sink"]
    assert result.link_powers_w == {"path": 10}
    result.temperatures_k["heater"] = 1
    assert solve_steady(network, backend=backend).temperatures_k["heater"] == 305


@pytest.mark.parametrize("power, temperature", [(0, 300), (-20, 290)])
@pytest.mark.parametrize("backend", ["dense", "sparse"])
def test_zero_load_and_extraction(power, temperature, backend):
    result = solve_steady(
        Network(
            [Node("a", power_w=power), Node("b", fixed_temperature_k=300)],
            [Link("ab", "a", "b", 2)],
        ),
        backend=backend,
    )
    assert result.temperatures_k["a"] == temperature
    assert result.link_powers_w["ab"] == power


@pytest.mark.parametrize("backend", ["dense", "sparse"])
def test_parallel_links_and_reversed_orientation(backend):
    result = solve_steady(
        Network(
            [Node("a", power_w=12), Node("b", fixed_temperature_k=300)],
            [Link("forward", "a", "b", 1), Link("reverse", "b", "a", 2)],
        ),
        backend=backend,
    )
    assert result.temperatures_k == {"a": 304, "b": 300}
    assert result.link_powers_w == {"forward": 4, "reverse": -8}


@pytest.mark.parametrize("backend", ["dense", "sparse"])
def test_all_fixed_nodes_and_empty_links(backend):
    nodes = [
        Node("hot", fixed_temperature_k=350),
        Node("cold", fixed_temperature_k=300),
    ]
    result = solve_steady(
        Network(nodes, [Link("bc", "hot", "cold", 2)]), backend=backend
    )
    assert result.temperatures_k == {"hot": 350, "cold": 300}
    assert result.link_powers_w == {"bc": 100}
    assert solve_steady(Network(nodes), backend=backend).link_powers_w == {}


@pytest.mark.parametrize("backend", ["dense", "sparse"])
def test_separate_anchored_networks_are_valid(backend):
    result = solve_steady(
        Network(
            [
                Node("a", power_w=4),
                Node("b", fixed_temperature_k=300),
                Node("c", power_w=-2),
                Node("d", fixed_temperature_k=350),
            ],
            [Link("ab", "a", "b", 2), Link("cd", "c", "d", 1)],
        ),
        backend=backend,
    )
    assert result.temperatures_k == {"a": 302, "b": 300, "c": 348, "d": 350}


@pytest.mark.parametrize(
    "network",
    [
        Network([Node("a")]),
        Network([Node("a", power_w=1)]),
        Network([Node("a"), Node("b")], [Link("ab", "a", "b", 1)]),
        Network([Node("a"), Node("b", fixed_temperature_k=300)]),
        Network(
            [
                Node("a", power_w=1),
                Node("b", power_w=-1),
                Node("fixed", fixed_temperature_k=300),
            ],
            [Link("ab", "a", "b", 1)],
        ),
    ],
)
@pytest.mark.parametrize("backend", ["dense", "sparse"])
def test_unanchored_nodes_rejected_even_with_balanced_loads(network, backend):
    with pytest.raises(ValueError, match="path to a fixed temperature"):
        solve_steady(network, backend=backend)


@pytest.mark.parametrize("bad", [None, {}, [], 1])
@pytest.mark.parametrize("backend", ["dense", "sparse"])
def test_wrong_input_type(bad, backend):
    with pytest.raises(ValueError, match="must be a Network"):
        solve_steady(bad, backend=backend)


@pytest.mark.parametrize("power", [-600, -602, 1e308])
@pytest.mark.parametrize("backend", ["dense", "sparse"])
def test_nonpositive_or_overflowed_temperature(power, backend):
    conductance = 1e-300 if power > 0 else 2
    with pytest.raises(ValueError, match="temperatures must be finite and positive"):
        solve_steady(
            Network(
                [Node("a", power_w=power), Node("b", fixed_temperature_k=300)],
                [Link("ab", "a", "b", conductance)],
            ),
            backend=backend,
        )


@pytest.mark.parametrize(
    "conductance, fixed_temperature",
    [(1e308, 300), (1e-300, 1e-300)],
)
@pytest.mark.parametrize("backend", ["dense", "sparse"])
def test_boundary_term_outside_range(conductance, fixed_temperature, backend):
    with pytest.raises(ValueError, match="system is singular or outside float range"):
        solve_steady(
            Network(
                [Node("a"), Node("b", fixed_temperature_k=fixed_temperature)],
                [Link("ab", "a", "b", conductance)],
            ),
            backend=backend,
        )


@pytest.mark.parametrize("backend", ["dense", "sparse"])
def test_summed_conductance_overflow(backend):
    with pytest.raises(ValueError, match="system is singular or outside float range"):
        solve_steady(
            Network(
                [Node("a"), Node("b", fixed_temperature_k=1e-300)],
                [Link("one", "a", "b", 1e308), Link("two", "a", "b", 1e308)],
            ),
            backend=backend,
        )


@pytest.mark.parametrize("backend", ["dense", "sparse"])
def test_weak_anchor_lost_to_roundoff(backend):
    with pytest.raises(ValueError, match="system is singular or outside float range"):
        solve_steady(
            Network(
                [Node("a"), Node("b"), Node("sink", fixed_temperature_k=300)],
                [Link("ab", "a", "b", 1), Link("bs", "b", "sink", 1e-30)],
            ),
            backend=backend,
        )


@pytest.mark.parametrize(
    "hot, cold, conductance", [(350, 300, 1e308), (2e-100, 1e-100, 1e-300)]
)
@pytest.mark.parametrize("backend", ["dense", "sparse"])
def test_link_power_outside_range(hot, cold, conductance, backend):
    with pytest.raises(ValueError, match="link power is outside float range"):
        solve_steady(
            Network(
                [
                    Node("a", fixed_temperature_k=hot),
                    Node("b", fixed_temperature_k=cold),
                ],
                [Link("ab", "a", "b", conductance)],
            ),
            backend=backend,
        )
