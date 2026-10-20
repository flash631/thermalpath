# Decision 0026: deterministic evidence reports

Use an immutable serialized snapshot for JSON and Markdown reports. Require
inputs, explicit units, results, numerical checks, provenance, source revision
and limitations. Keep caller declarations visible as declarations.

The report layer adds no thermal equations. A numerical screen checks only
`abs(value) <= tolerance` in the declared unit. A missing value is `not_run`;
failed checks remain present. It does not infer physical validation, design
acceptance, convergence or a general accuracy guarantee.

Retain every result in the Markdown evidence block as well as in JSON. This
avoids losing failed cases or cell fields when making a shorter check table.
Sort object keys, preserve sequence order and copy the snapshot at construction.
Bound serialization and reject nonfinite numbers and unsupported objects.
Escape prose and use a data-dependent code fence to contain supplied markup.

Source revision is explicit and may be `unknown`. Do not inspect a checkout or
collect host/environment metadata during export. Explicit caller text still
requires privacy review. The unchanged synthetic heat-spreader study demonstrates
the contract using its existing frozen requirements and numerical tolerances.
