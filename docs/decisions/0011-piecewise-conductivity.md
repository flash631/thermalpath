# Use the two half-cell resistances at material faces

Status: accepted.

Extend `solve_plate` with a flat positive conductivity sequence in x-first cell
order while retaining the scalar input and `PlateResult`. This keeps material
assignment explicit and avoids introducing a material database or a second
solver. Copy validated sequence values before assembling the network.

Assume isotropic, temperature-independent conductivity inside each cell,
cell-aligned interfaces and perfect thermal contact. Flux and temperature
continuity give `G=A/(d_i/k_i+d_j/k_j)`. Unequal widths require distance weights;
an unweighted or arithmetic conductivity mean fails the series-resistance
reference. Fixed edges use the local half-cell conductivity and distance.
Equal-k faces keep the established scalar arithmetic.

Positive conductances preserve the anchored graph-energy proof, uniqueness,
maximum principle and internal power cancellation. Verify a two-material
continuum solution with unequal cells in both axes and flow directions,
including interface temperatures reconstructed from both adjacent centers.
An independent rational 2D matrix checks material ordering and all face powers.
Reject zero-rounded/nonfinite resistance factors and conductances. Keep
floating-point range and conditioning limits explicit; successful tests do not
establish physical validation or general spatial convergence.

See [derivations and test budgets](../plate_materials.md).
