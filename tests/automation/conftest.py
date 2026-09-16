"""All workflow Git tests use temporary local repositories and fake identities."""

from datetime import UTC, datetime

import pytest

from scripts import daily_state as workflow


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    for key in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(key, "example")
    for key in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(key, "123+example" + "@users.noreply.github.com")
    for key in ("GIT_AUTHOR_DATE", "GIT_COMMITTER_DATE"):
        monkeypatch.setenv(key, "2025-02-03T12:00:00+00:00")
    root = tmp_path / "project"
    root.mkdir()
    workflow.git(root, "init", "-b", "main")
    workflow.git(root, "config", "user.name", "example")
    workflow.git(
        root, "config", "user.email", "123+example" + "@users.noreply.github.com"
    )
    workflow.git(root, "config", "commit.gpgsign", "false")
    (root / ".gitignore").write_text(".thermalpath-private/\n", encoding="utf-8")
    (root / "ROADMAP.md").write_text(
        "\n".join(f"- [ ] D{i:02} | synthetic increment" for i in range(1, 31)),
        encoding="utf-8",
    )
    state = {
        "project_root": str(root.resolve()),
        "status": "IN_PROGRESS",
        "origin": None,
        "repository_id": 123,
        "timezone": "America/New_York",
        "first_eligible_run_date": "2025-02-03",
        "active_increment": "D01",
        "owned_files": {},
        "pending_publication_sha": None,
        "last_verified_remote_sha": None,
        "ci_status": None,
    }
    workflow.save(root, state)
    workflow.acquire(root, "test-run")
    workflow.checkpoint(root, state, "test-run", "IN_PROGRESS")
    return root, state, "test-run", datetime(2025, 2, 3, 12, tzinfo=UTC)
