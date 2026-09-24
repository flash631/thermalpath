# D09 decision: explicit rectangular edge coordinates

Use one immutable `RectangularGrid` with x/y edge coordinates and constant
thickness. Explicit edges describe both uniform and unequal rectangular cells
without separate constructors. The geometry has no material properties, loads
or thermal boundary conditions. Cells are addressed by an x-first flat index;
neighbor and lateral-face tuples have a fixed west/east/south/north order.

The preimplementation analysis derives planar area, extruded volume and face
areas directly from the rectangular prism. Increasing edges produce a unique
partition with no gaps or overlapping interiors. Internal neighbors are
reciprocal; shared face areas agree because the transverse interval is shared.
Summed cell areas telescope to the outer rectangle in exact arithmetic.
No differential equation, solution uniqueness or time stability is involved.

Validate finite positive widths/products and strictly interior centers. Use
positive-product monotonicity to test extreme widths/heights, with independent
checks on total domain measures. Store axis data only. Compute centers as
left edge plus half width, avoiding addition of two large same-sign endpoints.
Retain rejection of collapsed widths, nonrepresentable centers and arithmetic
range failures. Accepted subnormal values have no relative-accuracy guarantee.

Independent exact fractions, an explicit index/neighbor table, area partition,
shared-face and scaling checks verify this scope. Their tolerances are recorded
in [the geometry documentation](../grid.md). Geometry alone cannot establish
thermal accuracy or physical validity. No material analytical issue remains.
