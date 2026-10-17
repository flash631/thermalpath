# Hash-bound temperature reference tables

Date: 2026-10-17. Status: accepted.

Use one CSV for scalar absolute temperatures and one versioned JSON sidecar for
their declarations. The sidecar contains the exact CSV byte hash. Import both
as bytes so newline translation cannot silently change the recorded identity.
Return hashes of both files, immutable rows and immutable location descriptions.
The importer performs no network or filesystem access.

Require explicit seconds and kelvin. Reject incompatible units rather than
guessing offsets or scales. A transient table has a nonnegative finite elapsed
time in every row; a steady table has blank times. Temperatures are positive
and finite. Reject nonzero decimal tokens that round to zero, while documenting
ordinary binary64 rounding. These are representation rules, not accuracy bounds.

Each row has a unique ID, a declared location and a source-record locator.
Preserve ordering and repeated observations. Require source, stated license,
description, method and synthetic/experimental label for both kinds of data.
Reject incomplete declarations and common bare placeholders. Bound input bytes,
rows and text lengths; do not return a partial table after a failure.

Hash agreement binds the two supplied files but cannot establish the truth of
their declarations. Calibration, uncertainty, legal rights and physical
comparability require source review. No experimental dataset is shipped here.
The included synthetic table follows a stated arithmetic recipe and has no
measurement or solver-validation claim.

This increment changes no heat equation, discretization, stability condition or
conservation convention. Its independent reference is exact rational arithmetic
for four representable samples. Matching and error metrics remain outside this
import contract. No material analytical issue remains unresolved.
