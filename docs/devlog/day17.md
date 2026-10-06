# D17: three-grid spatial refinement report

Completion date: 2026-10-06.

Added a reproducible [spatial report](../plate_refinement.md) for the smooth
benchmark and grid family frozen in D16. The standalone example exports
inputs, all 252 cell values and loads, norm errors, both observed orders,
edge outflow, physical cell/global residuals and the assembled linear residual.

Mean absolute errors are 1.01463456, 0.27686118 and 0.07101946 K; RMS errors
are 1.04267601, 0.28698983 and 0.07378144 K. Maximum errors are 1.34498883,
0.44362035 and 0.12512698 K, with orders 1.60020 and 1.82593. These lower
maximum-norm orders are retained and explained through the boundary terms in
the exact discrete error equation and its quadratic comparison bound.
Total input remains 208/45 W; the largest absolute global imbalance is about
1.13e-13 W. Conservation near roundoff does not remove temperature error.

Five new tests cover an independent sine-mode solution on all three grids,
rational integrated loads and discrete comparison identities, every cell
temperature, independent equation substitution and edge powers, report norms,
the two orders, fixed inputs and standalone JSON replay. The reference uses
no production matrix assembly or linear solver. The existing D16 rational
coarse-grid check remains intact. No production solver or public API changed.

See the [decision](../decisions/0017-spatial-refinement.md). The complete local
quality, package and publication checks are required for this revision;
delivery and CI must be verified for the exact commit. These results support
the stated numerical benchmark, not physical validation or general accuracy.
