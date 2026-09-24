# ThermalPath

ThermalPath is a Python library for checking thermal design calculations in
electronics cooling. It is intended for engineers and students who want clear
units, reproducible examples, and evidence they can inspect.

The library implements a steady series-resistance calculation, typed network
inputs with SI validation, a steady conductance-matrix network solver, and
connectivity and signed heat-balance diagnostics, versioned JSON cases, and a
network command. It also evaluates a one-node thermal RC step response and
backward-Euler networks with piecewise constant loads.
Step energy reports and fixed time-refinement examples separate discrete
conservation from temporal error; see [transient verification](docs/transient_energy.md).
Rectangular grid geometry provides cell centers, areas, volumes and neighbors;
see [the geometry API](docs/grid.md).
A 2D heat spreader, design studies, reports, and a small Streamlit interface are planned in
[ROADMAP.md](ROADMAP.md). Those calculations and interfaces are not yet available.

## Install

Python 3.12 is the tested baseline. From the repository root on Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation .
.\.venv\Scripts\python.exe examples\series_stack.py
```

No activation or execution-policy change is needed. Portable equivalents:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation .
.venv/bin/python examples/series_stack.py
```

The lock contains third-party packages only. It records tested versions, with
platform markers for platform-specific dependencies. The network solver uses
NumPy; SciPy and Matplotlib are included for subsequent increments.
D01 physics uses the standard library.
The `app` extra reserves Streamlit as an optional dependency; D01 has no app.
No package registry publication is implied by this repository's package name.

## A runnable calculation

```python
from thermalpath import conduction_resistance, series_temperature

r_tim = conduction_resistance(50e-6, 5.0, 2e-4)
temperature_k = series_temperature(318.15, 15.0, [1.0, r_tim, 2.0])
print(temperature_k)  # 363.9 K
```

| Quantity | Value | Unit |
| --- | ---: | --- |
| Interface layer resistance | 0.05 | K/W |
| Total series resistance | 3.05 | K/W |
| Heat input | 15 | W |
| Temperature rise | 45.75 | K |
| Source temperature | 363.90 | K |
| Source temperature for presentation | 90.75 | °C |

These are synthetic illustrative inputs, not measurements or device specifications.
The headless example prints JSON with a unit for each numerical result.

## Equations and assumptions

For a layer of thickness `L`, conductivity `k`, and cross-sectional area `A`,

```text
R = L / (k A)                    [K/W]
T_source = T_ambient + P sum(R)   [K]
```

The same prescribed power flows through every resistance to a fixed-temperature
sink. Conductivity and geometry are constant. Each resistance must represent a
distinct part of this path. There is no storage, parallel heat loss, or feedback
from temperature to power. See [theory](docs/theory.md) for the derivation and
the separate formulation planned for the depth-averaged plate.

For transient network inputs, interval load conventions, and a runnable example,
see [backward-Euler networks](docs/transient_networks.md).

## Verification and a design decision

An independent exact-rational calculation gives `R_TIM = 1/20 K/W` and
`T_source = 3639/10 K`. Tests compare the implementation to these references,
check signed heat balance, split a layer into two equivalent layers, and exercise
scaling, zero inputs, invalid domains, and floating-point range limits.
[Verification](docs/verification.md) explains the tolerances;
[the D01 devlog](docs/devlog/day01.md) records executed checks.

For these inputs, the interface contributes only `0.05 / 3.05 ≈ 1.64%` of the
total resistance. Even an ideal zero-resistance interface reduces the source
temperature by only `15 × 0.05 = 0.75 K`. This supports examining the other
resistances first **within this illustrative model**. It does not establish a
safe product temperature or a hardware recommendation. The later heat-spreader
study is described in [case study](docs/case_study.md).

## API, CLI, and app

The calculation API contains `conduction_resistance` and `series_temperature`.
Both use SI units and raise `ValueError` for invalid numeric inputs or
unrepresentable calculated outputs. Internally, absolute temperatures are kelvin.
Celsius conversion occurs only when presenting the example.

`Node`, `Link`, and `Network` define immutable network inputs. Node powers are
signed watts, conductances are positive W/K, and prescribed temperatures are
positive kelvin. Constructors reject invalid domains, duplicate IDs, missing
endpoints, and conflicting boundary definitions. See [network inputs](docs/models.md)
for a complete example and the limits of structural validation. These records
do not solve temperatures or establish that a steady solution exists.

`solve_steady(network)` solves small constant-conductance networks and returns
`SteadyResult.temperatures_k` and `SteadyResult.link_powers_w` dictionaries by ID.
Every unknown node must have a path to a fixed-temperature boundary. Positive
link power flows from `node_a` to `node_b`. See [steady networks](docs/networks.md)
for a runnable example, the governing equations, and numerical limits. Independent
hand-solved references are recorded in the [D03 devlog](docs/devlog/day03.md).

`check_connectivity(network)` identifies anchored components and names groups
with missing temperature boundaries. `heat_balance(network, result.link_powers_w)`
reports node residuals, signed reservoir powers, and total heat input/output.
Check the node residuals even when the global balance is zero. See
[diagnostics](docs/diagnostics.md) for the sign convention and a runnable example.

`loads_case` and `dumps_case` read and write version-1 JSON network inputs.
Run `thermalpath run-network examples/cases/heater.json` after installation,
or use `python -m thermalpath.cli run-network examples/cases/heater.json`.
The command prints temperatures, signed link powers, and heat-balance diagnostics
as JSON. See [case format and exit codes](docs/cases.md). The Streamlit interface
is planned for D27.

`rc_step` evaluates the closed-form response of a single body with positive heat
capacity and resistance to a fixed reservoir. `RCResult` separates stored energy
change in joules from boundary heat flow and storage rate in watts. See the
[RC response](docs/transient.md) for equations, a runnable example, references
and floating-point limits.

## Run the checks

```powershell
.\.venv\Scripts\python.exe scripts\check.py
.\.venv\Scripts\python.exe -m pytest
```

The gate runs Ruff lint and format checks, pytest with branch measurement and
at least 90% combined coverage over every implemented package module, then a
wheel/source build. Tests cover the public API, numerical reference, headless
example, and quality-gate driver. Examples and tests restrict numerical thread
pools to one.

The same gate is configured for standard GitHub-hosted Windows and Ubuntu
runners, with read-only workflow permissions. Inspect the actual run for the
source revision being assessed; a configured workflow alone is not execution
evidence.

## Limits and contribution

This release predicts prescribed series paths, steady lumped networks, and a
one-node and network transients with constant properties and fixed boundary
temperatures.
It does not predict
airflow or convection coefficients, perform physical validation, or guarantee
device safety. Finite-precision representability checks do not establish
engineering accuracy. Read [limitations](docs/limitations.md) before using a
result to guide a design.

Contribution guidance is in [CONTRIBUTING.md](CONTRIBUTING.md). The release is
licensed under [MIT](LICENSE), with attribution to ThermalPath contributors.

## References

- [NASA: verification and validation](https://www.grc.nasa.gov/www/wind/valid/tutorial/overview.html)
  distinguishes numerical verification from physical validation.
