"""Singular plate classification, summation and diagnostic range guards."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from thermalpath import (
    Convection,
    Link,
    Network,
    Node,
    PlateBalance,
    PlateResult,
    RectangularGrid,
    RectangularHeater,
    solve_plate,
    solve_steady,
)
from thermalpath.plate_diagnostics import _plate_balance


@pytest.mark.parametrize("film", [None, Convection(0, 300)])
@pytest.mark.parametrize("flux", [0, 2, -2])
def test_balanced_unanchored_plate_remains_nonunique(film, flux):
    with pytest.raises(ValueError, match="balanced unanchored.*nonunique"):
        solve_plate(
            RectangularGrid((0, 1, 3), (0, 2), 0.5),
            3,
            face_convection=film,
            edge_flux_w_m2={"west": flux, "east": -flux},
        )


@pytest.mark.parametrize("flux", [-2, 2, 1e-20])
def test_unbalanced_prescribed_flux_has_no_steady_solution(flux):
    with pytest.raises(ValueError, match="incompatible net input") as error:
        solve_plate(
            RectangularGrid((0, 1), (0, 1), 1), 1, edge_flux_w_m2={"east": flux}
        )
    assert repr(-flux) in str(error.value)


@pytest.mark.parametrize("power", [1, 1e-20])
def test_unanchored_heating_is_incompatible_even_when_tiny(power):
    with pytest.raises(ValueError, match="incompatible net input"):
        solve_plate(
            RectangularGrid((0, 1), (0, 1), 1),
            1,
            heaters=[RectangularHeater(0, 1, 0, 1, power)],
            edge_convection={"west": Convection(0, 300)},
        )


def test_balanced_heater_and_flux_still_need_anchor():
    with pytest.raises(ValueError, match="nonunique"):
        solve_plate(
            RectangularGrid((0, 1, 2), (0, 1), 1),
            1,
            heaters=[RectangularHeater(0, 1, 0, 1, 4)],
            edge_flux_w_m2={"east": 4},
        )


def test_net_check_keeps_small_term_lost_in_rounded_cell_load():
    with pytest.raises(ValueError, match="incompatible net input 1.0 W"):
        solve_plate(
            RectangularGrid((0, 1, 2), (0, 1), 1),
            1,
            heaters=[RectangularHeater(0, 1, 0, 1, 1)],
            edge_flux_w_m2={"west": 1e16, "east": -1e16},
        )


def test_unanchored_net_input_overflow():
    with pytest.raises(ValueError, match="net prescribed plate power"):
        solve_plate(
            RectangularGrid((0, 1, 2), (0, 1), 1),
            1,
            edge_flux_w_m2={"west": -1e308, "east": -1e308},
        )


def test_tiny_positive_anchor_can_be_numerically_singular():
    with pytest.raises(ValueError, match="steady system is singular"):
        solve_plate(
            RectangularGrid((0, 1, 2), (0, 1), 1),
            1,
            edge_convection={"west": Convection(1e-30, 300)},
        )


def test_direct_sum_retains_watt_lost_by_rounded_subtotals():
    # Synthetic accounting input: 1e16 W in, 1e16 W out and 1 W returned.
    report = _plate_balance(
        RectangularGrid((0, 1), (0, 1), 1),
        (1e16,),
        [[1e16, -1, 0, 0]],
        [0],
        (0,),
    )
    assert report.heater_input_w - sum(report.edge_outflow_w) == 0
    assert report.imbalance_w == 1
    assert report.cell_residual_w == (1,)
    assert isinstance(report, PlateBalance)
    with pytest.raises(FrozenInstanceError):
        report.imbalance_w = 0


def test_balance_sum_overflow_is_explicit():
    with pytest.raises(ValueError, match="plate balance sum"):
        _plate_balance(
            RectangularGrid((0, 1, 2), (0, 1), 1),
            (1e308, 1e308),
            [[0] * 4, [0] * 4],
            [0, 0],
            (0, 0),
        )


def test_nonfinite_matrix_residual_is_rejected(monkeypatch):
    monkeypatch.setattr(np.linalg, "solve", lambda a, b: np.array([1e308]))
    with pytest.raises(ValueError, match="linear residual is outside float range"):
        solve_steady(
            Network(
                [Node("cell"), Node("bath", fixed_temperature_k=300)],
                [Link("boundary", "cell", "bath", 2)],
            )
        )


def test_fixed_only_network_has_no_unknown_residual():
    result = solve_steady(Network([Node("bath", fixed_temperature_k=300)]))
    assert result.linear_residual_w == {}


def test_older_manual_plate_result_has_no_claimed_diagnostics():
    assert PlateResult((300,), ((0, 0, 0, 0),)).balance is None
