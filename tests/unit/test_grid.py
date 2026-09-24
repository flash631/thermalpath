"""Geometry domains, indexing boundaries and immutable inputs."""

import math
from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from thermalpath import RectangularGrid


@pytest.mark.parametrize("axis", ["x_edges_m", "y_edges_m"])
@pytest.mark.parametrize(
    "edges",
    [
        (),
        (0,),
        (0, 0),
        (1, 0),
        (0, 2, 1),
        "01",
        None,
        {0, 1},
        (0, True),
        (0, "1"),
        (0, float("nan")),
        (0, float("inf")),
        (-1e308, 1e308),
        (1.0, math.nextafter(1.0, math.inf)),
        (0, 5e-324),
    ],
)
def test_invalid_axes(axis, edges):
    inputs = dict(x_edges_m=(0, 1), y_edges_m=(0, 1), thickness_m=1)
    inputs[axis] = edges
    with pytest.raises(ValueError):
        RectangularGrid(**inputs)


@pytest.mark.parametrize("thickness", [0, -1, True, "1", None, math.inf, math.nan])
def test_invalid_thickness(thickness):
    with pytest.raises(ValueError, match="thickness_m"):
        RectangularGrid((0, 1), (0, 1), thickness)


@pytest.mark.parametrize(
    "x,y,t",
    [
        ((0, 1e200), (0, 1e200), 1e-200),  # area overflows
        ((0, 1e-200), (0, 1e-200), 1e200),  # area underflows
        ((0, 1e100), (0, 1e100), 1e200),  # volume overflows
        ((0, 1e-100), (0, 1e-100), 1e-200),  # volume underflows
        ((0, 1e200), (0, 1e-200), 1e200),  # x lateral area overflows
        ((0, 1e-200), (0, 1e200), 1e200),  # y lateral area overflows
        ((0, 1e-200), (0, 1e200), 1e-200),  # x lateral area underflows
        ((0, 1e200), (0, 1e-200), 1e-200),  # y lateral area underflows
        ((-1e308, 0, 1e308), (0, 1e-308), 1),  # domain span overflows
        ((0, 1e154, 2e154), (0, 1e154), 1),  # total area overflows
        ((0, 1e100, 2e100), (0, 1e100), 1e108),  # total volume overflows
    ],
)
def test_unrepresentable_measures(x, y, t):
    with pytest.raises(ValueError):
        RectangularGrid(x, y, t)


def test_inputs_are_copied_and_frozen():
    edges = [0, 1, 3]
    grid = RectangularGrid(edges, [0, 2], 0.5)
    edges[1] = 2
    assert grid.x_edges_m == (0.0, 1.0, 3.0)
    assert grid.y_edges_m == (0.0, 2.0)
    with pytest.raises(FrozenInstanceError):
        grid.thickness_m = 2
    assert grid == RectangularGrid((0, 1, 3), (0, 2), 0.5)


@pytest.mark.parametrize("bad", [-1, 4, 1.0, True, "0", None])
def test_flat_index_validation(bad):
    grid = RectangularGrid((0, 1, 2), (0, 1, 2), 1)
    for method in (
        grid.indices,
        grid.neighbors,
        grid.center_m,
        grid.cell_area_m2,
        grid.cell_volume_m3,
        grid.face_areas_m2,
    ):
        with pytest.raises(ValueError):
            method(bad)


@pytest.mark.parametrize("bad", [-1, 2, 1.0, True, "0", None])
def test_axis_index_validation(bad):
    grid = RectangularGrid((0, 1, 2), (0, 1, 2), 1)
    with pytest.raises(ValueError):
        grid.index(bad, 0)
    with pytest.raises(ValueError):
        grid.index(0, bad)


def test_numpy_integer_indices_and_real_edges():
    grid = RectangularGrid((np.float64(0), np.float64(2)), (0, 1), 1)
    assert grid.index(np.int64(0), np.int64(0)) == 0
    assert grid.indices(np.int64(0)) == (0, 0)
    assert grid.neighbors(np.int64(0)) == (None, None, None, None)


@pytest.mark.parametrize(
    "x,y,expected",
    [
        ((0, 2), (0, 3), [(None, None, None, None)]),
        ((0, 1, 2), (0, 3), [(None, 1, None, None), (0, None, None, None)]),
        ((0, 2), (0, 1, 3), [(None, None, None, 1), (None, None, 0, None)]),
    ],
)
def test_single_cell_row_column(x, y, expected):
    grid = RectangularGrid(x, y, 1)
    assert [grid.neighbors(k) for k in range(grid.cell_count)] == expected


def test_rounded_input_edges_cannot_recover_small_cell():
    with pytest.raises(ValueError, match="width"):
        RectangularGrid((1e16, 1e16 + 1), (0, 1), 1)
