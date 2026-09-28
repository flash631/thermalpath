# Rectangular heater inputs

`RectangularHeater(x_min_m, x_max_m, y_min_m, y_max_m, power_w)` describes
uniform heat input over a projected rectangular footprint. Coordinates are in
metres and power is the total in watts. Power must be finite and nonnegative;
zero disables heating while retaining geometry checks. The footprint must have
positive finite area and lie fully inside the grid, including when power is
zero. An outside footprint raises an error instead of being clipped or moved.

`map_heaters(grid, heaters)` returns one input per cell in x-first order.
`solve_plate(..., heaters=heaters)` uses that same mapping as its cell load.
The default empty sequence preserves the previous boundary-only calculation.
Multiple heaters may overlap; their contributions add without removing area
from either footprint. A heater already specifies total input, so there is no
extra thickness factor or factor of two for the broad faces.

```python
from thermalpath import RectangularGrid, RectangularHeater, map_heaters, solve_plate

grid = RectangularGrid((0, 1, 3), (0, 2), 0.5)
heaters = [RectangularHeater(0.5, 2, 0.5, 1.5, 12)]
assert map_heaters(grid, heaters) == (4, 8)
result = solve_plate(grid, 3, west_k=300, east_k=300, heaters=heaters)
assert max(abs(t - ref) for t, ref in zip(result.temperatures_k, (301, 302))) < 2e-12
```

Run `python examples/rectangular_heaters.py` for this synthetic two-cell solve
and three nonaligned mappings. These inputs are numerical examples, not device
measurements.

## Overlap integral and conservation

For heater bounds `[a,b] x [c,d]` and total power P, the prescribed areal
input is `s = P/((b-a)*(d-c))` in W/m2. The overlap dimensions with cell i are

```text
dx_i = max(0, min(x_right_i,b) - max(x_left_i,a))     [m]
dy_i = max(0, min(y_top_i,d) - max(y_bottom_i,c))     [m]
P_i  = P * (dx_i/(b-a)) * (dy_i/(d-c))              [W]
```

An edge or corner intersection alone has zero area. The cells partition the
fully contained footprint, so the sum of overlap areas is `(b-a)*(d-c)`.
Consequently `sum_i P_i = P` in exact arithmetic. Applying this argument to
each heater establishes conservation for overlapping footprints as well.
The implementation uses length ratios to avoid forming a very large areal
input; it sums the contributions with `math.fsum`. It does not renormalize
the outputs to conceal geometric or arithmetic errors.

At steady state each cell satisfies
`sum_lateral Q_out + Q_broad_out = P_i`. Prescribed outward edge flux is
subtracted from the network load; a heater supplies positive input. Internal
conductive powers cancel between neighbors. The existing conductance matrix
is unchanged by heating. Its positive graph energy and a reservoir anchor
therefore still give a unique solution. Heaters do not anchor temperature,
and entirely insulated plates remain rejected. Heater temperatures can exceed
all boundary temperatures; the source-free maximum bound does not apply.

## Independent reference checks

A 12 W heater on `[0.5,3.5] x [0.5,2.5]` has a uniform input of 2 W/m2.
The tests use three separately specified rational overlap tables:

| Cells | Overlap widths [m] | Overlap heights [m] | Total [W] |
| --- | --- | --- | --- |
| 4 | 3/2, 3/2 | 1, 1 | 12 |
| 9 | 1/2, 2, 1/2 | 1/2, 1, 1/2 | 12 |
| 20 | 1/4, 3/4, 1, 3/4, 1/4 | 1/4, 3/4, 3/4, 1/4 | 12 |

Each expected cell value is twice its tabulated width times height. Exact
rational sums give 12 W on all three grids. Thickness changes leave these
prescribed watts unchanged. Translation, length scaling, coincident edges,
single-cell footprints, empty input and overlapping heaters are checked too.

The runnable two-cell example has 4 W and 8 W loads. Conductances are 6 W/K
at the west boundary, 2 W/K internally and 3 W/K at the east boundary.
Writing `theta = T - 300 K` gives the independent discrete system

```text
[ 8 -2 ] [theta_0] = [4]
[-2  5 ] [theta_1]   [8]
```

Its determinant is 36 and the exact solution is `(1,2) K`. The exterior
powers are 6 W at each end. Tests also transpose the problem and scale the
heater power. A separate single-cell reference combines 10 W heating,
2 W outward edge loss and 8 W broad-face loss, giving 302 K at a 300 K ambient.

For the overlap fixtures, binary-exact coordinates leave only the ratios,
products and sums to round. With at most 20 cells, total power 12 W and unit
roundoff about 1.11e-16, a 5e-14 W total budget covers these operations with
margin; the cell budget is 2e-14 W. These are fixture bounds, not a universal
error estimate for arbitrary coordinates. The two-cell matrix has infinity
condition number 25/9. Its 2e-12 K comparison budget allows small dense-solve
roundoff on a roughly 300 K baseline. At most 8 W/K of row conductance times
twice that temperature budget is below the 5e-11 W cell balance budget;
the global budget is 1e-10 W.

## Limits

Overlap integration conserves prescribed power; it does not prove temperature
accuracy or a spatial convergence order. Replacing each partial-cell source
by its cell average can change the temperature error near footprint edges.
The two-cell reference checks the discrete equations, not an exact continuum
solution for a discontinuous source. No contact resistance, through-thickness
gradient, temperature-dependent electrical power or physical validation is
included. The existing small-grid dense-solver limits still apply.

Invalid or zero-rounded footprint area, lost positive cell contributions and
overflowing cell sums are rejected. Extremely small ratios may underflow even
when another multiplication order could retain a result. Accepted subnormal
values have no relative-accuracy guarantee. Coordinates are the supplied
floating-point values; detail already lost during conversion cannot be recovered.
A retained test maps a 1e-20 W input correctly but its temperature rise rounds
away at 300 K, leaving zero computed boundary outflow. Conservation of the
prescribed inputs alone does not certify the solved heat balance.
