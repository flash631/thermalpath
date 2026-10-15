# D21 decision: bounded independent uniform input studies

Use independent uniform distributions for one to eight steady-network inputs,
with explicit finite supports, a caller-supplied seed and at most 256 paired
cases. This supports a small reproducible experiment without adding fitted
distributions, correlations, adaptive sampling or design selection.

For each input, X=lower+(upper-lower)U with U uniform on [0,1). Floating-point
rounding can include either bound. Reject nonfinite or reversed supports and
nonfinite support widths. Equal bounds represent constants. Require positive
temperature and conductance supports, preserve negative power, and verify
generated values against the closed supports without clipping. Use a local
PCG64 generator and record the NumPy version and full sampled cases.

The steady solver is unchanged. Positive conductances and a prescribed
temperature in every connected component yield a positive-definite reduced
conductance matrix and a unique algebraic solution. Negative loads may still
produce nonpositive absolute temperatures, and finite arithmetic can fail.
These failures remain in the CSV. There is no rejection/resampling step and no
claim that passing samples establish validity throughout the support.

Compute sample P5/P50/P95 with the explicit linear order-statistic interpolation
only when all cases succeed. Omit the whole percentile map after any failure;
report its count and every case instead. This avoids hidden conditioning on a
successful subset. The finite percentiles describe the assumed input model;
they do not certify tails, extrema, design feasibility or physical validity.

Independent verification uses raw PCG64 words for the sampling transformation,
exact rational two-node heat balances for each draw, and rational interpolation
weights for sorted reference temperatures. Fixed absolute tolerances are
2e-12 K/W, with zero relative allowance. Stream/replay equality is checked in
the tested environment; cross-version and cross-platform bit identity is not
promised. The documented NumPy stream restrictions and finite support limits
are part of the result's interpretation. No material unresolved analytical
issue remains within this bounded scope.
