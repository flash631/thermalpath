"""Energy signs, input boundaries, range failures and visible residuals."""

from dataclasses import FrozenInstanceError

import pytest

from thermalpath import Link, Network, Node, solve_transient, transient_energy_balance


def heater():
    return Network(
        (Node("a", power_w=10), Node("bath", fixed_temperature_k=300)),
        (Link("ab", "a", "bath", 2),),
    )


def arguments():
    return dict(
        network=heater(),
        heat_capacities_j_k={"a": 2},
        old_temperatures_k={"a": 300, "bath": 300},
        new_temperatures_k={"a": 302.5, "bath": 300},
        duration_s=1,
    )


def test_exact_heating_step_and_independent_maps():
    args = arguments()
    report = transient_energy_balance(**args)
    assert report.storage_j == {"a": 5}
    assert report.source_j == {"a": 10}
    assert report.boundary_j == {"bath": -5}
    assert report.node_residual_j == {"a": 0}
    assert (report.total_storage_j, report.total_source_j, report.total_boundary_j) == (
        5,
        10,
        -5,
    )
    assert report.imbalance_j == 0
    report.storage_j["a"] = 123
    assert args["heat_capacities_j_k"] == {"a": 2}
    assert report.source_j == {"a": 10}
    with pytest.raises(FrozenInstanceError):
        report.imbalance_j = 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("network", None),
        ("heat_capacities_j_k", {}),
        ("heat_capacities_j_k", {"a": 2, "bath": 1}),
        ("heat_capacities_j_k", {"a": 0}),
        ("old_temperatures_k", {"a": 300}),
        ("new_temperatures_k", {"a": 302, "bath": 300, "extra": 1}),
        ("old_temperatures_k", []),
        ("old_temperatures_k", {"a": 0, "bath": 300}),
        ("new_temperatures_k", {"a": float("nan"), "bath": 300}),
        ("old_temperatures_k", {"a": 300, "bath": 301}),
        ("new_temperatures_k", {"a": 302, "bath": 301}),
        ("duration_s", 0),
        ("duration_s", -1),
        ("duration_s", True),
        ("duration_s", float("inf")),
        ("duration_s", "1"),
        ("powers_w", {}),
        ("powers_w", {"a": False}),
        ("powers_w", {"a": float("inf")}),
    ],
)
def test_invalid_step(field, value):
    args = arguments()
    args[field] = value
    with pytest.raises(ValueError):
        transient_energy_balance(**args)


def test_signed_override_and_arbitrary_snapshot_residual():
    args = arguments()
    args["new_temperatures_k"] = {"a": 299, "bath": 300}
    report = transient_energy_balance(**args, powers_w={"a": -5})
    assert report.storage_j == {"a": -2}
    assert report.source_j == {"a": -5}
    assert report.boundary_j == {"bath": 2}
    assert report.node_residual_j == {"a": -1}
    assert report.imbalance_j == -1


def test_local_residuals_cannot_be_hidden_by_zero_global_sum():
    network = Network((Node("a"), Node("b")), ())
    report = transient_energy_balance(
        network, {"a": 1, "b": 1}, {"a": 300, "b": 300}, {"a": 301, "b": 299}, 1
    )
    assert report.node_residual_j == {"a": -1, "b": 1}
    assert report.imbalance_j == 0


def test_all_fixed_exchange_and_isolated_boundary():
    network = Network(
        tuple(
            Node(name, fixed_temperature_k=t)
            for name, t in [("hot", 310), ("cold", 300), ("alone", 290)]
        ),
        (Link("hc", "hot", "cold", 2),),
    )
    row = {n.id: n.fixed_temperature_k for n in network.nodes}
    report = transient_energy_balance(network, {}, row, row, 3, {})
    assert report.boundary_j == {"hot": 60, "cold": -60, "alone": 0}
    assert report.storage_j == report.source_j == report.node_residual_j == {}
    assert report.total_boundary_j == report.imbalance_j == 0


def test_tiny_heating_lost_in_temperature_is_visible_in_balance():
    network = Network((Node("a", power_w=1e-20),), ())
    result = solve_transient(network, {"a": 1}, {"a": 300}, [0, 1])
    report = transient_energy_balance(network, {"a": 1}, *result.temperatures_k, 1)
    assert report.storage_j["a"] == 0
    assert report.node_residual_j["a"] == report.imbalance_j == 1e-20


def test_direct_imbalance_preserves_small_remainder():
    network = Network((Node("a", power_w=1e16), Node("b", power_w=1)), ())
    report = transient_energy_balance(
        network, {"a": 1e16, "b": 1}, {"a": 300, "b": 300}, {"a": 301, "b": 300}, 1
    )
    assert report.total_source_j - report.total_storage_j == 0
    assert report.imbalance_j == 1


def test_boundary_total_uses_individual_terms():
    network = Network(
        (Node("bath", fixed_temperature_k=301), Node("a"), Node("b"), Node("c")),
        (
            Link("a0", "bath", "a", 1e16),
            Link("b0", "bath", "b", 1),
            Link("c0", "bath", "c", 1e16),
        ),
    )
    row = {"bath": 301, "a": 300, "b": 300, "c": 302}
    report = transient_energy_balance(network, {"a": 1, "b": 1, "c": 1}, row, row, 1)
    assert report.boundary_j == {"bath": 1}
    assert report.total_boundary_j == report.imbalance_j == 1


@pytest.mark.parametrize(
    "capacity,duration,power", [(1e308, 1, 0), (1, 1e308, 10), (1, 1e-300, 1e-300)]
)
def test_product_range_failures(capacity, duration, power):
    network = Network((Node("a", power_w=power),), ())
    with pytest.raises(ValueError, match="outside float range"):
        transient_energy_balance(
            network, {"a": capacity}, {"a": 300}, {"a": 303}, duration
        )


def test_link_power_range_failure():
    network = Network(
        (Node("a"), Node("bath", fixed_temperature_k=300)),
        (Link("ab", "a", "bath", 1e308),),
    )
    with pytest.raises(ValueError, match="outside float range"):
        transient_energy_balance(
            network, {"a": 1}, {"a": 303, "bath": 300}, {"a": 303, "bath": 300}, 1
        )


def test_energy_sum_overflow():
    network = Network((Node("a", power_w=1e308), Node("b", power_w=1e308)), ())
    with pytest.raises(ValueError, match="energy sum"):
        transient_energy_balance(
            network, {"a": 1, "b": 1}, {"a": 300, "b": 300}, {"a": 300, "b": 300}, 1
        )
