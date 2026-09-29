# D14: plate balance, residuals and singularity checks

Completion date: 2026-09-29.

Added immutable `PlateBalance` reports to computed plate results. Physical cell
residuals and direct global imbalance remain separate from the actual assembled
matrix residual. Reports include mapped heater input and signed exterior edge
and broad-face powers. The network solver exposes the matrix residual it
computes from its own assembled bytes. Older result constructors remain usable.
See [the decision](../decisions/0014-plate-diagnostics.md).

Analytical review checked watts, signs, internal-face cancellation, graph
connectivity, the anchored positive quadratic form, the constant nullspace
without losses, and net-input compatibility. Unanchored cases now distinguish
incompatible prescribed input from balanced but nonunique absolute temperature.
The check retains small terms before cell-load rounding; it uses no arbitrary
near-zero tolerance or imposed reference temperature.

Independent two-cell matrix references test both axes and three power scales.
Deliberately incorrect temperatures give -12 W and +12 W local residuals with
zero global imbalance. A mixed single cell gives 302 K, 10 W heater input,
2 W lateral loss and 8 W broad loss. Tests also cover inward exchange, immutable
reports, old constructors, overflow, and numerical singularity despite a weak
positive anchor. The [diagnostic documentation](../plate_diagnostics.md)
derives fixture tolerances and states the acceptance limits.

Adverse cases remain explicit: 1e-20 W heating and the smallest positive
binary64 heater can have zero matrix residual but nonzero physical imbalance;
a boundary-temperature difference can also be unresolved. Direct accounting
retains a 1 W remainder lost by rounded 1e16 W subtotals. No spatial convergence
or physical validation is claimed. CI evidence must be checked for the
delivered revision.
