"""Regression checks for guard boundaries found during the implementation review."""

from datetime import timedelta

import pytest

from scripts import daily_state as w


def test_waiting_cannot_reuse_earlier_analysis_verdict(workspace):
    root, state, run_id, now = workspace
    w.resolve_analysis(root, state, run_id, "Earlier review")
    identity = w.fingerprint(w.public_manifest(root))
    w.begin_request(root, state, run_id, "D01-A01", "R01", identity)
    assert not state["analysis_resolved"]
    with pytest.raises(ValueError, match="gates"):
        w.publication_ready(root, state, run_id, True, True, now)


def test_commit_guard_checks_first_eligibility(workspace):
    root, state, run_id, now = workspace
    w.resolve_analysis(root, state, run_id, "Reviewed")
    with pytest.raises(ValueError, match="eligible"):
        w.publication_ready(root, state, run_id, True, True, now - timedelta(days=1))


def test_unrelated_modification_and_deletion_are_detected(workspace):
    root, state, _, _ = workspace
    original = (root / "ROADMAP.md").read_bytes()
    (root / "ROADMAP.md").write_bytes(original + b"changed")
    with pytest.raises(ValueError, match="Unexplained"):
        w.verify_owned(root, state)
    (root / "ROADMAP.md").write_bytes(original)
    w.git(root, "add", "--", "ROADMAP.md")
    (root / "ROADMAP.md").unlink()
    assert w.dirty_manifest(root)["ROADMAP.md"] is None
    with pytest.raises(ValueError, match="Unexplained"):
        w.verify_owned(root, state)


def test_wrong_branch_blocks_readiness(workspace):
    root, state, _, now = workspace
    w.git(root, "symbolic-ref", "HEAD", "refs/heads/unrelated")
    with pytest.raises(ValueError, match="main"):
        w.decision(root, state, now)


def test_no_analysis_verdict_blocks_publication(workspace):
    root, state, run_id, now = workspace
    with pytest.raises(ValueError, match="gates"):
        w.publication_ready(root, state, run_id, True, True, now)


def test_status_rejects_bad_state(workspace):
    root, state, _, _ = workspace
    state["status"] = "UNKNOWN"
    w.save(root, state)
    with pytest.raises(ValueError, match="Unknown"):
        w.load(root)


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_research_metadata_accepts_portable_line_endings(workspace, newline):
    root, state, run_id, _ = workspace
    identity = w.fingerprint(w.public_manifest(root))
    w.begin_request(root, state, run_id, "D01-A01", "R01", identity)
    source = root / w.PRIVATE / "D01-A01-R01_solution.txt"
    source.write_bytes(
        newline.join(
            [
                "Request-ID: D01-A01",
                "Round: R01",
                f"Input-Fingerprint: {identity}",
                "Synthetic untrusted answer",
            ]
        ).encode()
    )
    w.register_answer(root, state, run_id, source)
    assert state["answer"]["sha256"] == w.digest(source.read_bytes())


def test_incidental_identifier_in_answer_is_not_matching_metadata(workspace):
    root, state, run_id, _ = workspace
    identity = w.fingerprint(w.public_manifest(root))
    w.begin_request(root, state, run_id, "D01-A01", "R01", identity)
    source = root / w.PRIVATE / "D01-A01-R01_solution.txt"
    source.write_text(
        f"Request-ID: D02-A01\nRound: R01\nInput-Fingerprint: {identity}\n"
        "This text incidentally mentions D01-A01.\n",
        "utf-8",
    )
    with pytest.raises(ValueError, match="identifiers"):
        w.register_answer(root, state, run_id, source)


@pytest.mark.parametrize("ci_status", ["pending", "failure"])
def test_ci_blocks_new_publication(workspace, ci_status):
    root, state, run_id, now = workspace
    w.resolve_analysis(root, state, run_id, "Reviewed")
    state["ci_status"] = ci_status
    with pytest.raises(ValueError, match="CI"):
        w.publication_ready(root, state, run_id, True, True, now)


def test_pending_commit_blocks_new_commit_on_later_date(workspace):
    root, state, run_id, now = workspace
    w.resolve_analysis(root, state, run_id, "Reviewed")
    state["pending_publication_sha"] = "a" * 40
    with pytest.raises(ValueError, match="Pending publication"):
        w.publication_ready(root, state, run_id, True, True, now + timedelta(days=1))
