# Bounded Monte Carlo inputs

`thermalpath.uncertainty.monte_carlo_network` samples independent uniform
ranges for a small steady thermal network. Use it to explore an explicitly
chosen input model. The ranges are assumptions supplied by the caller; they
are not inferred from measurements or certified material tolerances.

```python
from thermalpath import Link, Network, Node
from thermalpath.uncertainty import UniformInput, monte_carlo_network

network = Network(
    (Node("body", power_w=10), Node("sink", fixed_temperature_k=300)),
    (Link("path", "body", "sink", 2),),
)
study = monte_carlo_network(
    network,
    (
        UniformInput("power_w", "body", 8, 12),
        UniformInput("conductance_w_k", "path", 1, 3),
    ),
    count=64,
    seed=2026,
)
print(study.percentiles_k["body"])  # P5, P50, P95 in kelvin
print(study.failed_count)
```

The fields are `power_w` in watts on an unknown node,
`fixed_temperature_k` in kelvin on a fixed node, and `conductance_w_k` in W/K
on a link. Bounds must be finite and ordered, with a finite difference.
Temperature and conductance supports must be strictly positive. Equal bounds
give a constant input. Power may be negative, representing heat extraction.
There is no normal, triangular, correlated or fitted distribution in this API.

Each study has one to eight distinct inputs, one to 256 cases, and an explicit
integer seed between 0 and 2**64-1. Networks retain the sweep limits of 64 nodes,
128 links and 32768 characters per full case. Values in the same sample row
are evaluated together; this is not a Cartesian product of sample columns.
Every other network field keeps its base value.

## Reproduce and inspect a study

The result records the input specifications, seed, count, PCG64 generator name,
NumPy version, ordered samples and complete solver CSV. Sampling uses a local
`Generator(PCG64(seed))` with one `uniform` call of shape `(count, input_count)`.
Constant columns also consume draws. The global random state is unchanged.
Changing column order, count or call pattern changes the experiment.

Use the same environment to reproduce the stream. NumPy's
[random compatibility policy](https://numpy.org/doc/stable/reference/random/compatibility.html)
places conditions on exact stream reproduction; a seed alone is not a portable
archive of the experiment. Save the full result, for example with
`dataclasses.asdict` and JSON, as well as the source revision used. Actual
binary64 samples can include the upper endpoint through rounding, as described
in the [uniform sampler documentation](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.uniform.html).
Every returned sample is checked against its closed finite support. Tiny
ranges can collapse to very few distinct floats.

The `cases_csv` field uses the existing [sweep CSV format](studies.md).
`replay_network_sweep(study.cases_csv)` recomputes every saved input without
drawing again. It retains all original cases, including invalid solutions.
Each row contains temperatures, signed link powers, a linear residual and
global heat imbalance separately. Small residuals do not validate the assumed
input distribution or the physical model.

## What the percentiles mean

If every case succeeds, the result gives P5, P50 and P95 for every node in
kelvin, using NumPy's explicit
[`method="linear"` percentile definition](https://numpy.org/doc/stable/reference/generated/numpy.percentile.html).
For sorted temperatures y[0] through y[n-1], let h=(n-1)q/100, j=floor(h)
and w=h-j. The result is (1-w)y[j]+w*y[min(j+1,n-1)]. A single sample therefore
gives the same temperature at every level; it says nothing about the tails.

These are **conditional model outputs, not safety bounds**. They depend on the
chosen topology, loads, boundary conditions, constant conductances, uniform
supports and independence assumption. A sample P95 is neither a worst-case
temperature nor a confidence bound for the population P95. No failure
probability, sample-convergence guarantee or physical validation is supplied.

A positive conductance support does not guarantee a valid thermal output:
large negative power can give a nonpositive absolute temperature. Such cases
keep their sampled inputs and error. No case is removed, redrawn, clipped or
replaced. If **any** case fails, `percentiles_k` is empty for the whole study.
This avoids presenting percentiles conditioned on an undisclosed success-only
subset. The failed count is evidence about this finite run, not a certified
population failure rate.

## Synthetic example and independent checks

Run `python examples/network_uncertainty.py` to print a JSON report with 64
main cases and 16 separate adverse cases, both seeded with 2026. The main
example uses power uniform on [8,12] W and conductance uniform on [1,3] W/K.
Its scalar balance is T=300+P/G K. Under these exact model assumptions, the
full support lies between 302.6666666667 and 312 K by monotonicity in P and G.
That analytic model range is separate from the sampled percentiles and is
not a physical safety guarantee. The example is synthetic, not measured data.

Tests reconstruct uniforms from raw PCG64 bits, independently solve two-node
balances using rational arithmetic, and interpolate sorted reference outputs
with rational percentile weights. The absolute tolerance for thermal values
and balances is 2e-12 K or W, as applicable, with zero relative tolerance.
Fresh-process tests check repeatability and replay. Invalid inputs, mixed and
all-failed studies, constant inputs, narrow supports, maximum resource bounds
and unexpected internal errors are exercised. See [D21 evidence](devlog/day21.md)
for the measured example and gate results.
