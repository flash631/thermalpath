# Rectangular structured-grid geometry

`RectangularGrid(x_edges_m, y_edges_m, thickness_m)` defines the Cartesian
product of two ordered edge lists, extruded through a constant thickness.
Coordinates and thickness use metres. Edges may start at a negative coordinate,
and spacing may be unequal. Each axis needs at least two finite, strictly
increasing values; thickness must be finite and positive. Input lists are copied
into immutable tuples.

```python
from thermalpath import RectangularGrid

grid = RectangularGrid((0, 0.01, 0.03, 0.06), (0, 0.01, 0.04), 0.002)
assert (grid.nx, grid.ny, grid.cell_count) == (3, 2, 6)
assert grid.index(2, 1) == 5
assert grid.indices(5) == (2, 1)
assert grid.neighbors(0) == (None, 1, None, 3)
```

Run `python examples/rectangular_grid.py` for the complete JSON geometry report.
This synthetic plate is 60 mm by 40 mm by 2 mm. Its planar area is
0.0024 m² and volume is 0.0000048 m³. The six cell areas and volumes sum to
these values within the documented floating-point tolerance.

## Coordinates, indexing and faces

The x direction increases from west to east; y increases from south to north.
Cell indices start at zero. The flat index is `k = iy * nx + ix`: x varies
fastest. Integer division and remainder by `nx` recover `iy` and `ix` uniquely.
Negative indices, booleans, fractional indices and out-of-range indices fail
with `ValueError`.

For cell `(ix, iy)`, define `dx = x[ix+1] - x[ix]` and
`dy = y[iy+1] - y[iy]`. Geometry follows directly from a rectangular prism:

| Quantity | Expression | Unit |
| --- | --- | --- |
| Planar cell area; each top/bottom face | `dx * dy` | m² |
| Cell volume | `dx * dy * thickness` | m³ |
| West/east lateral face area | `dy * thickness` | m² |
| South/north lateral face area | `dx * thickness` | m² |
| Cell center | `(x[ix] + dx/2, y[iy] + dy/2)` | m |

The corresponding methods are `cell_area_m2(k)`, `cell_volume_m3(k)`,
`face_areas_m2(k)` and `center_m(k)`. Face-area and neighbor tuples always use
west, east, south, north order. Areas are unsigned; they do not prescribe a
heat-flow sign. `neighbors(k)` returns `None` at an outer boundary. It does not
assign insulation, temperature or any other thermal boundary condition.

Adjacent cells share the same transverse interval and therefore the same face
area. Every internal neighbor relationship has its opposite. Along either
axis, summing consecutive widths cancels internal edges. Consequently, the
exact sum of cell areas is `(x_last - x_first) * (y_last - y_first)`; multiplying
by thickness gives total volume. `area_m2` and `volume_m3` use the outer edges.
The geometry stores only axis data and computes individual cells on request.

## Verification and numerical limits

An independent rational fixture has widths `(1/3, 1/2, 1) m`, heights
`(1/4, 3/4) m` and thickness `1/10 m`. Its six exact cell areas are
`(1/12, 1/8, 1/4, 1/4, 3/8, 3/4) m²`; total area is `11/6 m²`,
and total volume is `11/60 m³`. Tests compare each center, area and volume,
an explicit neighbor/index table, and independently specified face areas.
Five grid shapes also check summed domain measures, reciprocal neighbors,
identical shared faces and total outer lateral area. Translation, uniform
length scaling, thickness scaling and one-cell/row/column cases are covered.

For these modest, well-separated coordinates, comparisons use `5e-15` relative
tolerance and zero absolute tolerance for areas and volumes. This allows about
22 binary64 epsilons for conversion, subtraction, products and summation.
Centers use `2e-16 m` absolute tolerance with zero relative tolerance. These
are fixture budgets, not error bounds for arbitrary coordinates.

Every width and center must remain representable; a center must lie strictly
inside its cell. All cell/face areas, cell volumes and total domain measures
must be finite and positive after rounding. Products are monotone on positive
inputs, so checking minimum and maximum widths/heights bounds all cell products
without constructing a full grid array. Rejection includes overflow and products
rounded to zero. Positive subnormal products can still have poor relative
accuracy. A large coordinate offset can erase a small width before construction;
for example, `1e16 + 1` rounds to `1e16`. Adjacent floating-point edges without
a representable interior center are also rejected.

Range checks are conservative: an overflowing intermediate can reject a final
mathematical product that would fit after rescaling. Summed rounded cell areas
need not equal the rounded outer-edge area bit for bit. Geometry verification
does not establish thermal accuracy, mesh convergence or physical validation.
