# D29: fresh installation, runtime and discussion notes

Completed on 2026-10-25.

Created an empty Python 3.12 virtual environment with system packages disabled.
The initial package listing contained only pip 25.0.1. Installed the unchanged
development lock and a normal, non-editable ThermalPath build. Dependency
consistency passed, and isolated Python imported ThermalPath from that
environment's site-packages directory. Package-manager download caches were
used; this was a fresh environment, not a clean-cache installation.

| Component | Observed version |
| --- | --- |
| Python | 3.12.14 |
| ThermalPath | 0.0.1 |
| NumPy | 2.5.3 |
| SciPy | 1.18.1 |
| Matplotlib | 3.11.2 |
| Streamlit | 1.66.0 |

The README demo reproduced interface resistance 0.05 K/W, source temperature
363.9 K, presentation temperature 90.75 degC and power 15 W. Each of five
subsequent runs passed the case, unit and absolute 1e-12 value checks with zero
relative tolerance. The independent reference and timing protocol are recorded
in [decision 0029](../decisions/0029-fresh-installation.md).

## Observed runtime

Five serial fresh Python processes ran the installed package's series demo.
Times include interpreter startup, imports, calculation, JSON output and exit;
installation, environment creation and output validation are excluded.
Numerical thread pools were restricted to one. All observations are retained
in order, rounded here to seven decimal places:

| Run | Elapsed seconds |
| --- | ---: |
| 1 | 0.2633488 |
| 2 | 0.2522610 |
| 3 | 0.2507319 |
| 4 | 0.2553279 |
| 5 | 0.2542904 |

Median: 0.2542904 s. Minimum: 0.2507319 s. Maximum: 0.2633488 s.
These are Windows process observations, not isolated solver times. The first
sample is included. The runs shared filesystem caches and used one environment;
no cold-cache, cross-platform, high-load or scaling comparison was performed.
No speed threshold, runtime guarantee or multi-session capacity is inferred.

## Additional checks and scope

The installed CLI reproduced the bundled heater case: heater 305 K, bath
300 K, link power 10 W toward the bath, bath input -10 W, and zero reported
node/global imbalance. This fixture follows `T = 300 + 10/2 = 305 K`.

Four focused timing-example tests passed. Three reject incorrect temperature,
unit or case labels; one executes the timing example from an unrelated working
directory and checks all five samples and their summary. There is no network
installation inside these tests and no runtime cutoff assertion.

Added fresh-install commands and engineering discussion notes explaining model
scope, independent references, heat balance versus accuracy, UI/library
separation, retained failed evidence and reproduction limits. Corrected stale
README statements that still described the implemented reports and worksheet
as planned features. Included the example, tests and documents in the source
distribution inventory.

The installed solver source is unchanged from D28. This increment adds no heat
model or accuracy claim. Physical validation and device safety remain
unestablished. The final release audit is D30 and was not performed here.
