# D07 decision: backward-Euler networks

Use a separate `transient_networks.py` module and the existing immutable network
inputs. Do not add heat capacities to steady nodes or change the JSON schema.
Require complete capacity and initial-temperature maps for nonfixed nodes only.
Keep prescribed temperatures constant and omit reservoir storage.

Choose explicit interval load maps on the integration grid. Each map replaces
all nonfixed node loads for its interval; there are no partial updates or hidden
interpolation rules. This makes event timing testable without an event engine.
No capacity is required for fixed nodes, including an entirely fixed network.

The derivation in [network integration](../transient_networks.md) proves a
unique backward-Euler update with positive capacities, including insulated
components. Its mode factors lie in `(0,1]`. The matrix uses units W/K, the
right side W, and the result K. Internal conductances conserve heat by opposite
signed contributions. A scalar insulated node reduces to `T_new=T_old+h*P/C`.
A steady solution is invariant under stepping with the same loads. These
limits are independently tested.

Use dense NumPy binary64 solves at each interval. Reject detected arithmetic
range errors, numerical singularity and invalid output temperatures. Capacity
can be rounded away beside enormous conductances; the exact SPD proof does
not guarantee a numerically invertible matrix. Small heating can vanish from
reported absolute temperatures. Preserve both cases as numerical limits.

The acceptance target is the discrete two-node update with fixed boundaries
and explicit load changes. The exact-rational reference uses a closed 2-by-2
inverse rather than the production assembly or linear solver. D08 will add
step energy reporting and measured first-order time refinement. No physical
validation or arbitrary-input accuracy bound is established here.
