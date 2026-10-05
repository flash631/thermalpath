# D16: manufactured two-dimensional solution

Completion date: 2026-10-05.

Added a smooth polynomial benchmark with independently derived heat input
and fixed edge data. The [derivation](../manufactured_plate.md) checks spatial
derivatives, SI dimensions, flux signs, compatible corner traces, uniqueness
and exact cell-load integrals. All source and boundary data come from the
chosen field; no fitted temperatures or measured hardware data are used.

Nineteen new tests cover rational polynomial differentiation at sixteen
interior/edge/corner points, exact source and face integrals, an independently
assembled and inverted 12-cell rational matrix, and the standalone example.
Every discrete face and cell temperature is compared with that reference.
The example loads are checked cell by cell against independently integrated
fractions. Tests retain both continuum temperature error and the difference
between discrete and continuum edge outflow partitions.

The 4 by 3 example has 208/45 W of total input, a maximum absolute
centre-temperature error of about 1.344988828041 K, and global physical
imbalance about 6.1e-16 W. The rational matrix condition number in the infinity
norm is about 6.771714. These observations verify the stated discrete fixture;
they do not establish general spatial convergence or physical validation.

No production solver or API changed. See the
[decision](../decisions/0016-manufactured-plate.md). The complete local quality,
package and publication checks are required for this revision; CI evidence
must be checked for the exact delivered commit.
