# D10: constant-conductivity plate

Use one unknown per rectangular cell and reuse the steady network solve.
The bounded model is steady, source-free and isotropic, with constant positive
conductivity, uniform thickness, insulated broad faces and explicit fixed or
insulated lateral edges. No additional material or source model is needed.

The integrated outward-flow equation gives `G=k*A/d`, using thickness-scaled
face area, adjacent half widths internally and one half width at a fixed edge.
Construct each internal face once. Return its power with opposite signs for
the adjacent cells; omit insulated connections. Store tuple results in x-first
cell order. Corner faces retain their individual boundary conditions.

At least one fixed edge anchors the connected positive-conductance graph.
The graph-energy identity proves a symmetric positive-definite matrix and a
unique solution. The maximum principle and cancellation of internal powers
provide additional checks. Pure insulation is nonunique and is rejected.
See [the derivation and limits](../plate.md).

Independent acceptance evidence includes constant fields, an unequal-width
linear continuum profile in each axis and both heat-flow directions, a rational
four-cell 2D system, and a one-cell conductance-weighted mean. Conductivity and
thickness scaling preserve temperatures and scale powers. Arithmetic failures
and a lost small temperature rise remain explicit adverse tests.

Dense reuse keeps one established algebraic solver and is appropriate for small
verification grids. It does not provide a general discretization error bound,
physical validation or production-scale mesh performance. No material analysis
remains unresolved for this scope.
