# D10: constant-conductivity finite-volume plate

Completion date: 2026-09-25.

Added `solve_plate` and immutable `PlateResult` for a source-free steady plate.
Fixed-temperature and insulated lateral edges use explicit outward-flow signs.
Cell temperatures and west/east/south/north face powers follow the grid's
x-first order. The existing dense network solver performs the linear solve.

Analytical review checked integrated Fourier conduction, SI dimensions,
half-cell boundary distances, shared-face cancellation, positive-definite
anchoring, the maximum principle and constant/linear limits. The entirely
insulated nonunique problem is rejected. See [the decision](../decisions/0010-constant-conductivity-plate.md).

Independent rational substitution verifies the four-cell temperatures
`(2120/7, 320, 320, 2360/7) K` and all signed face powers. Unequal-cell linear
profiles pass in both axes and both directions. Constant fields, one-cell
weighted boundaries, exact opposite shared-face powers, conductivity/thickness
scaling and invalid domains are covered. The runnable synthetic example has
west/east outward powers +4 W and -4 W.

Adverse tests preserve conductance overflow/underflow, matrix overflow and a
temperature rise lost to rounding with a nonzero cell power imbalance. The
[plate documentation](../plate.md) gives explicit comparison budgets and dense
solver limitations. This increment establishes neither a general mesh
convergence rate nor physical validation. CI evidence must be checked for
the delivered revision.

D10 adds 56 tests. The complete local suite passes 612 tests with 99.22%
combined statement/branch coverage across 586 statements and 188 branches.
The plate module reaches 100% coverage. The example passes its subprocess
comparison with the independent linear-profile values.
