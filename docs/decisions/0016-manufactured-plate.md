# Decision 0016: a smooth polynomial plate benchmark

Use `T=300+320 X(1-X)Y(1-Y)` K on the declared 0.06 by 0.04 m rectangle.
Differentiation supplies a nonnegative projected-area forcing and compatible
300 K data on all four edges. This exercises both spatial directions while
allowing exact rational checks of derivatives, cell integrals and face powers.

Represent the smooth forcing by its exact cell integrals through the existing
rectangular heater interface. This is sufficient for this finite-volume
verification problem and requires no change to the solver or public API.
Keep the continuum field fixed when a later grid is introduced, and regenerate
the cell loads. The heater rectangles themselves are not the benchmark input.

The independent 12-cell rational matrix checks the assembled discrete problem.
Comparison with continuum centre values retains a roughly 1.345 K maximum
temperature error, despite a global imbalance near roundoff. Continuum and
computed edge partitions are also reported separately. A small matrix residual
or global balance does not measure continuum accuracy.

The [derivation](../manufactured_plate.md) records units, signs, corner handling,
uniqueness, integral construction, numerical tolerances and limits. The
three-grid spatial report belongs to D17; no spatial order is claimed here.
