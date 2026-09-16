# Network inputs

`Node`, `Link`, and `Network` are immutable records. They validate input structure
and physical domains; they do not calculate temperatures or diagnose whether a
network has enough fixed boundaries for a unique solution.

```python
from thermalpath import Link, Network, Node

network = Network(
    nodes=(
        Node("heater", power_w=10.0),
        Node("sink", fixed_temperature_k=300.0),
    ),
    links=(Link("path", "heater", "sink", conductance_w_k=2.0),),
)
```

Each node represents one temperature. IDs are nonempty, case-sensitive strings
without surrounding whitespace. Node IDs must be unique; link IDs must also be
unique. The two namespaces are separate. Links reference existing, distinct nodes.
Parallel links may use the same endpoints if each link has a different ID.

| Field | Unit | Contract |
| --- | --- | --- |
| `Node.power_w` | W | Finite; positive into the node, negative for extraction |
| `Node.fixed_temperature_k` | K | None for unknown temperature, otherwise finite and strictly positive |
| `Link.conductance_w_k` | W/K | Finite and strictly positive |

The link's orientation defines the sign of heat flow:

```text
q_ab = G_ab (T_a - T_b)  [W]
q_ba = -q_ab
```

This is a constant, passive conductance law. Temperature difference is in kelvin;
multiplying it by W/K gives watts. Reversing endpoint order reverses the reporting
sign, not the physical path. When two nodes have equal temperature, the link
power is zero. At an unknown steady node, the intended balance is prescribed
power minus the sum of outgoing link powers equals zero. Neither equation is
evaluated by these records.

A fixed-temperature node represents an ideal reservoir. Its supplied or removed
power follows from the surrounding network. `power_w` must therefore remain zero
on that record. This is an input convention: a more general formulation could
account separately for a local load and the reservoir reaction. This version
does not provide that distinction. It rejects simultaneous nonzero power and
fixed temperature, including arbitrarily small nonzero power.

Omit a link to represent insulation. Zero conductance and infinite conductance
are rejected. An ideal thermal short is not represented by a finite-conductance
link. The series calculation's allowance for zero resistance does not extend to
this link representation. Absolute zero is outside the input temperature domain.
Finite real scalars are converted to floats; booleans, numeric strings, complex
numbers, nonfinite values, and values outside the float range are rejected.
No unit conversion or inference occurs, so callers must supply SI values.

`Network` accepts tuples or lists and copies lists into tuples. It requires at
least one node and allows no links. Fields cannot be reassigned after validation.
Invalid inputs raise `ValueError`. Disconnected or unanchored networks remain
valid records: they may not have a unique steady solution. Valid finite inputs
also do not ensure that later matrix assembly or solutions fit in float range.

The tests use synthetic records to check these contracts. They establish neither
physical validation nor numerical solver accuracy. See the
[D02 decision](decisions/0002-network-inputs.md) for the scope of this increment.
