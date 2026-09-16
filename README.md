# ThermalPath

ThermalPath is a Python library for checking thermal design calculations in
electronics cooling. It is intended for engineers and students who want clear
units, reproducible examples, and evidence they can inspect.

**D01 implements a steady series-resistance path.** Networks, transients, a 2D
heat spreader, design studies, reports, and a small Streamlit interface are planned
in [ROADMAP.md](ROADMAP.md). They are not available in this version.

## Install

Python 3.12 is the tested baseline. From the repository root on Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe examples\series_stack.py
```

No activation or execution-policy change is needed. Portable equivalents:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv/bin/python examples/series_stack.py
```

The lock contains third-party packages only. It records tested versions, with
platform markers for platform-specific dependencies. NumPy, SciPy, and Matplotlib
are included for subsequent increments; D01 physics uses the standard library.
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

The public API contains only `conduction_resistance` and `series_temperature`.
Both use SI units and raise `ValueError` for invalid numeric inputs or
unrepresentable calculated outputs. Internally, absolute temperatures are kelvin.
Celsius conversion occurs only when presenting the example.

A physics CLI is planned for D05 and the Streamlit interface for D27. Workflow
helpers under `scripts/` are available now; they are not a thermal-model CLI.

## Run the checks

```powershell
.\.venv\Scripts\python.exe scripts\check.py
.\.venv\Scripts\python.exe -m pytest
```

The gate runs Ruff lint and format checks, pytest with branch measurement and
at least 90% combined coverage over every implemented package module, then a
wheel/source build. Workflow helpers have separate behavioral tests, including
temporary Git repositories and local remotes. Tests make no model calls and do
not publish to GitHub or modify a real schedule. Examples and tests restrict
numerical thread pools to one.

The same gate is configured for standard GitHub-hosted Windows and Ubuntu
runners, with read-only workflow permissions. CI contains no coding agent,
uploads, deployment secrets, or external coverage service. A workflow file alone
is not evidence that either CI job passed; inspect the actual run.

## Development and research workflow

Development follows the first unfinished roadmap item, one meaningful increment
at a time. [Automation](docs/automation.md) explains private state, date guards,
publication recovery, and native desktop scheduling. The tracked
[daily prompt](.codex/daily_prompt.md) is reusable; the local project mapping,
schedule, and timezone remain private. No automation is installed by cloning.

Material unresolved mathematics pauses publication. A human transfers a
self-contained question to GPT 6 Pro and returns a text file. The desktop agent
checks that proposed solution independently before resuming the same increment.
See [research workflow](docs/research_workflow.md). Raw exchanges remain ignored.

## Limits and contribution

This release predicts only a prescribed single thermal path. It does not predict
airflow or convection coefficients, perform physical validation, or guarantee
device safety. Finite-precision representability checks do not establish
engineering accuracy. Read [limitations](docs/limitations.md) before using a
result to guide a design.

The project was created with AI assistance for implementation, tests, and
documentation. Analytical checks and test evidence are reviewable; AI assistance
is not independent physical validation or peer review.

Contribution guidance is in [CONTRIBUTING.md](CONTRIBUTING.md). The release is
licensed under [MIT](LICENSE), with attribution to ThermalPath contributors.

## References

- [NASA: verification and validation](https://www.grc.nasa.gov/www/wind/valid/tutorial/overview.html)
  distinguishes numerical verification from physical validation.
- [Python: zoneinfo](https://docs.python.org/3/library/zoneinfo.html) describes
  IANA timezone handling and the cross-platform `tzdata` dependency.
- [GitHub: commit email addresses](https://docs.github.com/en/account-and-profile/reference/email-addresses-reference)
  describes GitHub-provided noreply identity formats.
- [Native scheduled tasks](https://developers.openai.com/codex/app/automations)
  explains desktop project execution and local availability requirements.
