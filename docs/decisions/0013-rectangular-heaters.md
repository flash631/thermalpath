# D13: integrate rectangular heater footprints

Use an immutable `RectangularHeater` with four geometric bounds and total
nonnegative power. Keep geometric mapping available as `map_heaters` so the
prescribed cell watts can be inspected separately from a thermal solve.
`solve_plate` accepts the same heater sequence and adds its mapped inputs
to the cell right-hand side. Existing calls retain their behavior.

Require full containment instead of silently clipping a heater. This makes
the conservation denominator unambiguous: total power refers to the complete
specified rectangle. Exact rectangular overlaps handle unequal cells and
nonaligned edges without assigning all power to cells whose centers happen
to lie inside the heater. Overlapping heaters add independently. Zero power
is valid; zero-area footprints and negative heater powers are not.

The partition proof and dimensions establish power conservation in exact
arithmetic. No thickness multiplication, face-count multiplier or adjustment
to force the rounded total is applied. Positive heating changes only the
load vector, so anchored uniqueness is unchanged. Floating-point range
failures remain explicit. Source integration and temperature accuracy are
separate questions; the scope and fixture tolerances are in
[heater documentation](../sources.md).

Acceptance uses independent rational overlap tables on three nonaligned
grids, overlapping inputs, translated/scaled geometry, and a hand-derived
two-cell heated system in both coordinate directions. The discrete system
is not claimed to reproduce the continuum discontinuous-source solution.
