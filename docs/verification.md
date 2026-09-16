# Numerical credibility

Verification asks whether the implemented equations are solved correctly.
Comparison with another numerical model checks agreement under stated inputs.
Validation tests whether predictions describe independent physical measurements
within their uncertainty. These are separate forms of evidence, following the
[NASA overview](https://www.grc.nasa.gov/www/wind/valid/tutorial/overview.html).

## D01 references and tolerances

The test reference uses exact rational arithmetic independently of the public
functions:

```text
R_TIM = (50 / 1,000,000) / (5 × 2 / 10,000) = 1/20 K/W
R_total = 1 + 1/20 + 2 = 61/20 K/W
T = 31815/100 + 15 × 61/20 = 3639/10 K
T_C = 3639/10 - 27315/100 = 363/4 °C
```

The resistance comparison uses relative tolerance `1e-14` with zero absolute
tolerance; the temperature and heat-balance checks allow `1e-12 K` and `1e-12 W`.
These bounds cover binary64 rounding in a small number of operations at these
scales. They are not uncertainties on material properties or measurements.

The rejected heat is independently reconstructed as
`P_out = (T_source - T_ambient)/(61/20)`. The signed balance `P_in - P_out`
must vanish within the stated tolerance. Other checks cover geometric scaling,
monotonicity, subdivision of a homogeneous layer, zero power/resistances,
empty input, invalid signs, nonfinite inputs, and calculated overflow/underflow.

## Coverage and future verification

`scripts/check.py` measures lines and branches over `thermalpath`, including
implemented modules not imported by a particular test. The combined threshold
is 90%; no module is excluded to raise the score. Helper tests run in the same
pytest session but do not substitute for package coverage.

D01 has no mesh/time-step refinement or physical dataset. Later increments must
add their own analytical references, conservation tests, invalid-input cases,
and regressions. D16 requires an independently derived manufactured solution;
D17 requires three meshes and an observed-order estimate on a smooth problem.
Refinement results must report the actual grid family and tolerances, including
adverse or unresolved outcomes.

See [day01.md](devlog/day01.md) for executed local evidence. Public CI outcomes
must be obtained from the specific run, not inferred from local execution.
