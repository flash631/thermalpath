# Worksheet bounds and bounded numerical correction

Keep the existing worksheet topology. Each render solves one case with three
nodes, two links and two unknown temperatures. There are no grid cells, random
samples, file uploads or user-selected allocation sizes. Test this fixed size
instead of adding unused grid or sampling features. This does not establish a
process memory ceiling, runtime deadline or multi-user capacity.

Validate the existing inclusive control ranges at the server adapter boundary:
0 to 1000 W, 1 to 1000 K, and 0.1 to 100 W/K. Reject nonfinite values before
constructing the network. Keep an explicit submitted-input tuple per session,
so a rerun cannot label unsubmitted edits as the calculated case. On a failed
case, show its input message and no stale result tables; permit resubmission.

The equations remain Ts = Tb + P/Gs and Th = Ts + P/Gc. Positive conductances
and the prescribed sink give a unique steady solution, with each link carrying
P toward the sink and reservoir input -P. No new physics or discretization is
introduced.

The initial D28 protocol applied an absolute tolerance of 2e-10 K or W, with
zero relative tolerance, to three representative cases and all 16 combinations
of input-range endpoints. The initial temperature screen failed two cases. Exact
rational analysis of the binary64 assembled matrix isolates assembly rounding
as the dominant difference from the physical series reference. The existing
solver documents possible accuracy loss at extreme conductance ratios; D27's
four passing reference cases did not establish a bound over the whole range.

Keep every reference case and the original threshold. Repair the library solver
so the UI continues to display the same direct library result. Attempt one
correction from original link balances, retaining individual conductances before
diagonal rounding. With exact matrix A, assembled matrix Ah and error e = T-T*,
the ideal correction gives e_new = (I - inverse(Ah)*A)*e. Thus improvement depends
on the assembly perturbation and conditioning; it is not guaranteed for every
network. Floating-point residual evaluation and addition add further errors.

Accept the correction only when temperatures remain finite and positive and
the maximum absolute original-equation residual strictly decreases. Keep the
direct result on an unusable correction. Preserve initial singularity/range
rejection, final power checks and assembled-matrix residual reporting. At most
two dense solves occur per library call; no new settings or convergence loop
are introduced. The app calls the library once per render.

All 19 original cases now pass. Additional tests cover the two failed cases
with reversed node/link order and equal scaling of loads/conductances, plus
rejection of unhelpful corrections. The devlog retains the pre-repair failures.
These are finite software and numerical observations, without a whole-range
error bound, physical validation or a device-safety conclusion.
