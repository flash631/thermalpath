# D19: parameter sweeps and CSV export

Date: 2026-10-13.

Added bounded Cartesian sweeps of steady-network powers, reservoir temperatures
and conductances. CSV rows retain complete SI inputs, deterministic indices,
results or failure reasons. Replay recomputes from exported inputs. The example
writes a new file and preserves an existing destination.

Analytical review retained the anchored conductance-system assumptions and
checked units, signs, zero load, inverse-conductance scaling, positive absolute
temperatures, and disconnected cases. Independent rational balances cover 18
two-unknown-node cases. Absolute tolerances are 2e-12 K and 2e-12 W with zero
relative tolerance. The example has nine cases: six successes with body
temperatures 300, 300, 310, 305, 320 and 310 K, and three preserved failures at
zero conductance. The measured maximum absolute global imbalance is 0 W for
these six exactly representable scalar cases. This does not establish zero
error for general networks or physical validation.

Focused tests cover admission bounds, ordering, duplicate values, scalar and
network failures, quoted identifiers, stale-output replacement, replay, and
fresh-process export. An initial oversized-input test used an excessively long
automatically generated test name and failed during Windows test setup; a short
explicit test ID fixed the harness without changing the tested size limit.
Initial import and documentation-example formatting were corrected before the
final publication gate.

The complete quality gate passed 1039 public tests with 99.53% package-wide
branch-inclusive coverage (948 statements and 328 branches); the new studies
module has 100% coverage. All 73 private workflow tests passed. Lint, formatting,
package builds and publication checks passed. Archive inspection matched all
160 tracked source files and 17 wheel modules. A separately installed wheel
reproduced the example CSV bytes. These checks support this implementation and
the stated finite examples. No later roadmap increment is included.
