# Flux and convection boundaries

`solve_plate` accepts constant outward heat flux and convection on lateral
edges, plus convection from the two broad faces. Conductivity may be uniform
or cellwise. Geometry, perfect-contact interfaces and the small dense-solver
scope remain as described in [plate.md](plate.md).

```python
from thermalpath import Convection, RectangularGrid, solve_plate

grid = RectangularGrid((0, 1, 3), (0, 1, 4), 0.25)
result = solve_plate(
    grid,
    2,
    edge_flux_w_m2={"west": -10},
    edge_convection={"east": Convection(5, 300)},
)
assert abs(result.temperatures_k[0] - 314.5) < 2e-12
assert abs(result.temperatures_k[1] - 307) < 2e-12
```

## Inputs and signs

`edge_flux_w_m2` and `edge_convection` are mappings with keys `west`, `east`,
`south` or `north`. An omitted edge is insulated unless its existing `west_k`,
`east_k`, `south_k` or `north_k` argument specifies a positive fixed temperature.
Each edge permits exactly one boundary type. Conflicts are errors even when
the supplied flux or coefficient is zero. Different edges of a corner cell
remain separate faces with their own areas.

Flux is in W/m2 and positive outward: a negative value heats the plate.
Multiplication by the lateral area gives watts. West/east areas are thickness
times cell height; south/north areas are thickness times cell width.
Prescribed flux does not anchor an absolute temperature. At least one fixed
edge or positive convection coefficient is required; pure-flux cases are
rejected even if their total prescribed power is zero.

`Convection(coefficient_w_m2_k, ambient_temperature_k)` stores a finite
nonnegative coefficient in W/(m2 K) and a finite positive ambient temperature
in kelvin. Zero coefficient disables that exchange. The ambient must still
be valid at zero coefficient. Coefficients and ambient temperatures are
constant, supplied inputs; this API does not estimate them from fluid flow.

## Edge convection includes the half cell

For cell temperature T_i, geometric surface temperature T_s, ambient T_a,
local conductivity k, half width d and lateral area A, steady outward power is

```text
Q = (k*A/d)*(T_i-T_s) = h*A*(T_s-T_a)             [W]
T_i-T_a = Q*(d/k + 1/h)/A                         [K]
G_edge = A/(d/k + 1/h)                           [W/K].
```

Eliminating T_s gives the conductance to the ambient reservoir. Using `h*A`
alone would place convection at the cell center and lose the half-cell drop.
For h approaching infinity, G_edge approaches k*A/d, the existing fixed-edge
conductance. For h approaching zero, G_edge approaches zero. The code handles
h = 0 by omitting the connection, without division by zero. The surface
temperature can be reconstructed as `T_i-Q*d/(k*A)` or `T_a+Q/(h*A)`.

## Broad-face coefficient convention

`face_convection=Convection(h_sum, T_a)` describes both broad faces together:

```text
h_sum = h_top + h_bottom                         [W/(m2 K)]
G_broad,i = h_sum * dx_i * dy_i                   [W/K]
Q_broad,i = G_broad,i * (T_i-T_a)                 [W].
```

No factor of two and no thickness multiplier are added. To model one exposed
face, supply its coefficient; the other face is treated as insulated. For
two faces with h = 5 W/(m2 K) each, supply 10. Both faces use the same ambient.
The reduced model assumes uniform temperature through the thickness, so it
does not add a half-thickness conduction resistance. Assess that assumption
separately for a physical plate; large coefficients can invalidate it.

`PlateResult.broad_face_powers_w` returns one combined outward power per cell
in x-first order. `face_powers_w` keeps its four lateral values. Solver results
always provide a broad-face tuple, including zeros when insulated. The new
field defaults to an empty tuple for compatibility with two-argument manual
construction of `PlateResult`; that empty default is not a computed balance.

## Conservation and uniqueness

There is no volume heat generation or storage. Each cell satisfies
`sum(Q_lateral_out) + Q_broad_out = 0`. Prescribed outward flux powers enter
the existing network solver as negative cell loads. Internal face powers are
computed once and assigned exact opposite signs in neighboring cells.
The global sum therefore contains only outer-edge and broad-face exchange.

The matrix energy is the sum of positive internal conductances times squared
cell differences, plus each fixed/convective reservoir conductance times the
squared adjacent cell value. Connectivity and at least one positive reservoir
connection make the matrix positive definite and the solution unique in exact
arithmetic. Flux only changes the right-hand side. Without prescribed flux,
the discrete maximum principle bounds temperatures by reservoir temperatures.
Nonzero flux can drive them beyond that range. Nonpositive solved temperatures
are rejected; that can indicate excessive imposed extraction.

## Independent checks

The example above has k = 2 W/(m K), length 3 m, west input flux 10 W/m2,
east h = 5 W/(m2 K), and ambient 300 K. Direct integration gives east surface
302 K and `T(x)=302+5*(3-x) K`. At x centers 0.5 and 2 m, temperatures are
314.5 and 307 K. Total cross section is 1 m2, so outward powers are -10 W
west and +10 W east. Run `python examples/plate_boundaries.py`. Tests rotate
the case to y, exchange the incoming/outgoing edges, reverse the heat flow,
and change thickness, using unequal axial and transverse cells.

A two-material strip adds a film at each end. Layer lengths 2 and 3 m,
conductivities 2 and 6 W/(m K), ambients 360 and 300 K, and films 2 and
4 W/(m2 K) give series resistance per area 9/4 m2 K/W. Thus flux is
80/3 W/m2 and the material interface is 320 K. This independently checks
the film and material resistances together on unequal cells.

A mixed two-cell reference uses x edges `(0,1,3) m`, y edges `(0,3) m`,
thickness 0.5 m and conductivities `(2,4) W/(m K)`. West convection has
h = 4 and ambient 300 K; south is fixed at 310 K. East outward flux is
-10 W/m2 and north outward flux is 2 W/m2. Combined broad-face h = 1 has
ambient 290 K. Direct area/resistance arithmetic gives

```text
3*M = [[29, -9], [-9, 35]]          M [W/K]
3*b = [5927, 7739]                 b [W]
T = [138548/467, 138887/467]        [K].
```

Tests substitute these fractions into the independent system and separately
verify each rational face power and exact cell balance. One-cell tests check
the broad-face area convention: width 2 m, height 3 m, thickness t, west flux
-20 W/m2 and combined h = 5 give `T-T_a=2*t K` and outward broad power 60*t W
when t is expressed in metres. Zero coefficients reproduce insulation.
Finite sequences toward small/large edge coefficients and large broad-face
coefficients are compared to derived bounds or exact scalar formulas.

## Numerical budgets and limits

The small reference temperature tolerance is 2e-12 K, with zero relative
tolerance. In the flux/film cases the largest internal conductance is 3 W/K,
so two temperature errors contribute at most 1.2e-11 W. Edge conductance
is below 6 W/K. Recovered edge flux has temperature sensitivity
`1/(d/k+1/h) <= 20/9 W/(m2 K)`, so its 5e-11 W/m2 budget covers propagated
temperature error and roundoff. Surface reconstruction uses 5e-11 K; the
largest reconstruction factor is 0.5 m2 K/W. Flux/film cell balances use
2e-10 W. The mixed case has at most 6 W/K broad
conductance, 3 W/K internal conductance and row diagonal 35/3 W/K. Its power
budget is 5e-11 W and cell-balance budget is 1e-10 W; twice that diagonal times
the temperature allowance is below 4.7e-11 W. The one-cell broad conductance
30 W/K uses a 1e-10 W power allowance. These are fixture budgets, not
certified error bounds for arbitrary inputs.

Positive edge resistance factors, their sum and all conductances must be
finite and nonzero in the evaluated arithmetic. Nonzero flux products rounded
to zero, overflowing products/sums and out-of-range solves are rejected.
Extreme scales may fail even when an algebraically rearranged formula fits.
A tiny heating flux can leave the computed temperature at the ambient after
rounding while its prescribed power remains nonzero; the adverse test retains
that unresolved balance. Large broad coefficients amplify small temperature
errors in recovered power, so temperature convergence alone does not certify
power accuracy. No general spatial order, arbitrary-input accuracy certificate
or physical validation is established. Heater mapping and dedicated plate
diagnostics remain separate increments.
