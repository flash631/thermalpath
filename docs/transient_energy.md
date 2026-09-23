# Transient energy and time refinement

`transient_energy_balance` accounts for one step from supplied old and new
temperature maps. It returns `TransientEnergyBalance`, with per-node storage,
source, reservoir and residual energies, plus signed totals. All energies are
joules. Positive source and reservoir energy enter the network; positive storage
means warming. Negative values represent extraction, reservoir removal or cooling.

```python
from thermalpath import Link, Network, Node, solve_transient, transient_energy_balance

network = Network(
    (Node("body", power_w=10), Node("bath", fixed_temperature_k=300)),
    (Link("loss", "body", "bath", 2),),
)
capacity = {"body": 2}
result = solve_transient(network, capacity, {"body": 300}, [0, 1])
balance = transient_energy_balance(
    network, capacity, result.temperatures_k[0], result.temperatures_k[1], 1
)
assert balance.storage_j == {"body": 5}
assert balance.source_j == {"body": 10}
assert balance.boundary_j == {"bath": -5}
assert balance.node_residual_j == {"body": 0}
assert balance.imbalance_j == 0
```

Capacity maps contain exactly the nonfixed nodes; both temperature maps contain
every node, including reservoirs. Fixed temperatures must match the network in
both snapshots. Duration, capacities and absolute temperatures must be positive
and finite. Optional `powers_w` replaces all nonfixed-node loads for this step.
When using `interval_powers_w` in the solver, pass the corresponding map here.
No load history is inferred from temperature snapshots. Insulated, disconnected
and all-fixed networks are allowed; no steady-state anchoring is required.

## Step equations

For a step of duration h, define an oriented link energy from a to b using the
new temperatures:

```text
E_ab = h G_ab (T_new_a - T_new_b)              [J]
S_i  = C_i (T_new_i - T_old_i)                 [J]
Q_i  = h P_i                                 [J]
r_i  = Q_i - sum(outward E at i) - S_i         [J]
B_f  = sum(outward E at fixed node f)         [J]
R    = sum(Q_i) + sum(B_f) - sum(S_i)          [J]
```

The backward-Euler equation gives r_i = 0 in exact arithmetic. Each internal
link enters its two node equations with opposite signs. Summing leaves only
reservoir exchange, hence R = sum(r_i). A link between two reservoirs contributes
opposite energies to their individual reports and zero net energy. Reservoirs
have no storage term: their temperatures are prescribed and the external source
or sink maintains them.

The source term is the exact integral of a constant prescribed load over the
step. The link term uses endpoint quadrature, the same approximation as backward
Euler. It is generally not the exact continuous-time conductive energy integral.
Thus a nearly zero discrete residual can coexist with a large temperature error.

## Four fixed time grids

Run `python examples/transient_refinement.py` for a JSON report. The synthetic
case has C = 10 J/K, G = 0.5 W/K, P = 5 W, a 300 K reservoir, initial temperature
300 K and final time 20 s. Its exact temperature is
`310 - 10 exp(-t/20) K`, so the final reference is `306.3212055882856 K`.
The predefined steps are 4, 2, 1 and 0.5 s, with 5, 10, 20 and 40 steps.

| Step [s] | Final temperature [K] | Absolute error [K] | Observed order |
| ---: | ---: | ---: | ---: |
| 4 | 305.981224279835 | 0.339981308450 | n/a |
| 2 | 306.144567105705 | 0.176638482581 | 0.944656 |
| 1 | 306.231105171270 | 0.090100417016 | 0.971194 |
| 0.5 | 306.275693763022 | 0.045511825264 | 0.985292 |

These are executed numerical results, rounded for display. The order is
`log2(error_h/error_(h/2))`. For a decaying mode, backward Euler gives
`(1+h/tau)^(-t/h)`. Expanding its logarithm gives
`-t/tau + t*h/(2*tau^2) + O(h^2)`, so the leading global error is proportional
to h. The measured orders approach one as expected.

On the 0.5 s grid, total applied energy is 100 J, storage change is
62.756937630219 J and reservoir input is -37.243062369781 J. Across all four
grids the largest individual step imbalance is below `5e-13 J`, while the
finest final-temperature error remains 0.0455 K. Rounding and platform arithmetic
can change the last digits; the automated fixture budget is stated in
[verification](verification.md#d08-energy-and-temporal-verification).

Tests also refine an insulated coupled pair with C_a = C_b = 2 J/K,
G_ab = 1 W/K and initial temperatures 310 and 290 K. The mean remains 300 K;
the modes are `300 +/- 10 exp(-t) K`. Four steps 0.2, 0.1, 0.05 and 0.025 s
reach 1 s. This checks a coupled conduction mode and conserved total storage.

## Interpretation and range limits

Inspect every node residual as well as the global imbalance. Opposite local
errors can cancel. The routine accepts arbitrary valid temperature snapshots;
it checks their energy balance without claiming that they came from the solver.
There is no automatic tolerance or accuracy verdict. Use a tolerance justified
by the problem's scales and required accuracy.

Sums use `math.fsum`. The global imbalance and total reservoir input use
individual terms rather than rounded subtotal subtraction. Displayed subtotals
can therefore differ in their last digits from these direct sums. Nonfinite
products, overflowing sums and nonzero products rounded to zero raise
`ValueError`. Intermediate link power must fit before multiplication by duration;
this can reject a finite final energy. Subnormal nonzero products are allowed
and may have poor relative accuracy. These checks do not bound floating-point
error. Differences already lost from supplied temperatures cannot be recovered:
a 1e-20 W isolated load over 1 s at 300 K gives zero reported storage and a
1e-20 J residual.

The refinement evidence covers these two smooth linear fixtures only. Load
changes must remain grid-aligned in any refined piecewise case. No general
adaptive time-step selection, error certificate or physical validation is provided.
