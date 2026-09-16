# Native desktop development workflow

The desktop agent performs coding; `scripts/daily_state.py` is a local
checkpoint/guard helper. It makes no model calls, creates no scheduler, and
does not autonomously commit or publish. Only the native app automation should
trigger daily work, in the same local checkout. A disposable worktree cannot
carry the ignored state and inbox reliably.

## Private configuration and read-only readiness

`.thermalpath-private/` must be completely ignored before any private write.
It contains `state.json`, `run.lock`, `snapshots/`, `research/requests/`,
`research/inbox/`, and private operational evidence. It is not a secret vault.
Never put credentials there. The original personalized bootstrap request is
not part of this repository.

State records the canonical project root, origin and verified repository ID,
automation ID, timezone/schedule, first eligible run date, active increment,
status, owned-file hashes, research IDs/rounds, received-answer hashes,
last development/delivery dates, pending publication SHA, and last verified
remote SHA. Actual values are local configuration, not tracked examples.
Atomic JSON replacement protects against partial writes. The exclusive run
file survives after a helper process exits; it is not a short-lived OS lock.

From the project root:

```powershell
.\.venv\Scripts\python.exe scripts\daily_state.py status
.\.venv\Scripts\python.exe scripts\daily_state.py dry-run
.\.venv\Scripts\python.exe scripts\daily_state.py acquire --run-id unique-run-id
.\.venv\Scripts\python.exe scripts\daily_state.py checkpoint --run-id unique-run-id
.\.venv\Scripts\python.exe scripts\daily_state.py release --run-id unique-run-id
```

`status` and `dry-run` make no edits, network calls, model calls or commits.
They inspect local Git evidence only; fresh remote/CI verification belongs to
the agent before work/publication. The helper fails closed if configuration is
missing. Never initialize over unexplained existing state. An abandoned lock
requires identifying the owning run and preserving its work before explicit
release; do not automatically steal or expire it.

A checkpoint explicitly adopts reviewed dirty files, stores hashes and private
copies, and invalidates the prior quality fingerprint. Compare owned files
before resuming; do not checkpoint unexplained changes just to bypass a guard.
Expected dirty research work can resume. Unexpected files/edits, renames,
symlinks or root/origin changes need explicit review.

## State transitions and publication

| State | Required next action |
| --- | --- |
| READY | Check dates/CI, then select the first unfinished item |
| IN_PROGRESS | Work on that same item and preserve checkpoints |
| WAITING_FOR_ANALYSIS | Review a matching registered answer, or exit unchanged |
| BLOCKED_OPERATIONAL | Resolve the recorded operational blocker before new work |
| READY_TO_PUBLISH | Recheck the prepared snapshot and make one commit |
| COMMITTED_NOT_PUSHED | Retest/review and retry that exact commit first |
| COMPLETE | No-op; pause this automation only |

`resolve_analysis` records the agent's independent mathematical review.
`publication_ready` binds reported successful quality/privacy gates to the exact
public-file fingerprint; it does not execute checks or certify the truth of a
reported review. The agent must actually run the gate and inspect its result.
Gate receipts and raw command logs remain private.

Before the first commit, configure repository-local identity using the verified
public GitHub handle and its GitHub-provided noreply email. Inspect effective
author and committer identities; environment overrides can change them.
Check candidate content and staged blobs with the privacy helper:

```powershell
.\.venv\Scripts\python.exe scripts\privacy_check.py --public-handle PUBLIC_HANDLE --noreply VERIFIED_NOREPLY --staged
```

Immediately before push, add `--history` and, after the first publication,
`--base VERIFIED_REMOTE_SHA`. Verify that base from a fresh observation of the
same public repository ID and origin/main. Inspect every outgoing tree, including
deleted content in earlier commits. Review generated assets manually; a private
JSON mapping of relative asset names to SHA-256 hashes can be supplied with
`--reviewed-assets`. The scanner emits categories and hashed file identifiers,
never a discovered secret. It is a heuristic, not a guarantee.

Update the day's roadmap entry/devlog before committing. Stage explicit reviewed
filenames and inspect the staged diff. Use Conventional Commits with
`Roadmap-Day: DNN` and a real `Run-Date: YYYY-MM-DD` trailer. Re-run gates after
any public-file change, including docs. Record the exact commit using
`record_commit`; a crash after Git commit can be reconciled if parent, trailers
and checked source still match. Never make a second progress-only commit.

Push normally to verified origin/main. On failure retain the same SHA and
COMMITTED_NOT_PUSHED. On an uncertain result, query the remote before retrying.
`reconcile_remote` accepts a fresh, agent-verified repository ID and remote SHA:
it recognizes exact delivery, preserves a retry, and rejects divergence.
A delayed delivery conservatively uses the date on which it is verified.
Git's real committer timestamps remain authoritative if local JSON was lost.
If reconciliation is ambiguous, preserve evidence and block rather than guess.

At most one new development commit per configured local date. A delivery of an
older pending commit also consumes today's slot. A same-day retry of the same
undelivered commit is allowed. CI for the exact SHA must be checked; pending CI
holds later work and failed CI requires a genuine repair in the next available
development slot. A failed check is never re-labelled as successful.

For a CI repair, set `repairing_ci_sha` to the verified affected remote commit
and retain its roadmap ID. The publication guard accepts a failed-CI state only
for that explicit repair; pending CI and an existing unpublished commit still
block a new commit.

## Native task setup and lifecycle

After D01 is pushed and readiness checks pass, create exactly one native local
project automation with the saved `.codex/daily_prompt.md`. Save its ID privately.
Select the available subscription coding model, stable local mode, and the
configured IANA timezone with daylight saving behavior. Set first eligibility
to the day after successful D01 completion. Read the task back and verify ID,
enabled/approval state, destination, execution mode, saved prompt, timezone
context and next run. A timezone-free recurrence string is insufficient evidence.
If the supported interface cannot express or verify this, report NOT SCHEDULED
or BLOCKED and preserve the exact prompt for native-app setup.

Inspect, pause, edit or remove this task through the app's Scheduled/Automations
view or its supported automation tool using the saved ID. Do not alter other
tasks, manually edit undocumented databases, or install another scheduler.
After D30 and all repairs are delivered with successful CI, mark COMPLETE and
pause only this task. Completion guards make later triggers harmless.

Local execution needs the computer awake, app running, project available,
network/authentication and subscription allowance. Do not change power/login
settings. Missed dates do not trigger catch-up commits. An app configuration is
not proof of future execution or of approval to access unavailable resources.
See the [official native scheduling documentation](https://developers.openai.com/codex/app/automations).
