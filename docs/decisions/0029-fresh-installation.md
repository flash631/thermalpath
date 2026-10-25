# Decision 0029: fresh installation and demo timing

Use a newly created Python 3.12 virtual environment without system packages.
Install the repository's pinned dependencies and a non-editable package build.
Check the installed module location, dependency consistency, and documented
series demo before collecting timing observations. This detects reliance on
the development environment or an import from the source directory.

The series reference is independent of the implementation:
R = (50e-6)/(5 * 2e-4) = 1/20 K/W, total resistance = 61/20 K/W,
and T = 318.15 + 15 * 3.05 = 363.9 K = 90.75 degC. Positive resistances
and a prescribed sink give one steady temperature for this constant-property
series path. There is no heat storage or parallel heat loss. Each output uses
an absolute 1e-12 comparison with zero relative tolerance and an explicit unit
check. This small-case screen is not a general error bound.

Time five serial child processes with a monotonic elapsed-time clock. Each
process starts Python, imports the installed package, calculates the demo,
prints JSON and exits. Include the first observation and report all five,
their median and range. Validation takes place after each timed interval.
Installation, environment creation and validation are outside those intervals.
Limit numerical thread pools to one. There is no runtime pass/fail threshold.

A new process is not a cold filesystem cache. Cache state and other activity
can affect observations; results describe one execution environment. The
record is not a solver benchmark, capacity limit, platform comparison or
physical-validation result. Keep machine names, local paths and user details
out of the published measurements.
