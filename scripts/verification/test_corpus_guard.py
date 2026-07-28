"""Deterministic test-corpus inventory and retirement/replacement guardrails."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


RETIREMENT_SCHEMA = "uaa.test_corpus_retirements.v1"
RETIREMENT_LEDGER = Path("docs/verification/test_corpus_retirements.json")
BASE_SHA_ENV = "UAA_VERIFICATION_BASE_SHA"
SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
ASSERTION_EQUIVALENCE_REF_PATTERN = re.compile(
    r"assertion-equivalence-ref:sha256:[0-9a-f]{64}"
)
TEST_CORPUS_EVIDENCE_REF_PATTERN = re.compile(
    r"test-corpus-evidence-ref:sha256:[0-9a-f]{64}"
)
MAX_TEST_FILE_BYTES = 5_000_000
MAX_RETIREMENT_LEDGER_BYTES = 1_000_000
FRONTEND_TEST_PATTERN = re.compile(
    r"(?<![.\w$])(?:it|test)(?:\.(?:concurrent|fails|only|skip|todo))*\s*\("
)
FRONTEND_EACH_PATTERN = re.compile(
    r"(?<![.\w$])(?:it|test)(?:\.(?:concurrent|fails|only|skip|todo))*\.each\b"
)
TEST_FILE_PATTERNS = (
    "tests/**/test_*.py",
    "tests/**/*_test.py",
    "apps/control-center/src/**/*.test.ts",
    "apps/control-center/src/**/*.test.tsx",
    "apps/control-center/tests/**/*.ts",
    "apps/control-center/tests/**/*.tsx",
)


class TestCorpusGuardError(RuntimeError):
    """Raised when corpus inventory or retirement evidence is invalid."""


@dataclass(frozen=True)
class TestDeclaration:
    ref: str
    kind: str


def _normalized_frontend_title(value: str) -> str:
    return " ".join(value.split())


def _skip_javascript_string(text: str, start: int) -> int:
    quote = text[start]
    index = start + 1
    while index < len(text):
        character = text[index]
        if character == "\\":
            index += 2
            continue
        if character == quote:
            return index + 1
        index += 1
    raise TestCorpusGuardError("frontend test inventory has an unterminated string")


def _skip_javascript_comment(text: str, start: int) -> int:
    if text.startswith("//", start):
        newline = text.find("\n", start + 2)
        return len(text) if newline < 0 else newline + 1
    if text.startswith("/*", start):
        end = text.find("*/", start + 2)
        if end < 0:
            raise TestCorpusGuardError(
                "frontend test inventory has an unterminated comment"
            )
        return end + 2
    return start


def _javascript_code_mask(text: str) -> bytearray:
    mask = bytearray(b"\x01" * len(text))
    index = 0
    while index < len(text):
        if text[index] in "\"'`":
            end = _skip_javascript_string(text, index)
            mask[index:end] = b"\x00" * (end - index)
            index = end
            continue
        comment_end = _skip_javascript_comment(text, index)
        if comment_end != index:
            mask[index:comment_end] = b"\x00" * (comment_end - index)
            index = comment_end
            continue
        index += 1
    return mask


def _skip_balanced_javascript(text: str, start: int) -> int:
    pairs = {"(": ")", "[": "]", "{": "}"}
    opening = text[start]
    if opening not in pairs:
        raise TestCorpusGuardError("frontend parameterized test data is invalid")
    stack = [pairs[opening]]
    index = start + 1
    while index < len(text):
        character = text[index]
        if character in "\"'`":
            index = _skip_javascript_string(text, index)
            continue
        comment_end = _skip_javascript_comment(text, index)
        if comment_end != index:
            index = comment_end
            continue
        if character in pairs:
            stack.append(pairs[character])
        elif character == stack[-1]:
            stack.pop()
            if not stack:
                return index + 1
        index += 1
    raise TestCorpusGuardError(
        "frontend parameterized test data has unbalanced delimiters"
    )


def _parameterized_frontend_titles(
    text: str,
    code_mask: bytearray,
) -> tuple[str, ...]:
    titles: list[str] = []
    for match in FRONTEND_EACH_PATTERN.finditer(text):
        if not code_mask[match.start()]:
            continue
        index = match.end()
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text):
            raise TestCorpusGuardError("frontend parameterized test data is missing")
        if text[index] == "(":
            index = _skip_balanced_javascript(text, index)
        elif text[index] == "`":
            index = _skip_javascript_string(text, index)
        else:
            raise TestCorpusGuardError("frontend parameterized test data is invalid")
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text) or text[index] != "(":
            raise TestCorpusGuardError("frontend parameterized test title is missing")
        index += 1
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text) or text[index] not in "\"'`":
            raise TestCorpusGuardError("frontend parameterized test title is invalid")
        title_start = index + 1
        title_end = _skip_javascript_string(text, index) - 1
        titles.append(text[title_start:title_end])
    return tuple(titles)


def _deduplicate_refs(refs: Iterable[tuple[str, str]]) -> tuple[TestDeclaration, ...]:
    counts: dict[str, int] = {}
    declarations: list[TestDeclaration] = []
    for raw_ref, kind in refs:
        occurrence = counts.get(raw_ref, 0) + 1
        counts[raw_ref] = occurrence
        ref = raw_ref if occurrence == 1 else f"{raw_ref}#{occurrence}"
        declarations.append(TestDeclaration(ref=ref, kind=kind))
    return tuple(declarations)


def parse_python_declarations(path: str, text: str) -> tuple[TestDeclaration, ...]:
    try:
        tree = ast.parse(text, filename=path)
    except SyntaxError as exc:
        raise TestCorpusGuardError(
            f"cannot parse Python test inventory: {path}"
        ) from exc

    refs: list[tuple[str, str]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                refs.append((f"{path}::{node.name}", "python_test"))
            continue
        if not isinstance(node, ast.ClassDef):
            continue
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                child.name.startswith("test_")
            ):
                refs.append((f"{path}::{node.name}::{child.name}", "python_test"))
    return _deduplicate_refs(refs)


def parse_frontend_declarations(path: str, text: str) -> tuple[TestDeclaration, ...]:
    refs: list[tuple[str, str]] = []
    code_mask = _javascript_code_mask(text)
    for match in FRONTEND_TEST_PATTERN.finditer(text):
        if not code_mask[match.start()]:
            continue
        index = match.end()
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text) or text[index] not in "\"'`":
            if ".skip" in match.group(0):
                # Playwright permits test.skip(condition, reason) as a
                # runtime annotation inside an already-declared test.
                continue
            raise TestCorpusGuardError(f"frontend test title is invalid: {path}")
        title_start = index + 1
        title_end = _skip_javascript_string(text, index) - 1
        title = _normalized_frontend_title(text[title_start:title_end])
        if not title or len(title) > 500:
            raise TestCorpusGuardError(f"frontend test title is invalid: {path}")
        refs.append((f"{path}::{title}", "frontend_test"))
    for raw_title in _parameterized_frontend_titles(text, code_mask):
        title = _normalized_frontend_title(raw_title)
        if not title or len(title) > 500:
            raise TestCorpusGuardError(f"frontend test title is invalid: {path}")
        refs.append((f"{path}::{title}", "frontend_test"))
    return _deduplicate_refs(refs)


def parse_test_declarations(path: str, text: str) -> tuple[TestDeclaration, ...]:
    if path.endswith(".py"):
        return parse_python_declarations(path, text)
    return parse_frontend_declarations(path, text)


def discover_test_files(repo: Path) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                path.relative_to(repo).as_posix()
                for pattern in TEST_FILE_PATTERNS
                for path in repo.glob(pattern)
                if path.is_file()
            }
        )
    )


def _read_bounded_regular_text(
    path: Path,
    *,
    max_bytes: int,
    unsafe_message: str,
    invalid_message: str,
) -> str:
    descriptor: int | None = None
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
    except FileNotFoundError as exc:
        raise TestCorpusGuardError(invalid_message) from exc
    except OSError as exc:
        raise TestCorpusGuardError(unsafe_message) from exc

    try:
        opened = os.fstat(descriptor)
        linked = os.lstat(path)
        identity = (opened.st_dev, opened.st_ino)
        if (
            not stat.S_ISREG(opened.st_mode)
            or not stat.S_ISREG(linked.st_mode)
            or opened.st_nlink != 1
            or linked.st_nlink != 1
            or identity != (linked.st_dev, linked.st_ino)
            or opened.st_size > max_bytes
        ):
            raise TestCorpusGuardError(unsafe_message)

        content = bytearray()
        while len(content) <= max_bytes:
            chunk = os.read(
                descriptor,
                min(64 * 1024, max_bytes + 1 - len(content)),
            )
            if not chunk:
                break
            content.extend(chunk)
        if len(content) > max_bytes:
            raise TestCorpusGuardError(unsafe_message)

        closed_over = os.fstat(descriptor)
        still_linked = os.lstat(path)
        if (
            not stat.S_ISREG(closed_over.st_mode)
            or not stat.S_ISREG(still_linked.st_mode)
            or closed_over.st_nlink != 1
            or still_linked.st_nlink != 1
            or (closed_over.st_dev, closed_over.st_ino) != identity
            or (still_linked.st_dev, still_linked.st_ino) != identity
            or (
                closed_over.st_size,
                closed_over.st_mtime_ns,
                closed_over.st_ctime_ns,
            )
            != (opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns)
        ):
            raise TestCorpusGuardError(unsafe_message)
        try:
            return bytes(content).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise TestCorpusGuardError(invalid_message) from exc
    except TestCorpusGuardError:
        raise
    except OSError as exc:
        raise TestCorpusGuardError(unsafe_message) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _read_worktree_text(repo: Path, path: str) -> str:
    candidate = repo / path
    return _read_bounded_regular_text(
        candidate,
        max_bytes=MAX_TEST_FILE_BYTES,
        unsafe_message=f"test inventory file is unsafe: {path}",
        invalid_message=f"cannot read test inventory: {path}",
    )


def inventory_worktree(repo: Path) -> tuple[TestDeclaration, ...]:
    declarations: list[TestDeclaration] = []
    for path in discover_test_files(repo):
        text = _read_worktree_text(repo, path)
        declarations.extend(parse_test_declarations(path, text))
    refs = [item.ref for item in declarations]
    if len(refs) != len(set(refs)):
        raise TestCorpusGuardError("test inventory contains duplicate stable refs")
    if not declarations:
        raise TestCorpusGuardError("test inventory is empty")
    return tuple(sorted(declarations, key=lambda item: item.ref))


def _run_git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
    )


def _resolve_base_sha(repo: Path, requested: str | None) -> str | None:
    if requested is not None:
        if SHA_PATTERN.fullmatch(requested) is None:
            raise TestCorpusGuardError("test-corpus comparison base SHA is malformed")
        probe = _run_git(repo, ["cat-file", "-e", f"{requested}^{{commit}}"])
        if probe.returncode != 0:
            raise TestCorpusGuardError("test-corpus comparison base commit is missing")
        return requested

    ci_ref = _run_git(repo, ["rev-parse", "--verify", "refs/uaa-ci/base-main"])
    if ci_ref.returncode == 0:
        try:
            value = ci_ref.stdout.decode("ascii").strip()
        except UnicodeDecodeError as exc:
            raise TestCorpusGuardError(
                "canonical CI comparison base is malformed"
            ) from exc
        if SHA_PATTERN.fullmatch(value) is None:
            raise TestCorpusGuardError("canonical CI comparison base is malformed")
        probe = _run_git(repo, ["cat-file", "-e", f"{value}^{{commit}}"])
        if probe.returncode != 0:
            raise TestCorpusGuardError("canonical CI comparison base commit is missing")
        return value

    if os.environ.get("CI", "").lower() == "true":
        raise TestCorpusGuardError("canonical CI comparison base is missing")

    merge_base = _run_git(repo, ["merge-base", "HEAD", "origin/main"])
    if merge_base.returncode == 0:
        try:
            value = merge_base.stdout.decode("ascii").strip()
        except UnicodeDecodeError as exc:
            raise TestCorpusGuardError("local comparison base is malformed") from exc
        if SHA_PATTERN.fullmatch(value):
            return value
    return None


def _changed_test_paths(repo: Path, base_sha: str) -> tuple[str, ...]:
    result = _run_git(
        repo,
        [
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            f"{base_sha}...HEAD",
            "--",
            "tests",
            "apps",
        ],
    )
    if result.returncode != 0:
        raise TestCorpusGuardError("cannot derive changed test corpus")
    try:
        paths = result.stdout.decode("utf-8").split("\0")
    except UnicodeDecodeError as exc:
        raise TestCorpusGuardError("changed test corpus paths are malformed") from exc
    changed = tuple(sorted(path for path in paths if path and _is_test_path(path)))
    for path in changed:
        _validate_test_path(path)
    return changed


def _is_test_path(path: str) -> bool:
    candidate = Path(path)
    if path.startswith("tests/"):
        return candidate.suffix == ".py" and (
            candidate.name.startswith("test_") or candidate.name.endswith("_test.py")
        )
    if not path.startswith("apps/control-center/"):
        return False
    return (
        candidate.name.endswith(".test.ts")
        or candidate.name.endswith(".test.tsx")
        or (
            path.startswith("apps/control-center/tests/")
            and candidate.suffix in {".ts", ".tsx"}
        )
    )


def _validate_test_path(path: str) -> None:
    parts = Path(path).parts
    if (
        path.startswith("/")
        or "\\" in path
        or ":" in path
        or any(part in {"", ".", ".."} for part in parts)
        or any(ord(character) < 32 for character in path)
    ):
        raise TestCorpusGuardError("changed test path is unsafe")


def _base_text(repo: Path, base_sha: str, path: str) -> str | None:
    size = _run_git(repo, ["cat-file", "-s", f"{base_sha}:{path}"])
    if size.returncode != 0:
        return None
    try:
        byte_count = int(size.stdout.decode("ascii").strip())
    except (UnicodeDecodeError, ValueError) as exc:
        raise TestCorpusGuardError(f"base test size is invalid: {path}") from exc
    if byte_count > MAX_TEST_FILE_BYTES:
        raise TestCorpusGuardError(f"base test file exceeds byte budget: {path}")
    result = _run_git(repo, ["show", f"{base_sha}:{path}"])
    if result.returncode != 0:
        return None
    try:
        return result.stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TestCorpusGuardError(f"base test file is not UTF-8: {path}") from exc


def removed_declarations(repo: Path, base_sha: str) -> tuple[str, ...]:
    removed: set[str] = set()
    for path in _changed_test_paths(repo, base_sha):
        prior = _base_text(repo, base_sha, path)
        if prior is None:
            continue
        prior_refs = {item.ref for item in parse_test_declarations(path, prior)}
        current_path = repo / path
        if current_path.is_file():
            current_text = _read_worktree_text(repo, path)
            current_refs = {
                item.ref for item in parse_test_declarations(path, current_text)
            }
        else:
            current_refs = set()
        removed.update(prior_refs - current_refs)
    return tuple(sorted(removed))


def _load_ledger(repo: Path) -> dict[str, Any]:
    path = repo / RETIREMENT_LEDGER
    try:
        value = json.loads(
            _read_bounded_regular_text(
                path,
                max_bytes=MAX_RETIREMENT_LEDGER_BYTES,
                unsafe_message="test-corpus retirement ledger is unsafe",
                invalid_message="test-corpus retirement ledger is invalid",
            )
        )
    except TestCorpusGuardError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TestCorpusGuardError("test-corpus retirement ledger is invalid") from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "retirements"}
        or value.get("schema_version") != RETIREMENT_SCHEMA
    ):
        raise TestCorpusGuardError("test-corpus retirement ledger schema is invalid")
    return value


def validate_retirements(
    current_refs: set[str],
    removed_refs: set[str],
    ledger: dict[str, Any],
) -> int:
    records = ledger.get("retirements")
    if not isinstance(records, list):
        raise TestCorpusGuardError("test-corpus retirements must be a list")
    by_retired_ref: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise TestCorpusGuardError(
                "test-corpus retirement record must be an object"
            )
        if set(record) != {
            "retired_ref",
            "replacement_refs",
            "reason",
            "assertion_equivalence_ref",
            "evidence_ref",
        }:
            raise TestCorpusGuardError(
                "test-corpus retirement record fields are invalid"
            )
        retired_ref = record.get("retired_ref")
        replacements = record.get("replacement_refs")
        reason = record.get("reason")
        equivalence_ref = record.get("assertion_equivalence_ref")
        evidence_ref = record.get("evidence_ref")
        if (
            not isinstance(retired_ref, str)
            or "::" not in retired_ref
            or not retired_ref.split("::", 1)[1]
            or len(retired_ref) > 2_000
            or any(ord(character) < 32 for character in retired_ref)
        ):
            raise TestCorpusGuardError("retired test ref is invalid")
        retired_path = retired_ref.split("::", 1)[0]
        _validate_test_path(retired_path)
        if not _is_test_path(retired_path):
            raise TestCorpusGuardError("retired test ref is invalid")
        if retired_ref in by_retired_ref:
            raise TestCorpusGuardError(f"duplicate retired test ref: {retired_ref}")
        if retired_ref in current_refs:
            raise TestCorpusGuardError(f"retired test is still active: {retired_ref}")
        if (
            not isinstance(replacements, list)
            or not replacements
            or any(not isinstance(item, str) for item in replacements)
            or len(replacements) != len(set(replacements))
        ):
            raise TestCorpusGuardError(
                f"replacement refs are invalid for retired test: {retired_ref}"
            )
        missing = sorted(set(replacements) - current_refs)
        if missing:
            raise TestCorpusGuardError(
                f"retired test has missing replacements: {retired_ref}: {missing}"
            )
        if (
            not isinstance(reason, str)
            or not 20 <= len(reason.strip()) <= 500
            or any(ord(character) < 32 for character in reason)
        ):
            raise TestCorpusGuardError(
                f"retired test reason is too weak: {retired_ref}"
            )
        if (
            not isinstance(equivalence_ref, str)
            or ASSERTION_EQUIVALENCE_REF_PATTERN.fullmatch(equivalence_ref) is None
        ):
            raise TestCorpusGuardError(
                f"retired test equivalence ref is invalid: {retired_ref}"
            )
        if (
            not isinstance(evidence_ref, str)
            or TEST_CORPUS_EVIDENCE_REF_PATTERN.fullmatch(evidence_ref) is None
        ):
            raise TestCorpusGuardError(
                f"retired test evidence ref is invalid: {retired_ref}"
            )
        by_retired_ref[retired_ref] = record

    unaccounted = sorted(removed_refs - set(by_retired_ref))
    if unaccounted:
        raise TestCorpusGuardError(
            f"removed tests lack retirement/replacement evidence: {unaccounted}"
        )
    return len(records)


def inventory_fingerprint(declarations: tuple[TestDeclaration, ...]) -> str:
    payload = [
        {"ref": declaration.ref, "kind": declaration.kind}
        for declaration in declarations
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return f"test-corpus-inventory-ref:sha256:{hashlib.sha256(encoded).hexdigest()}"


def verify_test_corpus_guard(
    repo: Path,
    *,
    base_sha: str | None = None,
) -> dict[str, object]:
    declarations = inventory_worktree(repo)
    current_refs = {item.ref for item in declarations}
    resolved_base = _resolve_base_sha(
        repo,
        base_sha if base_sha is not None else os.environ.get(BASE_SHA_ENV),
    )
    removed = (
        set(removed_declarations(repo, resolved_base))
        if resolved_base is not None
        else set()
    )
    retirement_count = validate_retirements(
        current_refs,
        removed,
        _load_ledger(repo),
    )
    return {
        "test_declaration_count": len(declarations),
        "python_test_count": sum(item.kind == "python_test" for item in declarations),
        "frontend_test_count": sum(
            item.kind == "frontend_test" for item in declarations
        ),
        "inventory_ref": inventory_fingerprint(declarations),
        "comparison_base_status": (
            "bound" if resolved_base is not None else "unavailable_local_only"
        ),
        "removed_test_count": len(removed),
        "retirement_record_count": retirement_count,
    }
