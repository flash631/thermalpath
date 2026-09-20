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

## D03 network references and tolerances

The two-unknown reference uses 2 W/K from a to a 300 K boundary, 1 W/K
between a and b, and 3 W/K from b to a 320 K boundary. Applied loads are
10 W at a and -30 W at b. Independent elimination gives

```text
3 T_a - T_b = 610,     -T_a + 4 T_b = 930
T_a = 3370/11 K,       T_b = 3400/11 K
q_a,cold = 140/11 W,   q_a,b = -30/11 W,   q_b,warm = -360/11 W.
```

The series fixture uses resistances 1, 1/20, and 2 K/W with a 318.15 K
boundary and 15 W input. Exact rational arithmetic gives 363.90, 348.90,
348.15, and 318.15 K along the chain and 15 W through each link. Tests also
multiply every conductance and the applied load by 0.5 and 8; temperatures
must stay unchanged while powers scale by the same factor. Expected results
are computed independently with rational arithmetic, without a matrix solve
or calls to the resistance API.

For the two reduced reference matrices, the infinity-norm condition numbers
`||A||_inf ||A^-1||_inf` are 25/11 and 298.2. The series inverse is
`[[3.05, 2.05, 2], [2.05, 2.05, 2], [2, 2, 2]] K/W`, giving norms
42 W/K and 7.1 K/W. Uniform conductance scaling leaves the condition number
unchanged. With binary64 epsilon `2^-52`, a first-order temperature error budget
`8 n epsilon condition_inf max(T)` is about 2.50e-12 K for two unknowns and
5.79e-10 K for three unknowns. The factor 8 allows for assembly and the short
direct solve on these fixtures; this is a regression budget, not a rigorous
error bound for every LAPACK implementation or arbitrary network.

Round those budgets upward to temperature tolerances of 1e-11 K and 1e-9 K.
Propagate endpoint errors with `|delta q| <= G (|delta T_a| + |delta T_b|)`
and allow additional rounding in subtraction/multiplication: the link-power
tolerances are 1e-10 W and 5e-7 W, respectively. The latter includes the
largest tested conductance, 160 W/K. Each two-boundary nodal balance sums two
link powers and allows 2e-10 W. Relative tolerances are zero. These allowances
concern arithmetic only; they say nothing about input or measurement uncertainty.

Separate tests reject unanchored inputs, nonpositive solved temperatures,
matrix/boundary arithmetic range errors, and link-power overflow or underflow.
One connected fixture has a boundary conductance of 1e-30 W/K beside a
1 W/K internal link: the boundary diagonal contribution rounds away and the
numerical system is singular. Its rejection is preserved as an expected outcome.
These finite tests do not certify every extreme input. See
[solver limits](networks.md#numerical-scope) and the [D03 devlog](devlog/day03.md).

## D04 heat-accounting references

The exact integer ledger uses temperatures a=310 K, b=320 K, cold=300 K,
and warm=340 K. Two oppositely oriented 1 W/K links connect a and cold;
a 1 W/K link connects a to b and a 3 W/K link connects b to warm.
The powers are +10, -10, -10, and -60 W in those orientations. Independent
accounting gives loads +10 W at a and -50 W at b, reservoir inputs -20 W at
cold and +60 W at warm, and total input/output of 70 W. These small integer
values are exactly representable; the accounting assertions use exact equality.
Reversing every link preserves the node and boundary ledger.

The D03 rational reference gives reservoir inputs -140/11 W and +360/11 W.
Including the +10 W and -30 W loads gives both source and sink totals 470/11 W.
Each boundary receives one link, so its tolerance remains 1e-10 W. Each unknown
node sums two link powers, allowing 2e-10 W per residual. The total input/output
tolerances are 2e-10 W, and the global imbalance allows 4e-10 W, covering the
two nodal error budgets. These extend the D03 propagation budget; relative
tolerances remain zero. They are regression allowances for this finite fixture,
not general error certificates or physical uncertainty bounds.

Adverse checks perturb an internal flow by 1 W: the two node errors are -1 W
and +1 W while global imbalance stays zero. Perturbing a boundary flow by 1 W
gives a -1 W global error. Another test preserves the 1 W remainder of external
terms 1e16, 1, and -1e16 W; separately rounded input and output totals are equal.
A 1e-20 W load connected by 1 W/K to a 300 K boundary produces a temperature
rise lost to rounding and a zero reported link power. Its nodal and global
errors remain 1e-20 W. No tolerance conceals that outcome.

Additional checks cover fixed-to-fixed transfer, separate anchored components,
isolated fixed nodes, cycles, component ordering, balanced/unbalanced unanchored
groups, malformed power mappings, and overflowing sums. The supplied flow
checks deliberately do not establish q=G*dT. See [D04 limits](diagnostics.md)
and the [D04 devlog](devlog/day04.md).

## JSON and command verification

Version-1 cases preserve node/link order, identifiers, and normalized binary64
values through `loads_case(dumps_case(network))`. Tests reject malformed JSON,
duplicate or unknown fields, unsupported versions, wrong types, invalid model
domains, overflowing numbers, and nonzero floating tokens rounded to zero.
UTF-8 file errors and unanchored solver inputs produce an error exit without
successful result output. Subprocess tests exercise help and usage exit codes.

The CLI reproduces the exact single-link reference T=300+10/2=305 K and q=10 W.
It also reproduces the D03 rational temperatures/powers and D04 source/sink
totals, using the same absolute error budgets documented above. A tiny load
whose temperature rise rounds away retains its 1e-20 W residual in JSON output.
These checks verify the interface to the existing solver; they add no new
physical validation or general accuracy certificate. See the
[D05 devlog](devlog/day05.md) and [case schema](cases.md).

## Coverage and future verification

`scripts/check.py` measures lines and branches over `thermalpath`, including
implemented modules not imported by a particular test. The combined threshold
is 90%; no module is excluded to raise the score. Quality-driver tests run in the same
pytest session but do not substitute for package coverage.

D01 has no mesh/time-step refinement or physical dataset. Later increments must
add their own analytical references, conservation tests, invalid-input cases,
and regressions. D16 requires an independently derived manufactured solution;
D17 requires three meshes and an observed-order estimate on a smooth problem.
Refinement results must report the actual grid family and tolerances, including
adverse or unresolved outcomes.

See [day01.md](devlog/day01.md) for executed local evidence. Public CI outcomes
must be obtained from the specific run, not inferred from local execution.
