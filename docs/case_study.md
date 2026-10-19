# Electronics heat-spreader study

Within the two specified operating cases, the 2 mm plate is the only tested
thickness that meets the 325 K plate-temperature requirement. Its finest-grid
stress-case peak is 324.453 K, leaving 0.547 K of model margin. Carry this
candidate forward for contact, cooling-system and prototype assessment. That
margin is too small to treat the result as a device approval: the model has
ideal cooling edges and no package or contact temperature drop.

The 1 mm candidate meets the nominal case but exceeds the stress-case limit.
The 0.5 mm candidate exceeds the limit in both cases. All candidates remain in
the output. These are synthetic design calculations; no experimental data,
commercial material, manufacturer rating or measured cooling boundary is used.

## Frozen specification

The specification and numerical acceptance checks were fixed before the first
study solve. The objective is to screen three thicknesses within a 2 mm plate
envelope, using the same footprint, heat input and boundary conditions. Mass
is reported as a tradeoff, with an assigned common density. Cost, strength,
availability and manufacturing feasibility have not been evaluated.

| Input | Assigned value |
| --- | --- |
| Plate length and width | 0.06 m by 0.04 m |
| Isotropic conductivity | 150 W/(m K), constant |
| Density for mass calculation | 2700 kg/m3 |
| Candidate thicknesses, in order | 0.0005, 0.001, 0.002 m |
| Uniform heater footprint | x = 0.02 to 0.04 m; y = 0.01 to 0.03 m |
| Nominal operating case | 10 W heater; both x edges at 300 K |
| Stress operating case | 12 W heater; both x edges at 310 K |
| Other boundaries | Both y edges and both broad faces insulated |
| Temperature requirement | Maximum plate cell temperature at most 325 K |
| Decision band | 0.25 K; equality or margin within the band is borderline |
| Grids, in order | 6 by 4, 12 by 8, 24 by 16 uniform cells |
| Power checks | Absolute total-input error, global imbalance, largest cell residual and matrix residual each at most 1e-8 W |
| Grid check | Last two peak temperatures differ by at most 0.5 K |

Every candidate is evaluated on every grid for both cases: 18 attempted solves.
The heater edges align with all grids, so each refinement integrates the same
footprint and watts. A failed solve remains in place with its error message.
Any failed solve or numerical check makes that candidate/case classification
`unknown`. For completed cases the margin is `325 K - finest-grid peak`.
After numerical checks pass, margins above +0.25 K are `meets`, below -0.25 K
are `exceeds`, and the inclusive band is `borderline`. A recommendation requires
`meets` in both cases. The decision band and grid-change threshold serve
different purposes; neither is a physical uncertainty allowance or error bound.

## Model and independent checks

For temperature uniform through thickness, the governing equation is

```text
-k t (d2T/dx2 + d2T/dy2) = q_area             [W/m2]
Q = integral(heater footprint) q_area dA     [W]
m = density * length * width * thickness    [kg]
```

Positive conductivity and thickness, together with the two fixed-temperature
edges, give a unique steady solution. The finite-volume system has positive
conductances and an anchored positive-definite matrix. Heat leaves through
the two x edges; positive edge flow is outward. Symmetry requires each cooling
edge to carry half the prescribed power. The plate has no storage, through-
thickness gradient, package/contact resistance, radiation or temperature-
dependent properties. Its peak is not a semiconductor junction temperature.

An independent test uses a discrete sine expansion in x and cosine expansion
in y. It does not call the production mesh, heater-mapping or matrix builders.
For cell widths dx, dy, let Gx = k t dy/dx and Gy = k t dx/dy. The eigenvalues are

```text
lambda(m,n) = 4 Gx sin²(m pi / (2 nx)) + 4 Gy sin²(n pi / (2 ny))
m = 1,...,nx; n = 0,...,ny-1
```

The x modes are `sin(m pi (i+1/2)/nx)` and the y modes are
`cos(n pi (j+1/2)/ny)`. Projecting the heater watts onto these modes, dividing
by their eigenvalues and reconstructing gives every discrete temperature.
All 18 fields agree with that calculation within the frozen 2e-9 K absolute
tolerance, with zero relative tolerance. Power/thickness scaling, additive
sink-temperature shifts, reflection symmetry and equal edge outflows are also
checked. This verifies these discrete predictions. It is not an independent
continuum solution or physical validation.

## Results

All 18 solves completed; none failed or were excluded. All numerical checks
passed. Values below are rounded for reading; the example prints full values
and every cell temperature.

| Thickness (mm) | Mass (g) | Nominal peak (K) | Nominal margin (K) | Stress peak (K) | Stress margin (K) | Nominal / stress |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0.5 | 3.24 | 348.177 | -23.177 | 367.813 | -42.813 | exceeds / exceeds |
| 1.0 | 6.48 | 324.089 | 0.911 | 338.906 | -13.906 | meets / exceeds |
| 2.0 | 12.96 | 312.044 | 12.956 | 324.453 | 0.547 | meets / meets |

| Thickness (mm) | Case | 6 by 4 peak (K) | 12 by 8 peak (K) | 24 by 16 peak (K) | Last change (K) |
| ---: | --- | ---: | ---: | ---: | ---: |
| 0.5 | nominal | 347.756410 | 348.080469 | 348.177447 | 0.096978 |
| 0.5 | stress | 367.307692 | 367.696563 | 367.812937 | 0.116374 |
| 1.0 | nominal | 323.878205 | 324.040235 | 324.088724 | 0.048489 |
| 1.0 | stress | 338.653846 | 338.848281 | 338.906468 | 0.058187 |
| 2.0 | nominal | 311.939103 | 312.020117 | 312.044362 | 0.024245 |
| 2.0 | stress | 324.326923 | 324.424141 | 324.453234 | 0.029093 |

The peaks increase with refinement and successive changes decrease in every
case. The largest last change is 0.116374 K. These are finite-grid observations;
they do not bound the unsampled continuum maximum. The nonsmooth heater edge
and changing peak sample location also prevent treating these numbers as the
smooth manufactured benchmark's convergence rate.

Maximum discrepancies over the 18 solves were 2.73e-12 K against the independent
discrete reference, 1.96e-12 W global imbalance, 2.39e-13 W cell residual and
2.28e-13 W matrix residual (rounded upward). Small residuals show that the
discrete balances close; they do not measure modelling error.

## Engineering decision and limits

The 2 mm candidate doubles the 1 mm plate mass from 6.48 to 12.96 g and halves
its predicted temperature rise above the common sink. That scaling follows
from the stated constant-k, insulated-face model. It is the only candidate
eligible for further evaluation under the frozen two-case rule. It is not an
optimized or globally best thickness, and the code does not select a winner.

The stress case is one assigned operating point, not an uncertainty range or
probability statement. At its 12 W load, an additional uniform 0.547 K sink
rise would consume the 2 mm candidate's model margin. This sensitivity makes
cooling-edge temperature and contact characterization the next useful work.
Before accepting a real design, establish actual conductivity, contact and
package resistances, heat load, available cooling, three-dimensional effects
and a matching temperature measurement. A real requirement must identify its
sensor or junction location. No safety, reliability or physical-validation
claim follows from this study.

## Reproduce

From an installed source checkout:

```sh
python examples/heat_spreader.py
python -m pytest tests/verification/test_heat_spreader_reference.py tests/integration/test_heat_spreader_example.py
```

The example prints fixed inputs, grid edges, x-first cell arrays, signed power
diagnostics, counts and classifications. It uses one numerical thread and no
random inputs. It writes no files. Running it twice produces identical output
in the tested environment; floating-point last digits can differ by platform.
See [plate formulation](plate.md), [heater integration](sources.md),
[plate verification](verification.md) and [decision record](decisions/0025-heat-spreader-study.md).

## Earlier series-path illustration

In the series example, the interface is 0.05 K/W of a 3.05 K/W path.
Its fraction is `1/61 ≈ 1.64%`. Replacing this interface with an ideal
connection reduces temperature by `15 × 0.05 = 0.75 K`, to 363.15 K.
This is an algebraic upper bound on interface-only improvement while all other
inputs stay fixed. Examine the larger path resistances first in this model.

This series calculation uses different assumptions from the plate study. Its
interface resistance is not silently added to the plate model, and neither
example chooses a commercial material or certifies a device.
