# D24: signed residuals and RMSE

Date: 2026-10-18.

Added `TemperaturePrediction`, `TemperatureResidual`, `ReferenceComparison`
and `compare_reference`. Predictions match exact reference location IDs and
elapsed times. The caller records coordinate/sensor and time correspondence.
No interpolation, fitting, unit conversion or solver equation changed.

Review established r = T_prediction - T_reference in kelvin, and equal-row
RMSE = sqrt(sum(r squared) / n) over matched nonexcluded rows. The divisor is
the matched count, without a sample-variance correction. Repeated observations
each count once. Missing rows and exclusions retain their source rows and
reasons; unused predictions remain available. The three row counts sum to the
reference count. A zero denominator returns None. Duplicate prediction keys
are rejected because they would make the match ambiguous.

The calculation scales by the largest absolute residual before squaring.
The normalized squares lie between zero and one, and their mean does too.
Thus intermediate squaring cannot overflow even when ordinary squared
residuals would. Equal very small residuals also survive this scaling.
Rounding, tiny relative contributions and final subnormal rounding remain.
No differential equation, conservation identity or stability condition is
introduced by this descriptive statistic. Solver conservation diagnostics and
temperature agreement remain separate evidence.

Independent Fraction arithmetic and high-precision Decimal square roots test
signed residuals and RMSE. Ordinary examples use an absolute 1e-14 K tolerance
with zero relative tolerance. Extreme-value comparisons use relative 2e-15
and zero absolute tolerance. Cases include repeated values, zero residuals,
positive and negative residuals, empty matched subsets, incompatible time
keys, invalid inputs and values whose direct squares overflow or underflow.
All 63 focused unit, independent arithmetic and example checks passed. Initial
import ordering and long-line lint findings were corrected before the complete
gate. The mathematical review found no unresolved issue within this scope.

The runnable example retains residuals +3 and -4 K, one missing prediction,
one explicit exclusion and one unused prediction. Its two-row RMSE is
sqrt(25/2) K, about 3.5355339059327378 K. These are assigned synthetic
arithmetic values. They do not establish solver accuracy or physical validation.
Exclusions are declared for the example; the API cannot enforce that users
choose exclusions before looking at errors. Comparisons must report their
matched, missing and excluded counts beside the subset metric.
