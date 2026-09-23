# D08 decision: explicit step energy and fixed refinement fixtures

Keep energy accounting separate from the temperature solver. The function takes
one duration, two complete temperature maps, capacities and the applied interval
loads. This allows checking altered or independently obtained snapshots without
solving them again. The existing temperature result and JSON/CLI contracts remain
unchanged. No automatic refinement controller is needed for this increment.

Use C times temperature change for storage, duration times signed applied power
for sources, and duration times endpoint conductive power for links. Fixed nodes
have zero modeled storage and supply their net outward link energy. Internal
links cancel exactly in the analytical sum, including exchanges between fixed
reservoirs. Report local residuals and the direct signed global sum. A zero sum
does not imply zero local errors, time accuracy or a valid physical model.

Before implementation the verification cases were fixed: the existing exact
two-node rational recurrence with three unequal steps and signed load changes;
a scalar heating mode with steps 4, 2, 1, 0.5 s to 20 s; and an insulated coupled
mode with steps 0.2, 0.1, 0.05, 0.025 s to 1 s. Both smooth modes span one time
constant. Continuous references use independently evaluated 70-digit Decimal
exponentials; discrete endpoint references use exact rational powers. They do
not call the closed-form RC API to establish expected values.

The modal logarithm expansion gives first-order global error; measured orders
lie within the predefined 0.93 to 1.01 window and increase toward one. Exact
rational per-step ledgers pass the propagated fixture budgets. The adverse
tests keep canceling local errors and rounded-away heating visible. Arithmetic
range rejection is retained and documented. No unresolved analytical issue
remains for this scope; general accuracy certification and experimental
validation are not established.
