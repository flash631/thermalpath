# D01: verified series thermal resistance

Implemented two public functions: uniform-layer conduction resistance and source
temperature for one steady series path. Added a headless JSON example, independent
verification, public documentation, a 30-increment roadmap, the same Windows/Ubuntu
CI gate, and tested privacy/state helpers for native desktop development.

The model integrates Fourier's law: `R = L/(k A)` and
`T_source = T_sink + P sum(R)`. Positive power flows toward the fixed sink;
properties are constant and lateral losses/storage are absent. The independent
rational result is `R_TIM = 1/20 K/W`, `T_source = 3639/10 K`, or 90.75 °C.
The interface-only improvement bound is 0.75 K for this example.

The analytical review is resolved locally; no GPT Pro request was necessary.
See [the decision](../decisions/0001-series-path.md) and
[verification tolerances](../verification.md). D01 has no discretization,
so mesh/time-step convergence is not claimed. The tests include signed balance
and equivalent layer subdivision.

An initial local run passed 101 tests with 100% combined package coverage.
Further workflow review added stricter research metadata checks and caught a
Windows CRLF parsing defect, which was corrected with explicit line-ending tests.
The complete local quality gate passed Ruff lint/format checks, pytest with
branch coverage, and wheel/source builds. All 50 package statements and 14
branches were covered (100% combined). The final suite contains 114 tests,
including a separate next-day crash-recovery regression. Dependency consistency
was checked with pip check. Earlier failures remain in private logs; they are
not presented as successful checks. The gate is rerun on the final publication
snapshot; exact delivery and CI status are recorded privately.

The privacy workflow scans candidate and staged contents, outgoing commit trees,
messages and effective identities with redacted findings. Raw research exchanges,
local settings, snapshots and logs stay ignored. Standard official checkout and
setup-python action tags were resolved to the pinned commit IDs in CI.
No CI execution is claimed before an actual remote run is inspected.

The native task must be created only after successful D01 publication/readiness.
Its actual ID, timezone configuration, next run and delivery evidence stay in
private/app state. The tracked recurring prompt alone is not a scheduled task.

Remaining limits: single prescribed heat path, synthetic inputs, no physical
measurements, no airflow/convection prediction, and no plate/network/transient
solver yet. Operational completion does not establish engineering validation.

Interview question: why does the same power flow through each series resistance,
and what omitted physical heat path would make that assumption fail?
