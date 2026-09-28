"""Heater input domains, overlap boundaries and arithmetic range failures."""

import math
from dataclasses import FrozenInstanceError

import pytest

from thermalpath import RectangularGrid, RectangularHeater, map_heaters, solve_plate


@pytest.fixture
def grid():
    return RectangularGrid((0, 1, 2), (0, 1, 2), 0.5)


@pytest.mark.parametrize(
    "name", ["x_min_m", "x_max_m", "y_min_m", "y_max_m", "power_w"]
)
@pytest.mark.parametrize("value", [True, "1", None, math.inf, math.nan])
def test_invalid_heater_scalars(name, value):
    arguments = dict(x_min_m=0, x_max_m=1, y_min_m=0, y_max_m=1, power_w=2)
    arguments[name] = value
    with pytest.raises(ValueError, match=name):
        RectangularHeater(**arguments)


@pytest.mark.parametrize(
    "values, message",
    [
        ((1, 1, 0, 1, 1), "width"),
        ((2, 1, 0, 1, 1), "width"),
        ((0, 1, 1, 1, 1), "height"),
        ((0, 1, 2, 1, 1), "height"),
        ((0, 1, 0, 1, -1), "nonnegative"),
        ((-1e308, 1e308, 0, 1, 1), "width"),
        ((0, 1e200, 0, 1e200, 1), "area"),
        ((0, 1e-200, 0, 1e-200, 1), "area"),
    ],
)
def test_invalid_geometry_and_power(values, message):
    with pytest.raises(ValueError, match=message):
        RectangularHeater(*values)


def test_immutable_and_normalized():
    heater = RectangularHeater(0, 1, 0, 1, 2)
    assert type(heater.x_min_m) is float
    assert type(heater.power_w) is float
    with pytest.raises(FrozenInstanceError):
        heater.power_w = 3


@pytest.mark.parametrize("heaters", [None, "heater", b"heater", {}, 2])
def test_invalid_sequence(grid, heaters):
    with pytest.raises(ValueError, match="sequence"):
        map_heaters(grid, heaters)


@pytest.mark.parametrize("heater", [None, {}, 2, (0, 1, 0, 1, 2)])
def test_invalid_heater_member(grid, heater):
    with pytest.raises(ValueError, match="only RectangularHeater"):
        map_heaters(grid, [heater])


def test_invalid_grid():
    with pytest.raises(ValueError, match="RectangularGrid"):
        map_heaters(None, [])


@pytest.mark.parametrize(
    "bounds", [(-1, 1, 0, 1), (0, 3, 0, 1), (0, 1, -1, 1), (0, 1, 0, 3)]
)
@pytest.mark.parametrize("power", [0, 5])
def test_outside_footprint_rejected_without_clipping(grid, bounds, power):
    with pytest.raises(ValueError, match="fully inside"):
        map_heaters(grid, [RectangularHeater(*bounds, power)])


def test_empty_zero_and_aligned_edges(grid):
    assert map_heaters(grid, []) == (0, 0, 0, 0)
    assert map_heaters(grid, [RectangularHeater(0, 2, 0, 2, 0)]) == (0, 0, 0, 0)
    assert map_heaters(grid, [RectangularHeater(1, 2, 1, 2, 7)]) == (0, 0, 0, 7)
    assert map_heaters(grid, [RectangularHeater(0.25, 0.75, 0.25, 0.75, 3)]) == (
        3,
        0,
        0,
        0,
    )


def test_no_heaters_preserves_existing_solution(grid):
    reference = solve_plate(grid, 3, east_k=300)
    assert solve_plate(grid, 3, east_k=300, heaters=[]) == reference
    assert (
        solve_plate(grid, 3, east_k=300, heaters=[RectangularHeater(0, 2, 0, 2, 0)])
        == reference
    )


def test_heating_does_not_supply_a_temperature_anchor(grid):
    with pytest.raises(ValueError, match="anchor"):
        solve_plate(grid, 3, heaters=[RectangularHeater(0, 2, 0, 2, 5)])


def test_positive_mapped_power_cannot_disappear(grid):
    with pytest.raises(ValueError, match="mapped power"):
        map_heaters(grid, [RectangularHeater(0, 2, 0, 2, 5e-324)])


def test_sum_overflow_rejected(grid):
    heater = RectangularHeater(0, 1, 0, 1, 1e308)
    with pytest.raises(ValueError, match="summed heater power"):
        map_heaters(grid, [heater, heater])


def test_heater_and_edge_input_overflow_rejected():
    grid = RectangularGrid((0, 1), (0, 1), 1)
    with pytest.raises(ValueError, match="summed flux"):
        solve_plate(
            grid,
            1,
            east_k=300,
            edge_flux_w_m2={"west": -1e308},
            heaters=[RectangularHeater(0, 1, 0, 1, 1e308)],
        )


def test_tiny_heat_survives_mapping_when_temperature_rounds_away():
    grid = RectangularGrid((0, 1), (0, 1), 1)
    heaters = [RectangularHeater(0, 1, 0, 1, 1e-20)]
    assert map_heaters(grid, heaters) == (1e-20,)
    result = solve_plate(grid, 1, east_k=300, heaters=heaters)
    assert result.temperatures_k == (300,)
    assert math.fsum(result.face_powers_w[0]) == 0
