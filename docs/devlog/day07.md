# D07: backward-Euler networks

Completion date: 2026-09-22.

Added `solve_transient` and `TransientResult` for small constant-conductance
networks. Each nonfixed node requires positive heat capacity and an initial
absolute temperature. The ordered time grid defines integration steps and all
load changes. Optional full interval maps replace constant node loads. Fixed
reservoir temperatures stay exact at every output time.

The analytical review derives `(C/h+L_uu) T_new = (C/h) T_old+P-L_uf T_f`.
Positive capacities make the matrix positive definite, even for insulated
components. Linear mode factors are `1/(1+h*lambda)` with `lambda>=0`.
Internal link terms cancel in the summed balance. Exact scalar heating, an
insulated pair, a steady-state invariant and time/capacity scaling check limits.
See [the decision](../decisions/0007-backward-euler-networks.md).

An independently inverted two-node matrix is evaluated with exact rational
arithmetic across three unequal intervals and three signed load maps.
After 1 s the node temperatures are `3625/12 K` and `3605/12 K`; after the load
change and two more seconds they are `46967/156 K` and `47143/156 K`.
A 300 K reservoir is unchanged. Reversed link orientation gives the same
results. All comparisons pass the documented `2e-12 K` fixture budget.

D07 adds 66 tests. The complete local suite passes 444 tests with 98.88%
combined statement/branch coverage over 397 statements and 138 branches.
The new module has 100% coverage. Lint and formatting pass, and the executable
example agrees with the rational reference. These are local numerical checks;
public CI status must be read from the delivered commit's actual run.

Invalid input maps, grids and load counts are rejected. Signed extraction that
produces a nonpositive output fails. The numerical tests preserve a tiny load
with no representable temperature rise and an extreme-scale insulated system
whose rounded matrix becomes singular. The latter raises an error. A syntax
typo during test creation, a code-block spacing issue, and an incorrect second
row in the example's expected table were corrected before final checks. The
exact rational recurrence supplied the corrected expected values.

No material analytical issue remains for this discrete update. Stability does
not establish time accuracy, arbitrary-conditioning robustness, positivity
between grid points under extraction, or physical validation. Step energy
accounting and measured time refinement remain D08 work.
