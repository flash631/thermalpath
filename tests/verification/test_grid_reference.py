"""Exact rational geometry and independent geometric invariants."""

import math
from fractions import Fraction as F

import pytest

from thermalpath import RectangularGrid


def test_nonuniform_rational_reference():
    # Exact widths: 1/3, 1/2, 1; heights: 1/4, 3/4; thickness: 1/10.
    x = (F(-1, 3), F(0), F(1, 2), F(3, 2))
    y = (F(-1, 2), F(-1, 4), F(1, 2))
    grid = RectangularGrid(x, y, F(1, 10))
    areas = [F(1, 12), F(1, 8), F(1, 4), F(1, 4), F(3, 8), F(3, 4)]
    centers = [
        (F(-1, 6), F(-3, 8)),
        (F(1, 4), F(-3, 8)),
        (F(1), F(-3, 8)),
        (F(-1, 6), F(1, 8)),
        (F(1, 4), F(1, 8)),
        (F(1), F(1, 8)),
    ]
    assert (grid.nx, grid.ny, grid.cell_count) == (3, 2, 6)
    for k, (area, center) in enumerate(zip(areas, centers, strict=True)):
        assert grid.center_m(k) == pytest.approx(
            tuple(map(float, center)), abs=2e-16, rel=0
        )
        assert grid.cell_area_m2(k) == pytest.approx(float(area), rel=5e-15, abs=0)
        assert grid.cell_volume_m3(k) == pytest.approx(
            float(area / 10), rel=5e-15, abs=0
        )
    assert grid.area_m2 == pytest.approx(11 / 6, rel=5e-15, abs=0)
    assert grid.volume_m3 == pytest.approx(11 / 60, rel=5e-15, abs=0)
    assert grid.face_areas_m2(0) == pytest.approx(
        (1 / 40, 1 / 40, 1 / 30, 1 / 30), rel=5e-15, abs=0
    )
    assert grid.face_areas_m2(5) == pytest.approx(
        (3 / 40, 3 / 40, 1 / 10, 1 / 10), rel=5e-15, abs=0
    )


def test_explicit_index_and_neighbor_table():
    grid = RectangularGrid((0, 1, 2, 4), (0, 1, 3), 0.5)
    table = [
        ((0, 0), (None, 1, None, 3)),
        ((1, 0), (0, 2, None, 4)),
        ((2, 0), (1, None, None, 5)),
        ((0, 1), (None, 4, 0, None)),
        ((1, 1), (3, 5, 1, None)),
        ((2, 1), (4, None, 2, None)),
    ]
    for k, (ij, neighbors) in enumerate(table):
        assert grid.indices(k) == ij
        assert grid.index(*ij) == k
        assert grid.neighbors(k) == neighbors


@pytest.mark.parametrize("nx,ny", [(1, 1), (1, 7), (7, 1), (3, 5), (8, 9)])
def test_partition_and_shared_faces(nx, ny):
    # Unequal rational subdivisions of a 2 m by 3 m rectangle.
    x = tuple(F(2 * i * i, nx * nx) for i in range(nx + 1))
    y = tuple(F(3 * j * j, ny * ny) for j in range(ny + 1))
    grid = RectangularGrid(x, y, F(1, 8))
    areas = [grid.cell_area_m2(k) for k in range(grid.cell_count)]
    volumes = [grid.cell_volume_m3(k) for k in range(grid.cell_count)]
    assert math.fsum(areas) == pytest.approx(6, rel=5e-15, abs=0)
    assert math.fsum(volumes) == pytest.approx(0.75, rel=5e-15, abs=0)
    outer_faces = []
    directed_internal_faces = 0
    for k in range(grid.cell_count):
        for direction, neighbor in enumerate(grid.neighbors(k)):
            area = grid.face_areas_m2(k)[direction]
            if neighbor is None:
                outer_faces.append(area)
            else:
                directed_internal_faces += 1
                opposite = (1, 0, 3, 2)[direction]
                assert grid.neighbors(neighbor)[opposite] == k
                assert grid.face_areas_m2(neighbor)[opposite] == area
    assert directed_internal_faces == 2 * ((nx - 1) * ny + (ny - 1) * nx)
    assert math.fsum(outer_faces) == pytest.approx(1.25, rel=5e-15, abs=0)


def test_translation_and_length_thickness_scaling():
    grid = RectangularGrid((-2, -1, 3), (1, 3, 4), 0.25)
    moved = RectangularGrid((6, 7, 11), (-3, -1, 0), 0.25)
    scaled = RectangularGrid((-4, -2, 6), (2, 6, 8), 0.5)
    thicker = RectangularGrid(grid.x_edges_m, grid.y_edges_m, 0.75)
    for k in range(grid.cell_count):
        assert moved.center_m(k) == tuple(
            c + shift for c, shift in zip(grid.center_m(k), (8, -4), strict=True)
        )
        assert moved.cell_area_m2(k) == grid.cell_area_m2(k)
        assert scaled.cell_area_m2(k) == 4 * grid.cell_area_m2(k)
        assert scaled.cell_volume_m3(k) == 8 * grid.cell_volume_m3(k)
        assert scaled.face_areas_m2(k) == tuple(a * 4 for a in grid.face_areas_m2(k))
        assert thicker.cell_volume_m3(k) == 3 * grid.cell_volume_m3(k)
        assert thicker.face_areas_m2(k) == tuple(a * 3 for a in grid.face_areas_m2(k))
        assert thicker.cell_area_m2(k) == grid.cell_area_m2(k)


def test_large_same_sign_coordinates_have_finite_centers():
    grid = RectangularGrid((1e308, 1.5e308), (0, 1e-308), 1)
    assert math.isfinite(grid.center_m(0)[0])
    assert grid.x_edges_m[0] < grid.center_m(0)[0] < grid.x_edges_m[1]
