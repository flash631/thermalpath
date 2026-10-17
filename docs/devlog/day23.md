# D23: reference CSV import with provenance

Date: 2026-10-17.

Added `loads_reference`, frozen reference rows and a dataset result carrying
source declarations and exact byte hashes. The CSV has unique sample IDs,
declared locations, elapsed seconds or blank steady times, absolute kelvin
temperatures and source-record locators. A versioned JSON sidecar declares
units, source, license, method, locations and synthetic/experimental kind.
Its CSV hash must match the supplied bytes.

Review checked absolute-temperature and elapsed-time domains, decimal-to-float
limits, strict schema admission and the distinction between file identity and
source authenticity. Repeated observations and original order are retained.
Missing metadata, incompatible units, malformed rows, duplicate IDs, mismatched
hashes and nonfinite or underflowed numbers reject the complete import.
No numerical solver or physical equation changed.

The shipped synthetic recipe is T(t) = 300 K + (0.25 K/s) t, evaluated at
0, 2.5, 10 and 2.5 s. Independent rational checks recover 300, 300.625, 302.5
and 300.625 K exactly, with zero error for these representable values. The
repeated time remains present. The data are arithmetic examples, not physical
measurements or a solved thermal transient.

The import tests cover steady/transient contracts, both kind labels using
synthetic parser fixtures, Unicode locators, BOMs, CRLF, quoted commas, retained
replicates, metadata and row rejection, byte/row limits and hash changes.
The example runs from an unrelated working directory. An initial example test
expected the shortened license label; it was corrected to check the complete
supplied declaration, `MIT; see LICENSE`.
The excessive-nesting fixture was also increased from 2000 to 10000 levels
because the smaller input did not exceed this interpreter's parser limit.
All 137 focused import tests then passed, including the exact rational fixture.

The importer checks supplied traceability fields but cannot authenticate a
source, evaluate measurement quality or establish license rights. Experimental
use still requires review of the source, sensors, conditions, processing and
uncertainty. No physical validation, fitting, residual or RMSE result is claimed.
