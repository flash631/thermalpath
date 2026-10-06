# Three-grid spatial refinement

Run `python examples/plate_refinement.py` to reproduce this synthetic study.
It uses the [manufactured polynomial](manufactured_plate.md) frozen in D16:
`T=300+320 X(1-X)Y(1-Y)` K on a 0.06 by 0.04 m plate, with thickness
0.002 m, conductivity 10 W/(m K), and all edges fixed at 300 K. There is no
broad-face loss. The only grids are 4 by 3, 8 by 6, and 16 by 12 uniform cells.
Each refinement halves both spacings. Exact integrals of the same smooth
forcing supply fresh cell loads; a coarse heater list is never reused.

The JSON report includes these inputs, every cell centre, computed and reference
temperatures, signed errors, cell loads, norm errors, both observed orders and
separate conservation diagnostics. Nothing is fitted or corrected after solving.
The production solver and public API are unchanged.

## Error definitions

Compare numerical temperatures with the continuum value at each cell centre,
not with a cell average or a coarse-grid interpolation. Let `e_i=T_i-T(x_i,y_i)`
in K, cell area `a_i`, and total area `A`. The reported norms are

```text
E1   = sum(a_i |e_i|)/A,             [K]
E2   = sqrt(sum(a_i e_i^2)/A),       [K]
Einf = max_i |e_i|.                 [K]
p    = log(E_coarse/E_fine)/log(2).  [dimensionless]
```

All cells have equal area on each declared grid, so the first two expressions
use weights `1/N`. E1 is the mean absolute error; E2 is the root mean square
error. Both adjacent grid pairs have their own order. There is no order for
the first grid. The continuum peak is 320 K, but centre samples need not land
on that peak; all errors compare the same physical locations.

## Executed results

| Grid | dx (m) | dy (m) | E1 (K) | E2 (K) | Einf (K) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4 by 3 | 0.015 | 0.0133333333333 | 1.014634561381 | 1.042676007811 | 1.344988828041 |
| 8 by 6 | 0.0075 | 0.00666666666667 | 0.276861183022 | 0.286989832313 | 0.443620351229 |
| 16 by 12 | 0.00375 | 0.00333333333333 | 0.0710194648773 | 0.0737814396765 | 0.125126977406 |

| Grid pair | p for E1 | p for E2 | p for Einf |
| --- | ---: | ---: | ---: |
| 4 by 3 to 8 by 6 | 1.873725507 | 1.861219407 | 1.600196733 |
| 8 by 6 to 16 by 12 | 1.962876402 | 1.959669780 | 1.825932683 |

The mean and RMS orders approach two. The maximum-norm orders are lower on
both pairs and remain part of the result. The largest errors occur in the
first or last row of cells, near the middle of the south or north edge.
Representative maximum-error centres are (0.0375, 0.006666667) m,
(0.02625, 0.003333333) m, and (0.028125, 0.001666667) m. Symmetry-related
cells agree up to roundoff, so which one is selected can vary.

| Grid | Input (W) | West/east outflow, each (W) | South/north outflow, each (W) | Global imbalance (W) |
| --- | ---: | ---: | ---: | ---: |
| 4 by 3 | 4.622222222222 | 0.743319890948 | 1.567791220164 | 6.11e-16 |
| 8 by 6 | 4.622222222222 | 0.718994064261 | 1.592117046850 | -3.68e-14 |
| 16 by 12 | 4.622222222222 | 0.713047880619 | 1.598063230492 | 1.13e-13 |

The exact input is 208/45 W. Continuum edge outflows are 32/45 W on west/east
and 8/5 W on south/north. Their numerical partition approaches these values.
The largest physical cell residual is below 1.4e-14 W on these runs; the
largest assembled linear residual is below 1.3e-14 W. A balance near roundoff
coexists with the finite temperature errors above. Last digits can vary with
the numerical library; the small global imbalance need not decrease with grid size.

## Independent discrete reference

Tests compute exact rational source integrals by integrating expanded
polynomials. For uniform cells define `gx=k t dy/dx` and `gy=k t dx/dy`,
both in W/K. In one dimension the fixed-boundary matrix has end diagonals
`3g`, interior diagonals `2g`, and adjacent off-diagonals `-g` for the declared
sizes. Its modes and eigenvalues are

```text
v_p(i) = sin(pi p (i+1/2)/n),   p=1,...,n; i=0,...,n-1,
lambda_p = 4 g sin^2(pi p/(2n)).
```

These follow by substitution into interior and end rows. The squared mode
norm is `n/2` except for `p=n`, where it is `n`. Products of the normalized
x/y modes diagonalize the two-dimensional matrix, with eigenvalues equal to
the sums of the corresponding one-dimensional eigenvalues. Transforming
the rational loads, dividing each coefficient by that sum, and transforming
back gives an independent solution for temperature rise above 300 K.

This reference calls no production assembly or matrix-solve routine. Tests
check mode orthonormality, every reference equation, all 252 computed
temperatures, every cell load, the norms, and exterior powers. The existing
D16 exact 12-cell rational solve remains an additional coarse-grid check.
The sine reference uses floating-point trigonometry; it is not an exact
rational solve or a formal floating-point certificate.

## Why the finite-grid maximum order is below two

The half-cell fixed-boundary flux and centre sampling matter here. The
following direct calculation bounds their effect without adding a grid or
changing the benchmark. Write `alpha=1/nx`, `beta=1/ny`, `D=20 K`,
`f(z)=z(1-z)`, and let `A_h` be the discrete matrix for temperature rise.
Substituting the continuum centre values into its rows gives the error equation

```text
A_h e = r,
gamma = (8/3) k t D dx dy [beta^2/Lx^2 + alpha^2/Ly^2],
r_ij = -gamma
       + I_x 8 D gx alpha^2 f(Y_j)
       + I_y 8 D gy beta^2 f(X_i).
```

`I_x` is one on the first/last x cell and zero otherwise; `I_y` is analogous.
The formula covers the declared grids, which have at least two cells per
direction. Gamma and r have units W. Interior cells have only the negative
constant term; boundary cells have the additional terms. Exact rational
tests verify this identity in every row, including corners.

Positive conductances and fixed boundaries make `A_h` positive definite.
Its discrete maximum principle also gives a nonnegative inverse: a negative
minimum under a nonnegative load contradicts a boundary row, or propagates
through neighbors until it reaches one. Since `0<=f<=1/4`, the constant
`U=D max(alpha^2,beta^2)` satisfies `r <= A_h(U*1)` componentwise. Thus `e<=U`.
For a lower bound use the nonnegative comparison vector

```text
w_ij = [x_i(Lx-x_i) + dx^2/4]/(2 k t dx dy),    [K/W]
A_h w >= 1,
max(w) <= W = (Lx^2+dx^2)/(8 k t dx dy).
```

The x-direction rows give exactly one; the y boundaries add nonnegative
terms. With `r>=-gamma*1`, inverse positivity gives
`-gamma W <= e_ij <= U`. Rational tests verify the comparison-vector
inequality and its maximum on each grid. At fixed aspect ratio both bounds
scale as the square of grid spacing. This proves an upper bound of that
order for this exact discrete benchmark; it does not prescribe the finite
two-grid slope or establish an asymptotic error expansion.

The measured positive maximum errors divided by `U=20/ny^2` are
0.605244973, 0.798516632, and 0.900914237. Their increasing coefficient
accounts for the slopes below two: `p=2+log2(C_coarse/C_fine)` when
`Einf=C*U`. Boundary-adjacent centres move closer to the boundary as the grid
is refined. The lower finite-grid orders are reproduced by the independent
mode solution and are consistent with the derived bound. They have not been
discarded, rounded to two, or replaced by an extra grid.

## Tolerances and limits

The same comparison vector bounds `||A_h^-1||_infinity` by W.
Since `||A_h||_infinity <= 4(gx+gy)`, condition-number upper bounds are
19.2578125, 73.6328125 and 291.1328125. Temperature regression budgets use
`64 N eps condition_bound 320 K`: approximately 1.05e-9, 1.61e-8 and
2.54e-7 K. They allow for input conversion, assembly, dense solving and
the independent mode transform. They are deliberately much smaller than the
reported continuum errors, but are not certified rounding-error bounds.
Norms use the same absolute K budgets; exterior-power budgets propagate them
through face conductances and face counts. Physical and linear residuals have
separate W budgets, `64 eps 320 K * 4(gx+gy)` per cell and N times that for
the global imbalance. No residual is used as a substitute for temperature error.

This study verifies one smooth, constant-conductivity problem and one fixed
grid family. It does not establish physical validation, a general solver
accuracy certificate, or convergence for discontinuous materials, mixed
boundaries, arbitrary grids or other sources. Three grids provide only two
observed slopes.
