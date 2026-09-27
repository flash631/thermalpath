# Piecewise material conductivity

`solve_plate` accepts a finite positive scalar conductivity or a flat sequence
with one value per cell in the grid's x-first order. Use a Python list or tuple;
the sequence must satisfy `collections.abc.Sequence`. Nested arrays, generators
and mappings are not accepted. Values have units W/(m K). Each value is constant
and isotropic inside its cell and independent of temperature. Materials meet at
cell faces with perfect thermal contact. A material boundary inside a cell is
outside this model.

```python
from thermalpath import RectangularGrid, solve_plate

grid = RectangularGrid((0, 0.5, 2, 3, 5), (0, 1, 3), 0.25)
result = solve_plate(grid, (2, 2, 6, 6) * 2, west_k=360, east_k=300)
assert abs(result.temperatures_k[1] - 335) < 2e-12
assert abs(result.face_powers_w[1][1] - 10) < 5e-11
```

The references here use steady, source-free plates with insulated broad faces
and fixed-temperature or insulated edges. Materials also work with the
[flux and convection boundaries](plate_boundaries.md).
`PlateResult` retains the same temperatures and signed outward lateral powers.
No material database or inferred material properties are used.

## Face resistance

Let cells i and j meet at a face of area A, including plate thickness. Their
centers are distances d_i and d_j from that face. For an eastward or northward
power Q, Fourier conduction across the two half cells gives

```text
T_i - T_face = Q*d_i/(k_i*A)
T_face - T_j = Q*d_j/(k_j*A)
T_i - T_j = Q*(d_i/k_i + d_j/k_j)/A
G_ij = A/(d_i/k_i + d_j/k_j)                    [W/K]
Q_ij = G_ij*(T_i-T_j)                           [W].
```

Continuity of temperature and power at the interface gives the series sum.
The effective face conductivity is `(d_i+d_j)/(d_i/k_i+d_j/k_j)`, a
distance-weighted harmonic mean. An unweighted harmonic mean only applies when
the half widths are equal. An arithmetic mean does not preserve these series
resistances. At a fixed boundary, use only the adjacent cell's half resistance:
`G_ib = k_i*A/d_i`. Insulated faces carry zero power.

Every accepted conductance is positive. The graph-energy proof in the
[plate equations](plate.md#equations-and-uniqueness) therefore still gives a
unique anchored solution and the discrete maximum principle in exact arithmetic.
The same computed internal power is assigned opposite signs in its two cells,
so internal contributions cancel exactly. No interface temperature is stored;
it can be reconstructed as `T_i-Q*d_i/(k_i*A)` or `T_j+Q*d_j/(k_j*A)`.
The two reconstructions may differ slightly after rounding.

## Independent references

For two layers of lengths L_1 and L_2, constant cross-sectional area A, and
left/right temperatures T_L and T_R, direct integration gives

```text
q'' = (T_L-T_R)/(L_1/k_1+L_2/k_2)               [W/m2]
Q = A*q''                                     [W]
T_interface = T_L-q''*L_1/k_1                   [K]
T(x) = T_L-q''*x/k_1                    for x <= L_1
T(x) = T_interface-q''*(x-L_1)/k_2       for x >= L_1.
```

The example uses synthetic lengths 2 m and 3 m, conductivities 2 and 6 W/(m K),
and edge temperatures 360 and 300 K. It gives `q''=40 W/m2` and interface
temperature 320 K. Edges `(0,0.5,2,3,5) m` create unequal widths on both sides
of the material interface. Exact center temperatures are
`(355,335,950/3,920/3) K`. The total area is `3*0.25=0.75 m2`, giving 30 W.
Run `python examples/layered_plate.py` to reproduce these values and both
interface reconstructions. Tests rotate the layers to y, reverse the hot/cold
boundaries, and use both one strip and unequal transverse strips. This aligned
piecewise-linear solution is exact at the ideal cell centers before rounding;
it does not establish a general spatial convergence rate.

A separate four-cell case varies conductivity in both directions. Its x edges
are `(0,1,3) m`, y edges `(0,2,3) m`, thickness 0.5 m, and x-first
conductivities `(2,4,8,16) W/(m K)`. West/east/south/north temperatures are
`(300,360,280,340) K`. Direct half-cell arithmetic gives internal conductances
`G_01=2`, `G_23=4`, `G_02=8/9`, `G_13=32/9 W/K` and the independent system

```text
9*M = [[71, -18,  -8,   0],    9*b = [13320, 23040, 46080, 123840]
       [-18,122,   0, -32],
       [ -8,  0, 188, -36],
       [  0,-32, -36, 428]]
T = (25400/83, 26840/83, 26840/83, 28280/83) K.
```

M has units W/K and b has units W. Exact rational elimination and substitution
check the matrix independently of the floating solver. Separately written face
relations close every rational cell balance. Tests also check constant fields,
scalar/uniform-sequence equality, scaling of all conductivities and thickness,
and two unequal cells with conductivity ratios of one million in either order.

## Comparison tolerances and limits

The small reference temperature allowance is `2e-12 K`, with zero relative
tolerance. For the layered cases, the largest boundary conductance is 6 W/K
and internal conductance is at most 3 W/K. A `5e-11 W` face allowance covers
the resulting temperature-error contribution plus arithmetic roundoff. The
interface allowance `1e-10 K` covers that power allowance multiplied by the
largest reconstruction resistance, 1.5 K/W, plus the temperature allowance.
The four-cell case uses `2e-10 W` per face and `3e-10 W` per cell balance:
`2*32*2e-12=1.28e-10 W` and `2*(428/9)*2e-12 < 1.91e-10 W` give conservative
propagation budgets before arithmetic roundoff. Scaling tests multiply the
power budget by twelve. The large-contrast test scales its face allowance
with the local boundary conductance; it does not demand tiny absolute power
errors after subtracting nearly equal temperatures. These are test budgets,
not rigorous error bounds for arbitrary inputs.

Equal-conductivity faces retain the original `(k*A)/(d_i+d_j)` evaluation;
fixed boundaries retain `(k*A)/d_i`. Unequal faces evaluate `d_i/k_i` and
`d_j/k_j`, then their sum, then A divided by that sum. Each resistance factor
and the final conductance must remain finite and strictly positive. A factor
rounded to zero is rejected rather than silently removing a half-cell
resistance. Tests retain factor overflow, factor underflow, sum overflow, and
conductance overflow/underflow. These evaluation paths can reject inputs even
when an algebraic rearrangement would fit in floating-point range.

Large conductivity contrasts can cause ill-conditioning and loss of temperature
differences. Finite outputs are not an accuracy certificate. The dense solver's
small-grid scope remains. Contact resistance, anisotropy, temperature-dependent
properties, unresolved material mixtures, general mesh convergence and physical
validation are not established by this increment.
