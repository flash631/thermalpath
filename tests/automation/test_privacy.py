"""Synthetic leaks are constructed at runtime; real personal files are never read."""

import hashlib

import pytest

from scripts import daily_state as w
from scripts import privacy_check as p

NOREPLY = "123+example" + "@users.noreply.github.com"


@pytest.mark.parametrize(
    "text,category",
    [
        (chr(92).join(["C:", "Users", "sample", "file.txt"]), "absolute-path"),
        ("/".join(["", "home", "sample", "file"]), "absolute-path"),
        ("192." + "168.3.4", "private-network"),
        ("ghp_" + "a" * 36, "token"),
        ("sample" + "@private.example", "nonapproved-email"),
        ("GTX " + "9999", "device-details"),
        ("-----BEGIN " + "PRIVATE KEY-----", "private-key"),
    ],
)
def test_redacted_categories(text, category):
    result = p.scan_text(text, NOREPLY)
    assert category in result
    assert all(text not in value for value in result)


def test_harmless_installation_and_verified_identity():
    assert (
        p.scan_text(r".venv\Scripts\python.exe examples\series_stack.py", NOREPLY) == []
    )
    assert p.scan_text(NOREPLY, NOREPLY) == []
    p.verify_identity("example", NOREPLY, "example", NOREPLY)
    with pytest.raises(ValueError):
        p.verify_identity("wrong", NOREPLY, "example", NOREPLY)


def test_asset_review_is_hash_bound():
    content = bytes([255, 0, 128])
    assert "unreviewed-binary" in p.scan_file("figure.png", content, NOREPLY, {})
    reviews = {"figure.png": hashlib.sha256(content).hexdigest()}
    assert p.scan_file("figure.png", content, NOREPLY, reviews) == []
    assert p.scan_file("figure.png", content + b"x", NOREPLY, reviews)


def test_private_paths_forbidden():
    assert "forbidden-public-file" in p.scan_file(
        ".thermalpath-private/settings.json", b"{}", NOREPLY, {}
    )


def test_staged_bytes_are_scanned_even_when_worktree_is_cleaned(workspace):
    root, _, _, _ = workspace
    file = root / "candidate.txt"
    file.write_text("ghp_" + "a" * 36, "utf-8")
    w.git(root, "add", "--", "candidate.txt")
    file.write_text("harmless replacement", "utf-8")
    assert p.inspect(root, "example", NOREPLY) == []
    findings = p.inspect(root, "example", NOREPLY, staged=True)
    assert any("token" in item["categories"] for item in findings)
    assert "a" * 36 not in str(findings)


def test_all_outgoing_history_is_scanned_including_deleted_leak(workspace):
    root, _, _, _ = workspace
    file = root / "candidate.txt"
    file.write_text("ghp_" + "a" * 36, "utf-8")
    w.git(root, "add", "--", "candidate.txt")
    w.git(root, "commit", "-m", "test: synthetic leak")
    w.git(root, "rm", "--", "candidate.txt")
    w.git(root, "commit", "-m", "test: remove synthetic leak")
    findings = p.inspect(root, "example", NOREPLY, history=True)
    assert any("token" in item["categories"] for item in findings)


def test_effective_identity_cannot_leak_from_environment(workspace, monkeypatch):
    root, _, _, _ = workspace
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "sample" + "@private.example")
    with pytest.raises(ValueError, match="identity"):
        p.inspect(root, "example", NOREPLY)
