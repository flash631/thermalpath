# Contributing

Read AGENTS.md and the first unfinished ROADMAP item before changing scope.
Use Python 3.12, the pinned development environment, and a small typed public
API. Explain SI units, signs, physical domains, and numerical tolerances.
Do not implement later APIs as empty functions or fake solver outputs.

For physics changes, derive an independent analytical/manufactured reference,
test invalid inputs, and check limiting cases and conservation where applicable.
Run `python scripts/check.py` with the intended environment's Python. Coverage
does not replace physical reasoning or independent measurements.

Keep changes focused. Preserve unrelated work and adverse results. Use
Conventional Commits, such as `fix(core): reject nonfinite temperature results`.
The daily workflow additionally uses `Roadmap-Day` and real `Run-Date` trailers.
Do not backdate commits or create progress-only commits to maintain a streak.

Review every public file and Git identity for privacy. Stage named files only.
Never commit raw research exchanges, credentials, environment dumps, absolute
local paths, private email addresses, or personal screenshots. Any suspected
secret in outgoing history blocks publication until a human-approved remedy.
Do not rewrite history, force push, or weaken security controls.

AI assistance is allowed when disclosed. Returned model output is untrusted
evidence and must be reviewed independently before use. A novel idea remains a
hypothesis until supported by checkable mathematics and evidence.
