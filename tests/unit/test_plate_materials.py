"""Cell conductivity domains, uniform compatibility and arithmetic limits."""

import pytest

from thermalpath import RectangularGrid, solve_plate


@pytest.mark.parametrize(
    "values",
    [
        [],
        [2],
        [2, 3, 4],
        [[2], [3]],
        [True, 3],
        [2, "3"],
        [2, None],
        [0, 3],
        [2, -3],
        [2, float("inf")],
        [float("nan"), 3],
        {0: 2, 1: 3},
    ],
)
def test_invalid_cell_conductivities(values):
    grid = RectangularGrid((0, 1, 3), (0, 1), 1)
    with pytest.raises(ValueError, match="conductivity"):
        solve_plate(grid, values, west_k=300)


@pytest.mark.parametrize("container", [list, tuple])
def test_uniform_sequence_matches_scalar_exactly(container):
    grid = RectangularGrid((0, 1, 3), (0, 2, 3), 0.5)
    boundaries = dict(west_k=300, east_k=360, south_k=280, north_k=340)
    values = container([6] * 4)
    assert solve_plate(grid, values, **boundaries) == solve_plate(grid, 6, **boundaries)
    assert values == container([6] * 4)


def test_single_cell_sequence():
    grid = RectangularGrid((0, 2), (0, 1), 0.5)
    assert solve_plate(grid, [4], west_k=300, east_k=320) == solve_plate(
        grid, 4, west_k=300, east_k=320
    )


@pytest.mark.parametrize("side", ["west_k", "east_k", "south_k", "north_k"])
def test_heterogeneous_constant_field(side):
    grid = RectangularGrid((0, 1, 3), (0, 2, 3), 0.5)
    result = solve_plate(grid, (2, 4, 8, 16), **{side: 321})
    assert result.temperatures_k == pytest.approx([321] * 4, rel=0, abs=2e-12)
    for powers in result.face_powers_w:
        assert powers == pytest.approx([0] * 4, rel=0, abs=2e-10)


def test_heterogeneous_all_insulated_is_nonunique():
    with pytest.raises(ValueError, match="at least one fixed"):
        solve_plate(RectangularGrid((0, 1, 3), (0, 1), 1), [2, 3])


@pytest.mark.parametrize(
    "edges,values",
    [
        ((0, 1, 2), (5e-324, 1)),
        ((0, 1e-100, 2e-100), (1e308, 1)),
        ((0, 1, 2), (4e-309, 5e-309)),
    ],
)
def test_half_cell_resistance_range_failure(edges, values):
    # Respectively: one factor overflows, underflows, or their sum overflows.
    grid = RectangularGrid(edges, (0, 1), 1)
    with pytest.raises(ValueError, match="face resistance factor"):
        solve_plate(grid, values, east_k=300)


def test_heterogeneous_conductance_overflow():
    grid = RectangularGrid((0, 1, 2), (0, 1), 10)
    with pytest.raises(ValueError, match="face conductance"):
        solve_plate(grid, (1e308, 5e307), east_k=300)


def test_heterogeneous_conductance_underflow():
    grid = RectangularGrid((0, 1, 2), (0, 1), 1e-100)
    with pytest.raises(ValueError, match="face conductance"):
        solve_plate(grid, (1e-300, 2e-300), east_k=300)
