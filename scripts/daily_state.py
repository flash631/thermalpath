"""Durable checkpoints and conservative publication guards; no model calls.

The desktop agent owns engineering review and Git publication. This module
records evidence and refuses inconsistent transitions. See docs/automation.md.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PRIVATE = ".thermalpath-private"
STATUSES = {
    "READY",
    "IN_PROGRESS",
    "WAITING_FOR_ANALYSIS",
    "BLOCKED_OPERATIONAL",
    "READY_TO_PUBLISH",
    "COMMITTED_NOT_PUSHED",
    "COMPLETE",
}


def git(root: Path, *args: str, allow_failure: bool = False) -> str:
    """Run Git without a shell; do not expose stderr containing private paths."""
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        check=False,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if result.returncode and not allow_failure:
        raise ValueError("Git operation failed; inspect private diagnostics locally")
    return result.stdout.decode("utf-8").rstrip("\n")


def digest(value: bytes) -> str:
    """Return a SHA-256 content identity."""
    return hashlib.sha256(value).hexdigest()


def fingerprint(manifest: dict) -> str:
    """Hash a deterministic relative-path manifest."""
    return digest(json.dumps(manifest, sort_keys=True).encode())


def atomic_json(path: Path, value: dict) -> None:
    """Replace one JSON file atomically on the same filesystem."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def private_directory(root: Path) -> Path:
    """Require Git's ignore rule before storing any private material."""
    if (
        git(root, "check-ignore", f"{PRIVATE}/probe", allow_failure=True)
        != f"{PRIVATE}/probe"
    ):
        raise ValueError("Private directory must be completely ignored first")
    if git(root, "ls-files", "--", PRIVATE):
        raise ValueError("Private files are present in the index")
    return root / PRIVATE


def load(root: Path) -> dict:
    """Read existing configuration without creating files."""
    state = json.loads((private_directory(root) / "state.json").read_text("utf-8"))
    if Path(state["project_root"]).resolve() != root.resolve():
        raise ValueError("Project mapping changed")
    if state["status"] not in STATUSES:
        raise ValueError("Unknown workflow status")
    return state


def save(root: Path, state: dict) -> None:
    """Persist private state only after rechecking the ignore boundary."""
    atomic_json(private_directory(root) / "state.json", state)


def acquire(root: Path, run_id: str) -> None:
    """Create an exclusive file that remains locked between tool invocations."""
    if not re.fullmatch(r"[A-Za-z0-9-]{1,80}", run_id):
        raise ValueError("Invalid run ID")
    directory = private_directory(root)
    directory.mkdir(exist_ok=True)
    try:
        with (directory / "run.lock").open("x", encoding="utf-8") as stream:
            json.dump(
                {"run_id": run_id, "created_utc": datetime.now(UTC).isoformat()}, stream
            )
    except FileExistsError as exc:
        raise ValueError("Run lock exists; never steal an unexplained lock") from exc


def require_lock(root: Path, run_id: str) -> None:
    """Reject mutations from a run that does not own the durable lock."""
    path = private_directory(root) / "run.lock"
    if not path.exists() or json.loads(path.read_text("utf-8"))["run_id"] != run_id:
        raise ValueError("Run does not own the lock")


def release(root: Path, run_id: str) -> None:
    """Release only the explicitly identified run's lock."""
    require_lock(root, run_id)
    (private_directory(root) / "run.lock").unlink()


def public_manifest(root: Path) -> dict[str, str]:
    """Hash tracked and unignored candidate files, rejecting links/escapes."""
    names = git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    result = {}
    for name in sorted(set(names.split("\0")) - {""}):
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Linked or escaping public file")
        if path.is_file():
            result[name] = digest(path.read_bytes())
    return result


def dirty_manifest(root: Path) -> dict[str, str | None]:
    """Record additions, modifications, and deletions; reject ambiguous renames."""
    entries = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    result = {}
    for entry in filter(None, entries.split("\0")):
        if "R" in entry[:2] or "C" in entry[:2]:
            raise ValueError("Resolve renamed files explicitly before checkpointing")
        path = root / entry[3:]
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Linked or escaping dirty file")
        result[entry[3:]] = digest(path.read_bytes()) if path.is_file() else None
    return result


def verify_owned(root: Path, state: dict) -> None:
    """Expected paused work can resume; any unexplained change blocks it."""
    if dirty_manifest(root) != state.get("owned_files", {}):
        raise ValueError("Unexplained workspace changes; preserve and review them")


def checkpoint(root: Path, state: dict, run_id: str, status: str) -> None:
    """Save explicitly reviewed owned work, with no-clobber private copies."""
    require_lock(root, run_id)
    if status not in {"IN_PROGRESS", "BLOCKED_OPERATIONAL", "WAITING_FOR_ANALYSIS"}:
        raise ValueError("Checkpoint status is invalid")
    owned = dirty_manifest(root)
    manifest = public_manifest(root)
    snapshot = private_directory(root) / "snapshots" / uuid.uuid4().hex
    snapshot.mkdir(parents=True)
    for name, checksum in owned.items():
        if checksum is not None:
            target = snapshot / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((root / name).read_bytes())
    atomic_json(snapshot / "manifest.json", {"owned": owned, "public": manifest})
    state.update(
        status=status,
        owned_files=owned,
        input_fingerprint=fingerprint(manifest),
        preserved_work_manifest=str((snapshot / "manifest.json").relative_to(root)),
    )
    state.pop("quality_fingerprint", None)
    save(root, state)


def local_date(now: datetime, timezone: str) -> str:
    """Use IANA rules, including daylight saving changes, for date guards."""
    if now.tzinfo is None:
        raise ValueError("A timezone-aware timestamp is required")
    return now.astimezone(ZoneInfo(timezone)).date().isoformat()


def development_dates(root: Path, timezone: str) -> set[str]:
    """Git timestamps are authoritative even if a crash lost private state."""
    if not git(root, "rev-parse", "--verify", "HEAD", allow_failure=True):
        return set()
    dates = set()
    for record in git(root, "log", "--format=%cI%x00%B%x1e").split("\x1e"):
        if "Roadmap-Day: D" in record:
            timestamp, _ = record.strip().split("\0", 1)
            dates.add(local_date(datetime.fromisoformat(timestamp), timezone))
    return dates


def first_unfinished(roadmap: str) -> str | None:
    """Choose the first incomplete stable ID, never a calendar-day offset."""
    items = re.findall(r"^- \[([ x])\] (D\d{2})\b", roadmap, re.MULTILINE)
    if [item for _, item in items] != [f"D{i:02}" for i in range(1, 31)]:
        raise ValueError("Roadmap must contain D01 through D30 exactly once in order")
    return next((item for checked, item in items if checked == " "), None)


def destination(root: Path, state: dict) -> None:
    """Verify the stable checkout, branch, and existing origin without editing."""
    if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root.resolve():
        raise ValueError("Wrong Git root")
    if git(root, "branch", "--show-current") != "main":
        raise ValueError("Expected main branch")
    actual = git(root, "remote", "get-url", "origin", allow_failure=True)
    if actual != (state.get("origin") or ""):
        raise ValueError("Origin changed")


def decision(root: Path, state: dict, now: datetime) -> str:
    """Read-only local readiness. A cached remote observation is not a fetch."""
    if state["status"] == "COMPLETE":
        return "COMPLETE_NOOP"
    destination(root, state)
    if state.get("pending_publication_sha"):
        if git(root, "rev-parse", "HEAD") != state["pending_publication_sha"]:
            raise ValueError("Pending commit differs from HEAD")
        verify_owned(root, state)
        today = local_date(now, state["timezone"])
        if state.get("last_delivery_date") == today or (
            today in development_dates(root, state["timezone"])
            and state.get("last_development_commit_date") != today
        ):
            return "DATE_SLOT_USED"
        return "RETRY_PUBLICATION"
    if state["status"] == "READY_TO_PUBLISH" and git(
        root, "rev-parse", "--verify", "HEAD", allow_failure=True
    ) != state.get("pre_commit_head", ""):
        return "RECONCILE_LOCAL_COMMIT"
    verify_owned(root, state)
    if state.get("ci_status") == "pending":
        return "VERIFY_CI_BEFORE_WORK"
    if state["status"] == "WAITING_FOR_ANALYSIS":
        return (
            "REVIEW_REGISTERED_ANSWER"
            if state.get("answer")
            else "WAITING_FOR_ANALYSIS"
        )
    today = local_date(now, state["timezone"])
    if today < state["first_eligible_run_date"]:
        return "BEFORE_FIRST_RUN"
    if today in development_dates(root, state["timezone"]) or today in {
        state.get("last_development_commit_date"),
        state.get("last_delivery_date"),
    }:
        return "DATE_SLOT_USED"
    if state.get("ci_status") in {
        "failure",
        "cancelled",
        "timed_out",
        "action_required",
    }:
        return "REPAIR_FAILED_CI"
    if state["status"] == "BLOCKED_OPERATIONAL":
        return "BLOCKED_OPERATIONAL"
    return (
        state.get("active_increment")
        or first_unfinished((root / "ROADMAP.md").read_text("utf-8"))
        or "VERIFY_COMPLETION"
    )


def begin_request(
    root: Path, state: dict, run_id: str, request_id: str, round_id: str, prompt: str
) -> None:
    """Persist one human-reviewed, self-contained research request and pause."""
    require_lock(root, run_id)
    if not re.fullmatch(r"D\d{2}-A\d{2}", request_id) or not re.fullmatch(
        r"R\d{2}", round_id
    ):
        raise ValueError("Invalid research identifier")
    previous = state.get("research")
    if previous and previous["id"] == request_id:
        if int(round_id[1:]) != int(previous["round"][1:]) + 1:
            raise ValueError("Research rounds must increase by one")
    elif round_id != "R01":
        raise ValueError("New research requests begin at R01")
    checkpoint(root, state, run_id, "IN_PROGRESS")
    if state["input_fingerprint"] not in prompt:
        raise ValueError("Request must include the current input fingerprint")
    name = f"{request_id}-{round_id}"
    path = private_directory(root) / "research" / "requests" / f"{name}_prompt.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(prompt)
    state["research"] = {
        "id": request_id,
        "round": round_id,
        "fingerprint": state["input_fingerprint"],
        "base_commit": git(root, "rev-parse", "--verify", "HEAD", allow_failure=True),
        "expected_answer": f"{name}_solution.txt",
        "request_sha256": digest(prompt.encode()),
    }
    state.update(status="WAITING_FOR_ANALYSIS", answer=None, analysis_resolved=False)
    save(root, state)


def register_answer(root: Path, state: dict, run_id: str, source: Path) -> None:
    """Register bytes as untrusted evidence, never execute returned content."""
    require_lock(root, run_id)
    verify_owned(root, state)
    request = state.get("research")
    if state["status"] != "WAITING_FOR_ANALYSIS" or not request:
        raise ValueError("There is no pending research request")
    if source.name != request["expected_answer"]:
        raise ValueError("Wrong answer filename")
    content = source.read_bytes()
    text = content.decode("utf-8-sig")
    expected = {
        "Request-ID": request["id"],
        "Round": request["round"],
        "Input-Fingerprint": request["fingerprint"],
    }
    if any(
        re.findall(rf"^{key}:\s*([^\r\n]+)\r?$", text, re.MULTILINE) != [value]
        for key, value in expected.items()
    ):
        raise ValueError("Answer identifiers or fingerprint do not match")
    if fingerprint(public_manifest(root)) != request["fingerprint"]:
        raise ValueError("Research inputs are stale")
    target = private_directory(root) / "research" / "inbox" / source.name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_bytes() != content:
        raise ValueError("A different answer already exists for this round")
    if not target.exists():
        target.write_bytes(content)
    state["answer"] = {"sha256": digest(content), "path": str(target.relative_to(root))}
    state.setdefault("received_answer_hashes", []).append(digest(content))
    save(root, state)


def resolve_analysis(root: Path, state: dict, run_id: str, note: str) -> None:
    """Record the agent's independent review; registration alone is insufficient."""
    require_lock(root, run_id)
    if state.get("research"):
        answer = state.get("answer")
        if (
            not answer
            or digest((root / answer["path"]).read_bytes()) != answer["sha256"]
        ):
            raise ValueError(
                "A matching unchanged answer must be independently reviewed"
            )
        if fingerprint(public_manifest(root)) != state["research"]["fingerprint"]:
            raise ValueError(
                "Resolve stale research inputs explicitly before acceptance"
            )
    if not note.strip():
        raise ValueError("Record a checkable analytical decision")
    if state.get("research"):
        state.setdefault("reviewed_research", []).append(
            {"request": state["research"], "answer": state["answer"], "decision": note}
        )
        state.update(research=None, answer=None)
    state.update(status="IN_PROGRESS", analysis_review=note, analysis_resolved=True)
    save(root, state)


def publication_ready(
    root: Path,
    state: dict,
    run_id: str,
    checks_passed: bool,
    privacy_passed: bool,
    now: datetime,
) -> None:
    """Bind successful gates to exact bytes; this never runs or claims a check."""
    require_lock(root, run_id)
    if not checks_passed or not privacy_passed or not state.get("analysis_resolved"):
        raise ValueError("Analysis, quality, and privacy gates must all pass")
    if state.get("pending_publication_sha"):
        raise ValueError("Pending publication occupies this development slot")
    if state.get("ci_status") == "pending":
        raise ValueError("Verify the pending CI run before publication")
    if state.get("ci_status") in {
        "failure",
        "cancelled",
        "timed_out",
        "action_required",
    }:
        if not state.get("repairing_ci_sha") or state["repairing_ci_sha"] != state.get(
            "last_verified_remote_sha"
        ):
            raise ValueError("Failed CI requires a repair of the affected commit")
    if state.get("research") or state["status"] == "WAITING_FOR_ANALYSIS":
        raise ValueError("Unresolved research blocks publication")
    if state["status"] not in {"IN_PROGRESS", "READY_TO_PUBLISH"}:
        raise ValueError("Resolve the operational status before publication")
    destination(root, state)
    verify_owned(root, state)
    today = local_date(now, state["timezone"])
    if today < state["first_eligible_run_date"]:
        raise ValueError("The first eligible development date has not arrived")
    if (
        today in development_dates(root, state["timezone"])
        or state.get("last_delivery_date") == today
    ):
        raise ValueError("Daily development/delivery slot is already used")
    state.update(
        status="READY_TO_PUBLISH",
        quality_fingerprint=fingerprint(public_manifest(root)),
        prepared_date=today,
        pre_commit_head=git(root, "rev-parse", "--verify", "HEAD", allow_failure=True),
    )
    save(root, state)


def record_commit(root: Path, state: dict, run_id: str, now: datetime) -> None:
    """Reconcile a single new commit, including a crash after git commit."""
    require_lock(root, run_id)
    if state["status"] != "READY_TO_PUBLISH":
        raise ValueError("Commit was not prepared")
    if state["quality_fingerprint"] != fingerprint(
        public_manifest(root)
    ) or dirty_manifest(root):
        raise ValueError("Committed snapshot differs from checked source")
    head = git(root, "rev-parse", "HEAD")
    parents = git(root, "rev-list", "--parents", "-n", "1", "HEAD").split()[1:]
    if parents != ([state["pre_commit_head"]] if state["pre_commit_head"] else []):
        raise ValueError("Expected exactly one development commit")
    today = local_date(now, state["timezone"])
    body = git(root, "log", "-1", "--format=%B")
    timestamp = datetime.fromisoformat(git(root, "log", "-1", "--format=%cI"))
    commit_date = local_date(timestamp, state["timezone"])
    if commit_date != state["prepared_date"] or commit_date > today:
        raise ValueError("Commit timestamp does not match its prepared run date")
    if f"Run-Date: {commit_date}" not in body:
        raise ValueError("Commit date changed; review before publication")
    if f"Roadmap-Day: {state['active_increment']}" not in body:
        raise ValueError("Commit roadmap trailer is missing")
    state.update(
        status="COMMITTED_NOT_PUSHED",
        pending_publication_sha=head,
        last_development_commit_date=commit_date,
        owned_files={},
    )
    save(root, state)


def reconcile_remote(
    root: Path,
    state: dict,
    run_id: str,
    remote_sha: str,
    repository_id: int,
    now: datetime,
) -> str:
    """Use an agent's fresh verified remote observation to reconcile delivery.

    Call after querying the public repository ID and origin/main, including
    after an ambiguous push. Never use a cached tracking ref as that evidence.
    """
    require_lock(root, run_id)
    destination(root, state)
    if repository_id != state["repository_id"]:
        raise ValueError("Repository identity changed")
    pending = state.get("pending_publication_sha")
    if pending and remote_sha == pending:
        if git(root, "rev-parse", "HEAD") != pending:
            raise ValueError("HEAD differs from delivered commit")
        state.update(
            status="READY",
            pending_publication_sha=None,
            last_verified_remote_sha=remote_sha,
            last_delivery_date=local_date(now, state["timezone"]),
            active_increment=None,
            ci_status="pending",
            owned_files={},
        )
        save(root, state)
        return "DELIVERY_VERIFIED"
    if remote_sha != (state.get("last_verified_remote_sha") or ""):
        raise ValueError("Remote diverged; preserve work and stop")
    return "RETRY_SAME_COMMIT" if pending else "REMOTE_UNCHANGED"


def main() -> int:
    """Expose read-only status and explicit lock/checkpoint/inbox commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "status",
            "dry-run",
            "acquire",
            "release",
            "checkpoint",
            "register-answer",
        ],
    )
    parser.add_argument("--run-id")
    parser.add_argument("--answer", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        if args.command in {"status", "dry-run"}:
            state = load(root)
            print(
                json.dumps(
                    {
                        "status": state["status"],
                        "decision": decision(root, state, datetime.now(UTC)),
                        "active_increment": state.get("active_increment"),
                        "research": state.get("research"),
                        "locked": (root / PRIVATE / "run.lock").exists(),
                    }
                )
            )
        else:
            if not args.run_id:
                raise ValueError("Mutations require --run-id")
            if args.command == "acquire":
                acquire(root, args.run_id)
            elif args.command == "release":
                release(root, args.run_id)
            elif args.command == "checkpoint":
                checkpoint(root, load(root), args.run_id, "IN_PROGRESS")
            else:
                if not args.answer:
                    raise ValueError("Supply --answer")
                register_answer(root, load(root), args.run_id, args.answer)
    except (ValueError, OSError, KeyError) as exc:
        # OSError text can contain absolute paths; keep diagnostics redacted.
        print(
            json.dumps(
                {"status": "BLOCKED_OPERATIONAL", "error_type": type(exc).__name__}
            )
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
