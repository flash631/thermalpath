# D32: sparse steady plate solving

Date: 2026-11-05

`solve_plate(..., backend="sparse")` now passes the existing plate network
to the sparse steady solver. The default remains dense. The cell geometry,
material interfaces, boundary laws, heater mapping, signed face powers and
balance fields retain their existing meanings. The fixed refinement example
also accepts the backend keyword. No package dependency changed.

## Engineering decision

The plate already forms a network of cells and temperature reservoirs.
Reusing that network's sparse backend preserves a single implementation of
the face laws. An internal face adds a positive conductance to two diagonals
and its negative to two off-diagonals. Eliminating a fixed reservoir adds a
diagonal and a load. Flux and heater power enter the load directly.

With positive conductances and at least one anchor, the reduced matrix is
positive definite in exact arithmetic. Its quadratic form sums
`G_ij*(v_i-v_j)^2` over internal faces and `G_ib*v_i^2` over anchors.
Shared-face powers cancel when cell balances are summed. The same equations
therefore apply to both storage formats; the floating-point solves can differ.

The [NIST finite-volume diffusion documentation](https://pages.nist.gov/fipy/en/stable/numerical/discret.html)
describes the adjacent-cell face-gradient approximation and its mesh limits.
The [SciPy sparse factorization reference](https://docs.scipy.org/doc/scipy-1.14.1/reference/generated/scipy.sparse.linalg.splu.html)
documents CSC input and reusable factor solves. The implementation retains the
D31 factorization and single optional balance correction. No independent
software performance comparison is claimed.

## Verification evidence

All 358 targeted tests passed. Existing analytical and rational plate tests
run with both backends and unchanged tolerances. They cover unequal cells
and conductivities, flux and film limits, broad-face exchange, heaters and
corner handling. Separate error tests retain small physical residuals that
rounded matrix residuals can hide. A deliberately inaccurate sparse solve
also demonstrates that zero global imbalance can conceal local errors.

The frozen manufactured study retains its 4x3, 8x6 and 16x12 grids, integrated
polynomial loads and independent sine-mode reference. Sparse maximum errors
against the continuum field were 1.344988828041, 0.443620351229 and
0.125126977406 K. The maximum-error orders remained 1.600196733 and
1.825932683; they are not replaced with a claim of second order on these
grids. Dense and sparse temperatures matched in binary64 in this run.
The largest absolute total imbalance was 1.20e-14 W. Small balance error
does not remove the reported spatial error.

The storage fixtures use a 0.06 by 0.04 m plate, 0.002 m thick,
k=10 W/(m K), west/east temperatures 300/320 K and other faces insulated.
The independent linear solution is `T=300+20*x/0.06 K`. Measurements used
NumPy 2.5.3 and SciPy 1.18.1. CSC bytes sum only data, row-index and
column-pointer buffers. Dense matrix bytes below are calculated as `8*N*N`;
those dense arrays were not allocated by this measurement.

| Grid | Cells | CSC entries | CSC buffer bytes | Calculated dense matrix bytes | L entries | U entries |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 8x6 | 48 | 212 | 2,740 | 18,432 | 263 | 263 |
| 32x24 | 768 | 3,728 | 47,812 | 4,718,592 | 12,692 | 12,692 |
| 64x48 | 3,072 | 15,136 | 193,924 | 75,497,472 | 75,122 | 75,122 |

Temperatures matched the independently evaluated binary64 linear expression
at every cell in these fixtures. The largest face-power error was 6.16e-17 W,
largest physical cell residual 2.09e-17 W, largest matrix residual 7.11e-15 W
and largest absolute total imbalance 2.36e-16 W. These measurements passed
the preselected nonzero budgets. They do not establish exact arithmetic for
all inputs. Tests intercept dense solves, sparse-to-dense conversion and
large square NumPy allocations. See [verification and reproduction](../verification.md#d32-sparse-plate-verification).

## Limits

CSC matrix storage grows linearly for this grid, but factorization fills
additional entries, as the L/U counts show. The measurements exclude peak
factorization memory, Python assembly objects and work arrays. Heater mapping
still examines all heaters for each cell. Runtime scaling, general capacity
and physical validation were not measured. Existing restrictions on
orthogonal grids, isotropic cellwise conductivity, depth averaging and
floating-point range remain in force.
