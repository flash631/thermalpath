# D08: transient energy and time refinement

Completion date: 2026-09-23.

Added `transient_energy_balance` and `TransientEnergyBalance`. The report accepts
one step's temperatures, capacities, duration and loads, then reports signed
storage, source, reservoir and residual energies in joules. Fixed-node exchange,
insulated components and arbitrary valid temperature snapshots are supported.
The existing temperature solver and case/CLI interfaces retain their contracts.

The analytical review multiplies each backward-Euler equation by the duration.
Internal links cancel pairwise; fixed-node outward energy is reservoir input.
Storage is C times temperature change. Endpoint conductive energy is an
approximation to the continuous integral, so conservation does not establish
time accuracy. See [the decision](../decisions/0008-transient-energy.md).

The independent exact-rational two-node ledger closes for all three unequal
intervals and signed load maps, including reversed link orientations. The
first step has total storage `65/12 J`, source `10 J` and reservoir input
`-55/12 J`. All float comparisons pass the propagated fixture budgets.

Two smooth modes use four fixed time-step sizes and independent 70-digit Decimal
exponentials. Rational powers also verify their discrete endpoints. For scalar
heating to 20 s, halving steps from 4 to 0.5 s reduces error from
0.339981308450 K to 0.045511825264 K. Measured orders are 0.944656, 0.971194 and
0.985292. The largest step energy imbalance over those grids is below `5e-13 J`.
An insulated coupled mode also passes the predefined first-order window and
conserves its mean temperature. Full inputs and results are in
[the energy report](../transient_energy.md).

D08 adds 36 tests. The complete local suite passes 480 tests with 99.00%
combined statement/branch coverage across 451 statements and 150 branches.
The energy module reaches 100% coverage. The executable report agrees with
exact rational discrete temperatures. CI status must be read from the actual
run for the delivered revision; local checks alone do not establish it.

Adverse tests retain opposite local residuals with zero global imbalance,
a 1 J remainder lost by subtracting rounded totals, and 1e-20 J of applied
heating whose temperature rise rounds away. Invalid maps, fixed-temperature
mismatches, nonfinite products, zero-rounded products and overflowing sums
are rejected. No material analytical issue remains for this increment.
Evidence supports these discrete balances and the two smooth refinement
fixtures. It does not establish general error bounds or physical validation.
