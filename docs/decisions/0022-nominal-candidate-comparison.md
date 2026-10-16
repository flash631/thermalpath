# Nominal candidate comparison

Date: 2026-10-16. Status: accepted.

Candidates share one immutable node collection, including powers and fixed
temperatures, and one requirement list. Each alternative supplies named passive
links. This makes the nominal load and boundary comparison explicit while
allowing different conductances and connectivity. Models with other node sets
or different loads belong in separate studies.

Use node upper limits in kelvin. Compute each margin as limit minus temperature
and assess the smallest required-node margin. A user-supplied finite nonnegative
band defines meets, exceeds and borderline outcomes. Equality at either band
edge remains borderline. The band has no implied numerical or physical coverage.
An exceedance controls the result even if another node is borderline.

Keep every alternative and equal result in input order. Do not select a winner:
temperature margin alone omits cost, mass and practical constraints. Preserve
solver failures with empty margins, their messages and complete inputs. Reject
malformed comparison specifications before solving; propagate unexpected errors.

Reuse the steady-network solver and existing replayable case format. Store the
common requirements, decision band, named assessments and nominal-only
qualification alongside that evidence. Positive conductances with anchored
connected components give unique model solutions. A disconnected unknown
component does not meet that condition and can be a retained failed alternative.

This increment does not propagate uncertainty. A nominal pass is conditional on
the supplied model, loads and boundaries. The uncertainty module's finite sample
percentiles cannot be substituted for safety bounds. Numerical reference tests
do not establish physical validation or manufacturability. No material analysis
question remains unresolved for this bounded comparison.
