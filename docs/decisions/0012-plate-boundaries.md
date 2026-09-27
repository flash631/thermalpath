# Constant flux and convection on reduced plates

Keep the existing fixed-edge arguments and scalar/cellwise conductivity API.
Add named-edge mappings for prescribed flux and convection, plus one combined
broad-face convection record. A boundary type is exclusive on each edge,
including explicit zeros. Use outward-positive powers throughout the result.

The edge film lies at the geometric surface. Eliminating its surface
temperature adds the half-cell conduction and film resistances in series.
The broad-face model instead assumes temperature uniform through thickness;
its supplied coefficient is the sum for both faces per projected area, with
a shared ambient. These conventions avoid hidden factors and distinguish the
two physical approximations. See [the derivation](../plate_boundaries.md).

Reuse the network solver with negative prescribed-outward powers as loads and
positive reservoir links for convection. At least one reservoir connection
is required. Keep the four lateral powers and append combined broad-face
powers to the result. Do not add heater mapping, a transient plate solver,
automatic coefficient estimation or the later diagnostics API.
