"""Independent rational overlaps and heated finite-volume balances."""

import math
from fractions import Fraction as F

import pytest

from thermalpath import (
    Convection,
    RectangularGrid,
    RectangularHeater,
    map_heaters,
    solve_plate,
)

# Heater [1/2,7/2] x [1/2,5/2], 12 W, hence exactly 2 W/m2.
# Hand-intersected widths/heights are supplied separately from the grid.
GRIDS = [
    ((0, 2, 4), (0, 1.5, 3), (F(3, 2),) * 2, (F(1),) * 2),
    ((0, 1, 3, 4), (0, 1, 2, 3), (F(1, 2), F(2), F(1, 2)), (F(1, 2), F(1), F(1, 2))),
    (
        (0, 0.75, 1.5, 2.5, 3.25, 4),
        (0, 0.75, 1.5, 2.25, 3),
        (F(1, 4), F(3, 4), F(1), F(3, 4), F(1, 4)),
        (F(1, 4), F(3, 4), F(3, 4), F(1, 4)),
    ),
]


@pytest.mark.parametrize("x,y,widths,heights", GRIDS)
@pytest.mark.parametrize("thickness", [0.01, 0.5, 2])
def test_nonaligned_power_on_three_grids(x, y, widths, heights, thickness):
    grid = RectangularGrid(x, y, thickness)
    heaters = [RectangularHeater(0.5, 3.5, 0.5, 2.5, 12)]
    expected = tuple(2 * width * height for height in heights for width in widths)
    assert sum(expected) == 12
    powers = map_heaters(grid, heaters)
    assert powers == pytest.approx(tuple(map(float, expected)), rel=0, abs=2e-14)
    assert math.fsum(powers) == pytest.approx(12, rel=0, abs=5e-14)


def test_overlapping_heaters_add_with_exact_cell_totals():
    grid = RectangularGrid((0, 1, 2), (0, 1, 2), 0.1)
    heaters = [
        RectangularHeater(0, 2, 0, 2, 8),
        RectangularHeater(0.5, 1.5, 0.5, 1.5, 12),
        RectangularHeater(1, 2, 0, 1, 3),
    ]
    assert map_heaters(grid, heaters) == (5, 8, 5, 5)
    assert map_heaters(grid, list(reversed(heaters))) == (5, 8, 5, 5)


@pytest.mark.parametrize("scale,offset", [(1, -8), (0.5, 0), (4, 16)])
def test_translation_and_length_scaling_preserve_mapped_watts(scale, offset):
    grid = RectangularGrid(
        tuple(offset + scale * x for x in (0, 1, 2)),
        tuple(offset + scale * y for y in (0, 1, 2)),
        scale,
    )
    heater = RectangularHeater(
        offset + scale / 2,
        offset + 3 * scale / 2,
        offset + scale / 2,
        offset + 3 * scale / 2,
        12,
    )
    assert map_heaters(grid, [heater]) == (3, 3, 3, 3)


@pytest.mark.parametrize("transpose", [False, True])
@pytest.mark.parametrize("factor", [0.25, 1, 8])
def test_two_cell_heated_rational_system(transpose, factor):
    # A=[[8,-2],[-2,5]] W/K, b=[4,8] W above the 300 K state.
    # det(A)=36; theta=(1,2) K. West/east loss is (6,6) W.
    matrix = ((F(8), F(-2)), (F(-2), F(5)))
    theta = (F(1), F(2))
    assert tuple(
        sum(a * t for a, t in zip(row, theta, strict=True)) for row in matrix
    ) == (4, 8)
    x, y = ((0, 2), (0, 1, 3)) if transpose else ((0, 1, 3), (0, 2))
    grid = RectangularGrid(x, y, 0.5)
    bounds = (0.5, 1.5, 0.5, 2) if transpose else (0.5, 2, 0.5, 1.5)
    heaters = [RectangularHeater(*bounds, 12 * factor)]
    boundary = (
        dict(south_k=300, north_k=300) if transpose else dict(west_k=300, east_k=300)
    )
    result = solve_plate(grid, 3, heaters=heaters, **boundary)
    assert map_heaters(grid, heaters) == pytest.approx((4 * factor, 8 * factor))
    assert result.temperatures_k == pytest.approx(
        (300 + factor, 300 + 2 * factor), rel=0, abs=2e-12
    )
    for faces, power in zip(
        result.face_powers_w, (4 * factor, 8 * factor), strict=True
    ):
        assert math.fsum(faces) == pytest.approx(power, rel=0, abs=5e-11)
    assert math.fsum(
        p for faces in result.face_powers_w for p in faces
    ) == pytest.approx(12 * factor, rel=0, abs=1e-10)


def test_heater_combines_with_flux_and_broad_convection():
    grid = RectangularGrid((0, 1), (0, 2), 0.5)
    # Broad G=4 W/K, 10 W heater minus 2 W west outward flux => 2 K rise.
    result = solve_plate(
        grid,
        3,
        heaters=[RectangularHeater(0, 1, 0, 2, 10)],
        edge_flux_w_m2={"west": 2},
        face_convection=Convection(2, 300),
    )
    assert result.temperatures_k == (302,)
    assert result.face_powers_w == ((2, 0, 0, 0),)
    assert result.broad_face_powers_w == (8,)
