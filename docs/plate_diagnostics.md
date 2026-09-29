# Plate power balance and residuals

Every `solve_plate` result includes an immutable `PlateBalance` in `result.balance`.
All diagnostic powers are in watts. Cell vectors use x-first order; edge totals
use west/east/south/north order. Older manually constructed `PlateResult` objects
default to `balance=None`, so they do not imply that diagnostics were evaluated.

```python
from thermalpath import Convection, RectangularGrid, RectangularHeater, solve_plate

result = solve_plate(
    RectangularGrid((0, 1), (0, 2), 0.5),
    3,
    heaters=[RectangularHeater(0, 1, 0, 2, 10)],
    edge_flux_w_m2={"west": 2},
    face_convection=Convection(2, 300),
)
assert result.temperatures_k == (302,)
assert result.balance.heater_input_w == 10
assert result.balance.edge_outflow_w == (2, 0, 0, 0)
assert result.balance.broad_face_outflow_w == 8
assert result.balance.cell_residual_w == (0,)
assert result.balance.linear_residual_w == (0,)
assert result.balance.imbalance_w == 0
```

Run `python examples/plate_balance.py` for this synthetic example and a case
whose matrix residual is zero despite unresolved physical heating.

## Two different residuals

For mapped heater input H_i, lateral face powers Q_if and combined broad-face
power B_i, the physical cell residual is

```text
r_physical,i = H_i - sum_faces Q_if - B_i                 [W].
I = sum_cells H_i - sum_exterior_faces Q_if - sum_cells B_i [W].
```

Positive residual means excess heat input. Face powers are positive outward,
including prescribed flux. A negative boundary power supplies heat. Internal
faces contribute equal and opposite powers to neighboring cells and are excluded
from the exterior totals. `imbalance_w` is the direct signed sum I; it is not
formed by subtracting rounded heater, edge and broad-face subtotals. Cell sums
and the global sum use `math.fsum`. A nonfinite sum is an error.

The linear residual is evaluated separately as `b - A @ T`, using the actual
binary64 matrix A and right-hand side b passed to the dense network solver.
Its units and sign agree with the physical cell residual, but its rounding
history differs. The network result also exposes this vector by unknown-node
ID as `linear_residual_w`; fixed-only networks return an empty dictionary.
Residual evaluation can itself round and is not an exact-arithmetic bound.
Nonfinite linear residuals are rejected.

For example, a one-cell plate with a 300 K west edge and 2 W/K boundary
conductance has a 600 W boundary term in b. Adding 1e-20 W of heater power
rounds back to 600 W. The computed temperature is 300 K, the linear residual
is zero, and the recovered boundary outflow is zero. The physical cell residual
and `imbalance_w` are both **1e-20 W**. That unmet input is reported without
changing the temperature or declaring the solution accurate.

Inspect every cell. For the two-cell matrix

```text
A = [[8, -2], [-2, 5]] W/K,
H = [4, 8] W, reservoirs = 300 K,
T_exact = [301, 302] K,
```

replacing the solution by `[302, 300] K` introduces temperature error
`e=[1,-2] K`. Both residual vectors become `-A e=[-12,12] W`, while the
global imbalance remains zero. Tests inject these incorrect temperatures to
check that neither cell error disappears from the report.

## Zero-loss plates

Positive conductivity on a rectangular connected grid gives a connected
conductance graph. With all fixed temperatures eliminated, its quadratic form is

```text
x^T A x = sum_internal G_ij (x_i-x_j)^2 + sum_anchors G_ia x_i^2.
```

Every G is positive and finite. A fixed edge or positive edge/broad convection
coefficient supplies an anchor. The quadratic form is then positive for every
nonzero x, so the real-valued system has a unique solution. Prescribed flux,
heaters and zero convection coefficients supply no anchor.

With no anchor, constants span the nullspace. Summing every cell equation
cancels internal conduction and requires net prescribed input to be zero:
mapped heaters minus prescribed outward edge powers. On this connected graph,
zero net input is also sufficient for a real discrete solution up to an
arbitrary additive temperature. It supplies no unique absolute kelvin value.
The solver therefore rejects both cases with distinct messages:

- Nonzero net prescribed input: incompatible loading; no steady solution.
- Exactly zero net prescribed input: nonunique absolute temperature.

The test uses `math.fsum` on the individual mapped heater and prescribed face
terms, before rounded cell right-hand sides can hide a small term. It applies
to the represented finite-volume data, including earlier overlap and flux-area
rounding. There is no implicit near-zero tolerance or arbitrary reference
temperature. Even a 1e-20 W imbalance is incompatible in a zero-loss model.
Overflowing net sums are rejected. Positive anchors can still be lost during
floating-point matrix assembly at extreme conductance ratios; existing
numerical-singularity checks remain active.

## Verification and limits

The independent two-cell fixture has determinant 36 and inverse
`[[5,2],[2,8]]/36 K/W`. Its row-sum condition number is `10*(10/36)=25/9`.
The existing 2e-12 K allowance gives at most 2e-11 W from temperature error
in either physical residual. A 5e-11 W cell/linear allowance covers the few
binary64 products and sums at these scales; the global allowance is 1e-10 W.
The same fixture is transposed and tested at three heater power scales.
These are small-fixture verification tolerances, not public API defaults.
The existing heterogeneous four-cell rational fixture also checks all four
exterior totals independently. Its 2e-10 W face allowance gives 4e-10 W per
two-face edge total; cell/linear and global allowances are 3e-10 W and 1.2e-9 W.

The mixed one-cell reference above uses exact integer arithmetic: 10 W heater
input equals 2 W lateral loss plus 8 W broad-face loss. Reverse flux and inward
broad-face exchange test both signs. Synthetic accounting also retains a 1 W
remainder that subtraction of rounded 1e16 W subtotals loses. Tests preserve
tiny unresolved heaters, boundary-temperature rounding, opposite local errors,
balanced/unbalanced zero-loss cases and a weak positive anchor rounded away
in the assembled matrix.

These reports measure discrete power balance and rounded algebraic residuals.
They do not estimate spatial discretization error, certify arbitrary-input
accuracy, establish convergence order, or validate the physical plate model.
Assess each residual against the problem's actual power scale and required
accuracy; a small global sum alone is insufficient.
