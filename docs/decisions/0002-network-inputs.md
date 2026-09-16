# D02: explicit network inputs and boundary conventions

Use frozen records for nodes, conductance links, and the containing network.
Store scalar values as floats, powers in watts, conductances in W/K, and absolute
temperatures in kelvin. Copy input lists to tuples so a caller cannot invalidate
references by later changing the original list.

The defining relation is `q_ab = G_ab (T_a - T_b)`. Positive conductance sends
heat from the hotter node to the colder node; endpoint reversal changes the
sign. A link contributes equal and opposite powers to its endpoints. Prescribed
node power is positive for heating and negative for extraction. These definitions
are dimensionally consistent and specify the balance for a later solver.

Represent a prescribed temperature as one optional field on a node. Reject any
nonzero power on that same fixed node. This avoids needing separate load and
reservoir-reaction fields in this increment. It is a deliberate restriction of
the input model, not a claim that such physical arrangements are impossible.
Duplicate node IDs are rejected even if their other fields agree. Conflicting
temperatures cannot silently overwrite one another.

Keep node and link ID namespaces separate. Permit distinct parallel links:
each can represent a separate physical path, and their powers would add. Reject
self-links, which would always carry zero power under the defining relation.
Reject zero or infinite conductance; omitted paths represent insulation.

Structural validity does not prove existence or uniqueness. For example, a
single isolated node with positive power is a valid record but cannot reach
steady balance; an isolated zero-power unknown node has no unique temperature.
Both cases remain representable. Connectivity and solver checks belong to later
increments. There is no time integration, discretization, numerical convergence
claim, or calculated-temperature tolerance in D02. Scalar/domain and identity
checks are exact after float conversion. Representable extreme values are not
certified as suitable for a later solve.

Review found no unresolved mathematical issue within this input-only scope.
Tests cover the acceptance rules, mutation resistance, and valid limiting input
cases. No physical measurements are used.
