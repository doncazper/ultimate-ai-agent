#!/usr/bin/env python3
from __future__ import annotations

# ruff: noqa: E402 - the built-in-only isolation bootstrap must run first

# Exact provenance must start before the script directory can satisfy imports.
# ``sys`` and the platform execution module are built into the interpreter, so
# this re-exec path cannot be shadowed by repository-local source or bytecode.
import sys as _foundation_bootstrap_sys

_FOUNDATION_BOOTSTRAP_SAFE = bool(
    _foundation_bootstrap_sys.flags.isolated
    and _foundation_bootstrap_sys.flags.no_site
)
if __name__ == "__main__" and not _FOUNDATION_BOOTSTRAP_SAFE:
    if _foundation_bootstrap_sys.platform == "win32":
        import nt as _foundation_bootstrap_os
    else:
        import posix as _foundation_bootstrap_os

    _foundation_bootstrap_os.execv(
        _foundation_bootstrap_sys.executable,
        (
            _foundation_bootstrap_sys.executable,
            "-I",
            "-B",
            "-S",
            __file__,
            *_foundation_bootstrap_sys.argv[1:],
        ),
    )

import argparse
import ctypes
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import sysconfig
import tempfile
import time
import warnings
from pathlib import Path

warnings.filterwarnings(
    "ignore",
    message=r"Using `httpx` with `starlette\.testclient` is deprecated.*",
    category=Warning,
)

ROOT = Path(__file__).resolve().parent.parent


_GIT_READ_CONFIG = (
    "-c",
    "core.fsmonitor=false",
    "-c",
    "core.untrackedCache=false",
    "-c",
    "core.trustctime=true",
    "-c",
    "core.checkStat=default",
    "-c",
    "core.ignoreStat=false",
    "-c",
    f"core.hooksPath={os.devnull}",
    "-c",
    f"core.attributesFile={os.devnull}",
)


def _sanitized_git_environment() -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("GIT_")
    }
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return environment


def _require_raw_clean_worktree(
    repository_root: Path,
    *,
    git_command: str,
    git_environment: dict[str, str],
) -> str:
    """Compare raw worktree bytes and modes with HEAD without Git conversions."""

    def run(*arguments: str, input_bytes: bytes | None = None) -> bytes:
        completed = subprocess.run(
            [
                git_command,
                "--no-replace-objects",
                *_GIT_READ_CONFIG,
                *arguments,
            ],
            cwd=repository_root,
            check=True,
            capture_output=True,
            env=git_environment,
            input=input_bytes,
        )
        return completed.stdout

    def records(payload: bytes, *, purpose: str) -> list[bytes]:
        if len(payload) > 16 * 1024 * 1024 or (payload and not payload.endswith(b"\0")):
            raise RuntimeError(f"Foundation Gate {purpose} is invalid")
        values = payload[:-1].split(b"\0") if payload else []
        if len(values) > 20_000 or any(not value for value in values):
            raise RuntimeError(f"Foundation Gate {purpose} is invalid")
        return values

    revision = run("rev-parse", "HEAD").decode("ascii", errors="strict").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise RuntimeError("Foundation Gate repository revision is invalid")
    object_format = (
        run("rev-parse", "--show-object-format")
        .decode("ascii", errors="strict")
        .strip()
    )
    if object_format not in {"sha1", "sha256"}:
        raise RuntimeError("Foundation Gate Git object format is invalid")

    tree_entries: dict[bytes, tuple[bytes, bytes, int]] = {}
    for record in records(
        run("ls-tree", "-rlz", "--full-tree", revision),
        purpose="Git tree census",
    ):
        try:
            metadata, path = record.split(b"\t", 1)
            mode, object_type, object_id, size_value = metadata.split(b" ", 3)
            size = int(size_value)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("Foundation Gate Git tree census is invalid") from exc
        components = path.split(b"/")
        if (
            object_type != b"blob"
            or mode not in {b"100644", b"100755", b"120000"}
            or not re.fullmatch(rb"[0-9a-f]{40}|[0-9a-f]{64}", object_id)
            or size < 0
            or size > 64 * 1024 * 1024
            or path.startswith(b"/")
            or any(component in {b"", b".", b".."} for component in components)
            or path in tree_entries
        ):
            raise RuntimeError("Foundation Gate Git tree census is invalid")
        if mode == b"120000":
            raise RuntimeError(
                "Foundation Gate exact provenance rejects tracked symlinks"
            )
        tree_entries[path] = (mode, object_id, size)
    if sum(size for _mode, _object_id, size in tree_entries.values()) > 1024**3:
        raise RuntimeError("Foundation Gate Git tree census is invalid")

    index_entries: dict[bytes, tuple[bytes, bytes]] = {}
    for record in records(run("ls-files", "--stage", "-z"), purpose="Git index census"):
        try:
            metadata, path = record.split(b"\t", 1)
            mode, object_id, stage = metadata.split(b" ", 2)
        except ValueError as exc:
            raise RuntimeError("Foundation Gate Git index census is invalid") from exc
        if (
            stage != b"0"
            or not re.fullmatch(rb"[0-9a-f]{40}|[0-9a-f]{64}", object_id)
            or path in index_entries
        ):
            raise RuntimeError("Foundation Gate Git index census is invalid")
        index_entries[path] = (mode, object_id)
    if {
        path: (mode, object_id)
        for path, (mode, object_id, _size) in tree_entries.items()
    } != index_entries:
        raise RuntimeError(
            "Foundation Gate revision provenance requires a clean worktree"
        )

    for path, (mode, object_id, expected_size) in tree_entries.items():
        components = [os.fsdecode(component) for component in path.split(b"/")]
        parent = repository_root
        try:
            for component in components[:-1]:
                parent = parent / component
                if not stat.S_ISDIR(os.lstat(parent).st_mode):
                    raise RuntimeError(
                        "Foundation Gate repository worktree path is invalid"
                    )
            target = parent / components[-1]
            before = os.lstat(target)
            hasher = hashlib.new(object_format)
            if not stat.S_ISREG(before.st_mode) or before.st_size != expected_size:
                raise RuntimeError(
                    "Foundation Gate revision provenance requires a clean worktree"
                )
            if os.name == "posix" and bool(before.st_mode & 0o111) != (
                mode == b"100755"
            ):
                raise RuntimeError(
                    "Foundation Gate revision provenance requires a clean worktree"
                )
            descriptor = os.open(
                target,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
            )
            try:
                opened = os.fstat(descriptor)
                if not os.path.samestat(before, opened):
                    raise RuntimeError(
                        "Foundation Gate repository worktree path changed"
                    )
                hasher.update(f"blob {opened.st_size}\0".encode("ascii"))
                while True:
                    chunk = os.read(descriptor, 1024 * 1024)
                    if not chunk:
                        break
                    hasher.update(chunk)
                closed_over = os.fstat(descriptor)
            finally:
                os.close(descriptor)
            if not os.path.samestat(opened, closed_over):
                raise RuntimeError(
                    "Foundation Gate repository worktree path changed"
                )
            after = os.lstat(target)
        except FileNotFoundError as exc:
            raise RuntimeError(
                "Foundation Gate revision provenance requires a clean worktree"
            ) from exc
        except OSError as exc:
            raise RuntimeError(
                "Foundation Gate repository worktree path is invalid"
            ) from exc
        if (
            not os.path.samestat(before, after)
            or before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
            or before.st_ctime_ns != after.st_ctime_ns
            or hasher.hexdigest().encode("ascii") != object_id
        ):
            raise RuntimeError(
                "Foundation Gate revision provenance requires a clean worktree"
            )

    if records(
        run(
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
        ),
        purpose="untracked-path census",
    ):
        raise RuntimeError(
            "Foundation Gate revision provenance requires a clean worktree"
        )
    if run("rev-parse", "HEAD").decode("ascii", errors="strict").strip() != revision:
        raise RuntimeError("Foundation Gate repository revision drift")
    return revision


def _index_has_hidden_worktree_entries(
    repository_root: Path,
    *,
    git_command: str,
    git_environment: dict[str, str],
) -> bool:
    entries = subprocess.run(
        [
            git_command,
            "--no-replace-objects",
            *_GIT_READ_CONFIG,
            "ls-files",
            "-v",
            "-z",
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        env=git_environment,
    ).stdout.split(b"\0")
    return any(
        entry
        and (entry[:1] in {b"S", b"s"} or (entry[:1].isalpha() and entry[:1].islower()))
        for entry in entries
    )


def _prepare_external_import_cache(
    repository_root: Path,
) -> tuple[tempfile.TemporaryDirectory, Path]:
    """Divert Python cache reads before repository modules become importable."""

    temporary_root = Path(tempfile.gettempdir()).resolve()
    try:
        root_metadata = temporary_root.lstat()
    except OSError as exc:
        raise RuntimeError("Foundation Gate import cache root is unavailable") from exc
    if (
        stat.S_ISLNK(root_metadata.st_mode)
        or not stat.S_ISDIR(root_metadata.st_mode)
        or temporary_root.is_relative_to(repository_root.resolve())
    ):
        raise RuntimeError("Foundation Gate import cache root is unsafe")
    cache_handle = tempfile.TemporaryDirectory(
        prefix="uaa-foundation-import-cache-",
        dir=temporary_root,
    )
    cache_root = Path(cache_handle.name)
    cache_root.chmod(0o700)
    cache_metadata = cache_root.lstat()
    if (
        not stat.S_ISDIR(cache_metadata.st_mode)
        or stat.S_ISLNK(cache_metadata.st_mode)
        or (hasattr(os, "getuid") and cache_metadata.st_uid != os.getuid())
        or stat.S_IMODE(cache_metadata.st_mode) != 0o700
        or any(cache_root.iterdir())
    ):
        raise RuntimeError("Foundation Gate import cache is unsafe")
    sys.pycache_prefix = str(cache_root)
    sys.dont_write_bytecode = True
    return cache_handle, cache_root


def _require_no_ignored_repository_import_sources(
    repository_root: Path,
    *,
    git_command: str,
    git_environment: dict[str, str],
) -> None:
    """Reject ignored sources reachable from the repository import roots."""

    completed = subprocess.run(
        [
            git_command,
            "--no-replace-objects",
            *_GIT_READ_CONFIG,
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            "-z",
            "--",
            ".",
            # A repository-local virtual environment is already active before
            # this module starts and its dot-prefixed name is not importable
            # from ROOT.  Every other ignored repository path is censused.
            ":(top,exclude,glob).venv/**",
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        env=git_environment,
    )
    payload = completed.stdout
    if len(payload) > 64 * 1024 * 1024 or (payload and not payload.endswith(b"\0")):
        raise RuntimeError("Foundation Gate ignored import census is invalid")
    paths = payload[:-1].split(b"\0") if payload else []
    if len(paths) > 200_000 or any(not path for path in paths):
        raise RuntimeError("Foundation Gate ignored import census is invalid")
    legacy_or_source_suffixes = (
        b".py",
        b".pyc",
        b".pyo",
        b".so",
        b".pyd",
        b".dll",
        b".dylib",
    )
    for path in paths:
        lowered = path.lower()
        components = lowered.split(b"/")
        try:
            metadata = os.lstat(repository_root / os.fsdecode(path))
        except OSError as exc:
            raise RuntimeError(
                "Foundation Gate ignored import census changed"
            ) from exc
        decoded_components = tuple(os.fsdecode(item) for item in path.split(b"/"))
        import_candidates = (decoded_components,)
        if decoded_components[:1] == ("src",):
            import_candidates += (decoded_components[1:],)
        if stat.S_ISLNK(metadata.st_mode) and any(
            candidate
            and all(component.isidentifier() for component in candidate)
            for candidate in import_candidates
        ):
            raise RuntimeError(
                "Foundation Gate repository has ignored symlink import sources"
            )
        if b"__pycache__" in components and lowered.endswith((b".pyc", b".pyo")):
            # The fresh external sys.pycache_prefix makes repository-local
            # cache directories unreachable to every subsequent import.
            continue
        if lowered.endswith(legacy_or_source_suffixes):
            raise RuntimeError(
                "Foundation Gate repository has ignored executable import sources"
            )


def _validate_posix_admin_path(path: Path) -> None:
    for component in (path, *path.parents):
        try:
            metadata = component.stat()
        except OSError as exc:
            raise RuntimeError(
                "Foundation Gate trusted Git lacks OS provenance"
            ) from exc
        if metadata.st_uid != 0 or metadata.st_mode & 0o022:
            raise RuntimeError("Foundation Gate trusted Git lacks OS provenance")


def _validated_windows_system_root() -> Path:
    if os.name != "nt":
        raise RuntimeError("Foundation Gate Windows system root is unavailable")
    value = os.environ.get("SystemRoot")
    if not value or len(value) > 260 or "\x00" in value:
        raise RuntimeError("Foundation Gate Windows system root is unavailable")
    try:
        buffer = ctypes.create_unicode_buffer(32_768)
        length = ctypes.windll.kernel32.GetWindowsDirectoryW(  # type: ignore[attr-defined]
            buffer,
            len(buffer),
        )
        configured = Path(value).resolve(strict=True)
        authoritative = Path(buffer.value).resolve(strict=True)
    except (AttributeError, OSError) as exc:
        raise RuntimeError("Foundation Gate Windows system root is unavailable") from exc
    if length <= 0 or length >= len(buffer) or configured != authoritative:
        raise RuntimeError("Foundation Gate Windows system root is unavailable")
    return authoritative


def _trusted_preimport_git() -> str:
    executable_value = shutil.which("git")
    if not executable_value:
        raise RuntimeError("Foundation Gate trusted Git is unavailable")
    try:
        executable = Path(executable_value).resolve(strict=True)
        metadata = executable.stat()
    except OSError as exc:
        raise RuntimeError("Foundation Gate trusted Git is unavailable") from exc
    if not stat.S_ISREG(metadata.st_mode) or not os.access(executable, os.X_OK):
        raise RuntimeError("Foundation Gate trusted Git is unsafe")
    system = platform.system().strip().lower()
    if os.name == "posix":
        _validate_posix_admin_path(executable)
        if system == "darwin":
            if executable != Path("/usr/bin/git"):
                raise RuntimeError("Foundation Gate trusted Git lacks OS provenance")
            signature = subprocess.run(
                (
                    "/usr/bin/codesign",
                    "--verify",
                    "--strict",
                    "-R=anchor apple",
                    str(executable),
                ),
                check=False,
                capture_output=True,
                timeout=30,
            )
            if signature.returncode != 0:
                raise RuntimeError("Foundation Gate trusted Git lacks OS provenance")
    elif os.name == "nt":
        system_root = _validated_windows_system_root()
        powershell = (
            system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
        )
        signature = subprocess.run(
            (
                str(powershell),
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "$s=Get-AuthenticodeSignature -LiteralPath $args[0];"
                "Write-Output ($s.Status.ToString()+' '+"
                "$s.SignerCertificate.Thumbprint)",
                str(executable),
            ),
            check=False,
            capture_output=True,
            timeout=30,
        )
        output = signature.stdout.decode("ascii", errors="strict").strip().split()
        if (
            signature.returncode != 0
            or len(output) != 2
            or output[0] != "Valid"
            or not re.fullmatch(r"[0-9A-F]{40,64}", output[1])
        ):
            raise RuntimeError("Foundation Gate trusted Git lacks OS provenance")
    else:
        raise RuntimeError("Foundation Gate trusted Git platform is unsupported")
    return str(executable)


def _preloaded_repository_module_paths(repository_root: Path) -> tuple[str, ...]:
    """Record repository code that executed before the provenance seal."""

    resolved_root = repository_root.resolve()
    this_module = Path(__file__).resolve()
    observed: set[str] = set()
    for module in tuple(sys.modules.values()):
        module_file = getattr(module, "__file__", None)
        if not isinstance(module_file, str):
            continue
        try:
            path = Path(module_file).resolve()
        except OSError:
            continue
        if path == this_module or not path.is_relative_to(resolved_root):
            continue
        observed.add(path.relative_to(resolved_root).as_posix())
    return tuple(sorted(observed))


def _runtime_dependency_path() -> Path:
    """Locate site-packages without executing any environment ``.pth`` files."""

    executable = Path(sys.executable)
    environment_root = executable.parent.parent
    if (environment_root / "pyvenv.cfg").is_file():
        if os.name == "nt":
            candidate = environment_root / "Lib" / "site-packages"
        else:
            candidate = (
                environment_root
                / "lib"
                / f"python{sys.version_info.major}.{sys.version_info.minor}"
                / "site-packages"
            )
    else:
        candidate = Path(sysconfig.get_path("purelib"))
    try:
        metadata = candidate.lstat()
    except OSError as exc:
        raise RuntimeError(
            "Foundation Gate runtime dependency path is unavailable"
        ) from exc
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise RuntimeError("Foundation Gate runtime dependency path is unsafe")
    return candidate


def _establish_preimport_repository_posture(repository_root: Path) -> str | None:
    """Prove or explicitly withhold clean provenance before repo imports."""

    git_command = _trusted_preimport_git()
    git_environment = _sanitized_git_environment()
    _require_no_ignored_repository_import_sources(
        repository_root,
        git_command=git_command,
        git_environment=git_environment,
    )
    try:
        revision = _require_raw_clean_worktree(
            repository_root,
            git_command=git_command,
            git_environment=git_environment,
        )
    except RuntimeError as exc:
        if str(exc) == (
            "Foundation Gate revision provenance requires a clean worktree"
        ):
            return None
        raise
    if _index_has_hidden_worktree_entries(
        repository_root,
        git_command=git_command,
        git_environment=git_environment,
    ):
        return None
    return revision


_PREIMPORT_REPOSITORY_MODULE_PATHS = _preloaded_repository_module_paths(ROOT)
_FOUNDATION_IMPORT_CACHE_HANDLE: tempfile.TemporaryDirectory | None = None
_FOUNDATION_IMPORT_CACHE: Path | None = None
if _FOUNDATION_BOOTSTRAP_SAFE:
    _FOUNDATION_IMPORT_CACHE_HANDLE, _FOUNDATION_IMPORT_CACHE = (
        _prepare_external_import_cache(ROOT)
    )
_PREIMPORT_CLEAN_REVISION = _establish_preimport_repository_posture(ROOT)

_FOUNDATION_DEPENDENCY_PATH = _runtime_dependency_path()
if str(_FOUNDATION_DEPENDENCY_PATH) not in sys.path:
    sys.path.append(str(_FOUNDATION_DEPENDENCY_PATH))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.gate import (  # noqa: E402
    FoundationGateCommandReceipt,
    FoundationGateEvaluator,
    FoundationGateLatencySummary,
    FoundationGateReport,
    FoundationGateReleaseLaneSummary,
    FoundationGateStatus,
)
from ultimate_ai_agent.core.gate.reports import (  # noqa: E402
    foundation_gate_evaluation_provenance_digest,
)
from scripts.verification.verification_github_prerequisites import (  # noqa: E402
    FoundationPrerequisiteManifest,
    load_foundation_prerequisite_manifest,
)


def exact_repository_revision(
    repository_root: Path,
    *,
    git_executable: str | Path = "git",
) -> str:
    git_command = str(git_executable)
    git_environment = _sanitized_git_environment()
    repository_probe = subprocess.run(
        [
            git_command,
            "--no-replace-objects",
            *_GIT_READ_CONFIG,
            "rev-parse",
            "--show-toplevel",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
        env=git_environment,
    )
    if repository_probe.returncode != 0:
        raise RuntimeError(
            "Foundation Gate exact revision provenance requires the repository root"
        )
    resolved_root = Path(repository_probe.stdout.strip()).resolve()
    if resolved_root != repository_root.resolve():
        raise RuntimeError(
            "Foundation Gate exact revision provenance requires the repository root"
        )
    revision = _require_raw_clean_worktree(
        resolved_root,
        git_command=git_command,
        git_environment=git_environment,
    )
    if resolved_root == ROOT.resolve():
        if not _FOUNDATION_BOOTSTRAP_SAFE:
            raise RuntimeError(
                "Foundation Gate exact provenance requires an isolated no-site process"
            )
        if _PREIMPORT_REPOSITORY_MODULE_PATHS:
            raise RuntimeError(
                "Foundation Gate exact provenance requires a fresh process"
            )
        if _PREIMPORT_CLEAN_REVISION is None:
            raise RuntimeError(
                "Foundation Gate revision provenance requires a clean worktree"
            )
        if revision != _PREIMPORT_CLEAN_REVISION:
            raise RuntimeError("Foundation Gate repository revision drift")
    if _index_has_hidden_worktree_entries(
        resolved_root,
        git_command=git_command,
        git_environment=git_environment,
    ):
        raise RuntimeError(
            "Foundation Gate revision provenance rejects hidden index entries"
        )
    revision_after = subprocess.run(
        [
            git_command,
            "--no-replace-objects",
            *_GIT_READ_CONFIG,
            "rev-parse",
            "HEAD",
        ],
        cwd=resolved_root,
        check=True,
        capture_output=True,
        text=True,
        env=git_environment,
    ).stdout.strip()
    if revision_after != revision:
        raise RuntimeError("Foundation Gate repository revision drift")
    return f"git-sha:{revision}"


def evaluate_foundation_gate_at_exact_repository_revision(
    repository_root: Path,
    *,
    git_executable: str | Path = "git",
) -> tuple[str, FoundationGateReport]:
    """Run the canonical evaluator and inseparably bind its clean revision."""

    evaluated_revision_ref = exact_repository_revision(
        repository_root,
        git_executable=git_executable,
    )
    report = FoundationGateEvaluator(repository_root).evaluate()
    if (
        exact_repository_revision(
            repository_root,
            git_executable=git_executable,
        )
        != evaluated_revision_ref
    ):
        raise RuntimeError("Foundation Gate revision changed during evaluation")
    bound = report.model_copy(update={"evaluated_revision_ref": evaluated_revision_ref})
    bound = bound.model_copy(
        update={
            "evaluation_provenance_digest_ref": (
                foundation_gate_evaluation_provenance_digest(bound)
            )
        }
    )
    return evaluated_revision_ref, bound


def evaluate_foundation_gate_for_repository_state(
    repository_root: Path,
    *,
    require_clean_revision: bool,
) -> tuple[str | None, FoundationGateReport]:
    """Preserve dirty-tree development checks without issuing provenance."""

    try:
        return evaluate_foundation_gate_at_exact_repository_revision(repository_root)
    except RuntimeError as exc:
        if (
            require_clean_revision
            or str(exc)
            != "Foundation Gate revision provenance requires a clean worktree"
        ):
            raise
    return None, FoundationGateEvaluator(repository_root).evaluate()


GATE_TESTS = [
    "tests/test_foundation_gate_criteria.py",
    "tests/test_foundation_gate_report.py",
    "tests/test_shadow_replay_m5.py",
    "tests/test_contract_compatibility.py",
    "tests/test_foundation_gate_blocked_modules.py",
    "tests/test_foundation_gate_secret_hygiene.py",
    "tests/test_foundation_gate_receipts.py",
    "tests/test_foundation_gate_rollback.py",
    "tests/test_foundation_gate_truth_evidence.py",
    "tests/test_foundation_gate_api_routes.py",
    "tests/test_model_profiles.py",
    "tests/test_model_routing_policy.py",
    "tests/test_model_router_decisions.py",
    "tests/test_model_router_privacy.py",
    "tests/test_model_router_context_budget.py",
    "tests/test_model_router_no_execution.py",
    "tests/test_cost_budgets.py",
    "tests/test_cost_governor.py",
    "tests/test_resource_governor.py",
    "tests/test_m7_api_routes.py",
    "tests/test_m7_gate_integration.py",
    "tests/test_api_manifest.py",
    "tests/test_openapi_contract.py",
    "tests/test_agents_md_guidance.py",
    "tests/test_m75_gate_integration.py",
    "tests/test_model_runtime_manifests.py",
    "tests/test_model_runtime_requests.py",
    "tests/test_model_runtime_simulator.py",
    "tests/test_model_runtime_no_real_calls.py",
    "tests/test_model_runtime_redaction.py",
    "tests/test_model_runtime_event_metadata.py",
    "tests/test_model_runtime_api_routes.py",
    "tests/test_m8_gate_integration.py",
    "tests/test_approval_requests.py",
    "tests/test_approval_authority.py",
    "tests/test_approval_validation.py",
    "tests/test_approval_expiration.py",
    "tests/test_approval_scope.py",
    "tests/test_approval_receipts.py",
    "tests/test_approval_integration_model_router.py",
    "tests/test_approval_integration_model_runtime.py",
    "tests/test_approval_integration_tool_broker.py",
    "tests/test_approval_integration_kernel.py",
    "tests/test_m85_api_routes.py",
    "tests/test_m85_gate_integration.py",
    "tests/test_local_loopback_endpoint_policy.py",
    "tests/test_local_loopback_transport.py",
    "tests/test_local_loopback_adapter.py",
    "tests/test_local_loopback_approval.py",
    "tests/test_local_loopback_no_remote.py",
    "tests/test_local_loopback_api_routes.py",
    "tests/test_m9_gate_integration.py",
    "tests/test_manual_loopback_smoke_policy.py",
    "tests/test_manual_loopback_smoke_transport.py",
    "tests/test_manual_loopback_smoke_script.py",
    "tests/test_manual_loopback_smoke_api_routes.py",
    "tests/test_m10_gate_integration.py",
    "tests/test_remote_worker_models.py",
    "tests/test_remote_worker_registry.py",
    "tests/test_remote_worker_policy.py",
    "tests/test_remote_worker_transports.py",
    "tests/test_remote_worker_dry_run.py",
    "tests/test_remote_worker_api_routes.py",
    "tests/test_remote_worker_no_network.py",
    "tests/test_remote_worker_gate_integration.py",
]


COMMAND_MODES = {
    "full",
    "legacy-full",
    "targeted-tests",
    "verify-all",
    "report-only",
    "ci-after-verify-all",
    "ci-parallel",
}


def run_command(
    command_ref: str, command_mode: str, args: list[str], safe_summary: str
) -> FoundationGateCommandReceipt:
    print(f"\nRunning: {' '.join(args)}")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    started = time.perf_counter()
    result = subprocess.run(args, cwd=ROOT, env=env, text=True)
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    status = "PASS" if result.returncode == 0 else f"FAIL ({result.returncode})"
    print(f"Command status: {status}")
    return FoundationGateCommandReceipt(
        command_ref=command_ref,
        command_mode=command_mode,
        status="passed" if result.returncode == 0 else "failed",
        satisfied_by="direct",
        safe_summary=safe_summary,
        return_code=result.returncode,
        elapsed_ms=elapsed_ms,
    )


def external_verify_all_receipt(command_mode: str) -> FoundationGateCommandReceipt:
    return FoundationGateCommandReceipt(
        command_ref="command:scripts.verify_all",
        command_mode=command_mode,
        status="satisfied_external",
        satisfied_by="ci-master-verification",
        safe_summary=(
            "Master verification was satisfied by the preceding CI step; "
            "Foundation Gate generated the typed report only."
        ),
    )


def parallel_ci_receipt(
    command_mode: str,
    *,
    prerequisite_path: Path,
    repository_sha: str,
    base_sha: str,
) -> FoundationGateCommandReceipt:
    prerequisite: FoundationPrerequisiteManifest = (
        load_foundation_prerequisite_manifest(
            prerequisite_path,
            ROOT,
            repository_sha,
            base_sha,
        )
    )
    return FoundationGateCommandReceipt(
        command_ref="command:ci.parallel_verification",
        command_mode=command_mode,
        status="satisfied_by_exact_receipts",
        satisfied_by=prerequisite.content_ref,
        safe_summary=(
            "Lint, complete pytest, and static verification were revalidated "
            "from exact-SHA, exact-plan GitHub job receipts; Foundation Gate "
            "generated the typed report without repeating those commands."
        ),
    )


def report_only_receipt(command_mode: str) -> FoundationGateCommandReceipt:
    return FoundationGateCommandReceipt(
        command_ref="command:foundation_gate.typed_report",
        command_mode=command_mode,
        status="report_only",
        satisfied_by="typed-foundation-gate-evaluator",
        safe_summary=(
            "No external verifier commands were run. The typed Foundation Gate "
            "evaluator and latency summary still run local read/probe code; use "
            "--no-write-latest when the latest report files must not be updated."
        ),
    )


def commands_for_mode(command_mode: str) -> list[tuple[str, list[str], str]]:
    if command_mode == "full":
        return [
            (
                "command:scripts.verify_all",
                [sys.executable, "scripts/verify_all.py"],
                "Run the master verifier once; it includes Ruff, pytest, static scans, baseline, skill, and OpenAPI checks.",
            )
        ]
    if command_mode == "legacy-full":
        return [
            (
                "command:foundation_gate.targeted_tests",
                [sys.executable, "-m", "pytest", *GATE_TESTS],
                "Run targeted Foundation Gate tests.",
            ),
            (
                "command:scripts.verify_current_baseline",
                [sys.executable, "scripts/verify_current_baseline.py"],
                "Run current baseline verification.",
            ),
            (
                "command:scripts.verify_skill_package_security_rule",
                [sys.executable, "scripts/verify_skill_package_security_rule.py"],
                "Run skill package security rule verification.",
            ),
            (
                "command:scripts.verify_all",
                [sys.executable, "scripts/verify_all.py"],
                "Run the master verification suite.",
            ),
        ]
    if command_mode == "targeted-tests":
        return [
            (
                "command:foundation_gate.targeted_tests",
                [sys.executable, "-m", "pytest", *GATE_TESTS],
                "Run targeted Foundation Gate tests only.",
            )
        ]
    if command_mode == "verify-all":
        return [
            (
                "command:scripts.verify_all",
                [sys.executable, "scripts/verify_all.py"],
                "Run the master verification suite only.",
            )
        ]
    return []


def build_latency_gate_summary(
    *,
    foundation_gate_report_json: str | None,
    foundation_gate_report_md: str | None,
    write_report: bool = True,
    precomputed_foundation_gate_ms: float | None = None,
    precomputed_foundation_gate_status: str | None = None,
    precomputed_foundation_gate_result_count: int | None = None,
) -> FoundationGateLatencySummary:
    from scripts.check_foundation_gate_latency import run_latency_gate_summary

    summary = run_latency_gate_summary(
        foundation_gate_report_json=foundation_gate_report_json,
        foundation_gate_report_md=foundation_gate_report_md,
        write_report=write_report,
        precomputed_foundation_gate_ms=precomputed_foundation_gate_ms,
        precomputed_foundation_gate_status=precomputed_foundation_gate_status,
        precomputed_foundation_gate_result_count=precomputed_foundation_gate_result_count,
    )
    return FoundationGateLatencySummary.model_validate(summary)


def build_release_lane_summary() -> FoundationGateReleaseLaneSummary:
    from scripts.verify_release_lanes import build_release_lane_manifest

    manifest = build_release_lane_manifest()
    summary = {
        "schema_version": manifest["schema_version"],
        "task_ref": manifest["task_ref"],
        "overall_status": manifest["overall_status"],
        "definition_status": manifest["definition_status"],
        "command_execution_status": manifest["command_execution_status"],
        "lane_count": manifest["lane_count"],
        "lane_ids": [lane["lane_id"] for lane in manifest["lanes"]],
        "status_semantics": manifest["status_semantics"],
        "accepted_failures": manifest["accepted_failures"],
        "validation_failures": manifest["validation_failures"],
        "report_safety": manifest["report_safety"],
        "safe_summary": manifest["safe_summary"],
    }
    return FoundationGateReleaseLaneSummary.model_validate(summary)


def write_markdown_payload(payload: dict, markdown_path: Path) -> None:
    lines = [
        "# Foundation Gate Report",
        "",
        f"- Report: `{payload['report_id']}`",
        f"- Version: `{payload['version']}`",
        f"- Overall status: `{payload['overall_status']}`",
        f"- Summary: {payload['summary']}",
        f"- Next action: {payload['next_recommended_action']}",
        f"- Command mode: `{payload.get('command_mode') or 'none'}`",
        "",
        "## Command Receipts",
        "",
    ]
    if payload.get("command_receipts"):
        for receipt in payload["command_receipts"]:
            lines.append(
                f"- `{receipt['command_ref']}`: `{receipt['status']}` "
                f"via `{receipt['satisfied_by']}` - {receipt['safe_summary']}"
            )
    else:
        lines.append("- No command receipts recorded.")
    latency_gate = payload.get("latency_gate")
    if latency_gate:
        lines.extend(
            [
                "",
                "## Latency Gate",
                "",
                f"- Status: `{latency_gate['status']}`",
                f"- p50/p95 status: `{latency_gate['p50_p95_status']}`",
                f"- Release latency: `{latency_gate['release_latency_status']}`",
                f"- Hot-path profile: `{latency_gate['hot_path_profile_status']}`",
                (
                    "- Foundation Gate latency: "
                    f"best `{latency_gate['foundation_gate_best_ms']}` ms "
                    f"(budget `{latency_gate['foundation_gate_best_budget_ms']}` ms), "
                    f"mean `{latency_gate['foundation_gate_mean_ms']}` ms "
                    f"(budget `{latency_gate['foundation_gate_mean_budget_ms']}` ms)"
                ),
            ]
        )
        if latency_gate.get("foundation_gate_report_json"):
            lines.append(
                f"- Report path: `{latency_gate['foundation_gate_report_json']}`"
            )
        accepted_failures = latency_gate.get("accepted_failures", [])
        lines.append(f"- Accepted failures: `{len(accepted_failures)}`")
        optional_prerequisites = latency_gate.get("optional_prerequisites", [])
        if optional_prerequisites:
            lines.extend(["", "### Optional Prerequisites", ""])
            for result in optional_prerequisites:
                reason_codes = ", ".join(result.get("reason_codes", [])) or "none"
                lines.append(
                    f"- `{result['safe_label']}`: `{result['status']}` ({reason_codes})"
                )
        lines.extend(["", "### Latency Path Results", ""])
        for result in latency_gate.get("path_results", []):
            p95 = result["p95_ms"] if result["p95_ms"] is not None else "not measured"
            p50 = result["p50_ms"] if result["p50_ms"] is not None else "not measured"
            lines.append(
                f"- `{result['safe_label']}`: `{result['status']}` "
                f"p50 `{p50}` ms, p95 `{p95}` ms, budget "
                f"`{result['budget_ms']}` ms, `{result['budget_status']}`"
            )
        if latency_gate.get("failures"):
            lines.extend(["", "### Latency Failures", ""])
            for failure in latency_gate["failures"]:
                lines.append(f"- {failure}")
    release_lanes = payload.get("release_verification_lanes")
    if release_lanes:
        lines.extend(
            [
                "",
                "## Release Verification Lanes",
                "",
                f"- Manifest status: `{release_lanes['overall_status']}`",
                f"- Definition status: `{release_lanes['definition_status']}`",
                f"- Command execution status: `{release_lanes['command_execution_status']}`",
                f"- Lane count: `{release_lanes['lane_count']}`",
                f"- Accepted failures: `{len(release_lanes.get('accepted_failures', []))}`",
                f"- Validation failures: `{len(release_lanes.get('validation_failures', []))}`",
                "- Lanes: "
                + ", ".join(
                    f"`{lane_id}`" for lane_id in release_lanes.get("lane_ids", [])
                ),
            ]
        )
        lines.extend(["", "### Lane Status Semantics", ""])
        for status, meaning in release_lanes.get("status_semantics", {}).items():
            lines.append(f"- `{status}`: {meaning}")
    lines.extend(
        [
            "",
            "## Criteria",
            "",
        ]
    )
    for result in payload["results"]:
        lines.append(
            f"- `{result['criterion_id']}`: `{result['status']}` - {result['safe_message']}"
        )
    write_text_atomic(markdown_path, "\n".join(lines) + "\n")


def write_text_atomic(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def write_json_atomic(path: Path, payload: str) -> None:
    if not payload.strip():
        raise ValueError("Foundation Gate JSON report payload must not be empty.")
    json.loads(payload)
    write_text_atomic(path, payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run M6 Foundation Gate checks.")
    parser.add_argument(
        "--command-mode",
        choices=sorted(COMMAND_MODES),
        default="full",
        help=(
            "Command mode. full runs the master verifier once; legacy-full preserves the old targeted+baseline+skill+verify_all sequence; "
            "report-only skips external verifier commands but still runs local typed evaluator/probe summaries; ci-after-verify-all records an external CI verification receipt; "
            "ci-parallel records verification satisfied by required parallel CI jobs."
        ),
    )
    parser.add_argument(
        "--skip-commands",
        action="store_true",
        help="Legacy alias for --command-mode report-only.",
    )
    parser.add_argument(
        "--no-write-latest",
        action="store_true",
        help="Do not update reports/foundation_gate/latest_* files.",
    )
    parser.add_argument(
        "--output", help="Optional path for an additional JSON report copy."
    )
    parser.add_argument("--ci-prerequisite-manifest")
    parser.add_argument("--ci-prerequisite-sha")
    parser.add_argument("--ci-prerequisite-base-sha")
    parser.add_argument(
        "--require-clean-revision",
        action="store_true",
        help=(
            "Fail unless the report can bind one clean exact Git revision. "
            "TAW-08 receipt issuance always enforces this independently."
        ),
    )
    args = parser.parse_args(argv)

    command_mode = "report-only" if args.skip_commands else args.command_mode
    prerequisite_values = (
        args.ci_prerequisite_manifest,
        args.ci_prerequisite_sha,
        args.ci_prerequisite_base_sha,
    )
    if command_mode == "ci-parallel" and not all(prerequisite_values):
        parser.error(
            "ci-parallel requires an exact prerequisite manifest and repository SHA"
        )
    if command_mode != "ci-parallel" and any(prerequisite_values):
        parser.error("CI prerequisite evidence is limited to ci-parallel mode")
    command_failures = []
    command_receipts: list[FoundationGateCommandReceipt] = []
    if command_mode == "ci-after-verify-all":
        command_receipts.append(external_verify_all_receipt(command_mode))
    elif command_mode == "ci-parallel":
        command_receipts.append(
            parallel_ci_receipt(
                command_mode,
                prerequisite_path=Path(args.ci_prerequisite_manifest),
                repository_sha=args.ci_prerequisite_sha,
                base_sha=args.ci_prerequisite_base_sha,
            )
        )
    elif command_mode == "report-only":
        command_receipts.append(report_only_receipt(command_mode))
    for command_ref, command, safe_summary in commands_for_mode(command_mode):
        receipt = run_command(command_ref, command_mode, command, safe_summary)
        command_receipts.append(receipt)
        if receipt.return_code != 0:
            command_failures.append(command_ref)

    foundation_gate_started = time.perf_counter()
    _evaluated_revision_ref, report = evaluate_foundation_gate_for_repository_state(
        ROOT,
        require_clean_revision=args.require_clean_revision,
    )
    foundation_gate_elapsed_ms = round(
        (time.perf_counter() - foundation_gate_started) * 1000,
        2,
    )
    report = report.model_copy(
        update={
            "command_mode": command_mode,
            "command_receipts": command_receipts,
        }
    )
    output_dir = ROOT / "reports" / "foundation_gate"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "latest_foundation_gate_report.json"
    markdown_path = output_dir / "latest_foundation_gate_report.md"
    latency_gate = build_latency_gate_summary(
        foundation_gate_report_json=None
        if args.no_write_latest
        else str(report_path.relative_to(ROOT)),
        foundation_gate_report_md=None
        if args.no_write_latest
        else str(markdown_path.relative_to(ROOT)),
        precomputed_foundation_gate_ms=foundation_gate_elapsed_ms,
        precomputed_foundation_gate_status=str(report.overall_status),
        precomputed_foundation_gate_result_count=len(report.results),
        write_report=not args.no_write_latest,
    )
    report = report.model_copy(
        update={
            "latency_gate": latency_gate,
            "release_verification_lanes": build_release_lane_summary(),
        }
    )
    report_payload = report.model_dump_json(indent=2)
    report_payload_dict = json.loads(report_payload)
    if not args.no_write_latest:
        write_json_atomic(report_path, report_payload)
        write_markdown_payload(report_payload_dict, markdown_path)
    requested_output_path = None
    if args.output:
        requested_output_path = Path(args.output)
        if not requested_output_path.is_absolute():
            requested_output_path = ROOT / requested_output_path
        requested_output_path.parent.mkdir(parents=True, exist_ok=True)
        write_json_atomic(requested_output_path, report_payload)

    print("\n=== Foundation Gate Summary ===")
    print(f"Command mode: {command_mode}")
    if args.no_write_latest:
        print("Report: latest report update skipped")
        print("Markdown: latest markdown update skipped")
    else:
        print(f"Report: {report_path.relative_to(ROOT)}")
        print(f"Markdown: {markdown_path.relative_to(ROOT)}")
    if requested_output_path:
        print("Requested output: custom report copy written")
    print(f"Overall status: {report.overall_status}")
    print(report.summary)
    if report.latency_gate is not None:
        print(f"Latency gate: {report.latency_gate.status}")
        print(f"Latency p50/p95 status: {report.latency_gate.p50_p95_status}")
    if report.release_verification_lanes is not None:
        print(
            f"Release lane definitions: {report.release_verification_lanes.definition_status}"
        )
        print(
            "Release lane command execution: "
            f"{report.release_verification_lanes.command_execution_status}"
        )
        print(f"Release lane count: {report.release_verification_lanes.lane_count}")

    if command_failures:
        print("\nCommand failures:")
        for failure in command_failures:
            print(f"- {failure}")
        return 1

    if report.overall_status != FoundationGateStatus.passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
