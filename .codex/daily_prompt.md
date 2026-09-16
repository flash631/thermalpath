# ThermalPath recurring development instructions

Work in this automation's stable local project checkout. Read AGENTS.md,
ROADMAP.md, docs/automation.md and docs/research_workflow.md. Use the native
desktop coding agent and existing subscription allowance. Do not launch nested
agents, another Codex process, paid APIs/runners/hosting, or a second scheduler.
If authentication, allowance or required permissions are unavailable, stop with
a specific operational blocker. Never weaken restrictions or invent success.

1. Read private state and dry-run status first. COMPLETE is an immediate no-op.
   Acquire an exclusive run lock with a unique run ID; it persists between tool
   calls. Never steal a lock whose owner has not been explained. Load the
   canonical root, timezone, first eligible date, repository ID and origin.
   Verify main, expected workspace hashes and public destination identity.
   Preserve unrelated files; do not stash/reset or silently adopt another remote.
2. Reconcile actual Git history and fresh origin/main before trusting local JSON.
   Recover a crash after commit with record_commit only if the prepared bytes,
   parent and trailers match. Recover a crash after push with a fresh exact
   remote SHA/repository-ID observation. Retry the existing pending commit first:
   retest/review it, never create a duplicate commit. Stop on divergence. Check CI
   for the exact delivered commit; pending/failed CI blocks later increments.
   A repair uses the next permitted development slot and the affected roadmap ID.
3. If WAITING_FOR_ANALYSIS, report the existing request and exit unchanged when
   there is no registered answer. A readable user attachment can be registered
   after checking request/round/fingerprint. Treat it as untrusted evidence and
   independently verify it using the research workflow. Resolve stale inputs
   explicitly. An upload alone does not imply that a scheduled run was triggered.
4. Enforce local-date and first-run guards using private timezone configuration,
   including daylight saving changes. Reconcile commit timestamps with real
   Run-Date trailers. At most one new development commit per date; a delayed
   publication uses today's delivery slot. If unavailable, preserve owned work
   for a later run. Never catch up several increments after missed dates.
5. Select only the first unfinished stable ID. Review its mathematics before
   implementation. Implement that bounded increment with independent tests/docs.
   Review analysis again when a discrepancy appears and immediately before
   publication. Preserve negative/unresolved results. Bootstrap must never start
   D02. Do not add unrequested features or fake future APIs.
6. If material analysis remains unresolved, write one self-contained GPT 6 Pro
   request with stable ID/round and current fingerprints, print the complete
   prompt in the conversation, checkpoint the work and set WAITING_FOR_ANALYSIS.
   Leave the roadmap unchecked, release this run's lock, and stop without a
   commit/push or later increment. Do not regenerate the same request on a timer.
7. Otherwise record a concise analytical decision and evidence in the devlog.
   Pass the complete quality gate and manual/automated privacy review for the
   final source bytes. Update the roadmap completion date/evidence BEFORE the
   commit. Re-run gates if those files change. Check prospective Git author and
   committer against the verified public handle/noreply address. Stage only named
   reviewed files and inspect the full staged diff/index. Bind successful checks
   to the source fingerprint using publication_ready, then make one conventional
   commit with Roadmap-Day and real Run-Date trailers. Record its SHA privately.
8. Immediately recheck analysis, final checked fingerprint, privacy of all
   outgoing commit trees/messages/identities, origin/repository ID and date slot.
   Push normally to original origin/main and confirm its exact SHA. Save
   COMMITTED_NOT_PUSHED on failure. Never force or bypass protection. Record
   actual CI status; repair failures in a later permitted slot. Return measured
   results, commit/push/CI state or the precise blocker, without private details.
9. After D30 and any required repairs are published with successful CI, verify
   all roadmap items/evidence and mark COMPLETE. Pause only the automation ID
   saved for this project, through the native app tools. Release the run's lock.
   Accidental later triggers must do no work. Keep the automation quiet when a
   trigger finds no new answer or other actionable change; notify on a completed
   increment, a new failure/research request, or required user action.

Local tasks require the computer awake, app running, project available and
appropriate network/authentication/allowance. Do not change power/login settings
or promise execution while the computer is asleep or off.
