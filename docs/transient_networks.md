# Backward-Euler thermal networks

`solve_transient` integrates a small lumped network with constant conductances,
positive heat capacities, and constant prescribed temperatures. Inputs use
seconds, watts, joules per kelvin, watts per kelvin, and absolute kelvin.
Positive load adds heat. A negative load extracts heat.

## Inputs and load changes

Use the existing `Network`, `Node`, and `Link` records. Supply heat-capacity and
initial-temperature maps containing exactly the nonfixed node IDs. Fixed nodes
are ideal reservoirs: they have no stored energy in this model, and their
prescribed temperatures apply to the initial state and every later state.
Insulated nodes and disconnected components are allowed.

The time grid is a list or tuple of at least two finite nonnegative, strictly
increasing times. The first time identifies the initial state; it need not be
zero. Each adjacent pair defines one integration step. Floating-point conversion
must retain distinct grid values.

`interval_powers_w=None` uses `Node.power_w` throughout. Otherwise supply exactly
one complete nonfixed-node power map per interval. These maps replace the node
loads, including explicit zero values. Map i acts on `[times[i], times[i+1])`.
The temperature at the right endpoint results from that interval's load. The
next map starts the next step; it causes no instantaneous temperature jump.
Every intended change must appear in the grid. There is no interpolation,
automatic event insertion, or time-dependent boundary temperature.

```python
from thermalpath import Link, Network, Node, solve_transient

network = Network(
    (Node("a"), Node("b"), Node("sink", fixed_temperature_k=300)),
    (Link("ab", "a", "b", 1), Link("a0", "a", "sink", 2), Link("b0", "b", "sink", 1)),
)
result = solve_transient(
    network,
    heat_capacities_j_k={"a": 2, "b": 3},
    initial_temperatures_k={"a": 300, "b": 300},
    times_s=[0, 1, 3],
    interval_powers_w=[{"a": 10, "b": 0}, {"a": 0, "b": 6}],
)
print(result.temperatures_k[1])
# a: 302.0833333333333 K, b: 300.4166666666667 K, sink: 300 K
```

Run `python examples/transient_network.py` for the complete table. Results have
`times_s` and `temperatures_k`, including the initial state. Each temperature
map is a separate copy, ordered like the input nodes.

## Update equation and checks

Let `C` be the diagonal matrix of nonfixed-node heat capacities [J/K], `L` the
conductance Laplacian [W/K], and `u,f` the nonfixed and fixed partitions. The
model is

```text
C dT_u/dt = P_u - L_uu T_u - L_uf T_f.
(C/h + L_uu) T_u_new = (C/h) T_u_old + P_u - L_uf T_f.
```

Each update term has units W. The load is constant over the step of length
`h > 0`; backward Euler evaluates conductive loss at the new temperature.
An internal link adds `G*(T_a-T_b)` to outward flow at a and its negative at b,
so internal exchanges cancel when summing the governing node equations.

For any nonzero vector v, `v^T L_uu v` is a sum of nonnegative link terms:
`G*(v_a-v_b)^2` for internal links and `G*v_a^2` for reservoir links.
Thus `v^T (C/h+L_uu) v > 0`. The update is unique even without a reservoir.
For the unforced perturbation, `C^(-1/2) L_uu C^(-1/2)` has eigenvalues
`lambda >= 0`. Each mode is multiplied by `1/(1+h*lambda)`, in `(0,1]`.
A zero mode in an insulated component persists; it does not decay to a unique
reservoir temperature. Nonnegative loads and positive old/boundary temperatures
produce positive new temperatures in exact arithmetic because the update matrix
has a nonnegative inverse. Signed extraction does not have that guarantee.

Backward Euler is first order for smooth time evolution: inserting a smooth
exact solution gives a derivative residual proportional to h. Unconditional
linear stability does not mean that a large step is accurate. This increment
verifies the discrete update; a measured time-refinement study is separate work.

## Limits

The dense binary64 solve is intended for small networks. Overflow, arithmetic
underflow detected during assembly, numerical singularity, and nonfinite or
nonpositive temperatures raise `ValueError`. Extreme scale ratios can erase a
capacity contribution and produce a numerically singular insulated system.
A finite solve does not certify conditioning or accuracy. A tiny heat input can
leave the rounded absolute temperature unchanged. No continuous-trajectory
positivity guarantee is provided for signed extraction between grid points.

The result provides temperatures only. It does not report step energy balances,
an error estimate, or a physical validation result. No experimental data were
used. The JSON case schema and steady CLI are unchanged.
