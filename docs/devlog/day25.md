# D25: electronics heat-spreader study

Completed 2026-10-19.

Added a fixed synthetic plate-thickness study using the existing steady solver.
Inputs, requirements and numerical thresholds were frozen before solving:
three thicknesses, two operating cases and three grids, for 18 attempted
solves. The example prints all cells, boundaries, units, power diagnostics,
counts, grid changes and requirement classifications. Failed solves remain
in order; incomplete or failed numerical checks yield unknown.

The independent reference diagonalizes the uniform discrete operator with
sine/cosine modes, without reusing production matrix assembly or heater
mapping. All 18 fields agree within 2e-9 K absolute tolerance; the measured
maximum difference is 2.73e-12 K. Additional tests verify linear scaling,
sink shifts, symmetry and equal cooling-edge outflows. Integration tests
check repeatable output and retained solve/balance/refinement failures.

All 18 solves completed and passed the frozen numerical checks. The largest
absolute global imbalance is below 1.96e-12 W, cell residual below 2.39e-13 W,
and matrix residual below 2.28e-13 W. The largest final peak change is
0.116374 K against the 0.5 K screen. These finite-grid checks are not a
continuum accuracy bound. No numerical threshold was adjusted after results.

The 0.5 mm plate exceeds 325 K in both cases. The 1 mm plate meets the nominal
case but exceeds the stress case. The 2 mm plate meets both, with stress peak
324.453 K and margin 0.547 K at 12.96 g assigned mass. It is recommended for
further assessment only. Ideal cooling edges and omitted contact/package
resistances prevent a real device approval. The stress case is not a
probabilistic uncertainty assessment. No measurements or physical validation
are claimed. Final analytical review found no unresolved issue in this scope.
