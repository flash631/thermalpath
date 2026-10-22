"""Independent arithmetic checks for the worksheet's library input mapping."""

from fractions import Fraction

import pytest

from app.network_app import make_network
from thermalpath.diagnostics import heat_balance
from thermalpath.networks import solve_steady


@pytest.mark.parametrize(
    "power,sink,contact,path",
    [(10, 300, 5, 2), (0, 300, 5, 2), (12, 310, 3, 4), (1000, 1, 1, 100)],
)
def test_submitted_values_match_independent_series_reference(
    power, sink, contact, path
):
    """Check every temperature, oriented power and reservoir sign independently."""
    network = make_network(power, sink, contact, path)
    result = solve_steady(network)
    spreader = Fraction(sink) + Fraction(power, path)
    heater = spreader + Fraction(power, contact)
    assert result.temperatures_k == pytest.approx(
        {"heater": float(heater), "spreader": float(spreader), "sink": sink},
        abs=2e-10,
        rel=0,
    )
    assert result.link_powers_w == pytest.approx(
        {"contact": power, "sink_path": power}, abs=2e-10, rel=0
    )
    balance = heat_balance(network, result.link_powers_w)
    assert balance.boundary_power_w["sink"] == pytest.approx(-power, abs=2e-10, rel=0)
    assert abs(balance.imbalance_w) <= 2e-10
    assert max(abs(v) for v in result.linear_residual_w.values()) <= 2e-10


@pytest.mark.parametrize("values", [(10, 0, 5, 2), (10, 300, 0, 2), (10, 300, 5, -2)])
def test_mapping_preserves_library_domain_checks(values):
    """The adapter does not bypass positive temperature/conductance validation."""
    with pytest.raises(ValueError):
        make_network(*values)
