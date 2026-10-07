# Decision 0018: plot supplied values with explicit geometry and scales

D18 introduces plotting helpers in a separate module. They return Agg figures
and a separate PNG exporter writes only new files. Numerical solver imports
remain lightweight. Existing numerical models and benchmark definitions are
unchanged.

For a rectangular grid, flat index `iy * nx + ix` becomes row `iy`, column `ix`
in a `(ny, nx)` array. The mesh uses the original edge arrays, not an image with
uniform pixel geometry. Equal x/y coordinate scale preserves physical aspect
ratio. Compared fields share the extrema of all supplied kelvin values, one
normalization object, and one colorbar. These choices can be checked with an
unequal-cell analytical linear profile and an asymmetric synthetic field.

Transient points and error norms are copied unchanged. One common pair of axes
prevents separate panel scaling from implying a false agreement. Logarithmic
error plots require positive norms; no clipping floor is invented for zero.
No order is estimated by the plotting layer. The example retains all three
published error series, including their finite-grid behavior.

The scalar example uses `T(t) = 310 - 10 exp(-t/20)` K. For a 1 s backward-Euler
step its independent recurrence gives `T_n = 310 - 10 (20/21)^n` K. The plot
shows samples of both, with connecting lines identified as visual guides.
It makes no change to the steady or transient stability and conservation
contracts. There is no material unresolved mathematical issue in this display
mapping.

Fixed defaults, bundled fonts, explicit PNG metadata and no display dependencies
support repeatable export in one environment. Tests inspect actual mesh and
curve values, screen-coordinate aspect ratio, shared scales, invalid domains,
input preservation, headless process replay, hashes and overwrite refusal.
Visual inspection checks label and legend readability. Cross-platform byte
identity and physical validation are outside this contract.
