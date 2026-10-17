# Reference data

`synthetic_temperature.csv` and its JSON sidecar are an original synthetic
arithmetic fixture distributed under this repository's MIT license. They are
not experimental measurements and do not describe a solved thermal transient.

The recipe is T(t) = 300 K + (0.25 K/s) t at times 0, 2.5, 10 and 2.5 s.
The resulting values are 300, 300.625, 302.5 and 300.625 K. The final row repeats
an earlier time deliberately; all four rows have distinct IDs. These decimal
values are exactly representable as binary64 numbers. The `body` location is a
prescribed scalar with no physical sensor or geometry. Every source-record
locator identifies one recipe evaluation in that order.

The sidecar declares units, source, license, generation method, kind, mode and
locations, and binds the exact CSV bytes by SHA-256. Keep LF line endings for
the distributed pair; any byte change requires a new corresponding hash.
See [the import contract](../../docs/comparison.md) for accepted metadata and
limits. No physical reference dataset is included. An external dataset needs
real source/license records and a separate review of measurement traceability
and physical comparability.
