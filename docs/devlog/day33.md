# D33: sparse transient networks with factor reuse

Date: 2026-11-07

`solve_transient(..., backend="sparse")` now assembles sparse backward-Euler
systems and reuses a factor for consecutive exactly equal computed time steps.
The dense default, existing positional arguments, interval-load semantics,
node ordering and result fields remain unchanged. No dependency was added.

## Engineering decision

The system for a step of length h is
`A = diag(C/h) + L_uu`, with right-hand side
`(C/h)*T_old + P - L_uf*T_fixed`. Capacities have units J/K, conductances W/K,
times s and temperatures K, so both sides have units W. Positive capacities
make A positive definite in exact arithmetic, including disconnected and
insulated components. Its quadratic form is the positive capacity sum plus
nonnegative internal-link and boundary-link terms. Internal exchanges cancel
in the total heat balance.

Conductances, topology, fixed-node selection and copied capacities do not
change within a call. Therefore equal h gives the same matrix, even when
interval loads change. The cache holds one factor, with no tolerance in the
step comparison. A changed h replaces it; a new call always starts empty.
No global cache or retained public solver object needs invalidation.

Assembly uses DOK followed by CSC. The step diagonal is added with checked
NumPy arithmetic before factorization. The
[SciPy splu reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.splu.html)
describes the sparse factorization and its returned solver. The
[SuperLU reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.SuperLU.html)
documents solving multiple right-hand sides with that factor. These operations
support reuse for an unchanged matrix; they do not establish time accuracy.

## Verification evidence

All 158 targeted tests passed. The existing network-domain, rational-update,
energy-ledger and temporal-refinement tests run with both backends and their
original tolerances. They cover signed piecewise loads, variable steps,
parallel links, reversed links, multiple reservoirs, insulated components,
fixed-only networks, range failures and positive-temperature checks.

Exact two-node rational updates agree within 2e-12 K. The original energy
budgets remain 1.2e-11 to 5e-11 J, depending on the reported quantity.
Instrumentation verifies one factor for four equal steps with changing loads,
three factors for step sizes `(0.5, 0.5, 1, 1, 0.5, 0.5)` s, and a fresh
factor for adjacent unequal binary64 steps. Separate calls rebuild after
operator changes and preserve input ordering. Numerical factor/solve failures
raise `ValueError`; no fallback silently changes the selected backend.

The continuous insulated-pair reference has C=2 J/K per node, G=1 W/K,
initial temperatures 310 and 290 K, and final time 1 s. A 70-digit Decimal
exponential supplies the independent continuous reference. For 5, 10, 20 and
40 steps, sparse final-temperature errors were 0.339981308450,
0.176638482581, 0.090100417016 and 0.045511825264 K. Observed orders were
0.944655748, 0.971193995 and 0.985292336. The remaining 0.0455 K error is
retained even though the discrete energy balance closes closely.

The larger fixtures prescribe the independent field
`T_i(t)=300+i/8+t/4 K`, C=2 J/K, G=1 W/K and eight steps of 0.5 s.
Each node receives 0.5 W, with endpoint adjustments -0.125 and +0.125 W
from the link laws. The linear time dependence makes backward Euler exact
in exact arithmetic for this fixture. Measurements used NumPy 2.5.3 and
SciPy 1.18.1. Each case used one factor and eight solves.

| Unknowns | CSC entries | CSC buffer bytes | L entries | U entries |
| ---: | ---: | ---: | ---: | ---: |
| 32 | 94 | 1,260 | 64 | 64 |
| 128 | 382 | 5,100 | 256 | 256 |
| 1,024 | 3,070 | 40,940 | 2,048 | 2,048 |

Across these fixtures, the largest temperature error was 1.71e-13 K,
largest nodal energy defect 1.99e-13 J, and largest total energy defect
3.26e-11 J. All passed the preselected nonzero budgets. Tests intercept
dense solves, diagonal dense construction, large square allocations and
sparse-to-dense conversion. The smaller fixtures also match the dense path
within 2e-10 K. See [reproduction commands](../verification.md#d33-sparse-transient-verification).

## Limits

The table counts only CSC data/index/pointer buffers and factor entries.
It excludes peak process memory, assembly objects and work arrays. LU fill
depends on topology and ordering; output history still grows with nodes
times time points. The cache does not impose a total resource limit.
Runtime superiority and physical validation were not measured.

Backward Euler remains first order. Reusing a factor does not remove time
discretization error or binary64 rounding. Extreme scale ratios can lose a
capacity contribution, and tiny temperature changes can round away. Positive
temperature checks cover computed states only. Constant properties and fixed
reservoir temperatures remain model assumptions.
