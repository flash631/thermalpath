# D02: typed network inputs

Completion date: 2026-09-16.

Added `Node`, `Link`, and `Network` records with explicit IDs and SI fields.
Constructors reject invalid scalar domains, duplicate node/link IDs, missing
endpoints, self-links, and nonzero power on a fixed-temperature node. Records
are frozen; list inputs are copied to tuples. Parallel links with distinct IDs
are supported. Later solver modules remain unimplemented.

The [decision](../decisions/0002-network-inputs.md) records the reviewed sign,
dimension, boundary, and limiting-case conventions. The relation
`q_ab = G_ab (T_a - T_b)` has units of watts and equal/opposite endpoint powers.
Structural checks alone do not establish steady-solution existence, uniqueness,
or physical validity. No unresolved analysis remained within D02's scope.

The public test suite passed 149 tests, including 86 input-model cases. Package
coverage was 100% across 115 statements and 40 measured branches. The input tests
use synthetic records; D01's independent rational references remain in the full
suite. These results verify the tested contracts and existing series calculation.
They do not validate a network solver or a physical device.

Final review added rejection of nonzero real inputs that underflow to zero on
float conversion. Artifact inspection also caught the explicit source inventory
omitting the new module. The inventory now includes the D02 module, tests, and
documents so the wheel built from the source archive contains the complete API.

The complete quality gate must pass for this final source snapshot before
publication. CI status must be checked against the delivered commit separately.
