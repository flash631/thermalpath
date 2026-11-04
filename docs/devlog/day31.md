# D31: explicit sparse steady-network solver

Date: 2026-11-04

`solve_steady(network, backend="sparse")` now assembles a sparse unknown-node
matrix and solves it with SciPy's SuperLU factorization. The default remains
the dense NumPy solve. Inputs, temperature and power units, result ordering,
anchoring checks and numerical range errors retain their existing meaning.
SciPy was already a required dependency; no package dependency changed.

The two backends use the same assembly loop and the same single optional
link-balance correction. The sparse backend keeps its factorization for that
correction. A correction is accepted only when it keeps temperatures finite
and positive and strictly reduces the largest physical nodal residual.
The reported matrix residual is then recomputed from the accepted temperatures.

## Engineering decision

For positive conductances and an anchored unknown component, the reduced
conductance matrix is positive definite in exact arithmetic:
`x^T A x = sum_links G_ab (x_a - x_b)^2`, with zero extension to fixed nodes.
Sparse storage changes the numerical representation and factorization, not
the heat-balance model. The [network equations and limits](../networks.md)
apply to both backends. A rounded matrix can still lose a weak anchor.

Dictionary-of-keys assembly preserves the existing accumulation order while
avoiding an empty dense square array. CSC storage is passed to `splu`, as
recommended by the [SciPy API documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.splu.html).
The [dictionary sparse-array documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.dok_array.html)
describes incremental insertion. Both APIs are documented in SciPy 1.14.1,
within the existing supported dependency range. These are dependency
references; independent analytical and rational balances check the results.

## Verification evidence

The targeted suite passed 112 tests. Existing series, two-boundary and
high-conductance-ratio references now run against both backends with their
original tolerances. Added cases cover a rational branched network with
parallel links, reversed orientations, signed loads and separate anchored
components, plus sparse factorization failure and correction reuse.
The full regression suite passed 1,608 tests with 99.53% package-wide coverage,
including branches. Coverage scope and the 90% minimum remain unchanged.

For a chain of n unknowns, unit conductances, a 300 K sink and a 0.125 W
load at node 0, every link carries 0.125 W and
`T_i = 300 + (n-i)/8 K`. This formula is evaluated without calling a solver.
Measurements below used NumPy 2.5.3 and SciPy 1.18.1. CSC bytes sum only its
data, index and column-pointer buffers. Dense bytes are calculated as `8*n*n`;
the large dense matrix was not allocated.

| Unknowns | CSC populated entries | CSC buffer bytes | Calculated dense matrix bytes | L entries | U entries |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 32 | 94 | 1,260 | 8,192 | 64 | 64 |
| 128 | 382 | 5,100 | 131,072 | 256 | 256 |
| 4,096 | 12,286 | 163,820 | 134,217,728 | 8,192 | 8,192 |

For these three chains, the final temperatures, link powers and reported
nodal/matrix residuals matched the exactly representable reference values with
zero measured binary64 error. Dense and sparse temperatures also matched for
32 and 128 unknowns. This exact result is specific to this dyadic chain;
the rational branched and high-ratio cases use nonzero error tolerances.

The large-chain test intercepts dense solver calls, sparse-to-dense conversions
and large square NumPy allocations. It also requires `3*n-2` matrix entries
and at most `64*n` CSC buffer bytes, allowing different index widths.
The [verification specification](../verification.md#d31-sparse-network-verification)
gives the temperature and power tolerances and reproduction command.

Two import-order lint findings in the new test files were corrected. No
numerical acceptance test failed and no tolerance was relaxed.
Archive review also found that the explicit source inventory omitted the new
sparse tests and this record. The three entries were added to `MANIFEST.in`
so the source archive includes the verification material.

## Limits

The storage measurements exclude Python assembly objects, work arrays and
factorization peak memory. LU fill for other graph structures can be much
larger. Runtime comparisons and physical validation were not performed.
The sparse backend shares the dense backend's floating-point limitations;
a small residual does not certify temperature error or engineering safety.
