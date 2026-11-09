# D34: constant-property transient plates

Date: 2026-11-09

`solve_transient_plate` integrates the depth-averaged rectangular plate model
with positive cell heat capacity. It accepts uniform or cellwise conductivity,
volumetric heat capacity and initial temperature. Boundary data and heater
loads stay constant during a call. Dense integration remains the default;
sparse integration is explicit. The result contains x-first cell-temperature
histories and signed step-energy records.

## Engineering decision

Steady and transient plates share the same conductance and heater assembly.
The steady solver retains its temperature-anchor requirement, face powers,
physical balances and linear residuals. The transient solver permits fully
insulated plates because their initial field and positive storage determine
their evolution.

Each cell capacity is `C_i = cvol_i*V_i` in J/K. The update matrix is
`diag(C/dt) + L_uu`, whose quadratic form is a positive storage sum plus
nonnegative internal and boundary conductance terms. It is positive definite
in exact arithmetic for positive capacities and time steps, even without a
temperature anchor. Backward Euler damps each homogeneous mode by
`1/(1 + lambda*dt)`; stability does not remove first-order time error.

Cell source energy combines heater input with prescribed inward edge flux.
Fixed-temperature and convective reservoir energies are reported separately
and are positive into the plate. Internal face transfers cancel in the total.
The records use endpoint heat flow, which is backward Euler's quadrature.
They are not exact continuous-time energy integrals.

## Independent references

All 130 targeted tests passed. Exact rational elimination checks an unequal
2x2 grid with heterogeneous conductivity and capacity, a fixed west edge,
east convection, south inward flux, zero north convection, broad-face loss,
and a nonaligned heater. The reference assembles its own geometry, overlap
fractions, face resistances and energy terms. It verifies the exact equations
by substitution before comparing the floating-point temperatures and energies.
Separate cases check isolated uniform heating and a one-cell convection
recurrence. The absolute budgets are 2e-10 K for those temperature comparisons,
5e-9 J for cell energy residuals and 2e-8 J for total imbalance.

The insulated two-dimensional cosine benchmark uses k=2 W/(m K), volumetric
heat capacity 10 J/(m3 K), length 2 m, width 1 m, thickness 0.2 m, mean
temperature 300 K and initial amplitude 20 K. Its final time is 0.2 s.
Independent discrete eigenvalues reproduce every computed time-grid state
within 2e-10 K with both backends.

The spatial study keeps eight time steps and compares against the
continuous-space backward-Euler mode. This isolates spatial error at the
same time discretization; it does not use the continuous-time exponential
as the spatial reference. Dense results are shown below; sparse results
agree to the displayed precision.

| Grid | Maximum spatial error (K) | RMS spatial error (K) |
| --- | ---: | ---: |
| 4x3 | 0.379134905336 | 0.236928768256 |
| 8x6 | 0.113370950661 | 0.059834831902 |
| 16x12 | 0.029590464407 | 0.014995105209 |

The original maximum-error orders were 1.74166026335 and 1.93784677791.
The first pair failed the original minimum-order criterion of 1.8 for both
backends. That failed result is retained. The full suite at that stage had
1,999 passes and these two failures, with 99.55% package-wide branch coverage.

For this mode, the sampled peak factor is
`cos(pi/(2*nx))*cos(pi/(2*ny))`; it changes from about 0.8001 to 0.9474 to
0.9867 across the three grids. The RMS factor is exactly 1/2 at every grid,
because the cell-centered cosine has mean square 1/2 on each axis. The
convergence criterion therefore uses the directly computed RMS error, checked
independently against the amplitude identity. Its observed orders are
1.98539590727 and 1.99649392660, within the 1.8 to 2.2 interval. The finest
maximum-error limit remains 0.08 K. No grid, time step, physical input or
production equation changed with this criterion correction.

The temporal study uses the fixed 8x6 grid and compares against its exact
semidiscrete exponential response. The maximum errors at 10, 20 and 40 steps
were 0.132975535812, 0.067347679442 and 0.033893731089 K. Observed orders
were 0.981460709 and 0.990609776, within the 0.9 to 1.1 interval; the finest
time-error limit is 0.06 K. The combined error against the continuous-space,
continuous-time solution at 40 steps remains 0.152474437928 K. It includes
spatial error and must not be replaced by the smaller temporal error.

An earlier targeted run had 126 passes and four failures. Two were the
maximum-error order checks above. The other two used an overflow fixture
whose time step caused the integrator's storage coefficient to underflow
before the intended energy-product overflow. The corrected fixture keeps
the integration coefficients representable and reaches the energy guard.
This changed the synthetic inputs, not a production tolerance or range check.

## Sparse case and limits

The 32x32 insulated fixture has total capacity 10 J/K and a full-area 1 W
heater, giving the exact uniform ramp `T=300+t/10 K`. Three steps of 0.125 s
used one factorization and three solves. The assembled CSC matrix had 4,992
entries and 64,004 data/index/pointer bytes. Maximum temperature error was
9.67e-13 K, maximum cell energy defect 1.71e-13 J, and maximum total energy
defect 1.50e-13 J. These passed the fixed 5e-10 K and 5e-8 J total budgets.
Tests block dense solves, large square allocations and sparse-to-dense
conversion. A variable-step case checks refactorization and a fresh call
checks that no factor survives between solves.

The byte count excludes assembly objects, factorization storage and output
histories. No peak-memory or runtime comparison was performed. These are
synthetic numerical checks, with no independent physical measurements.
Constant properties, perfect material contact, isotropic cell conductivity
and through-thickness uniformity remain assumptions. Temperature positivity
checks apply at computed states only.

See [transient plate inputs](../transient_plate.md) and the
[reproduction command](../verification.md#d34-transient-plate-verification).
