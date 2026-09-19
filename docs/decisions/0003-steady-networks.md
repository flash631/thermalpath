# D03 decision: eliminate fixed temperatures before solving

Use the D02 input records unchanged and expose `solve_steady` with a
`SteadyResult` containing temperatures and signed link powers indexed by ID.
Assemble the reduced conductance matrix directly, summing parallel links and
putting fixed-temperature contributions on the right side. Use a dense direct
solve for small networks. All-fixed networks require only power evaluation.

The [derivation](../networks.md) establishes dimensions, the load/flow signs,
and uniqueness when each unknown node reaches a fixed-temperature node. A short
reachability check is necessary to reject nonunique problems before a numerical
solver can return a misleading result. This check is part of the solver contract;
it does not introduce D04's component or reservoir-balance reporting API.

Link powers use the same temperature difference at both endpoints and opposite
signs in physical balance. The independent two-boundary reference checks each
unknown-node balance. The series reference checks the D01 limiting geometry
without calling the D01 calculation to generate expected values. Uniformly
scaling loads and conductances leaves temperatures unchanged. Reordering inputs
and reversing link directions preserves temperatures and reverses reported signs.

Review of numerical range included a weak anchor lost during matrix assembly,
overflow in diagonal sums and boundary products, underflow of a boundary product,
nonpositive temperature under excessive extraction, and link-power range loss.
Detected failures raise `ValueError`; finite results carry no general accuracy
guarantee. Tolerance budgets and conditioning are documented separately from
physical uncertainty. No material unresolved analysis remains for this bounded
constant-conductance solver. Nonlinear properties, transients, sparse solving,
and measured-device validation are outside D03.
