# D18: temperature, transient, and error plots

Completion date: 2026-10-07.

Added headless temperature maps, transient histories, spatial error curves,
and PNG export in `thermalpath.plotting`. Maps respect unequal cell widths,
x-first ordering, physical aspect ratio and common temperature scales. Curves
preserve every supplied point and use shared axes with SI labels. Exports use
fixed settings and refuse existing files.

The [runnable example](../plotting.md) recomputes the frozen plate refinement
and scalar RC benchmarks. It writes three PNGs, their full numerical inputs,
and content hashes. The finest plate maximum error remains about 0.125127 K.
At 20 s the 1 s backward-Euler temperature is about 306.231105 K, versus the
analytical 306.321206 K. Plotting adds no new numerical or physical claim.

Tests check unequal-cell linear-reference geometry, asymmetric field placement,
shared normalization, exact line data, independent scalar recurrence and
exponential values, invalid inputs, input preservation, headless replay,
repeatable PNG bytes, and no-clobber behavior. The complete package-wide quality
gate and private publication controls are required on the final source bytes.
See [decision 0018](../decisions/0018-thermal-plots.md) for the analytical review
and limits. Delivery and CI are checked for the exact commit.
