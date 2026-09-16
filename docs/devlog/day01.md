# D01: verified series thermal resistance

Implemented two public functions: uniform-layer conduction resistance and source
temperature for one steady series path. Added a headless JSON example,
verification tests, engineering documentation, packaging, a 30-increment roadmap,
and the same quality gate on Windows and Ubuntu.

The model integrates Fourier's law: `R = L/(k A)` and
`T_source = T_sink + P sum(R)`. Positive power flows toward the fixed sink;
properties are constant and lateral losses/storage are absent. The independent
rational result is `R_TIM = 1/20 K/W`, `T_source = 3639/10 K`, or 90.75 °C.
The interface-only improvement bound is 0.75 K for this example.

See [the derivation and decision](../decisions/0001-series-path.md) and
[verification tolerances](../verification.md). D01 has no discretization,
so mesh/time-step convergence is not claimed. Tests include signed heat balance,
equivalent layer subdivision, scaling, zero cases, invalid domains and numerical
range limits.

An early D01 run passed 101 tests; the final original run passed 114 tests.
Those historical counts reflect the original test inventory; they do not
describe the current product suite.
The measured package coverage was 100%: all 50 statements and 14 branches.
The numerical implementation, references, tolerances, and physical assumptions
are unchanged. Run the current product suite for its present test count.

D01 passed Ruff lint/format checks, pytest with branch measurement, wheel/source
builds and dependency consistency checks. The published D01 commit also passed
both Windows and Ubuntu CI. Those results refer to the tested revision; later
revisions require their own checks.

Remaining limits: single prescribed heat path, synthetic inputs, no physical
measurements, no airflow/convection prediction, and no plate/network/transient
solver yet. Passing numerical checks does not establish physical validation.

Engineering question: why does the same power flow through each series
resistance, and what omitted physical heat path would make that assumption fail?
