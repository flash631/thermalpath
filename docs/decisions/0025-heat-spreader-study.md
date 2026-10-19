# D25: fixed plate-thickness comparison

Use the existing plate solver in one runnable example, without adding a new
solver or generic report API. A 60 by 40 mm plate with a central 20 by 20 mm
heater compares 0.5, 1 and 2 mm thicknesses at common conductivity and density.
These are assigned inputs, not measured material properties. Both x edges have
the same fixed temperature; all other faces are insulated.

Before execution, freeze nominal 10 W/300 K and stress 12 W/310 K cases,
325 K maximum cell-temperature requirement, 0.25 K decision band and three
grids (6 by 4, 12 by 8, 24 by 16). Fix 1e-8 W absolute balance/residual
thresholds, 0.5 K final grid-change threshold and 2e-9 K absolute independent
discrete-reference tolerance with zero relative tolerance. Preserve every
candidate and failure; a failed solve or numerical check yields unknown.

The steady equation is -k t Laplacian(T) = q_area. Positive k and t with fixed
x edges give a unique anchored system. Heater watts are integrated over the
footprint. Symmetry splits outward power equally between the cooling edges.
An independent discrete sine/cosine expansion verifies all fields; scaling,
shifts, symmetry, power accounting and grid changes provide separate checks.
No continuum error bound is inferred from grid changes or balance closure.

The 2 mm candidate alone meets both assigned cases. Recommend it only for
further contact/cooling and prototype evaluation. Its 0.547 K stress margin
is small and omits package/contact drops and input uncertainty. No automatic
winner, commercial recommendation, safety claim or physical validation is
part of this example. The 1 mm nominal success and stress failure remain
visible. There is no unresolved mathematics within this stated model.
