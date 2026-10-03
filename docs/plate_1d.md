# One-dimensional plate verification

These synthetic cases compare `solve_plate` with independently integrated
temperature profiles and heat fluxes. They use the existing solver and heater
mapping. No new material law or boundary condition is introduced.

## Domain, signs and assumptions

Let the axial coordinate be x in [0, L], the transverse width be W, the
thickness be t, and the constant conductivity be k. The transverse edges and
both broad faces are insulated. A heater covers the whole projected area
and supplies s W/m2, so its prescribed power is P = s L W. Here s is a surface
power density, not a volumetric source; the equivalent volume density is s/t.
Temperature and loading are independent of the transverse coordinate.
All lengths are in metres, temperatures in kelvin, and k in W/(m K).

The steady equation and positive-x heat flux are

```text
-k t T''(x) = s,       q(x) = -k T'(x),       q'(x) = s/t.
```

Thus q has units W/m2 of lateral area. Heat flow through a transverse strip of
width w is q t w W. Outward flux is -q(0) at the low edge and q(L) at the high
edge. Internal faces carry equal and opposite outward powers. Direct integration
gives

```text
q(x) = q0 + s x/t,
T(x) = C - q0 x/k - s x^2/(2 k t).
```

The equations also apply after swapping x and y. They assume perfect lateral
conduction, constant properties and a uniform temperature through the thickness.
They do not determine whether these assumptions fit a physical device.

## Boundary cases

For fixed temperatures T(0) = TL and T(L) = TR,

```text
q0 = k (TL - TR)/L - s L/(2t),
T(x) = TL + (TR - TL) x/L + s x (L - x)/(2kt).
```

For an insulated low edge and a fixed high edge T(L) = TR,

```text
q0 = 0,
T(x) = TR + s (L^2 - x^2)/(2kt).
```

For a prescribed outward low-edge flux f and a high-edge film with coefficient
h > 0 and ambient Ta,

```text
q0 = -f,                          qL = -f + s L/t,
T(L) = Ta + qL/h,
T(x) = Ta + qL/h + q0 (L - x)/k + s (L^2 - x^2)/(2kt).
```

The film condition applies at the geometric edge. It includes the half-cell
conduction distance in the solver. In each case,
`t W [q(L) - q(0)] = s L W`; a negative outward edge power is an input.
With s = 0 the profiles become linear or constant. Existing
[material tests](plate_materials.md) and [boundary tests](plate_boundaries.md)
also cover source-free layers, two films, and reversed flow.

Each case has at least one fixed-temperature or positive-film anchor. For a
temperature perturbation v, the discrete energy is the sum of
`Gij (vi-vj)^2` over internal faces and `Gb vi^2` over anchored boundaries.
The connected grid and positive conductances make this sum positive for every
nonzero v. The discrete system therefore has a unique solution. The continuum
homogeneous difference problem has the same uniqueness property by integrating
the squared gradient and the film boundary term.

## Exact discrete offset on unequal cells

Let cell i have axial width di and centre xi. For these cases the exact solution
of the finite-volume equations is

```text
Ti = T(xi) + delta_i,       delta_i = s di^2/(8kt).
```

This expression gives centre values plus a discretization offset. It is not
a cell-average interpretation: the quadratic continuum average is
`T(xi) - s di^2/(24kt)`.

To check the offset without a numerical solve, take adjacent widths di and dj
meeting at face xf. Their centre spacing is `(di+dj)/2`. Substitution of the
quadratic continuum profile into the two-point flux gives

```text
k [T(xi)-T(xj)] / ((di+dj)/2) = q(xf) + s (dj-di)/(4t).
k [delta_i-delta_j] / ((di+dj)/2) = s (di-dj)/(4t).
```

The two error terms cancel, so the discrete face flux is q(xf), including on
unequal cells. At a fixed low edge,
`k [TL-T1]/(d1/2) = q(0)` after the same substitution. At the high edge,
`TN-TR = q(L) dN/(2k)` for a fixed temperature, or
`TN-Ta = q(L) [dN/(2k)+1/h]` for a film. A prescribed flux is already exact.
Each cell then satisfies `t w [q(right)-q(left)] = s di w`. Constant temperature
across each transverse strip makes its transverse flux zero. Uniqueness proves
that these substituted temperatures are the discrete solution.

For uniform widths the offset is constant. Unequal widths produce different
offsets, even though every face flux and the global power balance can be exact.
The offset vanishes with s and scales as di squared under axial refinement
for this restricted family. This identity does not establish the order of a
general two-dimensional or nonuniform-source calculation; those are separate
verification tasks. It also does not justify automatically correcting arbitrary
solver outputs.

## Test cases and roundoff allowances

`tests/verification/test_plate_1d_reference.py` uses exact rational arithmetic
for profiles, offsets, face fluxes and substitution checks before comparison
with the floating solver. The 72 parameter combinations use both axes, three
boundary cases, s = 0 or 3 W/m2, and t = 0.25 or 0.5 m. Axial edges are
`(0,4)`, `(0,1,2,3,4)` or `(0,0.5,2,4)` m. Transverse edges are `(0,0.5,2)` m;
k = 2 W/(m K), fixed data are 320/300 K, and the mixed film case uses
f = -4 W/m2, h = 4 W/(m2 K), Ta = 300 K. All resulting temperatures are positive.
These small synthetic dimensions make the checks easy to reproduce; they are
not proposed device dimensions.

Tests check every temperature and every outward face power. They compare the
observed continuum error with delta_i separately from numerical roundoff.
The smallest nonzero delta_i in the parameter set is 0.09375 K.

The floating allowance uses a conservative conditioning estimate. Write A in
W/K, let M be the cell count, dmin/dmax the axial width extrema, and wmin/wmax
the transverse width extrema. The nonnegative inverse of this anchored
conduction matrix and a positive uniform-heating comparison profile give

```text
B = [L^2/(2kt) + L/(ht) + dmax^2/(8kt)]/(dmin wmin),
||A^-1||_infinity <= B,
R = 8kt (wmax/dmin + dmax/wmin),      ||A||_infinity <= R.
```

For the comparison profile the low edge is insulated and the high film has
h = 4. Its uniform source is `1/(dmin wmin)`, so every cell receives at least
1 W. Fixed boundaries make stronger anchors and only reduce the inverse
comparison. The row bound R overestimates the sum of internal, boundary and
transverse conductances for these grids. The test temperature allowance is
`tauT = 64 epsilon M R B max(Ti)`, where epsilon is binary64 machine epsilon.
The factor 64 reserves room for assembly, factorization and reference rounding.
Every fixture must keep tauT below 1e-6 K. Per-face power allowance is `R tauT`,
with `M R tauT` for the global balance. These are conservative regression
budgets for these small systems, not a formal floating-point error certificate
or a guarantee for arbitrary conditioning. Exact rational identities supply
the discretization expectations independently of those budgets.

A separate two-cell system gives an easily checked reference. For widths
1 and 3 m, W = 2 m, t = 0.5 m, k = 2 W/(m K), s = 3 W/m2 and both ends at
300 K, the temperature rises satisfy

```text
[ 5   -1  ] [theta1] = [ 6] W,
[-1    7/3] [theta2]   [18]
```

The rises are exactly 3 and 9 K. The inverse infinity norm is 9/16 K/W,
the matrix norm is 6 W/K, and their product is 27/8. A 2e-12 K comparison
allowance covers roughly eight `epsilon * condition * 309 K` error units.
The 1e-11 W face and 2e-11 W summed-residual allowances cover the conductance
amplification and final subtractions. These tighter checks supplement the
broader fixture budgets.

## Runnable comparison and limits

```powershell
python examples/plate_1d.py
```

The example prints the two-cell case above as JSON. Its exact expected values
are:

| Centre x [m] | Discrete T [K] | Continuum centre T [K] | Error [K] |
| --- | --- | --- | --- |
| 0.5 | 303 | 302.625 | 0.375 |
| 2.5 | 309 | 305.625 | 3.375 |

The west/east outward powers are `(12,-6)` W in the first cell and `(6,12)` W
in the second. Each outer edge removes 12 W, balancing the 24 W heater. A small
power residual therefore coexists with a 3.375 K continuum temperature error.
The report retains that error; it does not subtract the analytical offset.

These tests verify a declared numerical model. They do not validate material
data, heat-transfer coefficients or real hardware. The exact offset formula
does not cover broad-face losses, varying conductivity, partial heater
footprints or general two-dimensional fields. Earlier tests and documented
limits for those features remain in place.
