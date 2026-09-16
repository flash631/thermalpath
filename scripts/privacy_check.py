"""Heuristic public-content guard with redacted findings, not a privacy proof."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

PATTERNS = {
    "absolute-path": r"(?i)(?:\b[A-Z]:[\\/]|/(?:home|Users)/[^\s/]+|\\\\[\w.-]+\\)",
    "private-network": (
        r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|"
        r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b"
    ),
    "token": (
        r"\b(?:gh[pousr]_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{16,}|"
        r"sk-[A-Za-z0-9_-]{20,})\b"
    ),
    "private-key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "device-details": (
        r"(?i)\b(?:NVIDIA\s+GeForce|GTX\s+\d{3,4}|Intel\(R\)|"
        r"serial[ _-]?number\s*[:=]|hostname\s*[:=])"
    ),
    "credential-assignment": (
        r"(?i)(?:api[_-]?key|access[_-]?token|password)"
        r"\s*[:=]\s*[\"'][^\"']{8,}[\"']"
    ),
}
EMAIL = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
FORBIDDEN_PARTS = {
    ".thermalpath-private",
    ".venv",
    "uploads",
    ".git",
    ".vscode",
    ".idea",
}
FORBIDDEN_SUFFIXES = {".log", ".pem", ".key", ".p12", ".pfx"}
# Exact harmless documentation examples only. No blanket test-file exemption.
ALLOWED_EMAILS = {"person@example.com"}


def git_bytes(root: Path, *arguments: str) -> bytes:
    """Read Git bytes without echoing discovered content or command stderr."""
    result = subprocess.run(
        ["git", *arguments], cwd=root, capture_output=True, check=False
    )
    if result.returncode:
        raise ValueError("Cannot inspect requested Git evidence")
    return result.stdout


def scan_text(text: str, noreply: str) -> list[str]:
    """Return categories only; never return a matching value."""
    findings = [name for name, pattern in PATTERNS.items() if re.search(pattern, text)]
    if any(email not in ALLOWED_EMAILS | {noreply} for email in EMAIL.findall(text)):
        findings.append("nonapproved-email")
    return findings


def scan_file(
    name: str, content: bytes, noreply: str, reviewed_assets: dict
) -> list[str]:
    """Scan paths and contents; require hash-bound manual review for binaries."""
    path = Path(name)
    findings = scan_text(name, noreply)
    if (
        any(part in FORBIDDEN_PARTS or part.startswith(".env") for part in path.parts)
        or path.suffix.lower() in FORBIDDEN_SUFFIXES
    ):
        findings.append("forbidden-public-file")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = ""
        if reviewed_assets.get(name) != hashlib.sha256(content).hexdigest():
            findings.append("unreviewed-binary")
    if (
        "\0" in text
        and reviewed_assets.get(name) != hashlib.sha256(content).hexdigest()
    ):
        findings.append("unreviewed-binary")
    findings.extend(scan_text(text, noreply))
    return sorted(set(findings))


def verify_identity(name: str, email: str, handle: str, noreply: str) -> None:
    """Require the separately verified public account identity exactly."""
    if not re.fullmatch(
        r"(?:\d+\+)?" + re.escape(handle) + r"@users\.noreply\.github\.com", noreply
    ):
        raise ValueError("Expected a verified GitHub noreply identity")
    if name != handle or email != noreply:
        raise ValueError("Git identity differs from the approved public identity")


def inspect(
    root: Path,
    handle: str,
    noreply: str,
    *,
    staged: bool = False,
    history: bool = False,
    base: str | None = None,
    reviewed_assets: dict | None = None,
) -> list[dict]:
    """Check candidate files, staged blobs, metadata, and unpublished history.

    The caller verifies base against the destination immediately before push.
    Every outgoing tree is inspected, so a later deletion cannot hide a leak.
    """
    assets = reviewed_assets or {}
    findings = []

    def examine(label: str, content: bytes) -> None:
        categories = scan_file(label, content, noreply, assets)
        if categories:
            findings.append(
                {
                    "file_id": hashlib.sha256(label.encode()).hexdigest()[:12],
                    "categories": categories,
                }
            )

    for variable in ("GIT_AUTHOR_IDENT", "GIT_COMMITTER_IDENT"):
        identity = git_bytes(root, "var", variable).decode().strip()
        match = re.fullmatch(r"(.+) <([^>]+)> \d+ [+-]\d{4}", identity)
        if not match:
            raise ValueError("Cannot parse effective Git identity")
        verify_identity(match[1], match[2], handle, noreply)
    names = git_bytes(
        root, "ls-files", "-z", "--cached", "--others", "--exclude-standard"
    )
    for name in sorted(set(names.decode().split("\0")) - {""}):
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Linked or escaping candidate file")
        if path.is_file():
            examine(name, path.read_bytes())
    if staged:
        entries = git_bytes(root, "ls-files", "--stage", "-z").decode().split("\0")
        for entry in filter(None, entries):
            metadata, name = entry.split("\t", 1)
            mode, sha, stage = metadata.split()
            if mode not in {"100644", "100755"} or stage != "0":
                raise ValueError("Unreviewed index mode or conflict")
            examine(name, git_bytes(root, "cat-file", "blob", sha))
    if history:
        revision = f"{base}..HEAD" if base else "HEAD"
        for sha in (
            git_bytes(root, "rev-list", "--reverse", revision).decode().splitlines()
        ):
            metadata = git_bytes(
                root, "show", "-s", "--format=%an%x00%ae%x00%cn%x00%ce%x00%B", sha
            ).decode()
            author, author_email, committer, committer_email, message = metadata.split(
                "\0", 4
            )
            verify_identity(author, author_email, handle, noreply)
            verify_identity(committer, committer_email, handle, noreply)
            examine("commit-message", message.encode())
            for entry in filter(
                None, git_bytes(root, "ls-tree", "-rz", sha).decode().split("\0")
            ):
                metadata, name = entry.split("\t", 1)
                mode, kind, blob = metadata.split()
                if kind != "blob" or mode not in {"100644", "100755"}:
                    raise ValueError("Unreviewed outgoing tree mode")
                examine(name, git_bytes(root, "cat-file", "blob", blob))
    return findings


def main() -> int:
    """Print a redacted JSON result and fail closed on inspection errors."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-handle", required=True)
    parser.add_argument("--noreply", required=True)
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--base")
    parser.add_argument("--reviewed-assets", type=Path)
    args = parser.parse_args()
    try:
        findings = inspect(
            Path(__file__).resolve().parents[1],
            args.public_handle,
            args.noreply,
            staged=args.staged,
            history=args.history,
            base=args.base,
            reviewed_assets=json.loads(args.reviewed_assets.read_text("utf-8"))
            if args.reviewed_assets
            else {},
        )
        print(json.dumps({"passed": not findings, "findings": findings}))
        return int(bool(findings))
    except (ValueError, OSError) as exc:
        print(json.dumps({"passed": False, "error_type": type(exc).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
