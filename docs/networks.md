# Steady thermal networks

`solve_steady(network)` returns node temperatures in kelvin and signed link powers
in watts. Conductances and loads are constant. The model assumes steady heat flow
between lumped nodes; each node has one temperature and no energy storage.

```python
from thermalpath import Link, Network, Node, solve_steady

network = Network(
    nodes=(Node("heater", power_w=10), Node("sink", fixed_temperature_k=300)),
    links=(Link("path", "heater", "sink", conductance_w_k=2),),
)
result = solve_steady(network)
print(result.temperatures_k)  # {'heater': 305.0, 'sink': 300.0}
print(result.link_powers_w)  # {'path': 10.0}
```

Both dictionaries use the input IDs and preserve input order. They are independent
copies that the caller may edit. Positive link power goes from `node_a` to
`node_b`; reversing those endpoints reverses its sign. Negative node power means
heat extraction. A fixed node represents a reservoir whose temperature is imposed.
Its input load must be zero; that does not mean its reservoir exchanges zero heat.

## Equations and uniqueness

For every unknown node i, outgoing heat equals the applied load:

```text
sum_j G_ij (T_i - T_j) = P_i
L_ii = sum_j G_ij,     L_ij = -sum(conductances between i and j)
L_uu T_u = P_u - L_uf T_f
```

Here u denotes unknown temperatures and f denotes prescribed temperatures.
The matrix entries have units W/K, its temperature product has units W, and
positive P adds heat. Parallel links add conductance. The implementation assembles
only the unknown-node matrix and moves fixed-neighbor terms to the right side.
Fixed-to-fixed links contribute to reported power without adding unknowns.

For a vector x on unknown nodes, extend x by zero at fixed nodes. Then

```text
x^T L_uu x = sum_links G_ab (x_a - x_b)^2.
```

All conductances are strictly positive. This expression is positive for every
nonzero x precisely when every unknown node has a path to a fixed node. Thus the
reduced matrix is symmetric positive definite and the real-valued solution is
unique under that condition. The solver checks reachability before assembly.
Separate components are allowed if each is anchored. An isolated fixed node is
also allowed. A component without a fixed temperature is rejected even with zero
net load: its absolute temperature is undetermined. With nonzero net load it
cannot satisfy steady balance at all.

An algebraically unique solution can still have a nonpositive absolute
temperature when extraction is excessive. The solver rejects that result rather
than accepting it as a physical state. It also rejects nonfinite temperatures,
detected arithmetic range errors, numerical singularity, and link power that
overflows or underflows to zero.

## Numerical scope

The solver uses a dense binary64 matrix and
[`numpy.linalg.solve`](https://numpy.org/doc/stable/reference/generated/numpy.linalg.solve.html).
NumPy documents a direct LAPACK solve for square full-rank systems. Dense storage
grows quadratically and solve work cubically with the number of unknown nodes;
this implementation is intended for small networks. There is no iterative or
mesh convergence criterion for this lumped steady calculation.

Mathematical uniqueness does not ensure an accurate floating-point answer.
Extreme conductance ratios can erase a weak boundary contribution or make the
matrix poorly conditioned, meaning small arithmetic errors cause larger solution
errors. A singular assembled matrix is rejected. No general condition estimate,
forward-error certificate, or automatic rescaling is returned. Boundary products
or sums outside float range are rejected even if a differently scaled formulation
could solve the mathematical problem. Small temperature differences can round
away; their powers may then be zero despite a small nonzero exact heat flow.
The link underflow check cannot recover a difference already lost to rounding.

The [verification cases](verification.md#d03-network-references-and-tolerances)
check finite synthetic networks with justified tolerances. They do not validate
conductance values, device geometry, or temperatures measured on hardware.
The [connectivity and heat-balance diagnostics](diagnostics.md) report component
membership, unknown-node residuals, and signed reservoir powers.
