# Decision 0017: retain both finite-grid orders

Use only the manufactured field and 4 by 3, 8 by 6, 16 by 12 family frozen in
D16. Regenerate exact integrated loads on each grid. Report area-normalized
L1/L2 errors, maximum centre-temperature error, both adjacent-grid orders,
and physical and linear residuals separately. Export every cell for arithmetic
replay. No solver or public API changes are required.

The maximum-norm rates are 1.60020 and 1.82593; mean/RMS rates are closer to
two. Preserve these measurements. An independent separable-mode solution
reproduces them, and an exact discrete error equation with comparison bounds
explains why a quadratic error bound does not force a slope of two on these
finite grids. The [report](../plate_refinement.md) gives the calculation,
tolerances, heat balances and scope. No unresolved discrepancy remains for
this bounded study, and no extra grid or fitted correction is introduced.

This is numerical verification of the stated synthetic benchmark. It does
not provide physical validation or a convergence guarantee for other cases.
