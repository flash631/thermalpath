# Manufactured two-dimensional plate solution

This benchmark starts with a chosen smooth temperature field and derives the
heat input that makes it solve the steady plate equation. It checks numerical
implementation against a known continuum solution. All inputs are synthetic.

## Frozen field and physical domain

The rectangle is `0 <= x <= Lx`, `0 <= y <= Ly`, with these fixed parameters:

| Parameter | Value | Unit |
| --- | ---: | --- |
| Lx | 0.06 | m |
| Ly | 0.04 | m |
| Thickness t | 0.002 | m |
| Conductivity k | 10 | W/(m K) |
| Edge temperature T0 | 300 | K |
| Peak continuum rise D | 20 | K |

Conductivity and thickness are constant, with no broad-face loss or storage.
Put `X=x/Lx`, `Y=y/Ly`, `f(z)=z(1-z)`. Choose

```text
T(x,y) = T0 + 16 D f(X) f(Y).                              [K]
```

Both spatial directions contribute. The maximum continuum temperature is
320 K at the rectangle centre. Every edge has the same trace, `T=T0`.
The four corners therefore have compatible Dirichlet data. The gradient
vanishes at each corner; there is no point heat source or extra corner weight.
A corner cell has two distinct exterior faces, each using its own area and
normal. There are no corner temperature unknowns in this cell-centred scheme.

## Derivatives, forcing and signs

Differentiating the polynomial gives

```text
T_x  = 16 D (1-2X) f(Y)/Lx,             T_y  = 16 D f(X)(1-2Y)/Ly,
T_xx = -32 D f(Y)/Lx^2,                 T_yy = -32 D f(X)/Ly^2,
T_xy = 16 D (1-2X)(1-2Y)/(Lx Ly).
```

First derivatives have units K/m and second derivatives K/m2. The required
projected-area heat input follows from the governing equation:

```text
-k t (T_xx + T_yy) = s,
s(x,y) = 32 k t D [f(Y)/Lx^2 + f(X)/Ly^2].                 [W/m2]
```

Here `k t` has units W/K. The source is nonnegative on the entire rectangle.
The conductive flux is `q=-k grad(T)` in W/m2; lateral face power is the
integral of `q dot n` times thickness, positive outward. The four exact
continuum edge powers are

```text
P_west = P_east = (8/3) k t D Ly/Lx = 32/45 W,
P_south = P_north = (8/3) k t D Lx/Ly = 8/5 W.
```

Their sum is `208/45 W`, equal to the integrated source. These are reference
fluxes, not additional prescribed boundary conditions: the solve uses only
the four fixed temperatures. Setting D to zero in the equations gives the
constant zero-input field. For two solutions with the same data, integration
of their homogeneous difference against itself gives
`k t integral(|grad(delta T)|^2)=0`; the fixed boundary then forces the
difference to vanish. This establishes uniqueness for the stated smooth problem.
The discrete matrix is likewise positive definite: its quadratic form sums
positive internal-face terms `G(v_i-v_j)^2` and boundary terms `G_b v_i^2`.

## Exact integrated loads with the existing heater interface

For a cell, let `dX`, `dY` be its dimensionless widths and `Xm`, `Ym` its
dimensionless centre. A quadratic's exact interval mean is

```text
mean(f(X)) = f(Xm) - dX^2/12,
mean(f(Y)) = f(Ym) - dY^2/12.
Q_cell = 32 k t D dx dy [mean(f(Y))/Lx^2 + mean(f(X))/Ly^2]. [W]
```

The example gives each cell a rectangular heater with exactly these bounds
and this total power. The solver receives the correct integral of the smooth
forcing in each control volume, up to floating-point arithmetic. It does not
receive a centre-sampled approximation or a new source API. The resulting
heater density is piecewise constant, so these rectangles must be rebuilt
from the same continuum forcing if the grid changes. A saved coarse-grid
heater list is not the definition of the continuum benchmark.

Tests independently expand the temperature into monomials in physical x and y,
differentiate their coefficients with exact rational arithmetic, and integrate
the resulting source. An unequal four-rectangle partition checks the integral
and signed continuum flux balance in each rectangle without a second solver
run. The checks include all corners and points on every edge.

## One-grid comparison and tolerances

Run `python examples/manufactured_plate.py`. The frozen D16 solve uses 4 by 3
uniform cells, x first. The script prints every centre temperature, its exact
continuum reference, its signed error, each cell load, and both continuum and
computed edge totals. The reference finite-volume matrix is constructed
separately in the tests with exact fractions:

```text
dx = 3/200 m, dy = 1/75 m,
Gx = k t dy/dx = 4/225 W/K,
Gy = k t dx/dy = 9/400 W/K.
```

Boundary conductances are twice the corresponding internal conductance.
Solving for temperature rise removes the 300 K boundary offset from this
independent reference system. Exact elimination checks its inverse and
recovers every cell temperature and face power. The matrix infinity norm is
`29/180 W/K`, its inverse norm is `18283151700/434988673 K/W`, and their
product is about 6.771714. The inverse has nonnegative entries.

The solver comparison budget is
`512 * 12 * eps * condition_infinity * 320 K`, about `3e-9 K` for binary64.
It allows for the small system's input conversion, matrix assembly and solve;
face-power budgets propagate that temperature budget through their
conductances. Polynomial evaluations use separate small roundoff allowances.
These are conservative regression tolerances for this fixture, not certified
error bounds for arbitrary inputs. They do not absorb continuum discretization
error, which is reported separately.

The executed 4 by 3 example gives:

| Quantity | Result |
| --- | ---: |
| Total heater input | 4.622222222222223 W |
| Maximum absolute centre-temperature error | 1.344988828040755 K |
| Computed west/east outflow, each | about 0.743319890948 W |
| Computed south/north outflow, each | about 1.567791220164 W |
| Global physical imbalance | about 6.1e-16 W |

Last digits can vary with the numerical library. The continuum west/east
power is about 0.711111111111 W each, and south/north power is 1.6 W each.
Thus the edge partition and temperatures have finite discretization errors
even though their total power balance closes. No correction is applied.

## Scope and next comparison

D16 establishes this manufactured field, forcing, boundary compatibility,
integrated-load construction and one independently checked discrete solve.
It does not measure a spatial order or establish physical validation. The
frozen family for D17 is `(nx,ny)=(4m,3m)` with `m=1,2,4`, using the same
physical parameters, all fixed edges, and freshly integrated cell loads.
D17 will report the resulting errors and conservation; those later solves
are not D16 evidence. This polynomial benchmark does not cover discontinuous
materials, mixed boundaries or arbitrary unstructured grids.
