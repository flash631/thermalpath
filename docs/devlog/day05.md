# D05: versioned JSON cases and network command

Completion date: 2026-09-20.

Added `loads_case` and `dumps_case` for strict version-1 network inputs, the
`thermalpath run-network` console command, a module entry point, and a synthetic
heater case. Output includes temperatures, signed link powers, and the existing
heat-balance diagnostics. The [schema](../cases.md) defines required fields,
defaults, SI units, round-trip behavior, numerical limits, and exit codes.

The [decision](../decisions/0005-network-cases.md) records the analytical review.
The interface preserves the existing equations, boundary conditions, and signs.
No new physical model or numerical solver was introduced. Decimal tokens round
to binary64; normalized values round-trip exactly. Duplicate and unknown fields,
invalid versions and model domains, nonfinite numbers, and underflow to zero
are rejected. Parsing alone does not establish a unique steady solution.

The 78 new tests check strict parsing, defaults, ordered round trips, signed
loads, UTF-8 identifiers, process exit codes, file/encoding errors, and output
failure. The CLI independently reproduces 305 K and 10 W for the heater case,
and 3370/11 K and 3400/11 K for the two-boundary reference. Rational temperature
and link-power tolerances are 1e-11 K and 1e-10 W; source/sink and imbalance
tolerances are 2e-10 W and 4e-10 W, using the D03/D04 propagation budgets.

The small-load regression preserves a 1e-20 W nodal/global residual when the
temperature rise rounds away. Exit code zero does not convert that residual
into a verified balance. No material unresolved analytical issue remains.

The complete public suite passed 290 tests with 99.48% combined package
coverage over 288 statements and 100 measured branches. The module-launch
guard is executed by subprocess integration tests but is not counted by the
in-process coverage collector. No coverage scope was excluded. The checked
references are synthetic verification, without physical validation or an
arbitrary-conditioning accuracy guarantee.

The complete quality gate, distribution inspection, and publication checks are
required on the final source bytes before delivery. CI is checked separately
for the delivered revision. D06 remains unfinished.
