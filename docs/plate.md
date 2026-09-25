# Constant-conductivity steady plate

`solve_plate` solves a source-free plate with constant isotropic conductivity
and uniform thickness on a `RectangularGrid`. Each lateral edge is either a
fixed positive temperature in kelvin or insulated. Both broad faces are
insulated. The temperature is assumed uniform through the thickness. Inputs
are synthetic unless separate measurement provenance is supplied.

```python
from thermalpath import RectangularGrid, solve_plate

grid = RectangularGrid((0, 0.01, 0.03, 0.06), (0, 0.01, 0.04), 0.002)
result = solve_plate(grid, 150, west_k=300, east_k=320)
assert abs(result.temperatures_k[0] - 905 / 3) < 2e-12
assert abs(result.face_powers_w[0][0] - 1) < 5e-11
```

The conductivity is in W/(m K), coordinates and thickness are in metres.
Omitted `west_k`, `east_k`, `south_k` or `north_k` values default to `None`,
which means zero outward heat flow. At least one edge must have a prescribed
temperature. An entirely insulated source-free plate has an arbitrary constant
temperature, so this solver rejects it as nonunique.

`PlateResult.temperatures_k` is a tuple in x-first flat cell order. The tuple
`face_powers_w` contains one west/east/south/north tuple per cell. Positive power
leaves that cell. Insulated outer faces return exactly zero. Each shared face
is evaluated once and assigned opposite signs in its two cells. Corner cells
have two distinct boundary faces; no corner temperature is invented. Different
temperatures on adjacent edges are permitted, but the resulting boundary jump
can reduce continuum regularity near that corner.

## Equations and uniqueness

For constant conductivity k and thickness t, the depth-averaged source-free
equation is `-div(k*t*grad(T)) = 0`. Integrating over a cell gives

```text
Q_out,f = G_f * (T_cell - T_other)     [W]
G_f = k * A_f / d_f                   [W/K]
sum_faces Q_out,f = 0                 [W]
```

On west/east faces, `A_f = t*dy`; on south/north faces, `A_f = t*dx`.
An internal face uses the sum of its adjacent half widths for `d_f`.
A fixed boundary uses the cell half width and the prescribed edge temperature.
An insulated face contributes no connection. Thus a fixed edge acts at the
geometric edge, not at the outermost cell center. Using a full width there
would add resistance and fail the linear-profile reference.

The rectangular cell graph is connected. Its matrix has positive diagonal
entries and nonpositive off-diagonal entries. For a vector v on the cells,

```text
v^T M v = sum_internal G_ij*(v_i-v_j)^2 + sum_fixed_faces G_ib*v_i^2.
```

Positive conductances and at least one fixed edge make this expression positive
for every nonzero v, so the discrete solution is unique. At a cell maximum,
every outward difference is nonnegative. The balance and connectivity then
give the discrete maximum principle: the solution lies between the minimum
and maximum fixed temperatures in exact arithmetic. Summing cell equations
cancels shared-face powers, leaving zero net outer-edge flow. These are
properties of the equations; rounded solutions can have small residuals.

## Independent references

A common temperature on every fixed edge gives a constant field, even with
only one fixed edge and the remaining edges insulated. For fixed west/east
temperatures and insulated south/north edges, direct integration of `T''=0`
gives

```text
T(x) = T_w + (T_e-T_w)*(x-x_w)/(x_e-x_w)
Q_east = -k*t*height*(T_e-T_w)/(x_e-x_w).
```

This linear field satisfies every finite-volume face relation on unequal
cells, so there is no spatial truncation error for this reference in exact
arithmetic. Tests also rotate the profile to y and reverse the hot/cold edges.
This exactness does not establish a general spatial convergence order.

Run `python examples/steady_plate.py` for a 60 mm by 40 mm by 2 mm example.
With k = 150 W/(m K), west = 300 K and east = 320 K, the three x-center
temperatures are 301.666666667, 306.666666667 and 315 K in both rows.
Total outward powers are +4 W west and -4 W east; the other edges are insulated.

A separate 2D reference uses x edges `(0,1,3) m`, y edges `(0,2,3) m`,
t = 0.5 m and k = 6 W/(m K), with west/east/south/north temperatures
`(300,360,280,340) K`. Direct face arithmetic gives

```text
M [W/K] = [[21, -4, -2,  0],    b [W] = [4440, 3840, 3840, 5160]
           [-4, 20,  0, -4],
           [-2,  0, 16, -2],
           [ 0, -4, -2, 21]]
T [K] = [2120/7, 320, 320, 2360/7].
```

The test substitutes these exact fractions into the independent matrix before
comparing the numerical result. Separately written face formulas give zero
cell balances in rational arithmetic and check all sixteen signed powers.

## Numerical scope

The implementation converts the cell connections to the existing dense steady
network solver. For N cells, matrix storage is O(N squared) and the direct
solve costs O(N cubed) operations. Use small grids. No sparse solve, variable
material, heater mapping, flux/convection boundary or transient plate API is
provided by this increment.

The small references use `2e-12 K` absolute temperature tolerance and `5e-11 W`
absolute face-power tolerance, with zero relative tolerance. At 340 K the
temperature budget is about 27 binary64 epsilons. The largest rational-reference
face conductance is 12 W/K, so two such temperature errors contribute at most
`4.8e-11 W` before multiplication roundoff. The linear fixtures have at most
16 W/K on a fixed boundary (one solved-temperature error) and 4 W/K internally
(two errors), both within the same power budget. The four-cell balance uses `1e-10 W`;
`2*21*2e-12 = 8.4e-11 W` bounds its propagated temperature budget before
roundoff. Scaling tests multiply the power allowance by the largest scale, 12.
These tolerances are fixture budgets, not rigorous bounds for arbitrary inputs.

Nonfinite/zero-rounded conductances, singular or out-of-range solves, and
nonpositive solved temperatures fail explicitly. Evaluation uses `(k*A)/d`;
an intermediate product may overflow or underflow even if a rearranged final
expression would fit. Extreme aspect ratios, coordinate offsets, conductance
scales and accepted subnormal values can reduce accuracy. Half widths represent
the ideal cell midpoint distances; stored absolute centers may round slightly.
An adjacent-representable boundary temperature test retains a nonzero cell
balance when its temperature rise rounds away. A successful return is not an
accuracy certificate. No general mesh-convergence or physical validation claim
is made. Detailed plate diagnostics and spatial refinement remain separate
roadmap increments.
