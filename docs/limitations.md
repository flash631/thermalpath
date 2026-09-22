# Applicability limits

D01 models a steady chain with one prescribed power and one fixed sink
temperature. Every resistance represents a distinct thermal connection.
The calculation omits parallel losses, thermal storage, temperature-dependent
material properties, radiation, spreading resistance, and spatial variation.

Inputs are synthetic. No measurements, device datasheets, or experimentally
established uncertainty bounds support this example. A calculated source
temperature cannot establish compliance with a component limit unless the
network, load, environment, and limit are independently justified.

The later plate is depth averaged with prescribed convection. It will not solve
airflow, turbulence, boiling, or thickness gradients. It will not estimate a
convection coefficient from fan speed or enclosure shape.

Finite inputs can still exceed floating-point range. The API rejects a
nonfinite output and a conduction resistance that underflows to zero. Very small
finite temperature rises can round away when added to a much larger ambient;
the API does not promise relative accuracy on such a rise.

D03 extends the calculation to small constant-conductance networks with multiple
fixed boundaries and signed node loads. It retains the lumped-temperature and
steady-state assumptions. Every unknown node must reach a fixed boundary.
The dense solver rejects detected singularity and arithmetic range errors, but
does not certify accuracy for poorly conditioned systems or small temperature
differences. See [network limits](networks.md#numerical-scope). Conductances and
boundary conditions still require independent engineering justification.

D04 accounts for supplied link powers and inferred reservoir powers. Zero global
imbalance can hide nonzero node residuals, so each unknown-node balance must be
checked. Even zero nodal residuals do not verify the temperature/conductance law
or physical validity. Sums can overflow and boundary totals are rounded before
global accounting. See [diagnostic limits](diagnostics.md#arithmetic-and-interpretation-limits).

D06 represents one uniform-temperature body with constant positive heat capacity
and resistance to a fixed reservoir under constant signed power. It requires
positive initial and equilibrium temperatures. Stored energy change and power
can retain information lost from a rounded absolute temperature. Extremely small
time ratios and products can underflow, while conservative intermediate-range
checks can reject a finite requested result. See [RC scope](transient.md#numerical-scope).
The RC function has no network time integration or arbitrary-input error
certificate. No physical validation is claimed.

D07 adds constant-conductance network time integration with positive capacities,
fixed reservoirs and piecewise constant loads on an explicit time grid.
Backward Euler is stable for the passive linear model, but a coarse step can
have large temporal error. Finite positive grid temperatures do not prove a
positive continuous trajectory under extraction. Extreme scales can destroy
matrix accuracy, and small temperature rises may round away. There are no
step energy reports or time-refinement measurements yet. See
[transient network limits](transient_networks.md#limits).
