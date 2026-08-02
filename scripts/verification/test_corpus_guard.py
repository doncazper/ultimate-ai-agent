"""Deterministic test-corpus inventory and retirement/replacement guardrails."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import select
import stat
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from scripts.verification.test_corpus_evidence import (
    ASSERTION_EVIDENCE_SCHEMA as ASSERTION_EVIDENCE_SCHEMA,
    ASSERTION_EQUIVALENCE_SCHEMA as ASSERTION_EQUIVALENCE_SCHEMA,
    RETIREMENT_EVIDENCE_SCHEMA as RETIREMENT_EVIDENCE_SCHEMA,
    TEST_RESULT_EVIDENCE_SCHEMA as TEST_RESULT_EVIDENCE_SCHEMA,
    TestCorpusEvidenceError,
    retirement_artifact_ref as retirement_artifact_ref,
)
from scripts.verification.test_corpus_evidence import (
    validate_retirements as _validate_retirement_evidence,
)
from scripts.verification.test_corpus_frontend import (
    FrontendInventoryError,
    parse_frontend_refs,
)
from scripts.verification.verification_github_transport import (
    VerificationGithubTransportError,
    decode_github_job_output,
)


RETIREMENT_SCHEMA = "uaa.test_corpus_retirements.v1"
RETIREMENT_LEDGER = Path("docs/verification/test_corpus_retirements.json")
BASE_SHA_ENV = "UAA_VERIFICATION_BASE_SHA"
SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
MAX_TEST_FILE_BYTES = 5_000_000
MAX_RETIREMENT_LEDGER_BYTES = 1_000_000
MAX_GIT_STDOUT_BYTES = 8_000_000
MAX_CHANGED_PATH_BYTES = 4_000_000
MAX_CHANGED_TEST_PATHS = 20_000
GIT_INSPECTION_TIMEOUT_SECONDS = 30.0
FRONTEND_TEST_EXTENSIONS = (
    "js",
    "jsx",
    "ts",
    "tsx",
    "cjs",
    "cjsx",
    "cts",
    "ctsx",
    "mjs",
    "mjsx",
    "mts",
    "mtsx",
)
TEST_FILE_PATTERNS = (
    "tests/**/test_*.py",
    "tests/**/*_test.py",
    *(
        f"apps/control-center/src/**/*.{kind}.{extension}"
        for kind in ("test", "spec")
        for extension in FRONTEND_TEST_EXTENSIONS
    ),
    *(
        f"apps/control-center/tests/**/*.{extension}"
        for extension in FRONTEND_TEST_EXTENSIONS
    ),
)


class TestCorpusGuardError(RuntimeError):
    """Raised when corpus inventory or retirement evidence is invalid."""


class TestCorpusSourceRefMissingError(RuntimeError):
    """Raised only when a replacement source ref is absent from the worktree."""


@dataclass(frozen=True)
class TestDeclaration:
    ref: str
    kind: str


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
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}

    def collected_methods(
        class_node: ast.ClassDef,
        visiting: set[str],
    ) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
        if class_node.name in visiting:
            raise TestCorpusGuardError(
                f"cannot resolve Python test class inheritance: {path}"
            )
        methods: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
        next_visiting = {*visiting, class_node.name}
        for base in class_node.bases:
            if isinstance(base, ast.Name) and base.id in classes:
                methods.update(collected_methods(classes[base.id], next_visiting))
        for child in class_node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if child.name.startswith("test_"):
                    methods[child.name] = child
                else:
                    methods.pop(child.name, None)
        return methods

    def has_constructor(class_node: ast.ClassDef, visiting: set[str]) -> bool:
        if class_node.name in visiting:
            raise TestCorpusGuardError(
                f"cannot resolve Python test class inheritance: {path}"
            )
        if any(
            isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and child.name in {"__init__", "__new__"}
            for child in class_node.body
        ):
            return True
        next_visiting = {*visiting, class_node.name}
        return any(
            has_constructor(classes[base.id], next_visiting)
            for base in class_node.bases
            if isinstance(base, ast.Name) and base.id in classes
        )

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                refs.append((f"{path}::{node.name}", "python_test"))
            continue
        if not isinstance(node, ast.ClassDef) or not node.name.startswith("Test"):
            continue
        if has_constructor(node, set()):
            continue
        for method_name in collected_methods(node, set()):
            refs.append((f"{path}::{node.name}::{method_name}", "python_test"))
    return _deduplicate_refs(refs)


def parse_frontend_declarations(path: str, text: str) -> tuple[TestDeclaration, ...]:
    try:
        refs = parse_frontend_refs(path, text)
    except FrontendInventoryError as exc:
        raise TestCorpusGuardError(str(exc)) from None
    return tuple(TestDeclaration(ref=ref, kind="frontend_test") for ref in refs)


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


def _close_quietly(*descriptors: int | None) -> None:
    for descriptor in descriptors:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass


def _read_bounded_regular_text(
    repo: Path,
    relative_path: Path,
    *,
    max_bytes: int,
    unsafe_message: str,
    invalid_message: str,
    missing_error: type[TestCorpusSourceRefMissingError] | None = None,
) -> str:
    descriptor: int | None = None
    parent_descriptor: int | None = None
    try:
        parts = relative_path.parts
        if (
            relative_path.is_absolute()
            or not parts
            or any(part in {"", ".", ".."} for part in parts)
        ):
            raise TestCorpusGuardError(unsafe_message)
        directory_flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        parent_descriptor = os.open(repo, directory_flags)
        parent_info = os.fstat(parent_descriptor)
        if not stat.S_ISDIR(parent_info.st_mode):
            raise TestCorpusGuardError(unsafe_message)
        for component in parts[:-1]:
            next_descriptor = os.open(
                component,
                directory_flags,
                dir_fd=parent_descriptor,
            )
            try:
                next_info = os.fstat(next_descriptor)
                if not stat.S_ISDIR(next_info.st_mode):
                    raise TestCorpusGuardError(unsafe_message)
                os.close(parent_descriptor)
            except BaseException:
                _close_quietly(next_descriptor)
                raise
            parent_descriptor = next_descriptor
        descriptor = os.open(
            parts[-1],
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_descriptor,
        )
    except FileNotFoundError as exc:
        _close_quietly(descriptor, parent_descriptor)
        if missing_error is not None:
            raise missing_error(invalid_message) from exc
        raise TestCorpusGuardError(invalid_message) from exc
    except TestCorpusGuardError:
        _close_quietly(descriptor, parent_descriptor)
        raise
    except OSError as exc:
        _close_quietly(descriptor, parent_descriptor)
        raise TestCorpusGuardError(unsafe_message) from exc

    try:
        opened = os.fstat(descriptor)
        linked = os.stat(
            parts[-1],
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
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
        still_linked = os.stat(
            parts[-1],
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
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
        if parent_descriptor is not None:
            os.close(parent_descriptor)


def _read_worktree_text(
    repo: Path,
    path: str,
    *,
    missing_error: type[TestCorpusSourceRefMissingError] | None = None,
) -> str:
    return _read_bounded_regular_text(
        repo,
        Path(path),
        max_bytes=MAX_TEST_FILE_BYTES,
        unsafe_message=f"test inventory file is unsafe: {path}",
        invalid_message=f"cannot read test inventory: {path}",
        missing_error=missing_error,
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
    command = ["git", *args]
    try:
        process = subprocess.Popen(
            command,
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise TestCorpusGuardError("git inspection is unavailable") from exc
    if process.stdout is None:
        process.kill()
        process.wait()
        raise TestCorpusGuardError("git inspection output is unavailable")

    chunks: list[bytes] = []
    total = 0
    deadline = time.monotonic() + GIT_INSPECTION_TIMEOUT_SECONDS
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TestCorpusGuardError("git inspection timed out")
            ready, _, _ = select.select([process.stdout], [], [], remaining)
            if not ready:
                raise TestCorpusGuardError("git inspection timed out")
            chunk = os.read(
                process.stdout.fileno(),
                min(64 * 1024, MAX_GIT_STDOUT_BYTES + 1 - total),
            )
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_GIT_STDOUT_BYTES:
                raise TestCorpusGuardError("git inspection output exceeds byte budget")
        return subprocess.CompletedProcess(
            args=command,
            returncode=process.wait(),
            stdout=b"".join(chunks),
            stderr=b"",
        )
    except BaseException:
        if process.poll() is None:
            process.kill()
        process.wait()
        raise
    finally:
        process.stdout.close()


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
    commands = (
        [
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            base_sha,
            "HEAD",
            "--",
            "tests",
            "apps",
        ],
        [
            "diff",
            "--cached",
            "--name-only",
            "--no-renames",
            "-z",
            "--",
            "tests",
            "apps",
        ],
        [
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            "--",
            "tests",
            "apps",
        ],
        [
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            "tests",
            "apps",
        ],
    )
    raw_paths = bytearray()
    for command in commands:
        result = _run_git(repo, command)
        if result.returncode != 0:
            raise TestCorpusGuardError("cannot derive changed test corpus")
        raw_paths.extend(result.stdout)
        if len(raw_paths) > MAX_CHANGED_PATH_BYTES:
            raise TestCorpusGuardError("changed test corpus paths exceed byte budget")
    try:
        paths = bytes(raw_paths).decode("utf-8").split("\0")
    except UnicodeDecodeError as exc:
        raise TestCorpusGuardError("changed test corpus paths are malformed") from exc
    changed = tuple(sorted({path for path in paths if path and _is_test_path(path)}))
    if len(changed) > MAX_CHANGED_TEST_PATHS:
        raise TestCorpusGuardError("changed test corpus path count exceeds budget")
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
    vitest_suffixes = tuple(
        f".{kind}.{extension}"
        for kind in ("test", "spec")
        for extension in FRONTEND_TEST_EXTENSIONS
    )
    return candidate.name.endswith(vitest_suffixes) or (
        path.startswith("apps/control-center/tests/")
        and candidate.suffix.removeprefix(".") in FRONTEND_TEST_EXTENSIONS
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


def _validate_test_ref(value: str) -> None:
    if (
        "::" not in value
        or not value.split("::", 1)[1]
        or len(value) > 2_000
        or any(ord(character) < 32 for character in value)
    ):
        raise TestCorpusEvidenceError("retired test ref is invalid")
    path = value.split("::", 1)[0]
    try:
        _validate_test_path(path)
    except TestCorpusGuardError as exc:
        raise TestCorpusEvidenceError("retired test ref is invalid") from exc
    if not _is_test_path(path):
        raise TestCorpusEvidenceError("retired test ref is invalid")


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
        raise TestCorpusGuardError(f"cannot read base test file: {path}")
    try:
        return result.stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TestCorpusGuardError(f"base test file is not UTF-8: {path}") from exc


def test_source_ref(test_ref: str, source_text: str) -> str:
    artifact = {
        "schema_version": "uaa.test_corpus_source.v1",
        "test_ref": test_ref,
        "source_digest": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
    }
    encoded = json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode()
    return f"test-source-ref:sha256:{hashlib.sha256(encoded).hexdigest()}"


def _source_ref_from_text(test_ref: str, source_text: str) -> str:
    declarations = parse_test_declarations(test_ref.split("::", 1)[0], source_text)
    if test_ref not in {declaration.ref for declaration in declarations}:
        raise TestCorpusEvidenceError(
            f"replacement assertion source is missing: {test_ref}"
        )
    return test_source_ref(test_ref, source_text)


def _worktree_source_ref(repo: Path, test_ref: str) -> str:
    path = test_ref.split("::", 1)[0]
    text = _read_worktree_text(
        repo,
        path,
        missing_error=TestCorpusSourceRefMissingError,
    )
    try:
        return _source_ref_from_text(test_ref, text)
    except TestCorpusEvidenceError as exc:
        raise TestCorpusSourceRefMissingError(
            f"replacement assertion source is missing: {test_ref}"
        ) from exc


def _resolve_assertion_source_ref(
    repo: Path,
    test_ref: str,
    historical_source_refs: dict[str, str],
) -> str:
    try:
        return _worktree_source_ref(repo, test_ref)
    except TestCorpusSourceRefMissingError:
        historical = historical_source_refs.get(test_ref)
        if historical is None:
            raise TestCorpusEvidenceError(
                f"replacement assertion source is missing: {test_ref}"
            ) from None
        return historical


def _validate_verification_envelope(
    _repo: Path,
    encoded_envelope: str,
    _replacement_refs: list[str],
    _resolve_assertion_source_ref: Callable[[str], str],
) -> None:
    try:
        decode_github_job_output(encoded_envelope)
    except VerificationGithubTransportError as exc:
        raise TestCorpusEvidenceError(
            "retired test verification receipt is invalid"
        ) from exc
    raise TestCorpusEvidenceError(
        "retired test verification receipt lacks independent GitHub attestation"
    )


def _historical_source_refs(ledger: dict[str, Any]) -> dict[str, str]:
    source_refs: dict[str, str] = {}
    records = ledger.get("retirements")
    if not isinstance(records, list):
        return source_refs
    for record in records:
        if not isinstance(record, dict):
            continue
        equivalence = record.get("assertion_equivalence_artifact")
        if not isinstance(equivalence, dict):
            continue
        evidence = equivalence.get("preserved_assertion_evidence")
        if not isinstance(evidence, list):
            continue
        for item in evidence:
            artifact = item.get("artifact") if isinstance(item, dict) else None
            if not isinstance(artifact, dict):
                continue
            replacement_ref = artifact.get("replacement_ref")
            source_ref = artifact.get("source_ref")
            if isinstance(replacement_ref, str) and isinstance(source_ref, str):
                existing = source_refs.setdefault(replacement_ref, source_ref)
                if existing != source_ref:
                    raise TestCorpusGuardError(
                        "historical replacement source refs conflict"
                    )
    return source_refs


def removed_declarations(repo: Path, base_sha: str) -> tuple[str, ...]:
    removed: set[str] = set()
    current_paths = set(discover_test_files(repo))
    for path in _changed_test_paths(repo, base_sha):
        prior = _base_text(repo, base_sha, path)
        if prior is None:
            continue
        prior_refs = {item.ref for item in parse_test_declarations(path, prior)}
        if path in current_paths:
            current_text = _read_worktree_text(repo, path)
            current_refs = {
                item.ref for item in parse_test_declarations(path, current_text)
            }
        else:
            current_refs = set()
        removed.update(prior_refs - current_refs)
    return tuple(sorted(removed))


def _parse_ledger_text(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TestCorpusGuardError("test-corpus retirement ledger is invalid") from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "retirements"}
        or value.get("schema_version") != RETIREMENT_SCHEMA
    ):
        raise TestCorpusGuardError("test-corpus retirement ledger schema is invalid")
    return value


def _load_ledger(repo: Path) -> dict[str, Any]:
    return _parse_ledger_text(
        _read_bounded_regular_text(
            repo,
            RETIREMENT_LEDGER,
            max_bytes=MAX_RETIREMENT_LEDGER_BYTES,
            unsafe_message="test-corpus retirement ledger is unsafe",
            invalid_message="test-corpus retirement ledger is invalid",
        )
    )


def _load_base_ledger(repo: Path, base_sha: str) -> dict[str, Any]:
    path = RETIREMENT_LEDGER.as_posix()
    listing = _run_git(
        repo,
        ["ls-tree", "--name-only", "-z", base_sha, "--", path],
    )
    if listing.returncode != 0:
        raise TestCorpusGuardError("cannot inspect base test-corpus retirement ledger")
    try:
        paths = {item for item in listing.stdout.decode("utf-8").split("\0") if item}
    except UnicodeDecodeError as exc:
        raise TestCorpusGuardError(
            "base test-corpus retirement ledger path is invalid"
        ) from exc
    if path not in paths:
        return {"schema_version": RETIREMENT_SCHEMA, "retirements": []}
    size = _run_git(repo, ["cat-file", "-s", f"{base_sha}:{path}"])
    if size.returncode != 0:
        raise TestCorpusGuardError("cannot inspect base test-corpus retirement ledger")
    try:
        byte_count = int(size.stdout.decode("ascii").strip())
    except (UnicodeDecodeError, ValueError) as exc:
        raise TestCorpusGuardError(
            "base test-corpus retirement ledger size is invalid"
        ) from exc
    if byte_count > MAX_RETIREMENT_LEDGER_BYTES:
        raise TestCorpusGuardError(
            "base test-corpus retirement ledger exceeds byte budget"
        )
    result = _run_git(repo, ["show", f"{base_sha}:{path}"])
    if result.returncode != 0:
        raise TestCorpusGuardError("cannot read base test-corpus retirement ledger")
    try:
        return _parse_ledger_text(result.stdout.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise TestCorpusGuardError(
            "base test-corpus retirement ledger is invalid"
        ) from exc


def validate_retirements(
    current_refs: set[str],
    removed_refs: set[str],
    ledger: dict[str, Any],
    *,
    resolve_assertion_source_ref: Callable[[str], str],
    validate_verification_envelope: Callable[[str, list[str]], None],
    base_ledger: dict[str, Any] | None = None,
) -> int:
    try:
        return _validate_retirement_evidence(
            current_refs,
            removed_refs,
            ledger,
            validate_test_ref=_validate_test_ref,
            resolve_assertion_source_ref=resolve_assertion_source_ref,
            validate_verification_envelope=validate_verification_envelope,
            base_ledger=base_ledger,
        )
    except TestCorpusEvidenceError as exc:
        raise TestCorpusGuardError(str(exc)) from None


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
    ledger = _load_ledger(repo)
    base_ledger = (
        _load_base_ledger(repo, resolved_base) if resolved_base is not None else None
    )
    historical_source_refs = _historical_source_refs(base_ledger or {})

    def resolve_source_ref(ref: str) -> str:
        return _resolve_assertion_source_ref(repo, ref, historical_source_refs)

    retirement_count = validate_retirements(
        current_refs,
        removed,
        ledger,
        resolve_assertion_source_ref=resolve_source_ref,
        validate_verification_envelope=lambda envelope, refs: (
            _validate_verification_envelope(repo, envelope, refs, resolve_source_ref)
        ),
        base_ledger=base_ledger,
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
