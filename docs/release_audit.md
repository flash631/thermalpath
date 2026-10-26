# v0.1.0 evidence audit

Audit date: 2026-10-26. The release keeps the numerical source from
`a557aef14ac38ecfe2764c53dc7a0b4d5a4a17ab`. It changes package metadata,
documentation and reviewed gallery assets. The evidence supports a small
thermal calculation library with tested examples. It does not establish
physical validation, arbitrary-input error bounds or device safety.

## Claim inventory

Each row identifies the supported claim, its evidence and its boundary.
The linked daily records retain the execution dates, original failures and
historical test counts. Those counts are not presented as current suite totals.
The verification files are distributed in the source archive.

| ID | Claim and evidence reviewed | Limit retained |
| --- | --- | --- |
| [D01](devlog/day01.md) | Series resistance and temperature; exact fractions in `test_series_reference.py`. | One prescribed path; synthetic inputs. |
| [D02](devlog/day02.md) | Immutable SI network records; model/domain tests. | Valid structure does not imply an anchored solution. |
| [D03](devlog/day03.md) | Anchored steady networks; rational balances in `test_network_reference.py`. | Weak anchors, rounding and poor conditioning remain possible. |
| [D04](devlog/day04.md) | Signed heat accounting; integer/rational `test_heat_balance_reference.py`. | Global cancellation can hide local errors. |
| [D05](devlog/day05.md) | Strict JSON cases and CLI; round-trip/domain and subprocess tests. | Successful exit is not an accuracy verdict. |
| [D06](devlog/day06.md) | Scalar RC response; 70-digit Decimal `test_rc_reference.py`. | Constant properties; no measured validation. |
| [D07](devlog/day07.md) | Backward-Euler networks; rational `test_transient_network_reference.py`. | Stability does not remove time-discretization error. |
| [D08](devlog/day08.md) | Step energies and four-grid time study; `test_transient_energy_reference.py`. | Endpoint flux is discrete quadrature; no universal tolerance. |
| [D09](devlog/day09.md) | Rectangular geometry; rational measures in `test_grid_reference.py`. | Extreme coordinates can lose representable cells. |
| [D10](devlog/day10.md) | Steady plates; constant, linear and rational `test_plate_reference.py`. | Small dense systems; no general continuum-error bound. |
| [D11](devlog/day11.md) | Cellwise conductivity; two-layer and rational `test_plate_material_reference.py`. | Perfect contact and aligned interfaces. |
| [D12](devlog/day12.md) | Flux/film/broad-face exchange; `test_plate_boundary_reference.py`. | Coefficients are supplied, not predicted from flow. |
| [D13](devlog/day13.md) | Heater overlap powers; exact `test_heater_reference.py`. | Conserved watts do not certify temperature accuracy. |
| [D14](devlog/day14.md) | Physical and matrix residuals; `test_plate_balance_reference.py`. | Residuals refer to different equations. |
| [D15](devlog/day15.md) | One-dimensional profiles and offsets; `test_plate_1d_reference.py`. | Quadratic continuum error persists despite balance. |
| [D16](devlog/day16.md) | Manufactured forcing and 12-cell rational solve; `test_manufactured_plate_reference.py`. | One smooth field and one coarse grid. |
| [D17](devlog/day17.md) | Three-grid error study; independent modes in `test_plate_refinement_reference.py`. | Two observed slopes; lower maximum-error orders retained. |
| [D18](devlog/day18.md) | Headless figures; plotting and example replay tests. | Rendering supplies no new scientific evidence. |
| [D19](devlog/day19.md) | Bounded ordered sweeps and CSV replay; `test_sweep_reference.py`. | Failed cases remain; no unrestricted batch service. |
| [D20](devlog/day20.md) | Local finite-difference sensitivity; three steps and `test_sensitivity_reference.py`. | Local derivatives depend on the valid stencil. |
| [D21](devlog/day21.md) | Seeded bounded sampling; raw-bit and rational `test_uncertainty_reference.py`. | Percentiles are conditional; failures suppress the summary. |
| [D22](devlog/day22.md) | Common-case candidate margins; `test_design_reference.py`. | Nominal classification; ties and failed alternatives remain. |
| [D23](devlog/day23.md) | Reference import with declared provenance and hashes; `test_reference_import.py`. | Structure and hashes do not authenticate measurements. |
| [D24](devlog/day24.md) | Exact-key residuals and equal-row RMSE; `test_comparison_arithmetic.py`. | Missing/excluded rows remain outside the stated denominator. |
| [D25](devlog/day25.md) | 18 heat-spreader solves; independent modal `test_heat_spreader_reference.py`. | The 2 mm candidate is conditional on two assigned cases. |
| [D26](devlog/day26.md) | Deterministic evidence reports; reporting and full study-export tests. | Caller declarations are not verified by formatting. |
| [D27](devlog/day27.md) | Local worksheet uses the library; adapter references and recorded browser checks. | Fixed topology; no hosted service or new heat model. |
| [D28](devlog/day28.md) | AppTest flows and one guarded residual correction; original corner cases still tested. | Original failures retained; no whole-range error bound. |
| [D29](devlog/day29.md) | Fresh normal installation and five checked process timings. | Windows observation with shared caches; no speed guarantee. |
| [D30](devlog/day30.md) | Release metadata, gallery replay, documentation/reference audit and distribution inspection. | A release is a software delivery milestone. |

## Mathematical review

The series model follows Fourier conduction, `R=L/(k A)` in K/W and
`T_source=T_sink+P sum(R)` in K. Every segment carries the same prescribed
power. The graph model uses `sum_j G_ij(T_i-T_j)=P_i`. Extending an unknown-node
vector by zero at fixed nodes gives graph energy
`sum_links G_ij(x_i-x_j)^2`; positive conductances and reservoir reachability
make the reduced matrix positive definite and the steady solution unique.
Excessive extraction can still give an inadmissible nonpositive temperature.

For transients, `C/h + L_uu` is positive definite for positive capacities and
step size, even for insulated components. Modal amplification is
`1/(1+h*lambda)` for nonnegative passive decay rates. This establishes linear
stability, not accuracy at large steps. The RC analytical limit, energy signs,
initial/long-time limits and fixed-step recurrence are checked separately.

The plate balance integrates outward watts over each cell. Internal powers
cancel in opposite pairs. The material face conductance is
`A/(d_i/k_i+d_j/k_j)`, and edge convection includes the half-cell resistance:
`A/(d/k+1/h)`. Broad-face convection uses the sum of exposed-face coefficients
times planform area, with no extra thickness or factor of two. Prescribed
flux and heater loads change the right-hand side; they do not anchor an
absolute temperature. The source-free maximum principle is not extended to
heated or extracted cases. Through-thickness uniformity remains an assumption.

The bounded steady correction solves the assembled matrix against the original
link residual. Its ideal error map is `(I - inverse(A_assembled)*A_exact)*e`.
There is no general contraction claim. The implementation accepts only a
finite positive candidate with strictly smaller maximum physical residual,
then recomputes the separate assembled-matrix residual. The finite reference
tests and all original tolerances remain unchanged.

Spatial and temporal truncation, matrix residual, physical balance, reference
temperature error and physical model error are separate quantities. The
manufactured-grid orders, exact rational references, modal comparisons and
synthetic CSV arithmetic support different claims and are not interchangeable.
No material mathematical question remains open within this release scope.

## References checked

The nine external technical URLs in the product documentation were opened
on the audit date. They support the following narrow uses; none validates this
package or supplies experimental measurements.

| Primary source | Use in the documentation |
| --- | --- |
| [NASA NPARC overview](https://www.grc.nasa.gov/www/wind/valid/tutorial/overview.html) | Distinction between verification and validation. |
| [Python math.fsum](https://docs.python.org/3.12/library/math.html#math.fsum) | Accurate summation with documented floating-point caveats. |
| [NumPy solve](https://numpy.org/doc/stable/reference/generated/numpy.linalg.solve.html) | Direct solve for square full-rank systems. |
| [NumPy random compatibility](https://numpy.org/doc/stable/reference/random/compatibility.html) | Conditions on stream reproduction. |
| [NumPy uniform](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.uniform.html) | Uniform sampling and possible rounded upper endpoint. |
| [NumPy percentile](https://numpy.org/doc/stable/reference/generated/numpy.percentile.html) | Explicit linear interpolation convention. |
| [Matplotlib pcolormesh](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.pcolormesh.html) | Flat cell shading and mesh dimensions. |
| [Matplotlib Agg](https://matplotlib.org/stable/api/backend_agg_api.html) | Headless raster rendering. |
| [Streamlit forms](https://docs.streamlit.io/develop/api-reference/execution-flow/st.form) | Submit the widget values together as a batch. |

The NumPy and Matplotlib stable URLs can change after this date; the dependency
lock records the versions used for the release checks. The project's equations
and rational/modal constructions are explained locally, rather than attributed
to sources that did not establish them. The bundled CSV and gallery are
synthetic project material under MIT. No third-party measurement or image
license is asserted.

## Corrections and retained evidence

The audit replaces stale future-tense descriptions of implemented plate and
refinement features, narrows the package description, and distinguishes
benchmark-specific fitting from the solver's D28 residual correction. Historical
decision records and run tables retain their dates and observations. Gallery
captions state the actual finite errors, and every plotted value is supplied.

The D28 pre-repair failures remain in the public devlog. Weak-anchor rejection,
rounded-away heating, cancellation of local residuals, failed design candidates,
invalid Monte Carlo cases, missing/excluded comparison rows and unavailable
report checks remain covered. There is no new tolerance, coverage exclusion,
reference fit or replacement of adverse data.

## Release boundaries

There is no experimental validation dataset, calibrated uncertainty model,
whole-domain numerical certificate, airflow model, radiation, nonlinear
material law, three-dimensional package model or product-safety approval.
The candidate study is a finite comparison, not a global optimization result.
The optional worksheet has fixed allocation size; this does not establish
process-memory, response-time or multi-user capacity limits. D29 timing samples
remain historical process measurements and are not a benchmark for the release
hardware or for another machine.

The GitHub tag and release identify the delivered source. The release page
and its exact-commit CI provide publication evidence after delivery. They do
not turn any of the scientific limitations above into established claims.
