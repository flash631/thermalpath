"""Behavioral tests of state transitions, stale inputs, dates, and Git recovery."""

import json
import subprocess
import sys
from datetime import datetime, timedelta

import pytest

from scripts import daily_state as w


def prepare_and_commit(workspace):
    root, state, run_id, now = workspace
    w.resolve_analysis(root, state, run_id, "Exact rational reference checked")
    w.publication_ready(root, state, run_id, True, True, now)
    w.git(root, "add", "--", ".gitignore", "ROADMAP.md")
    w.git(
        root,
        "commit",
        "-m",
        "feat(core): synthetic fixture",
        "-m",
        "Roadmap-Day: D01\nRun-Date: 2025-02-03",
    )
    return root, state, run_id, now


def request(workspace, round_id="R01"):
    root, state, run_id, _ = workspace
    identity = w.fingerprint(w.public_manifest(root))
    w.begin_request(
        root,
        state,
        run_id,
        "D01-A01",
        round_id,
        f"Synthetic question D01-A01 {round_id}; fingerprint {identity}",
    )
    return state["research"]


def answer(workspace, request_record):
    root, _, _, _ = workspace
    source = root / w.PRIVATE / request_record["expected_answer"]
    source.write_text(
        "\n".join(
            [
                f"Request-ID: {request_record['id']}",
                f"Round: {request_record['round']}",
                f"Input-Fingerprint: {request_record['fingerprint']}",
                "untrusted proposal",
            ]
        ),
        "utf-8",
    )
    return source


def test_lock_persists_across_processes(workspace):
    root, _, run_id, _ = workspace
    with pytest.raises(ValueError, match="lock exists"):
        w.acquire(root, "second-run")
    code = (
        "import sys; from pathlib import Path; "
        "from scripts.daily_state import acquire; "
        "acquire(Path(sys.argv[1]), 'second-process')"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(root)], capture_output=True
    )
    assert result.returncode != 0
    with pytest.raises(ValueError, match="own"):
        w.release(root, "wrong-run")
    w.release(root, run_id)
    w.acquire(root, "second-run")


def test_atomic_json_and_root_guard(workspace):
    root, state, _, _ = workspace
    assert w.load(root) == state
    w.atomic_json(root / w.PRIVATE / "extra.json", {"a": 1})
    w.atomic_json(root / w.PRIVATE / "extra.json", {"b": 2})
    assert json.loads((root / w.PRIVATE / "extra.json").read_text()) == {"b": 2}
    assert not list((root / w.PRIVATE).glob("*.tmp"))
    state["project_root"] = str(root / "wrong")
    w.save(root, state)
    with pytest.raises(ValueError, match="mapping"):
        w.load(root)


def test_private_must_be_ignored(workspace):
    root, _, _, _ = workspace
    (root / ".gitignore").write_text("", "utf-8")
    with pytest.raises(ValueError, match="ignored"):
        w.private_directory(root)


def test_selection_first_incomplete_and_completion():
    roadmap = "\n".join(f"- [{'x' if i < 7 else ' '}] D{i:02}" for i in range(1, 31))
    assert w.first_unfinished(roadmap) == "D07"
    assert w.first_unfinished(roadmap.replace("[ ]", "[x]")) is None
    with pytest.raises(ValueError):
        w.first_unfinished("- [ ] D02")


@pytest.mark.parametrize(
    "timestamp,expected",
    [
        ("2025-03-09T04:59:00+00:00", "2025-03-08"),
        ("2025-03-09T07:01:00+00:00", "2025-03-09"),
        ("2025-11-02T05:30:00+00:00", "2025-11-02"),
        ("2025-11-02T06:30:00+00:00", "2025-11-02"),
    ],
)
def test_timezone_and_dst(timestamp, expected):
    assert (
        w.local_date(datetime.fromisoformat(timestamp), "America/New_York") == expected
    )


def test_naive_time_rejected():
    with pytest.raises(ValueError):
        w.local_date(datetime(2025, 1, 1), "UTC")


def test_wait_without_answer_is_read_only_and_owned_work_resumes(workspace):
    root, state, _, now = workspace
    request(workspace)
    before = {
        str(p.relative_to(root)): p.read_bytes()
        for p in (root / w.PRIVATE).rglob("*")
        if p.is_file()
    }
    assert w.decision(root, state, now) == "WAITING_FOR_ANALYSIS"
    assert w.decision(root, state, now + timedelta(days=1)) == "WAITING_FOR_ANALYSIS"
    after = {
        str(p.relative_to(root)): p.read_bytes()
        for p in (root / w.PRIVATE).rglob("*")
        if p.is_file()
    }
    assert before == after
    (root / "unrelated.txt").write_text("unrelated work", "utf-8")
    with pytest.raises(ValueError, match="Unexplained"):
        w.decision(root, state, now)


def test_matching_answer_requires_independent_review(workspace):
    root, state, run_id, now = workspace
    record = request(workspace)
    source = answer(workspace, record)
    w.register_answer(root, state, run_id, source)
    assert w.decision(root, state, now) == "REVIEW_REGISTERED_ANSWER"
    assert not state.get("analysis_resolved")
    w.resolve_analysis(
        root, state, run_id, "Independently checked dimensions and limits"
    )
    assert state["status"] == "IN_PROGRESS"
    assert state["research"] is None
    assert len(state["reviewed_research"]) == 1


@pytest.mark.parametrize(
    "error", ["filename", "fingerprint", "stale", "tampered-inbox"]
)
def test_wrong_or_stale_answer_rejected(workspace, error):
    root, state, run_id, _ = workspace
    record = request(workspace)
    source = answer(workspace, record)
    if error == "filename":
        source = source.rename(source.with_name("wrong_solution.txt"))
    elif error == "fingerprint":
        source.write_text("D01-A01 R01 wrong fingerprint", "utf-8")
    elif error == "stale":
        (root / "ROADMAP.md").write_text("changed input", "utf-8")
    else:
        w.register_answer(root, state, run_id, source)
        (root / state["answer"]["path"]).write_text("modified", "utf-8")
        with pytest.raises(ValueError, match="unchanged"):
            w.resolve_analysis(root, state, run_id, "Review")
        return
    with pytest.raises(ValueError):
        w.register_answer(root, state, run_id, source)


def test_repeated_review_rounds_preserve_original(workspace):
    root, state, run_id, _ = workspace
    record = request(workspace)
    w.register_answer(root, state, run_id, answer(workspace, record))
    first = (
        root / w.PRIVATE / "research" / "requests" / "D01-A01-R01_prompt.txt"
    ).read_bytes()
    with pytest.raises(ValueError, match="increase"):
        request(workspace)
    request(workspace, "R02")
    assert state["answer"] is None
    assert state["research"]["expected_answer"] == "D01-A01-R02_solution.txt"
    assert (
        root / w.PRIVATE / "research" / "requests" / "D01-A01-R01_prompt.txt"
    ).read_bytes() == first


@pytest.mark.parametrize(
    "checks,privacy", [(False, True), (True, False), (False, False)]
)
def test_failed_gates_block_commit(workspace, checks, privacy):
    root, state, run_id, now = workspace
    w.resolve_analysis(root, state, run_id, "Reviewed")
    with pytest.raises(ValueError, match="gates"):
        w.publication_ready(root, state, run_id, checks, privacy, now)
    assert state["status"] != "READY_TO_PUBLISH"


def test_crash_after_commit_and_duplicate_date(workspace):
    root, state, run_id, now = prepare_and_commit(workspace)
    assert w.decision(root, state, now) == "RECONCILE_LOCAL_COMMIT"
    w.record_commit(root, state, run_id, now)
    assert w.decision(root, state, now) == "RETRY_PUBLICATION"
    with pytest.raises(ValueError, match="slot"):
        w.publication_ready(root, state, run_id, True, True, now)
    assert w.development_dates(root, state["timezone"]) == {"2025-02-03"}


def test_crash_after_commit_can_be_reconciled_on_a_later_date(workspace):
    root, state, run_id, now = prepare_and_commit(workspace)
    tomorrow = now + timedelta(days=1)
    assert w.decision(root, state, tomorrow) == "RECONCILE_LOCAL_COMMIT"
    w.record_commit(root, state, run_id, tomorrow)
    assert state["last_development_commit_date"] == "2025-02-03"
    assert w.decision(root, state, tomorrow) == "RETRY_PUBLICATION"


def test_push_failure_retry_and_crash_after_push(workspace, tmp_path):
    root, state, run_id, now = prepare_and_commit(workspace)
    w.record_commit(root, state, run_id, now)
    sha = state["pending_publication_sha"]
    remote = tmp_path / "remote.git"
    remote.mkdir()
    w.git(remote, "init", "--bare")
    w.git(root, "remote", "add", "origin", str(remote))
    state["origin"] = str(remote)
    assert w.reconcile_remote(root, state, run_id, "", 123, now) == "RETRY_SAME_COMMIT"
    assert state["pending_publication_sha"] == sha
    # A real temporary remote failure never changes the pending commit.
    w.git(root, "remote", "set-url", "origin", str(tmp_path / "missing.git"))
    result = subprocess.run(
        ["git", "push", "origin", "main"], cwd=root, capture_output=True
    )
    assert result.returncode != 0
    w.git(root, "remote", "set-url", "origin", str(remote))
    w.git(root, "push", "origin", "main")
    observed = w.git(root, "ls-remote", "origin", "refs/heads/main").split()[0]
    # Simulated crash: state still says pending after the actual push.
    assert (
        w.reconcile_remote(root, state, run_id, observed, 123, now)
        == "DELIVERY_VERIFIED"
    )
    assert state["last_verified_remote_sha"] == sha
    state["ci_status"] = "success"
    assert w.decision(root, state, now) == "DATE_SLOT_USED"
    assert w.git(root, "rev-list", "--count", "HEAD") == "1"


def test_delayed_delivery_uses_todays_slot(workspace):
    root, state, run_id, now = prepare_and_commit(workspace)
    w.record_commit(root, state, run_id, now)
    tomorrow = now + timedelta(days=1)
    sha = state["pending_publication_sha"]
    w.reconcile_remote(root, state, run_id, sha, 123, tomorrow)
    state["ci_status"] = "success"
    assert w.decision(root, state, tomorrow) == "DATE_SLOT_USED"


def test_destination_divergence_and_repository_identity(workspace):
    root, state, run_id, now = prepare_and_commit(workspace)
    w.record_commit(root, state, run_id, now)
    with pytest.raises(ValueError, match="identity"):
        w.reconcile_remote(root, state, run_id, "", 999, now)
    with pytest.raises(ValueError, match="diverged"):
        w.reconcile_remote(root, state, run_id, "a" * 40, 123, now)
    w.git(root, "remote", "add", "origin", "unexpected")
    with pytest.raises(ValueError, match="Origin"):
        w.destination(root, state)


def test_first_run_failed_ci_and_complete_noop(workspace):
    root, state, _, now = workspace
    assert w.decision(root, state, now - timedelta(days=1)) == "BEFORE_FIRST_RUN"
    state["ci_status"] = "failure"
    assert w.decision(root, state, now) == "REPAIR_FAILED_CI"
    state["last_delivery_date"] = w.local_date(now, state["timezone"])
    assert w.decision(root, state, now) == "DATE_SLOT_USED"
    state["status"] = "COMPLETE"
    (root / "unexpected.txt").write_text("unrelated", "utf-8")
    assert w.decision(root, state, now) == "COMPLETE_NOOP"


def test_checked_snapshot_cannot_change_before_commit(workspace):
    root, state, run_id, now = prepare_and_commit(workspace)
    (root / "ROADMAP.md").write_text("unexpected edit", "utf-8")
    with pytest.raises(ValueError, match="snapshot"):
        w.record_commit(root, state, run_id, now)
