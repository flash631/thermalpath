# D04 decision: report signed local and global power balances

Expose `check_connectivity` and `heat_balance` with a `HeatBalance` result.
The steady solver uses the same connectivity check so failures identify the
unanchored components. Keep the established support for separate anchored
components: disconnected geometry alone does not make a steady problem invalid.

Use a supplied link-power mapping for accounting. This keeps the check separate
from matrix assembly and permits independent reference flows and adverse cases.
Require exact link IDs and finite real values. Do not imply that matching IDs
establish provenance or verify the conductance law. Keep the solver result API
unchanged and let the caller request a report explicitly.

The [derivation](../diagnostics.md#signs-and-equations) checks dimensions and
signs by assigning each link once with opposite endpoint signs. Unknown-node
residuals are applied load minus outward power. Fixed-node reservoir input equals
outward power. Internal cancellation establishes whole-network conservation,
while the individual residuals reveal errors that cancel in the total.

Use accurate floating-point sums, including the original incident terms in
each residual. Compute the global imbalance directly, since subtracting large
rounded source and sink totals can hide a small error. Keep units dimensional
and expose residuals without a universal tolerance or a success flag.

Review covers integer and rational multi-node ledgers, reverse orientations,
parallel links, fixed-to-fixed transfer, independent components, zero flow,
balanced and unbalanced floating groups, and arithmetic overflow. Preserve a
tiny-load case whose solved temperature rise vanishes but whose balance error
remains visible. Anchoring establishes mathematical uniqueness under positive
conductance; it does not ensure numerical accuracy. No material unresolved
analysis remains for this bounded diagnostic. Temperature-law consistency,
condition estimates, transients, and physical validation are outside this change.
