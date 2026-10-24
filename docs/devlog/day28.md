# D28: worksheet tests and resource limits

Completed on 2026-10-24. The initial 2026-10-23 failures are retained below.

Added server checks for the existing input ranges and a submitted-case snapshot
per session. Added AppTest checks for valid cases, displayed values, useful
errors, recovery, session separation and fixed workload size. Each render uses
one three-node solve with two links, zero grid cells and zero random samples.
The app uses the library directly; the solver repair is described below.

## Initial results, 2026-10-23

The focused run passed 52 checks and failed two, including the seven existing
adapter checks. All 19 new valid cases displayed exactly the same temperatures
and link powers as independently constructed direct library calls. Seventeen
passed the frozen 2e-10 K temperature screen against the series reference.
The two failures used P = 1000 W, Gc = 100 W/K and Gs = 0.1 W/K:

| Sink temperature | Maximum temperature error | Frozen screen |
| --- | --- | --- |
| 1 K | 5.699e-10 K | failed |
| 1000 K | 6.263e-10 K | failed |

Errors above use exact rational values of the binary64 inputs and returned
temperatures. The pytest comparison rounds the rational reference to binary64
first and reports 5.693e-10 K and 6.257e-10 K respectively; both methods fail
the same threshold. Across all 19 cases, the maximum link-power error was
6.265e-11 W, below the unchanged 2e-10 W screen.

An independent exact solve of each assembled two-by-two binary64 matrix gave
a maximum difference of 2.528e-12 K from the library result. This separates
linear-solve error from matrix-assembly rounding. It explains the discrepancy
but does not make the physical-reference temperature screen pass.

The first test run also exposed test-runner behavior: AppTest resets unsubmitted
or invalid form values. Corrected the tests to resubmit valid edits and inject
invalid submitted state when exercising the server guard. The resulting
messages identify the affected input and allowed range; errors remove result
tables and a valid replacement restores them. Injected solver failures also
recover. At that stage the two numerical failures remained active, with no
skips, expected-failure markers or increased tolerance.

Publication was blocked by these acceptance failures.

## Repair and verification, 2026-10-24

The steady solver now attempts one correction from the original individual
link balances. It solves the existing matrix with the signed heat imbalance
as the right-hand side. A finite, positive candidate replaces the direct result
only if its maximum absolute link-balance residual decreases strictly. An
unusable correction retains the direct result. Initial singularity and range
checks remain, and the reported matrix residual is recomputed for the final
temperatures. See the [decision](../decisions/0028-worksheet-resource-limits.md)
for the error relation and its limits.

All 19 original cases pass the unchanged absolute 2e-10 K/W screens with zero
relative tolerance. Exact rational comparison of returned temperatures against
the original binary64-input equations gives:

| Case | Before repair | After repair |
| --- | --- | --- |
| 1000 W, 100 and 0.1 W/K, sink 1 K | 5.699e-10 K | 5.552e-13 K |
| 1000 W, 100 and 0.1 W/K, sink 1000 K | 6.263e-10 K | 5.552e-13 K |
| Maximum across all 19 cases | 6.263e-10 K | 1.111e-12 K |

The maximum link-power error across these cases is now zero at the returned
binary64 precision. This is finite test evidence, not exact arithmetic in the
solver. The maximum difference from the exact solution of the rounded assembled
matrix is now 6.253e-10 K: the correction targets the original link equations,
so agreement with the rounded matrix need not improve.

Twelve additional reference checks cover both formerly failing sink cases,
reversed node/link ordering and equal load/conductance scales of 0.5, 1 and 8.
Six solver tests check correction acceptance, rejection and failure handling.
The focused selection passed 121 tests. The complete regression suite passed
1,539 tests with 99.53% package-wide coverage including branches, without
excluding modules or weakening thresholds. Existing weak-anchor rejection,
arithmetic-range checks and small-load limitations still pass.

AppTest covers 47 new cases; the seven earlier adapter checks remain. The app
calls one three-node/two-link network calculation per render, using at most two
linear solves inside the library. It allocates no spatial grid or random
samples. Packaging includes the new tests and evidence documents.

No physical accuracy, whole-range numerical bound, browser rendering, runtime
deadline or multi-user capacity has been established by these tests.
