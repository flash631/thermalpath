# D06: one-node RC response

Completion date: 2026-09-21.

Added `rc_step` and immutable `RCResult` for a constant-power step with one
positive resistance and heat capacity. Results contain temperature, time
constant, stored energy change, boundary power and storage rate with explicit
SI units and signs. The steady-network schema remains unchanged.

The analytical review derives `C dT/dt=P-(T-Tb)/R`, `tau=RC` and the exponential
solution. Positive initial and equilibrium temperatures imply a positive,
monotone trajectory; deviations decay, establishing stability and uniqueness.
Stored energy is relative to the initial state. Instantaneous power balance and
the time-integrated boundary heat both follow from the same conservation law.
The [decision](../decisions/0006-one-node-rc.md) records implementation choices.

Independent 70-digit decimal references cover 24 combinations of elapsed time,
initial temperature and signed load. For the 300 K, 5 W, 2 K/W, 10 J/K case,
the 20 s result is 306.3212055882856 K with 63.2120558828558 J stored,
3.16060279414279 W flowing to the boundary and 1.83939720585721 W entering
storage. Integrated boundary heat is 36.7879441171442 J out of 100 J applied.
Initial/long-time limits, signs, monotonicity, capacity/time scaling and the
initial slope also pass. Tolerances and the finite reference scope are documented
in [verification](../verification.md#d06-rc-response).

D06 adds 88 tests. The local full suite passes 378 tests with 98.66% combined
statement/branch coverage over 336 statements and 112 branches. The two unexercised
transient guards reject nonfinite or nonpositive final outputs; domain and
intermediate-range rejection paths are exercised. The existing CLI module-launch
guard runs in subprocess tests outside in-process coverage. Lint and formatting
checks pass, and the subprocess example matches its independent expected values.

Small changes remain available in the energy/power fields when the temperature
rounds to 300 K. A dimensionless time that underflows gives zero energy change;
this adverse outcome is retained. Range checks conservatively reject an
unrepresentable full-step energy scale even for short elapsed times. These tests
provide numerical verification, not a universal error certificate or physical
validation. No material analytical issue remains for this bounded increment.
Multi-node integration and piecewise loads remain later work.
