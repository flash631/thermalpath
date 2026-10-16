# D22: candidate comparison to temperature requirements

Date: 2026-10-16.

Added named network link alternatives with common nodes, powers, prescribed
temperatures and upper temperature requirements. All alternatives remain in
input order, including equal results, unmet requirements and failed solves.
The complete network inputs and solve diagnostics remain replayable as CSV.
No ranking or automatic design selection is performed.

Analytical review checked the margin sign and units, positive-conductance
anchored-network uniqueness, disconnected alternatives, negative applied power,
multiple requirements and exact equality. The minimum margin is the upper limit
minus temperature, minimized over required nodes. An explicit absolute band
separates meets, exceeds and borderline decisions; equality is borderline.
The band is a decision convention, not an error estimate or uncertainty bound.
All assessments are nominal; uncertainty is not evaluated and physical
feasibility, safety and reliability are not established.

Twelve independent rational two-node cases agreed within the frozen absolute
tolerance of 2e-12 K/W and zero relative tolerance. Maximum temperature and
margin errors were 5.684341886080802e-14 K. Maximum absolute global imbalance
and linear residual were each 2.2737367544323206e-13 W. Every classification
also matched the independent rational reference. These are finite numerical
checks, separate from physical accuracy or uncertainty coverage.

The scalar example uses 10 W, a 300 K boundary and a 305 K upper limit. Its
conductances of 1, 2, 4 and 4 W/K give 310, 305, 302.5 and 302.5 K: one
exceedance, one borderline result and two equal passing alternatives. The fifth
disconnected alternative is retained as failed, with no temperature margin.
Repeated reports match in the tested environment, and complete inputs replay.

The complete gate passed 1170 public tests (48 added for this increment) and
73 private workflow tests. Package-wide coverage including branches was
99.62% over 1187 statements and 404 branches; design.py had 100% measured
coverage. Lint, formatting, builds and publication checks passed. Source archive
inspection matched all 184 tracked files, and the wheel matched all 20 package
modules. A separately installed wheel reproduced the source example, and the
documentation example ran successfully. No later increment is included.
