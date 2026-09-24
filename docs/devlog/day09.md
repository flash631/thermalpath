# D09: rectangular structured-grid geometry

Completion date: 2026-09-24.

Added `RectangularGrid` with immutable edge coordinates and constant thickness.
It provides centers, planar and lateral-face areas, volumes, x-first indexing
and reciprocal neighbors. Explicit edges allow unequal widths and translated
origins. Boundary neighbors are absent; geometry assigns no thermal conditions.

The analytical review establishes a unique rectangular partition, dimensional
consistency, matching shared faces and exact telescoping of the area sum.
The implementation checks extreme positive products without allocating a full
cell array. See [the decision](../decisions/0009-rectangular-grid.md).

An independent rational six-cell fixture gives total area `11/6 m²` and total
volume `11/60 m³`. Tests check every cell area, volume and center against exact
fractions, an explicit index/neighbor table, and face areas. Five grid shapes
verify total area/volume, external face area and internal-face counts. Translation
and length/thickness scaling, single-cell/row/column limits, immutable inputs
and invalid indices are covered. The synthetic runnable example reports
0.0024 m² and 0.0000048 m³ for a 60 mm by 40 mm by 2 mm plate.

Adverse tests retain collapsed widths at large offsets, adjacent edges without
representable interior centers, and cell/face/domain overflow or underflow.
The accepted scope and comparison tolerances are documented in
[grid.md](../grid.md). No unresolved analysis or physical validation is claimed.
CI evidence must come from the run for the delivered revision.

D09 adds 76 tests. The complete local suite passes 556 tests with 99.14%
combined statement/branch coverage across 533 statements and 166 branches.
The grid module reaches 100% coverage. The runnable geometry example passes
its subprocess checks against independently specified dimensional values.
