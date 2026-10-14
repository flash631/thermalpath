# Local network temperature sensitivities

`thermalpath.sensitivity.network_sensitivity` estimates how each steady node
temperature changes when one load, fixed boundary temperature, or link
conductance changes. All other inputs and the network topology stay fixed.
It uses the existing steady solver and the complete case records from
[network sweeps](studies.md).

```python
from thermalpath import Link, Network, Node
from thermalpath.sensitivity import network_sensitivity

base = Network(
    (Node("body", power_w=10), Node("sink", fixed_temperature_k=300)),
    (Link("path", "body", "sink", 2),),
)
study = network_sensitivity(base, "conductance_w_k", "path", (0.5, 0.25, 0.125))
for estimate in study.estimates:
    print(estimate.step, estimate.status, estimate.dimensional, estimate.scaled)
```

Supply 3 to 16 distinct positive absolute steps in W, K, or W/K, matching the
field. Their order is preserved. Networks retain the sweep limits of 64 nodes,
128 links, and 32768 characters per case specification. At most 33 cases are
solved: one baseline and two per step. A failed baseline raises `ValueError`.

## Derivative and units

Let the baseline parameter be p0 and its rounded perturbed values be lower and
upper. Define hm = p0 - lower and hp = upper - p0. For each node, the estimate is

```text
D = hm/(hm+hp) * (Tupper-T0)/hp + hp/(hm+hp) * (T0-Tlower)/hm.
```

This is the derivative of the quadratic interpolant at p0, allowing unequal
floating-point spacings. Taylor expansion cancels the second derivative term.
For a smooth response, the leading error is hm*hp*T'''(p0)/6. Equal steps
therefore have second-order truncation error. The anchored steady system
A(p)T=b(p) is smooth in the interior where positive conductances preserve its
positive definite matrix. This does not establish accuracy for arbitrarily
small steps or poorly conditioned networks.

`dimensional` contains dT/dp in K/W for power, K/K for prescribed temperature,
or K/(W/K) = K squared/W for conductance. `scaled` contains (p0/T0)*dT/dp,
which is dimensionless. T0 is the absolute temperature in kelvin, never a
Celsius value or a temperature rise. The scaled derivative is signed; at
p0=0 it is zero even when the dimensional derivative is nonzero. This scaling
does not describe relative changes about a zero input. All nodes are reported,
including fixed nodes with zero derivatives or the directly changed boundary
with derivative one.

## Constraints and numerical limits

Both perturbed cases must pass the existing physical and solver checks.
Conductances and prescribed temperatures must remain positive; extracted heat
must not make a solved temperature nonpositive. Failed estimates retain the
requested step, actual values, error, and both case records when representable.
Their derivative maps are empty. No automatic step reduction or one-sided
approximation is performed. Collapsed or nonfinite abscissae, an overflowing
span, and nonfinite derivative/scaling arithmetic are reported as failures.
For nonfinite abscissae, the result can contain infinity; callers serializing
such a failed record must explicitly encode it, rather than label it finite.

An `ok` status means the stencil was evaluated. It is not an error bound.
Subtraction can lose small temperature changes; finite underflow can erase a
derivative. Small steps may therefore give a zero or noisy estimate. Inspect
several steps against a reference when available; the function does not select
an optimum step or claim convergence from agreement alone. The validity is
local to this fixed topology and the model's physical domain. Near a constraint,
failed steps give no sensitivity on the excluded side and no global bound.

`base_case_csv` and each estimate's `cases_csv` contain full SI inputs,
temperatures, link powers, solver residuals and heat-balance closure. They can
be recomputed with `replay_network_sweep`; this replays the solver cases,
not the derivative calculation. The derivative formula, actual parameter
values, and retained temperatures provide the remaining calculation.

## Independent reference

Run `python examples/network_sensitivity.py`. Two unknown nodes have loads
Pa=12 W and Pb=4 W, a 300 K sink, conductance g=2 W/K between a and b, and
4 W/K between b and the sink. Node balances give

```text
Tb = 300 + (Pa+Pb)/4 = 304 K,
Ta = Tb + Pa/g = 310 K,
dTa/dg = -Pa/g**2 = -3 K squared/W.
```

For equal steps h, the finite-difference result is exactly -12/(4-h squared).
The absolute truncation error is 3*h squared/(4-h squared). At h=0.5, 0.25,
and 0.125 W/K, the exact errors are 1/5, 1/21, and 1/85 K squared/W.
The h=2 W/K stencil is retained as failed because its lower conductance is
zero. Tests independently check differentiated two-node balances, rational
finite-step errors, signed and zero-input scaling, unequal binary64 spacing,
and the runnable report. These are numerical verification cases; they do not
provide physical validation or a device safety assessment.
