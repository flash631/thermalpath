# Decision: explicit continuum and discrete plate references

Keep the existing plate solver and add independent analytical checks for
full-area uniform heating with fixed ends, an insulated/fixed pair, and a
prescribed-flux/film pair. Use both axes, unequal transverse strips, uniform
and unequal axial cells, two thicknesses and the zero-source limit.

Integrating the continuum equation gives a quadratic temperature and linear
flux. Exact rational substitution proves that discrete cell temperatures
include the offset `s di^2/(8kt)` while face fluxes are exact for this family.
Tests must preserve the continuum error rather than treating it as roundoff.
An independent rational two-cell matrix and a runnable report make this
distinction visible. No change to the solver or public API is required.

The [derivation](../plate_1d.md) records dimensions, signs, anchor uniqueness,
conservation and fixture-specific roundoff budgets. The result is restricted
to constant conductivity, full-area uniform heating and insulated transverse
and broad faces. It does not replace the later two-dimensional manufactured
solution or spatial-refinement study. No physical validation is claimed.
