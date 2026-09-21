# D06: closed-form one-node response

Use a scalar `rc_step` function and immutable `RCResult` for a constant-power
step with one resistance, one positive heat capacity and one fixed reservoir.
This directly represents the D06 equation without introducing a network time
integrator or changing the steady input schema.

The equation `C dT/dt=P-(T-Tb)/R` has the unique exponentially stable solution
derived in [the transient notes](../transient.md). Positive initial and
equilibrium temperatures keep the trajectory positive. Reject nonpositive
equilibrium for the whole step, including requests before a possible crossing
of zero kelvin under excessive extraction.

Report stored energy change in joules separately from instantaneous boundary
and storage powers in watts. Keep the analytic change independently of rounded
absolute temperature. Use `expm1` at short times and the nearer endpoint for
temperature to reduce cancellation. Reject nonfinite intermediates and an
unrepresentable time constant; document underflow and the conservative range
restriction rather than claiming arbitrary-range accuracy.

Independent decimal references, exact initial/long-time limits, monotonicity,
capacity/time scaling and integrated energy balance support this bounded API.
There is no time-discretization convergence claim because no integration step
is taken. Physical validation and multi-node transient integration are outside
this increment.
