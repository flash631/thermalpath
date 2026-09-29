# Decision: retain separate physical and matrix residuals

D14 adds `PlateBalance` to computed plate results. The report contains every
cell's physical residual, the actual assembled-system residual, mapped heater
input, signed exterior edge totals, combined broad-face outflow and a direct
signed global imbalance. Both residuals use positive excess-input signs.

The network solver already owns the assembled matrix and right-hand side.
It now reports `b-A*T` for its unknown nodes; this avoids rebuilding a second
matrix whose assembly could differ. Plate accounting independently uses the
recovered face powers and original mapped heater powers. Shared internal faces
cancel by construction. Global accounting uses individual exterior terms so
rounded subtotals cannot conceal a small remainder.

The plate's positive-conductance graph is connected. Without a fixed or
positive-film anchor, zero net prescribed input leaves an additive temperature
nullspace; nonzero net input is incompatible with steady conservation. Both
remain errors, now with different messages. No reference-temperature gauge,
near-zero tolerance, residual pass flag or new solver algorithm is introduced.

Independent fixtures test exact balances, incorrect temperatures with cancelling
local errors, and a zero matrix residual with nonzero physical heating.
The [derivation and tolerances](../plate_diagnostics.md) explain the limits.
