# D04: connectivity and signed heat-balance diagnostics

Completion date: 2026-09-19.

Added `check_connectivity`, `heat_balance`, and `HeatBalance`. Connectivity
errors name every component missing a fixed-temperature boundary. Separate
anchored components retain their existing solver behavior. The balance report
gives outward node powers, unknown-node residuals, signed reservoir inputs,
total heat input/output, and a directly summed global imbalance, all in watts.

The [decision](../decisions/0004-heat-accounting.md) and
[equations](../diagnostics.md#signs-and-equations) record the sign and conservation
review. Each link appears with opposite endpoint signs. Fixed reservoirs can
supply or remove heat. A unique absolute steady temperature requires an anchor
in each positive-conductance component; zero net load alone is insufficient.
No material unresolved analytical issue remains within this scope.

The 34 new tests include an exact integer four-node ledger with 70 W input and
70 W output, and the D03 rational fixture with totals of 470/11 W. Boundary,
nodal, and global tolerances follow the documented link-power error budgets.
Other cases cover reverse orientations, parallel links, fixed-to-fixed transfer,
separate components, zero flows, component errors, invalid inputs, and overflow.

Adverse cases remain visible: opposite 1 W node errors can cancel globally;
a 1 W imbalance can survive even when rounded total input and output match;
and a 1e-20 W load can lose its solved temperature rise while retaining its
balance error. No automatic tolerance converts these outcomes into a pass.

The complete public test suite passed 212 tests with 100% package coverage over
219 statements and 78 measured branches. These synthetic tests verify the
reported accounting and tested failure behavior. They do not establish the
conductance law for arbitrary supplied flows, certify ill-conditioned solutions,
or constitute physical validation.

The complete quality gate, distribution inspection, and publication checks are
required on the final source bytes before delivery. CI is checked separately for
the delivered revision. D05 remains unfinished.
