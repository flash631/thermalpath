# D13: rectangular heater mapping

Completion date: 2026-09-28.

Added immutable `RectangularHeater` inputs, `map_heaters` and the `heaters`
argument to `solve_plate`. Total nonnegative watts are distributed by the
exact rectangular cell/footprint overlap formula. Inputs must be fully inside
the plate; overlapping heater contributions add. Mapping is available
separately from the solve. See [the decision](../decisions/0013-rectangular-heaters.md).

Analytical review checked the projected-area integral, partition conservation,
SI dimensions, positive input/outward loss signs, unchanged anchored matrix,
zero input, boundary-only intersections and translation/scaling limits.
The source-free upper temperature bound does not apply to heated cells.
No clipping, center-based footprint selection or rounded-total correction is
used. The existing plate result and prior boundary/material behavior remain
supported.

Eighty new tests cover independently tabulated rational overlaps on three
nonaligned grids, overlapping heaters, zero input, containment and invalid
domains, coordinate/thickness scaling and arithmetic range failures. The
4-, 9- and 20-cell mappings each sum to 12 W within 5e-14 W. A hand-derived
two-cell system gives 4 W and 8 W input, 301 K and 302 K cell temperatures,
and 12 W exterior outflow within 1e-10 W. Tests transpose this system and
scale its power. A mixed one-cell calculation gives 302 K with 10 W heater
input, 2 W edge loss and 8 W broad-face loss. Tolerances are derived in
[the source documentation](../sources.md).

The complete public suite passed 821 tests with 99.37 percent combined
statement and branch coverage across all implemented modules. The source
mapping and plate modules have full measured coverage. Numerical checks are
synthetic; they do not replace measured comparison for a physical system.

A retained 1e-20 W heater maps correctly while its temperature rise rounds
away at 300 K. Thus mapped input conservation does not guarantee the computed
heat balance. Zero-rounded positive contributions and overflowing cell sums
raise errors. These checks verify geometry and discrete equations; they do
not establish general temperature convergence, an arbitrary-input error
certificate or physical validation. CI evidence must be checked for the
delivered revision.
