# Transient depth-averaged plates

`solve_transient_plate` adds cell heat storage to the rectangular plate model.
Conductivity, heat capacity, boundaries and heater loads stay constant during
each call. Temperatures are uniform through the thickness. The caller supplies
the time grid; backward Euler advances every interval.

```python
from thermalpath import RectangularGrid, RectangularHeater, solve_transient_plate

grid = RectangularGrid((0, 1, 3), (0, 1, 2), 0.5)
result = solve_transient_plate(
    grid,
    conductivity_w_m_k=2,
    volumetric_heat_capacity_j_m3_k=4,
    initial_temperatures_k=300,
    times_s=(0, 0.25, 0.75, 1),
    heaters=[RectangularHeater(0, 3, 0, 2, 6)],
    backend="sparse",
)
print(result.temperatures_k[-1])
print(result.energy_balances[-1].imbalance_j)
```

This synthetic insulated example has total volume 3 m3 and heat capacity
12 J/K. A 6 W heater gives a uniform rise of 0.5 K/s, so the final cell
temperatures are approximately 300.5 K. The heater covers every cell with
the same power per projected area. Its total watts already include the
thickness integration.

## Inputs and outputs

Conductivity uses W/(m K). Volumetric heat capacity is density times specific
heat, in J/(m3 K). Supply either a positive scalar or a flat positive sequence
with one value per cell for each material field. Initial temperature uses
the same scalar-or-sequence convention, in kelvin. Flat indices increase in
x first, exactly as in `RectangularGrid`.

Times must be finite, nonnegative and strictly increasing, with at least two
entries. The initial field applies at the first supplied time, which may be
greater than zero. All supplied material values, temperatures and calculated
cell capacities must lie in the supported finite positive range.

The [steady plate boundary conventions](plate_boundaries.md) also apply:
fixed temperature is prescribed on the geometric edge; edge flux is positive
outward and includes lateral area; edge convection includes half-cell
conduction in series with the film. Broad-face convection uses the sum of
the two coefficients times projected area once. Unspecified edges and broad
faces are insulated. A transient insulated plate is allowed because its
initial field and positive storage define a unique evolution.

`TransientPlateResult` contains:

- `times_s`: the requested time grid, including the initial time.
- `temperatures_k`: one tuple per time, with cells in x-first order.
- `energy_balances`: one `TransientEnergyBalance` per interval, using the
  new endpoint temperature for heat flow.

Energy dictionaries use cell keys `"0"`, `"1"` and subsequent decimal flat
indices. The source term combines heater energy with prescribed inward edge
flux; an outward prescribed flux is a negative source. Reservoir exchange
from fixed-temperature or convective edges has keys `west`, `east`, `south`
or `north`. Broad-face convection uses `broad`. Reservoir energy is positive
into the plate. Insulated boundaries have no reservoir entry.

For every interval, the reported total imbalance is source energy plus
reservoir input minus stored energy. Internal face transfers cancel in the
total, while each cell also has its own residual. A small total does not
remove a large local defect. See [transient energy accounting](transient_energy.md).

## Equation and stability

For cell i, volume V_i and volumetric heat capacity cvol_i give

```text
C_i = cvol_i V_i                                 [J/K]
C_i dT_i/dt = P_i - sum_j G_ij (T_i - T_j)       [W]
```

Here P_i includes the mapped heaters and prescribed inward edge-flux power.
The [plate face laws](plate_materials.md) provide constant conductances G_ij.
Boundary reservoirs keep their specified temperatures. With L the conductance
matrix and subscripts u/f for cell/fixed temperatures, backward Euler solves

```text
(diag(C/dt) + L_uu) T_new = diag(C/dt) T_old + P - L_uf T_fixed.
```

The quadratic form contains positive storage terms C_i/dt times x_i squared,
plus nonnegative internal and boundary conductance terms. Therefore the update
matrix is positive definite in exact arithmetic, including an insulated plate.
For a homogeneous mode with decay rate lambda >= 0, each step multiplies its
amplitude by `1/(1 + lambda*dt)`. This is linearly stable for every positive
step size. Time accuracy remains first order; a long step can give a poor
temperature prediction even when the solve and energy balance are accurate.

The cell-integrated storage term is also described in the
[NIST FiPy finite-volume documentation](https://pages.nist.gov/fipy/en/stable/numerical/discret.html).
The implementation here uses the existing ThermalPath plate assembly and
network integrator. No external solver results are used as test expectations.

## Backends and limits

The default is `backend="dense"`. Select `"sparse"` explicitly to use sparse
assembly and reuse one factorization for consecutive exactly equal computed
time steps. A changed step size replaces the factor, even when a later step
returns to an earlier size. No factor survives a new function call.

Dense matrix storage grows quadratically with cell count. Sparse assembly
follows the occupied entries, but factorization may need more storage. The
full temperature and energy history also grows with cells and intervals.

The model has no radiation, phase change, temperature-dependent properties,
contact resistance, varying-in-time loads or adaptive stepping. Conductivity
is isotropic within each cell, with perfect contact between cells. Negative
flux inputs may heat the plate; positive outward flux can cool it below the
supported temperature domain, in which case the calculation raises `ValueError`.
Positivity is checked at computed states, not throughout the continuous path.

The energy records use backward-Euler endpoint quadrature. They are not exact
continuous-time heat integrals. Spatial error, temporal error and discrete
conservation need separate checks. Neither finite outputs nor numerical
reference agreement establish validity against physical measurements.
