# D11: piecewise material conductivity

Completion date: 2026-09-26.

Extended `solve_plate` to accept positive cellwise conductivity in x-first
order, retaining the scalar API and `PlateResult`. Shared material faces use
the series sum of their two half-cell resistances. Fixed edges use local
conductivity, and equal-k faces retain the established arithmetic.

Analytical review checked Fourier conduction, temperature and flux continuity,
SI units, unequal-width weighting, boundary half widths, anchoring, uniqueness,
the discrete maximum principle and internal cancellation. Interfaces are aligned
with cell faces and have perfect contact. See [the decision](../decisions/0011-piecewise-conductivity.md).

Forty new tests cover independent two-layer profiles in both axes and flow
directions, interface reconstruction from either side, a rational 2D matrix,
uniform-input compatibility, scaling, constant fields, high contrasts and
invalid/range-limited inputs. Initial reference assembly omitted boundary
terms from two 2D matrix diagonals; the discrepancy was corrected by summing
the independently derived face conductances. Exact substitution and separate
face balances now verify that reference. No solver change was needed for it.

The runnable synthetic example gives 40 W/m2 eastward flux, 30 W total power,
and 320 K at the material interface. Computed center temperatures agree with
`(355,335,950/3,920/3) K` within `2e-12 K`. Both interface reconstructions agree
within `1e-10 K`. Full comparison budgets and arithmetic evaluation limits
are documented in [piecewise materials](../plate_materials.md).

Adverse tests retain resistance-factor overflow/underflow, sum overflow and
conductance range failures. Large conductivity contrast can amplify roundoff;
a successful solve does not certify accuracy. No general spatial convergence,
contact-resistance model or physical validation is claimed. CI evidence must
be checked for the delivered revision.
