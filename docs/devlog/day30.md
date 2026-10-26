# D30: release audit and v0.1.0

Source audit date: 2026-10-26.

Reviewed the thirty-increment evidence chain, the public claim boundaries,
mathematical assumptions, numerical references, documentation links and
distribution contents. The [audit](../release_audit.md) maps the scope to
independent tests and dated evidence. Nine external technical documentation
URLs were checked against their stated uses. No physical-validation claim
or new numerical guarantee was added.

Corrected stale descriptions of plate features and refinement as future work.
Clarified that the existing D28 residual correction is part of the solver and
is distinct from a benchmark-specific adjustment. Historical run numbers and
the original failed cases remain. Updated package version to 0.1.0 and added
release notes; solver, plotting and dependency-lock bytes are unchanged.

Generated the three README figures from the existing plotting example and
retained every plotted value plus SHA-256 hashes. The manufactured continuum
samples were checked with exact fractions; the RC discrete recurrence was
checked with rational powers and its analytical curve with 70-digit Decimal
arithmetic. The finest plate maximum error is about 0.125127 K and its two
observed maximum-error orders are about 1.60020 and 1.82593. At 20 s, the 1 s
RC step differs from the analytical result by about 0.090100 K. All three PNGs
were inspected for labels, signs, geometry and comparison scales.

All 22 runnable Python documentation blocks passed in an isolated output
directory with the bundled synthetic input files. A path check across 100
Markdown files and 28 section links found no broken local targets. The 18 heat-spreader solves
completed again, preserving the three candidates and both operating cases.

The public regression suite passed all 1,543 tests with 99.53% package-wide
coverage including branches. No numerical tests, tolerances or coverage scope
changed. Lint, formatting and wheel/source builds passed. Distribution review
compares the archive contents with the checked source, and an isolated installed
wheel replays the series demo and gallery before publication. This complements
the D29 fresh-environment observation; it is not a second clean-environment test.

The tag/release is published only after the delivered source commit passes CI.
Actual publication evidence is the
[v0.1.0 release](https://github.com/flash631/thermalpath/releases/tag/v0.1.0)
and its linked commit/run. This source record cannot assert a future CI result.
The release establishes software delivery, not experimental accuracy or safety.
