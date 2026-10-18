# Exact reference matching and conditional RMSE

Status: accepted. Date: 2026-10-18.

Match supplied predictions by exact reference location ID and elapsed time.
Require a note describing coordinate/sensor and time correspondence. Do not
infer physical equivalence from names or add hidden interpolation tolerances.
Reject duplicate prediction keys because they do not define a unique match.

Use predicted-minus-reference temperature residuals and equal-row RMSE in
kelvin. Preserve reference order and repeated observations. Retain explicit
exclusions with reasons, missing predictions and unused predictions. Exclusion
takes priority over missingness, so the three reference-row counts are disjoint.
Return None for an empty matched subset and report its denominator beside any
nonempty result. Scale before squaring to avoid avoidable intermediate overflow.

This boundary supports transparent arithmetic comparisons. It does not choose
sensors, interpolation methods, uncertainty weights, acceptance thresholds or
data exclusions for the caller. A small RMSE cannot establish that the source,
measurement quantity, geometry or experimental conditions match the model.
