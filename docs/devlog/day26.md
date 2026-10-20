# D26: JSON and Markdown evidence reports

Completed on 2026-10-20.

Added `EngineeringReport`, `NumericalCheck` and `Evidence` in
`thermalpath.reporting`. Reports contain inputs and units, declared source
revision, results, numerical checks, source records and limitations. JSON and
Markdown share the same immutable evidence snapshot. The report collects no
environment or filesystem metadata.

The mathematical review found no new solver equations. Check status uses an
inclusive absolute tolerance in the supplied unit. Missing checks are `not_run`;
negative residuals are tested by magnitude. No aggregate validation claim is
created. The heat-spreader example retains the original grid family, candidates,
requirements, tolerances and predictions.

Verification covers exact payload recovery from both formats, deterministic
repeated exports, input mutation isolation, order/duplicate/null retention,
finite-range handling, missing and failed checks, boundary equality, cyclic and
oversized inputs, inert Markdown text, and environment-independent output.
The report example preserves all 18 attempted solves and 78 numerical screens.
Tests compare its full evidence against the unchanged standalone study.

An initial output-size fixture stayed below the cap because it used 261 rows.
It was corrected to 262 rows to exercise JSON overhead beyond the 1 MiB cap;
the implementation limit was unchanged. Initial long-line lint findings and a
documentation-snippet formatting failure were also corrected. These were
test-fixture and presentation issues.

The complete package gate passed 1467 tests. Package-wide
branch-inclusive coverage was 99.71%; the reporting module was 100%.
Distribution inspection matched 212 source files and 22 package modules.
Both installed-wheel exports matched their source-checkout counterparts, and
the documentation example executed successfully. The synthetic report contained
167439 UTF-8 JSON bytes and 183041 Markdown bytes, with source revision `unknown`.
The final documentation bytes were checked again before publication.

These checks verify formatting and evidence retention. They do not authenticate
source declarations, prove that arbitrary caller data is private-information-free,
or establish physical validation.
