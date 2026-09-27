# D12: flux and convection boundaries

Completion date: 2026-09-27.

Added outward-positive edge flux, edge convection with half-cell conduction
resistance, and combined broad-face convection to `solve_plate`. The immutable
`Convection` record stores a nonnegative coefficient and positive ambient
temperature. Broad-face coefficients are summed per projected area, without
an extra factor of two. The result includes combined outward broad-face power
per cell. Existing fixed/insulated and scalar/cellwise conductivity calls remain
supported. See [the decision](../decisions/0012-plate-boundaries.md).

Analytical review checked the two boundary laws, surface-temperature
elimination, SI dimensions, outward signs, lateral versus projected areas,
positive graph energy, uniqueness with a reservoir anchor, and cancellation
of shared powers. The maximum principle applies without imposed flux;
prescribed heating can raise temperatures above all reservoir temperatures.
Broad-face convection retains the uniform-through-thickness approximation.

Eighty-nine new tests passed, bringing the public suite to 741 tests.
Package-wide statement and branch coverage was 99.32 percent, with full
measured coverage of the plate and convection modules. Independent checks
include continuum flux/film profiles in both axes and flow directions,
unequal cells and thickness scaling, two material layers between films,
and a mixed two-cell exact rational system with separate face balances.
Zero-coefficient, small/large-coefficient, invalid/conflicting input and
unanchored cases are covered.

The synthetic runnable strip returned center temperatures 314.5 and 307 K
within 2e-12 K, a reconstructed surface temperature of 302 K within 5e-11 K,
and 10 W boundary transfer within 5e-11 W. The two-layer film reference gives
80/3 W/m2 and an interface temperature of 320 K. The mixed reference gives
`(138548/467,138887/467) K`; independent rational balances are exactly zero.
Comparison budgets are derived in [boundary documentation](../plate_boundaries.md).

Range failures remain explicit. A 1e-20 W imposed input in the unit-area
adverse case leaves temperature at 300 K after rounding and retains the
nonzero balance. Large broad-face coefficients can amplify temperature
roundoff in the recovered power. These checks establish no general spatial
convergence order, arbitrary-input error certificate or physical validation.
CI evidence must be checked for the delivered revision.
