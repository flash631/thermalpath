# ThermalPath development roadmap

These are sequential increments, not calendar deadlines. Select only the first
unfinished item. Every item requires analytical review, independent tests,
the complete quality/privacy gates, and a reviewed publication snapshot.
Dates and evidence are entered before the item's atomic development commit;
delivery SHA and CI state remain private. A research pause leaves the item open.

- [x] D01 | resistance | Series resistance model, example, repository, CI,
  privacy/research workflow, and durable automation scaffold.
  Acceptance: independently obtain 0.05 K/W and 363.90 K; test domains, scaling,
  zero cases and range limits; pass full gate and publication preparation.
  Completion date: 2026-09-15. Evidence: docs/devlog/day01.md.
- [ ] D02 | models | Typed nodes, links, fixed temperatures, and SI validation.
  Acceptance: explicit identifiers and units; reject duplicates, invalid physical
  domains, missing endpoints, and ambiguous fixed-node definitions.
  Completion date: pending. Evidence: docs/devlog/day02.md.
- [ ] D03 | networks | Steady conductance-matrix network solver.
  Acceptance: an anchored hand-solved network and one series limiting case agree
  within derived tolerances; report temperatures and signed link powers.
  Completion date: pending. Evidence: docs/devlog/day03.md.
- [ ] D04 | diagnostics | Connectivity and signed heat-balance diagnostics.
  Acceptance: disconnected/unanchored components produce clear errors; source,
  sink, and link power accounting closes on independent multi-node fixtures.
  Completion date: pending. Evidence: docs/devlog/day04.md.
- [ ] D05 | io/cli | Versioned JSON cases and run-network command.
  Acceptance: document schema/units, reject unknown versions and malformed cases,
  round-trip a case, and integration-test CLI exit codes and numeric output.
  Completion date: pending. Evidence: docs/devlog/day05.md.
- [ ] D06 | transient | One-node RC response with positive heat capacity.
  Acceptance: verify the exponential step response and its initial/long-time
  limits; distinguish stored energy from boundary power.
  Completion date: pending. Evidence: docs/devlog/day06.md.
- [ ] D07 | transient | Backward-Euler networks with piecewise loads.
  Acceptance: positive capacitances, valid ordered times and load changes;
  derive the update matrix and verify a two-node reference and fixed boundaries.
  Completion date: pending. Evidence: docs/devlog/day07.md.
- [ ] D08 | verification | Transient energy accounting and time refinement.
  Acceptance: account for each step's storage/source/boundary energy and use
  at least three time steps to assess expected first-order temporal error.
  Completion date: pending. Evidence: docs/devlog/day08.md.
- [ ] D09 | grid | Rectangular structured-grid geometry.
  Acceptance: verify cell/face areas, thickness-scaled volumes, indexing,
  neighbor consistency, total domain area, and invalid dimensions.
  Completion date: pending. Evidence: docs/devlog/day09.md.
- [ ] D10 | plate | Constant-k finite-volume plate solver.
  Acceptance: fixed-temperature and insulated edges have explicit signs;
  recover a constant field and an independently derived linear profile.
  Completion date: pending. Evidence: docs/devlog/day10.md.
- [ ] D11 | plate | Piecewise material conductivity.
  Acceptance: derive resistance-consistent face conductances and verify the
  two-material 1D flux and interface temperature for unequal cell widths.
  Completion date: pending. Evidence: docs/devlog/day11.md.
- [ ] D12 | boundaries | Flux, edge convection, and face convection.
  Acceptance: use edge areas scaled by thickness, define face coefficient
  convention, and verify sign/zero-coefficient/large-coefficient limits.
  Completion date: pending. Evidence: docs/devlog/day12.md.
- [ ] D13 | sources | Rectangular heater mapping.
  Acceptance: integrate cell/heater overlaps so total prescribed power is
  preserved across nonaligned footprints and at least three grids.
  Completion date: pending. Evidence: docs/devlog/day13.md.
- [ ] D14 | diagnostics | Plate balance, residual, and singularity checks.
  Acceptance: report physical power balance separately from linear residual;
  detect unanchored zero-loss cases and reject incompatible net heating.
  Completion date: pending. Evidence: docs/devlog/day14.md.
- [ ] D15 | verification | Analytical 1D limiting plate cases.
  Acceptance: independently derive profiles/fluxes for declared boundaries,
  compare cell-location values, and justify discretization/roundoff tolerances.
  Completion date: pending. Evidence: docs/devlog/day15.md.
- [ ] D16 | verification | Manufactured 2D solution.
  Acceptance: derive forcing and boundary data independently from a smooth
  chosen temperature field; verify dimensions, derivatives, and corner handling.
  Completion date: pending. Evidence: docs/devlog/day16.md.
- [ ] D17 | verification | Three-grid spatial refinement report.
  Acceptance: use one frozen smooth benchmark/grid family, report norm errors,
  observed order and conservation; preserve unexpected order as unresolved.
  Completion date: pending. Evidence: docs/devlog/day17.md.
- [ ] D18 | plotting | Temperature, transient, and error plots.
  Acceptance: units and readable labels, correct geometry aspect ratio, shared
  comparison scales, deterministic headless export, no fabricated result images.
  Completion date: pending. Evidence: docs/devlog/day18.md.
- [ ] D19 | studies | Parameter sweeps and CSV export.
  Acceptance: bounded deterministic cases with complete inputs, units and
  failures preserved; test ordering and replay from the exported specification.
  Completion date: pending. Evidence: docs/devlog/day19.md.
- [ ] D20 | studies | Local sensitivity calculations.
  Acceptance: compare against a known derivative and at least three perturbation
  sizes; report dimensional/scaled sensitivities with validity near constraints.
  Completion date: pending. Evidence: docs/devlog/day20.md.
- [ ] D21 | uncertainty | Bounded seeded Monte Carlo inputs.
  Acceptance: validate bounds/distributions, record seed/count, reproduce samples,
  and label percentiles as conditional model outputs rather than safety bounds.
  Completion date: pending. Evidence: docs/devlog/day21.md.
- [ ] D22 | design | Candidate comparison to temperature requirements.
  Acceptance: explicit feasible alternatives, common loads/boundaries and
  requirements; preserve ties, infeasible cases and uncertainty qualifications.
  Completion date: pending. Evidence: docs/devlog/day22.md.
- [ ] D23 | comparison | Reference CSV import with provenance.
  Acceptance: require units, source/license and synthetic/experimental labels;
  reject missing or incompatible metadata and untraceable measurements.
  Completion date: pending. Evidence: docs/devlog/day23.md.
- [ ] D24 | comparison | Residuals and RMSE.
  Acceptance: verify using independent synthetic arithmetic, document matching
  coordinates/times, signed residual convention and excluded/missing rows.
  Completion date: pending. Evidence: docs/devlog/day24.md.
- [ ] D25 | case study | Electronics heat-spreader design study.
  Acceptance: freeze cases and requirements, reproduce credible predictions,
  compare feasible candidates and support a qualified engineering recommendation.
  Completion date: pending. Evidence: docs/devlog/day25.md.
- [ ] D26 | reporting | JSON and Markdown reports.
  Acceptance: include inputs/units, source revision, numerical checks, evidence
  provenance and limitations; test deterministic exports and privacy review.
  Completion date: pending. Evidence: docs/devlog/day26.md.
- [ ] D27 | app | Small Streamlit interface.
  Acceptance: controls call the existing library, show units and limitations,
  and provide results without duplicating physics or adding cloud services.
  Completion date: pending. Evidence: docs/devlog/day27.md.
- [ ] D28 | app/tests | AppTest coverage and resource limits.
  Acceptance: exercise valid/error flows, useful input messages, bounded grid
  and sample counts, and agreement with the same direct library case.
  Completion date: pending. Evidence: docs/devlog/day28.md.
- [ ] D29 | reproducibility | Fresh installation, runtime, interview notes.
  Acceptance: install into an empty environment, reproduce the documented demo,
  report measured runtime without machine identifiers and explain key decisions.
  Completion date: pending. Evidence: docs/devlog/day29.md.
- [ ] D30 | release | Final evidence audit and v0.1.0 release.
  Acceptance: audit every claim/reference, build README gallery from reviewed
  results, publish tag/release notes after required repairs and passing CI;
  mark COMPLETE and pause only the project's native automation.
  Completion date: pending. Evidence: docs/devlog/day30.md.
