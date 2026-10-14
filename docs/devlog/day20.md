# D20: local sensitivity calculations

Date: 2026-10-14.

Added local temperature sensitivities for a single steady-network load, fixed
temperature or conductance. Each study retains 3 to 16 requested step sizes,
actual rounded parameter values, dimensional and scaled derivatives, complete
solver cases and failed stencils. The solver and network topology are unchanged.

Analytical review differentiated A(p)T=b(p) in the anchored positive-conductance
domain, checked units and signs, and derived the unequal-spacing quadratic
stencil and its hm*hp*T'''/6 leading truncation error. Constraints, zero-input
scaling, cancellation and finite-range failures are explicit. A successful
stencil does not certify derivative accuracy. No material unresolved analysis
remains within the documented scope.

For the two-unknown-node reference, Ta=304+12/g and the exact derivative at
g=2 W/K is -3 K squared/W. Steps 0.5, 0.25 and 0.125 W/K produced derivatives
-3.1999999999999886, -3.047619047619037 and -3.0117647058823422 K squared/W.
Absolute errors were 0.19999999999998863, 0.04761904761903679 and
0.011764705882342241 K squared/W, consistent with the exact finite-step errors
1/5, 1/21 and 1/85. The h=2 W/K stencil remains failed because it includes zero
conductance. The measured maximum absolute global imbalance across valid
example cases was 0 W; the maximum linear residual was 4.263256414560601e-14 W.
These closure results are separate from the nonzero derivative errors.

Independent tests differentiate two-node balances, compare rational finite-step
errors with absolute 3e-12 tolerances and zero relative tolerance, and check
unequal binary64 spacing against exact rational interpolation at 3e-14 absolute
tolerance. Tests also retain a case where input changes are representable but
temperature changes disappear through rounding. The fresh-process example
replays all retained solver cases. Initial long lines and a documentation code
example were formatted before the final gate. This is numerical verification,
not physical validation.

The complete gate passed 1074 public tests with 99.56% package-wide coverage
including branches (1023 statements and 348 branches). The sensitivity module
has 100% measured coverage, and all 73 private workflow tests passed. Lint,
formatting, package builds and publication checks passed. Archive inspection
matched all 168 tracked source files and 18 wheel modules. The example from a
separately installed wheel matched the source example, and the documentation
example ran successfully. No later roadmap increment is included.
