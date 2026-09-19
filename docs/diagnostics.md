# Connectivity and steady heat balance

`check_connectivity(network)` returns connected groups of node IDs. It raises
`ValueError` listing all groups without a fixed-temperature boundary, including
isolated unknown nodes. Separate groups are valid when each has a boundary;
an isolated fixed node is also valid. Returned groups and their members follow
input node order. Link direction and parallel links do not change connectivity.

Positive conductances make a connected group's reduced conductance matrix
positive definite if it has a fixed boundary; see the [proof](networks.md#equations-and-uniqueness).
Without that boundary, a zero net load still leaves absolute temperature
undetermined. A nonzero net load cannot satisfy steady conservation. Both cases
are rejected. The check does not measure numerical conditioning.

## Read a heat-balance report

```python
from thermalpath import Link, Network, Node, heat_balance, solve_steady

network = Network(
    [Node("heater", power_w=10), Node("bath", fixed_temperature_k=300)],
    [Link("path", "heater", "bath", 2)],
)
solution = solve_steady(network)
balance = heat_balance(network, solution.link_powers_w)
print(balance.node_residual_w)  # {'heater': 0.0}
print(balance.boundary_power_w)  # {'bath': -10.0}
print(balance.total_input_w)  # 10.0
print(balance.total_output_w)  # 10.0
print(balance.imbalance_w)  # 0.0
```

The bath removes 10 W, so its signed input is -10 W. A hotter reservoir that
supplies heat has a positive boundary power. Reservoir power is inferred from
the supplied link flows; it is not an additional prescribed load.

`heat_balance` accepts a mapping with exactly the network's link IDs and finite
real powers in watts. Boolean, complex, missing, extra, and nonfinite inputs are
rejected. The function checks anchoring but does not solve temperatures. It also
accepts independently calculated or deliberately perturbed link powers, which
allows balance errors to be inspected. It leaves the input mapping unchanged.

## Signs and equations

For link a to b, q is positive from a to b. Define S_i as the sum of outward
link powers at node i. Add +q to S_a and -q to S_b. Then

```text
unknown node:  r_i = P_i - S_i            [W]
fixed node:    B_f = S_f                  [W]
whole network: I = sum_i P_i + sum_f B_f  [W]
```

Fixed nodes have zero prescribed P by the input contract. Positive residual r
means more input than outward flow; negative r means a deficit. For a consistent
steady solution, every r is zero within a justified arithmetic tolerance.
Summing S over all nodes cancels every internal link exactly in real arithmetic.
Consequently I equals the sum of the unknown-node residuals in exact arithmetic.
Floating-point summation can leave small differences between these quantities.

| Field | Meaning |
| --- | --- |
| `node_outflow_w` | S for every node, signed outward |
| `node_residual_w` | P minus outgoing flows for each unknown node |
| `boundary_power_w` | B at each fixed node, positive into the network |
| `total_input_w` | Sum of positive P and positive B |
| `total_output_w` | Positive magnitude of negative P and negative B |
| `imbalance_w` | Direct signed sum of P and B |

Dictionary fields retain node order and are independent mutable result copies.
The report has no automatic pass/fail threshold. Check every unknown-node
residual: opposite errors can cancel in the global imbalance, including across
separate components. A 1 W error on an internal link can produce residuals of
-1 W and +1 W while the global imbalance remains zero.

## Arithmetic and interpretation limits

Sums use [`math.fsum`](https://docs.python.org/3.12/library/math.html#math.fsum),
which tracks partial sums to reduce lost small terms. Nodal residuals use the
original incident powers rather than subtracting an already rounded outflow.
The global imbalance uses the external signed terms directly. For example,
sources of 1e16 W and 1 W against a 1e16 W sink give an imbalance of 1 W even
though subtracting the separately rounded totals gives zero. Boundary sums are
still rounded before global accounting. No summation method here recovers errors
already present in the supplied link powers.

A sum that overflows raises `ValueError`. Intermediate overflow may reject some
mathematically finite sums; the report does not rescale inputs or use arbitrary
precision. Floating-point results are not exact conservation certificates.

This is power accounting for the supplied flows. It does not check q=G(T_a-T_b),
temperature boundary agreement, or whether the powers came from the stated
network's solution. A divergence-free but incorrect circulation could pass the
balances. Use the matching solver result, inspect nodal errors alongside
temperatures and powers, and choose tolerances from the problem's scales and
required accuracy. A tiny load whose temperature difference rounds to zero is
reported as unbalanced; it is not silently accepted by a built-in tolerance.

There is no storage or time integration in this diagnostic, so there is no
time-step convergence parameter. The [test references](verification.md#d04-heat-accounting-references)
verify finite synthetic cases. They do not validate thermal properties,
measurements, device safety, or arbitrary ill-conditioned networks.
