"""Local Streamlit worksheet for a steady heater-to-sink network."""

import math

import streamlit as st

from thermalpath.diagnostics import heat_balance
from thermalpath.models import Link, Network, Node
from thermalpath.networks import solve_steady


def make_network(
    power_w: float,
    sink_temperature_k: float,
    contact_conductance_w_k: float,
    sink_conductance_w_k: float,
) -> Network:
    """Map worksheet inputs to the existing validated network model.

    Parameters
    ----------
    power_w : float
        Heater input [W], positive into the network.
    sink_temperature_k : float
        Prescribed sink temperature [K].
    contact_conductance_w_k, sink_conductance_w_k : float
        Constant positive link conductances [W/K].

    Returns
    -------
    Network
        Heater, unloaded spreader and fixed sink joined in that order.

    Raises
    ------
    ValueError
        An input is nonfinite or outside the worksheet's inclusive range.
    """
    for label, value, lower, upper, unit in (
        ("Heater power", power_w, 0.0, 1000.0, "W"),
        ("Sink temperature", sink_temperature_k, 1.0, 1000.0, "K"),
        ("Heater to spreader conductance", contact_conductance_w_k, 0.1, 100.0, "W/K"),
        ("Spreader to sink conductance", sink_conductance_w_k, 0.1, 100.0, "W/K"),
    ):
        if not math.isfinite(value) or not lower <= value <= upper:
            raise ValueError(
                f"{label} must be finite and between {lower:g} and {upper:g} {unit}."
            )
    return Network(
        (
            Node("heater", power_w=power_w),
            Node("spreader"),
            Node("sink", fixed_temperature_k=sink_temperature_k),
        ),
        (
            Link("contact", "heater", "spreader", contact_conductance_w_k),
            Link("sink_path", "spreader", "sink", sink_conductance_w_k),
        ),
    )


def main() -> None:
    """Render controls and display only results returned by the library."""
    st.set_page_config(page_title="ThermalPath | Steady heat path", layout="centered")
    st.title("Steady heat path")
    st.caption("THERMALPATH · LOCAL NETWORK WORKSHEET")
    st.write(
        "Explore how heat moves from a heater through a spreader to a sink held "
        "at a fixed temperature. Each node has one uniform temperature."
    )
    st.code("Heater  →  Spreader  →  Fixed-temperature sink", language=None)
    with st.form("network_inputs"):
        st.subheader("Inputs")
        left, right = st.columns(2)
        with left:
            power = st.number_input("Heater power [W]", 0.0, 1000.0, 10.0, step=1.0)
            contact = st.number_input(
                "Heater → spreader conductance [W/K]",
                0.1,
                100.0,
                5.0,
                step=0.1,
            )
        with right:
            sink = st.number_input("Sink temperature [K]", 1.0, 1000.0, 300.0, step=1.0)
            sink_path = st.number_input(
                "Spreader → sink conductance [W/K]",
                0.1,
                100.0,
                2.0,
                step=0.1,
            )
        submitted = st.form_submit_button("Calculate temperatures", type="primary")
    if "submitted_inputs" not in st.session_state:
        st.session_state["submitted_inputs"] = (10.0, 300.0, 5.0, 2.0)
    if submitted:
        st.session_state["submitted_inputs"] = (power, sink, contact, sink_path)
    power, sink, contact, sink_path = st.session_state["submitted_inputs"]
    st.caption(
        "Results use the default or last submitted inputs. "
        "Press Calculate temperatures to apply edits."
    )
    st.caption(
        "One case per calculation: three nodes, two links, no grid cells or random "
        "samples. Allowed inputs: 0–1000 W, 1–1000 K, and 0.1–100 W/K."
    )
    st.subheader("Submitted case")
    st.write(
        f"Heater: {power:g} W · Sink: {sink:g} K · "
        f"Conductances: {contact:g} and {sink_path:g} W/K"
    )
    try:
        network = make_network(power, sink, contact, sink_path)
        result = solve_steady(network)
        balance = heat_balance(network, result.link_powers_w)
    except ValueError as exc:
        st.error(f"The case could not be solved: {exc}")
        return
    st.metric("Heater temperature", f"{result.temperatures_k['heater']:.3f} K")
    st.table(
        [
            {"Node": node, "Temperature [K]": temperature}
            for node, temperature in result.temperatures_k.items()
        ]
    )
    st.subheader("Heat accounting")
    st.table(
        [
            {"Link": link, "Power toward sink [W]": power_w}
            for link, power_w in result.link_powers_w.items()
        ]
    )
    st.write(f"Sink reservoir input: {balance.boundary_power_w['sink']:.6g} W")
    st.caption("A negative reservoir input means heat leaves the network at the sink.")
    st.write(f"Global heat imbalance: {balance.imbalance_w:.6g} W")
    st.write(
        "Largest absolute matrix residual: "
        f"{max(abs(v) for v in result.linear_residual_w.values()):.6g} W"
    )
    st.subheader("Model limits")
    st.write(
        "Steady state with constant conductances and an ideal fixed-temperature "
        "sink. There is no heat storage, spatial temperature field, radiation, "
        "or temperature-dependent material behavior."
    )
    st.write(
        "Inputs are illustrative. Their control ranges are interface limits, "
        "not material ratings. Small residuals check numerical balance; they "
        "do not establish physical accuracy or device safety."
    )


if __name__ == "__main__":
    main()
