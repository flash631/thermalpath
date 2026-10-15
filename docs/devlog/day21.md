# D21: bounded seeded Monte Carlo inputs

Date: 2026-10-15.

Added `UniformInput` and `monte_carlo_network` for independent uniform ranges
on network powers, fixed temperatures and conductances. Studies retain one to
eight input specifications, one to 256 paired samples, the explicit seed,
PCG64 generator, NumPy version and full replayable case CSV. Solver equations
and topology are unchanged. Every failure remains; any failed case suppresses
the percentile map. P5/P50/P95 are conditional model outputs, not safety bounds.

Analytical review checked support domains, SI units, floating-point endpoints,
anchored-network uniqueness, possible invalid temperatures under negative
loads, the absence of rejection bias and the linear sample-quantile formula.
The exact scalar example is T=300+P/G. Independent two-node rational balances,
raw-bit reconstruction and rational percentile interpolation passed at the
frozen absolute tolerance of 2e-12 K/W and zero relative tolerance. No material
unresolved analysis remains. This is numerical verification, not physical
validation of the model or its assumed input distributions.

With seed 2026 and NumPy 2.5.3, all 64 main example cases succeeded. Body
P5/P50/P95 were 303.29441041658225, 305.11357613337464 and
308.57521559062127 K. Maximum absolute difference from T=300+P/G was
5.684341886080802e-14 K. Maximum absolute global imbalance was
1.580957587066223e-13 W and maximum linear residual was
1.1368683772161603e-13 W. These are finite-case numerical checks, separate
from sampling error or physical accuracy.

The separate 16-case adverse example retained two nonpositive-temperature
failures, fourteen successful cases and no percentiles. It did not retry the
failed draws. Repeat runs produced identical reports in the tested environment,
and both case collections replayed without random sampling.

The complete gate passed 1122 public tests (48 added for this increment) and
73 private workflow tests. Package-wide coverage including branches was
99.60% over 1108 statements and 376 branches; uncertainty.py had 100% measured
coverage. Lint, formatting, builds and publication checks passed. Source archive
inspection matched all 176 tracked files; the wheel matched all 19 package
modules. A separately installed wheel reproduced the source example, and the
documentation example ran successfully. No later increment is included.
