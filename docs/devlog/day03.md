# D03: steady conductance-matrix solver

Completion date: 2026-09-18.

Added `solve_steady` and `SteadyResult` for small constant-conductance networks.
The solver eliminates fixed-temperature nodes, checks that all unknowns reach a
fixed boundary, solves the dense reduced matrix, and reports temperatures [K]
and signed link powers [W]. Parallel links, multiple boundaries, negative loads,
separate anchored components, and all-fixed inputs are supported.

The [decision](../decisions/0003-steady-networks.md) records the mathematical
review. Positive conductances and anchoring make the reduced matrix positive
definite. Excessive extraction can still produce temperatures outside the
physical domain and is rejected. No material unresolved analysis remained.

The 29 new tests include exact-rational references for a two-boundary network and
a series path. They also cover orientation, ordering, common load/conductance
scaling, missing boundaries, and numerical range failures. The two-boundary
temperatures are 3370/11 K and 3400/11 K; the series source is 3639/10 K.
Each reference has a documented binary64 tolerance budget. These synthetic checks
verify the stated equations and tested failure contracts; they do not constitute
physical validation or establish accuracy for arbitrary ill-conditioned inputs.

The public suite passed 178 tests with 100% package coverage across 170 statements
and 68 measured branches. Final review
replaced unnecessarily tight reference tolerances with budgets derived from
matrix conditioning and propagation into link powers; no failing result prompted
that adjustment. A weak boundary connection can round out of the assembled
matrix, and the resulting singular system is rejected. Small temperature
differences can still disappear without a range exception; that limit is explicit.

The complete public and private gates, distribution checks, and publication review
must pass on the final source bytes before delivery. CI is checked for the exact
delivered revision separately. D04 remains unfinished.
