# JSON and Markdown reports

`thermalpath.reporting.EngineeringReport` freezes supplied engineering evidence
and exports it as JSON or Markdown. It does not rerun a solver or judge whether
the supplied inputs, results or references are true.

The report requires:

- Explicit inputs, quantity-to-unit declarations and results.
- A source revision: a full lowercase 40-character Git SHA, or `unknown`.
- Named numerical checks with values, units, absolute tolerances and explanations.
- Provenance records labelled synthetic, analytical, numerical or experimental.
- Explicit limitations.

The revision is a caller declaration. Use the revision of the code actually
executed; use `unknown` if that cannot be identified. Supplying a valid SHA
does not prove that the working tree was clean or that a result came from it.
The exporter never reads Git, paths, environment variables, clocks or the network.
Provenance declarations do not authenticate measurements or establish rights
to redistribute a source.

## Small example

```python
from thermalpath.reporting import EngineeringReport, Evidence, NumericalCheck

report = EngineeringReport(
    title="Synthetic one-link network",
    source_revision="unknown",
    inputs={"power_w": 10.0, "sink_k": 300.0, "conductance_w_k": 2.0},
    units={"power": "W", "temperature": "K", "conductance": "W/K"},
    results={"temperature_k": 305.0},
    checks=(NumericalCheck("nodal balance", "W", 0.0, 1e-9, "10 - 2*(305 - 300)."),),
    provenance=(
        Evidence(
            "analytical",
            "One-link steady balance",
            "T = sink + power/conductance",
            "Original arithmetic example; MIT",
            "Assigned inputs; no measurements.",
        ),
    ),
    limitations=("Constant conductance and ideal fixed sink.",),
)
json_text = report.to_json()
markdown_text = report.to_markdown()
```

The arithmetic is `T = 300 + 10/2 = 305 K`; the residual is exactly zero
for these representable values. The exporter merely stores those supplied
numbers. It cannot detect a wrong equation or an incorrectly reported residual.

## Numerical checks

For each `NumericalCheck`, `passed` means `abs(value) <= tolerance`.
Both numbers use the declared unit; tolerance is finite and nonnegative.
Equality passes. A value outside that band is `failed`; a value of `None`
is `not_run`. Give an explanation for a missing value. Empty check lists and
duplicate names are rejected. There is no aggregate success or validation badge.

Use a residual, error or difference as the value. To report a general inequality,
derive an appropriate residual first and describe that derivation; passing a
temperature directly would test its distance from zero.
Balance residuals, matrix residuals and grid differences remain separate checks.
None by itself certifies temperature accuracy, a continuum bound or device safety.
The exporter does not test dimensional consistency or unit completeness.

## Reproduce the heat-spreader report

From the repository root, with the package installed:

```text
python examples/heat_spreader_report.py --format json
python examples/heat_spreader_report.py --format markdown
```

Both commands print to standard output. The optional `--source-revision` argument
accepts the full SHA of the code used; its default is `unknown`.
The example uses the unchanged [heat-spreader study](case_study.md): all 18 grid
attempts, candidate and scenario ordering, inputs, full cell fields, counts,
diagnostics, comparisons and errors remain available. It records 78 checks:
four discrete power checks per grid and one final peak-change check per scenario.
The original `1e-8 W` and `0.5 K` screens are unchanged.
The assigned 325 K requirement and 0.25 K decision band remain in the evidence.
The example preserves failed grids and uses `not_run` for unavailable diagnostics.

The synthetic and numerical provenance labels separate assigned inputs from
computed cell temperatures. The report does not add an experimental claim.

## Export contract and privacy

The JSON schema version is 1. Object keys are sorted; arrays retain order,
duplicates and nulls. Integers remain exact within signed 64-bit range; finite
binary64 values are serialized without display rounding, including signed zero
and subnormal values. Tuples become arrays. No NaN or infinity is accepted.
Supported payload values are plain dictionaries, lists, tuples, strings,
integers, floats, booleans and nulls. There is no report import API.

The snapshot is independent of subsequent changes to caller dictionaries.
Repeated export of the same snapshot produces identical text with LF newlines
and one final newline. Repeating a numerical solve on another platform can
produce different floating-point results; the exporter does not promise
cross-platform solver bitwise equality.

The Markdown report has a numerical-check table, limitations and a complete
JSON evidence block. Text outside the block is escaped, and the fence exceeds
any backtick run inside the payload. No supplied text becomes an active link,
image or HTML element. A conforming Markdown renderer is assumed.

Limits are 1 MiB of encoded JSON, 100000 values including object keys, 16 nesting
levels below the envelope, 4096 characters per nonempty text, 256 checks,
64 provenance records and 64 limitations. Control characters and isolated
Unicode surrogates are rejected. The Markdown representation can be larger.
These bounds limit report size; they do not limit the cost of a preceding solve.

Only caller-supplied data is exported. This avoids automatic collection of
usernames, hostnames, local paths, timestamps or environment contents.
It is **not a redaction tool**: caller-supplied private text is retained.
Review every field, identifier, source locator and result message before sharing.
Escaping markup does not remove private information.
