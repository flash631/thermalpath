# D15: analytical one-dimensional plate cases

Completion date: 2026-10-03.

Added independent quadratic temperature and linear heat-flux references for
fixed/fixed, insulated/fixed and flux/film boundaries. The checks use exact
rational arithmetic before the floating solver comparison. There are 72
parameter combinations covering both axes, source-free limits, two thicknesses,
unequal transverse strips and three axial grids, including a single cell.
An additional rational two-cell test and an example integration test bring
the new test count to 74.

The [analysis](../plate_1d.md) derives the centre-temperature offset
`s di^2/(8kt)` on both uniform and unequal axial cells. It checks every face
law, signed cell/global conservation and uniqueness through the anchored
positive graph energy. Conditioning-based regression budgets distinguish
roundoff from the exact discretization error. The independent two-cell
matrix has inverse infinity norm 9/16 K/W and condition number 27/8 in that
norm; its temperatures are 303 and 309 K.

The runnable example keeps continuum errors of 0.375 and 3.375 K visible while
the 24 W heater balances two 12 W exterior losses. This adverse comparison is
expected from the numerical boundary closure. No solver change or automatic
correction was made. See [the decision](../decisions/0015-plate-1d-verification.md).

This increment supplies numerical verification of the stated one-dimensional
cases. It does not establish general two-dimensional convergence or physical
validation. CI evidence must be checked for the delivered revision.
