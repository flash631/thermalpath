"""Exercise the real worksheet with Streamlit's simulated UI."""

from fractions import Fraction
from itertools import product
from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from app.network_app import make_network
from thermalpath.diagnostics import heat_balance
from thermalpath.models import Link, Network, Node
from thermalpath.networks import solve_steady

APP = Path(__file__).resolve().parents[2] / "app" / "network_app.py"
ABS_TOL = 2e-10


def worksheet() -> AppTest:
    """Start the actual app without a browser or external server."""
    app = AppTest.from_file(str(APP), default_timeout=10).run()
    assert not app.exception
    return app


def submit(app: AppTest, power: float, sink: float, contact: float, path: float):
    """Apply all four form values as one submitted case."""
    for widget, value in zip(
        app.number_input, (power, contact, sink, path), strict=True
    ):
        widget.set_value(value)
    return app.button[0].click().run()


@pytest.mark.parametrize(
    "power,sink,contact,path",
    [(10.0, 300.0, 5.0, 2.0), (0.0, 275.0, 0.1, 100.0), (37.5, 310.0, 2.5, 0.5)]
    + list(product((0.0, 1000.0), (1.0, 1000.0), (0.1, 100.0), (0.1, 100.0))),
)
def test_submitted_results_match_direct_library_and_rational_reference(
    power, sink, contact, path
):
    app = submit(worksheet(), power, sink, contact, path)
    assert not app.exception and not app.error
    # Construct independently of the app adapter to catch input-wiring errors.
    network = Network(
        (
            Node("heater", power_w=power),
            Node("spreader"),
            Node("sink", fixed_temperature_k=sink),
        ),
        (
            Link("contact", "heater", "spreader", contact),
            Link("sink_path", "spreader", "sink", path),
        ),
    )
    direct = solve_steady(network)
    balance = heat_balance(network, direct.link_powers_w)
    temperatures = app.table[0].value.set_index("Node")["Temperature [K]"].to_dict()
    powers = app.table[1].value.set_index("Link")["Power toward sink [W]"].to_dict()
    assert temperatures == direct.temperatures_k
    assert powers == direct.link_powers_w
    p, b, gc, gs = map(Fraction, (power, sink, contact, path))
    assert temperatures == pytest.approx(
        {
            "heater": float(b + p / gs + p / gc),
            "spreader": float(b + p / gs),
            "sink": sink,
        },
        abs=ABS_TOL,
        rel=0,
    )
    assert powers == pytest.approx(
        {"contact": power, "sink_path": power}, abs=ABS_TOL, rel=0
    )
    assert app.metric[0].value == f"{direct.temperatures_k['heater']:.3f} K"
    text = "\n".join(element.value for element in app.markdown)
    assert f"Sink reservoir input: {balance.boundary_power_w['sink']:.6g} W" in text
    assert f"Global heat imbalance: {balance.imbalance_w:.6g} W" in text
    assert "do not establish physical accuracy or device safety" in text


def test_unsubmitted_edits_and_reruns_keep_last_submitted_case():
    app = worksheet()
    assert app.metric[0].value == "307.000 K"
    app.number_input[0].set_value(20.0).run()
    assert app.metric[0].value == "307.000 K"
    # AppTest discards unsubmitted form edits on run; submit the edit again.
    submit(app, 20.0, 300.0, 5.0, 2.0)
    assert app.metric[0].value == "314.000 K"
    app.number_input[2].set_value(400.0).run()
    assert app.metric[0].value == "314.000 K"
    submit(app, 20.0, 400.0, 5.0, 2.0)
    assert app.metric[0].value == "414.000 K"


@pytest.mark.parametrize(
    "index,label",
    [
        (0, "Heater power"),
        (1, "Sink temperature"),
        (2, "Heater to spreader"),
        (3, "Spreader to sink"),
    ],
)
@pytest.mark.parametrize(
    "value", [float("nan"), float("inf"), -float("inf"), -1.0, 1001.0]
)
def test_adapter_rejects_invalid_values_with_input_specific_message(
    index, label, value
):
    values = [10.0, 300.0, 5.0, 2.0]
    values[index] = value
    with pytest.raises(ValueError, match=label + ".*must be finite and between"):
        make_network(*values)


@pytest.mark.parametrize(
    "values,label",
    [
        ((1001.0, 300.0, 5.0, 2.0), "Heater power"),
        ((10.0, 0.0, 5.0, 2.0), "Sink temperature"),
        ((10.0, 300.0, 0.0, 2.0), "Heater to spreader"),
        ((10.0, 300.0, 5.0, 101.0), "Spreader to sink"),
    ],
)
def test_invalid_submitted_state_skips_solver_and_recovery_clears_error(values, label):
    app = worksheet()
    # Bypass widget sanitization to exercise the server's independent guard.
    app.session_state["submitted_inputs"] = values
    with patch("thermalpath.networks.solve_steady") as solver:
        app.run()
        solver.assert_not_called()
    assert not app.exception
    assert label in app.error[0].value
    assert not app.metric and not app.table
    submit(app, 20.0, 300.0, 5.0, 2.0)
    assert not app.error and not app.exception
    assert app.metric[0].value == "314.000 K"


def test_solver_error_is_visible_without_stale_results_and_recovers():
    app = worksheet()
    with patch(
        "thermalpath.networks.solve_steady",
        side_effect=ValueError("Synthetic solve failure"),
    ):
        app.button[0].click().run()
    assert not app.exception
    assert app.error[0].value == "The case could not be solved: Synthetic solve failure"
    assert not app.metric and not app.table
    app.button[0].click().run()
    assert not app.error and not app.exception
    assert app.metric[0].value == "307.000 K"


def test_fixed_resource_size_and_widget_bounds():
    with patch("thermalpath.networks.solve_steady", wraps=solve_steady) as solver:
        app = worksheet()
        assert solver.call_count == 1
        submit(app, 1000.0, 1000.0, 0.1, 0.1)
        assert solver.call_count == 2
        for call in solver.call_args_list:
            network = call.args[0]
            assert len(network.nodes) == 3 and len(network.links) == 2
    assert [(w.min, w.max) for w in app.number_input] == [
        (0.0, 1000.0),
        (0.1, 100.0),
        (1.0, 1000.0),
        (0.1, 100.0),
    ]
    assert len(app.button) == 1
    assert "no grid cells or random samples" in " ".join(c.value for c in app.caption)


def test_separate_sessions_do_not_share_submitted_inputs():
    first = submit(worksheet(), 20.0, 300.0, 5.0, 2.0)
    second = worksheet()
    assert first.metric[0].value == "314.000 K"
    assert second.metric[0].value == "307.000 K"
