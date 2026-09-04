from __future__ import annotations

import base64
import csv
import ctypes
import hashlib
import importlib.metadata as importlib_metadata
import io
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
import urllib.parse
import zipfile
from collections import defaultdict, deque
from ctypes import wintypes
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
_LOCKED_CHILD_REVISION_ENV = "UAA_TAW08_LOCKED_CHILD_REVISION"
_ENVIRONMENT_ROOT_ENV = "UAA_TAW08_ENVIRONMENT_ROOT"
_LOCKED_WHEELHOUSE_ENV = "UAA_TAW08_LOCKED_WHEELHOUSE"
_PREFLIGHT_COMPLETE_ENV = "UAA_TAW08_PREFLIGHT_COMPLETE"
_PREFLIGHT_DIGEST_ENV = "UAA_TAW08_PREFLIGHT_DIGEST"
_EXPORT_FOUNDER_INPUTS_ENV = "UAA_TAW08_EXPORT_FOUNDER_INPUTS"

if (
    os.environ.get(_EXPORT_FOUNDER_INPUTS_ENV) == "1"
    and not os.environ.get(_LOCKED_CHILD_REVISION_ENV)
    and not (
        sys.flags.isolated
        and sys.flags.no_site
        and sys.flags.dont_write_bytecode
        and os.environ.get(_PREFLIGHT_COMPLETE_ENV) == "1"
    )
):
    raise RuntimeError(
        "TAW-08 founder input export requires the isolated locked preflight"
    )

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib

from packaging.markers import InvalidMarker, Marker, default_environment  # noqa: E402
from packaging.requirements import InvalidRequirement, Requirement  # noqa: E402
from packaging.tags import sys_tags  # noqa: E402
from packaging.utils import canonicalize_name, parse_wheel_filename  # noqa: E402
from packaging.version import InvalidVersion, Version  # noqa: E402

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
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.evals.tool_aware_acceptance import (  # noqa: E402
    TAW08_ALLOWED_EVIDENCE_ONLY_PATH_REFS,
    TAW08_DELTA_VERIFICATION_MISSING_REF,
    TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF,
    TAW08_FINAL_PUBLICATION_MISSING_REF,
    TAW08_FOUNDATION_GATE_SOURCE_PREFIX,
    TAW08_FOUNDER_EVIDENCE_MISSING_REFS,
    TAW08_POSTMERGE_EVIDENCE_MISSING_REF,
    TAW08AcceptanceStatus,
    TAW08AcceptanceReport,
    TAW08_REQUIRED_ACCEPTANCE_PATH_REFS,
    TAW08_REPOSITORY_VERIFIER_PATH_REF,
    TAW08_UNRESOLVED_DYNAMIC_IMPORT_PATH_REFS,
    _CandidateLockVerificationReceipt,
    _EvaluatorEnvironmentReceipt,
    EvidenceOnlyDeltaManifest,
    _EvidenceOnlyDeltaVerificationReceipt,
    _FinalAcceptancePublicationReceipt,
    FoundationGateReceipt,
    _PublicationHistoryCensus,
    RevisionDeltaCensus,
    RevisionPathCensus,
    bind_revision_delta_census,
    bind_revision_path_census,
    evaluate_taw08_acceptance,
    _bind_candidate_lock_verification_receipt,
    _verify_and_bind_evidence_only_delta,
    _bind_publication_history_census,
    _bind_evaluator_environment_receipt,
    _verify_and_bind_final_acceptance_publication,
    _verify_and_bind_foundation_gate_report,
)
from ultimate_ai_agent.core.evals.tool_aware_baseline import (  # noqa: E402
    CandidateLock,
    CandidateManifestEntry,
    SourceDependencyClosure,
    SourceDependencyEntry,
    SourceProjection,
    canonical_digest,
    derive_local_python_dependencies,
    durable_payload_has_forbidden_fields,
    verify_candidate_lock,
)
from ultimate_ai_agent.core.gate.reports import (  # noqa: E402
    FoundationGateCommandReceipt,
    FoundationGateReport,
)


SLICE_CANDIDATE_PATHS = tuple(
    sorted(
        {
            *(
                ref.removeprefix("repo-path-ref:")
                for ref in TAW08_REQUIRED_ACCEPTANCE_PATH_REFS
            ),
            "docs/evals/TOOL_AWARE_COGNITION_TAW08_ACCEPTANCE.md",
            "docs/evals/TOOL_AWARE_COGNITION_TAW08_EVIDENCE_PHASE_DRIVER.md",
            "docs/DOCUMENTATION_INDEX.md",
            "scripts/verify_taw08_environment_preflight.py",
            "scripts/verify_tool_aware_cognition_taw08.py",
            "src/ultimate_ai_agent/core/evals/__init__.py",
            "tests/test_tool_aware_cognition_taw08.py",
            "tests/test_tool_aware_cognition_taw08_evidence_phases.py",
            "tests/test_m164_llama_cpp_gateway.py",
        }
    )
)
EVIDENCE_ONLY_DELTA_PATHS = tuple(
    path_ref.removeprefix("repo-path-ref:")
    for path_ref in TAW08_ALLOWED_EVIDENCE_ONLY_PATH_REFS
)

_WINDOWS_GIT_TRUST_SCRIPT = (
    "$ErrorActionPreference='Stop';"
    "$p=(Get-Item -LiteralPath $args[0] -Force).FullName;"
    "$roots=@("
    "[Environment]::GetFolderPath([Environment+SpecialFolder]::ProgramFiles),"
    "[Environment]::GetFolderPath([Environment+SpecialFolder]::ProgramFilesX86)"
    ")|Where-Object{$_};"
    "$root=$roots|Where-Object{"
    "$prefix=$_.TrimEnd([IO.Path]::DirectorySeparatorChar)+"
    "[IO.Path]::DirectorySeparatorChar;"
    "$p.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)"
    "}|Select-Object -First 1;"
    "if(-not $root){exit 11};"
    "$trusted=@('S-1-5-18','S-1-5-32-544',"
    "'S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464');"
    "$writeMask=([int64][Security.AccessControl.FileSystemRights]::Write -bor "
    "[int64][Security.AccessControl.FileSystemRights]::Delete -bor "
    "[int64][Security.AccessControl.FileSystemRights]::ChangePermissions -bor "
    "[int64][Security.AccessControl.FileSystemRights]::TakeOwnership -bor "
    "[int64][Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles);"
    "$q=Get-Item -LiteralPath $p -Force;"
    "while($true){"
    "$acl=Get-Acl -LiteralPath $q.FullName;"
    "$owner=$acl.GetOwner([Security.Principal.SecurityIdentifier]).Value;"
    "if($trusted -notcontains $owner){exit 12};"
    "$rules=$acl.GetAccessRules($true,$true,"
    "[Security.Principal.SecurityIdentifier]);"
    "foreach($ace in $rules){"
    "$applies=($ace.PropagationFlags -band "
    "[Security.AccessControl.PropagationFlags]::InheritOnly) -eq 0;"
    "$writes=([int64]$ace.FileSystemRights -band $writeMask) -ne 0;"
    "if($applies -and $writes -and "
    "$ace.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow "
    "-and $trusted -notcontains $ace.IdentityReference.Value){exit 13}"
    "};"
    "if([string]::Equals($q.FullName,$root,"
    "[StringComparison]::OrdinalIgnoreCase)){break};"
    "$q=$q.Parent;if($null -eq $q){exit 14}"
    "};"
    "$s=Get-AuthenticodeSignature -LiteralPath $p;"
    "if($s.Status.ToString() -ne 'Valid' -or $null -eq $s.SignerCertificate){"
    "exit 15};"
    "$chain=New-Object Security.Cryptography.X509Certificates.X509Chain;"
    "$chain.ChainPolicy.RevocationMode="
    "[Security.Cryptography.X509Certificates.X509RevocationMode]::NoCheck;"
    "$chain.ChainPolicy.VerificationFlags="
    "[Security.Cryptography.X509Certificates.X509VerificationFlags]::NoFlag;"
    "if(-not $chain.Build($s.SignerCertificate) -or "
    "$chain.ChainElements.Count -lt 1){exit 16};"
    "$signer=$s.SignerCertificate.Thumbprint.ToUpperInvariant();"
    "$anchor=$chain.ChainElements[$chain.ChainElements.Count-1].Certificate."
    "Thumbprint.ToUpperInvariant();"
    "$machineRoots=@(Get-ChildItem -Path Cert:\\LocalMachine\\Root|"
    "ForEach-Object{$_.Thumbprint.ToUpperInvariant()});"
    "if($machineRoots -notcontains $anchor){exit 17};"
    "Write-Output ($signer+' '+$anchor)"
)


def _validate_posix_admin_path(path: Path) -> None:
    for component in (path, *path.parents):
        try:
            metadata = component.stat()
        except OSError as exc:
            raise RuntimeError(
                "TAW-08 Git executable lacks trusted provenance"
            ) from exc
        if metadata.st_uid != 0 or metadata.st_mode & 0o022:
            raise RuntimeError("TAW-08 Git executable lacks trusted provenance")


def _validated_windows_system_root() -> Path:
    if os.name != "nt":
        raise RuntimeError("TAW-08 Windows system root is unavailable")
    value = os.environ.get("SystemRoot")
    if not value or len(value) > 260 or "\x00" in value:
        raise RuntimeError("TAW-08 Windows system root is unavailable")
    try:
        buffer = ctypes.create_unicode_buffer(32_768)
        length = ctypes.windll.kernel32.GetWindowsDirectoryW(  # type: ignore[attr-defined]
            buffer,
            len(buffer),
        )
        configured = Path(value).resolve(strict=True)
        authoritative = Path(buffer.value).resolve(strict=True)
    except (AttributeError, OSError) as exc:
        raise RuntimeError("TAW-08 Windows system root is unavailable") from exc
    if length <= 0 or length >= len(buffer) or configured != authoritative:
        raise RuntimeError("TAW-08 Windows system root is unavailable")
    return authoritative


def _validated_windows_git_provenance(
    executable: Path,
    powershell: Path,
) -> tuple[str, str]:
    signature = subprocess.run(
        [
            str(powershell),
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            _WINDOWS_GIT_TRUST_SCRIPT,
            str(executable),
        ],
        check=False,
        capture_output=True,
        timeout=30,
    )
    try:
        output = signature.stdout.decode("ascii", errors="strict").strip().split()
    except UnicodeDecodeError as exc:
        raise RuntimeError("TAW-08 Git executable lacks trusted provenance") from exc
    if (
        signature.returncode != 0
        or len(output) != 2
        or any(re.fullmatch(r"[0-9A-F]{40,64}", value) is None for value in output)
    ):
        raise RuntimeError("TAW-08 Git executable lacks trusted provenance")
    return output[0].lower(), output[1].lower()


@lru_cache(maxsize=1)
def _trusted_git_identity() -> tuple[Path, str, str]:
    """Resolve Git only across an OS-admin trust boundary and bind its bytes."""

    system = platform.system().strip().lower()
    executable_value = (
        "/usr/bin/git"
        if os.name == "posix" and system == "darwin"
        else shutil.which("git")
    )
    if not executable_value:
        raise RuntimeError("TAW-08 trusted Git executable is unavailable")
    executable = Path(executable_value)
    try:
        resolved = executable.resolve(strict=True)
        content = resolved.read_bytes()
    except OSError as exc:
        raise RuntimeError("TAW-08 trusted Git executable is unavailable") from exc
    if not resolved.is_file() or not content or len(content) > 256 * 1024 * 1024:
        raise RuntimeError("TAW-08 trusted Git executable is invalid")
    if os.name == "posix":
        _validate_posix_admin_path(resolved)
        if system == "darwin":
            if resolved != Path("/usr/bin/git"):
                raise RuntimeError("TAW-08 Git executable lacks trusted provenance")
            signature = subprocess.run(
                [
                    "/usr/bin/codesign",
                    "--verify",
                    "--strict",
                    "-R=anchor apple",
                    str(resolved),
                ],
                check=False,
                capture_output=True,
                timeout=30,
            )
            if signature.returncode != 0:
                raise RuntimeError("TAW-08 Git executable lacks trusted provenance")
            provenance_ref = "git-provenance-ref:apple-platform-signed"
        else:
            provenance_ref = "git-provenance-ref:posix-root-owned-nonwritable"
    elif os.name == "nt":
        system_root = _validated_windows_system_root()
        powershell = (
            system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
        )
        signer, anchor = _validated_windows_git_provenance(resolved, powershell)
        provenance_ref = (
            f"git-provenance-ref:windows-machine-authenticode:{signer}:{anchor}"
        )
    else:
        raise RuntimeError("TAW-08 Git executable platform is unsupported")
    return (
        resolved,
        "sha256:" + hashlib.sha256(content).hexdigest(),
        provenance_ref,
    )


def _git(
    *args: str,
    repository_root: Path = ROOT,
    input_bytes: bytes | None = None,
    extra_config: tuple[str, ...] = (),
) -> bytes:
    executable, _digest_ref, _provenance_ref = _trusted_git_identity()
    result = subprocess.run(
        [
            str(executable),
            "--no-replace-objects",
            *_GIT_READ_CONFIG,
            "-c",
            f"core.worktree={repository_root.resolve()}",
            f"--work-tree={repository_root.resolve()}",
            *extra_config,
            *args,
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        env=_sanitized_git_environment(),
        input=input_bytes,
    )
    return result.stdout


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


def _fresh_exact_repository_revision(repository_root: Path) -> str:
    """Obtain clean revision proof in an isolated, no-site Python process."""

    completed = subprocess.run(
        (
            sys.executable,
            "-I",
            "-B",
            "-S",
            str(repository_root / "scripts/run_foundation_gate.py"),
            "--preimport-revision-probe",
        ),
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
        env=_sanitized_git_environment(),
        timeout=180,
    )
    revision_ref = completed.stdout.strip()
    if (
        completed.returncode != 0
        or len(completed.stdout) > 128
        or not re.fullmatch(r"git-sha:[0-9a-f]{40}", revision_ref)
    ):
        raise RuntimeError("TAW-08 fresh Foundation revision probe failed")
    return revision_ref


def _load_candidate_foundation_source_for_census(
    *,
    repository_root: Path,
    revision: str,
) -> None:
    """Execute the exact tracked Foundation source without consulting bytecode."""

    module_name = "_uaa_taw08_verified_foundation_gate"
    source_path = repository_root / "scripts/run_foundation_gate.py"
    expected = _git(
        "show",
        f"{revision}:scripts/run_foundation_gate.py",
        repository_root=repository_root,
    )
    try:
        metadata = source_path.lstat()
        actual = source_path.read_bytes()
    except OSError as exc:
        raise RuntimeError("TAW-08 Foundation source is unavailable") from exc
    if (
        not stat.S_ISREG(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
        or actual != expected
    ):
        raise RuntimeError("TAW-08 Foundation source differs from the candidate")
    existing = sys.modules.get(module_name)
    if existing is not None:
        if getattr(existing, "__file__", None) != str(source_path):
            raise RuntimeError("TAW-08 Foundation source module is ambiguous")
        return
    module = ModuleType(module_name)
    module.__file__ = str(source_path)
    module.__package__ = "scripts"
    sys.modules[module_name] = module
    try:
        exec(
            compile(expected, str(source_path), "exec", dont_inherit=True),
            module.__dict__,
        )
    except BaseException:
        sys.modules.pop(module_name, None)
        raise


def _evaluate_foundation_gate_in_fresh_process(
    repository_root: Path,
) -> tuple[str, FoundationGateReport]:
    """Evaluate Foundation Gate beyond the repository pre-import boundary."""

    temporary, temporary_root = _prepare_private_temporary_directory(
        prefix="uaa-taw08-foundation-",
        repository_root=repository_root,
    )
    try:
        output_path = temporary_root / "foundation-gate.json"
        completed = subprocess.run(
            (
                sys.executable,
                "-I",
                "-B",
                "-S",
                str(repository_root / "scripts/run_foundation_gate.py"),
                "--command-mode",
                "report-only",
                "--no-write-latest",
                "--require-clean-revision",
                "--output",
                str(output_path),
            ),
            cwd=repository_root,
            check=False,
            capture_output=True,
            env=_sanitized_git_environment(),
            timeout=900,
        )
        payload = _read_private_regular_file(
            output_path,
            maximum=16 * 1024 * 1024,
        )
        if completed.returncode != 0 or not payload:
            raise RuntimeError("TAW-08 fresh Foundation evaluation failed")
        try:
            report = FoundationGateReport.model_validate_json(payload)
        except (UnicodeDecodeError, ValueError) as exc:
            raise RuntimeError("TAW-08 fresh Foundation report is invalid") from exc
    finally:
        temporary.cleanup()
    revision_ref = report.evaluated_revision_ref
    if not isinstance(revision_ref, str) or not re.fullmatch(
        r"git-sha:[0-9a-f]{40}", revision_ref
    ):
        raise RuntimeError("TAW-08 fresh Foundation revision binding is invalid")
    return revision_ref, report


def _report_only_receipt() -> FoundationGateCommandReceipt:
    return FoundationGateCommandReceipt(
        command_ref="command:foundation_gate.typed_report",
        command_mode="report-only",
        status="report_only",
        satisfied_by="typed-foundation-gate-evaluator",
        safe_summary=(
            "No external verifier commands were run. The typed Foundation Gate "
            "evaluator and latency summary still run local read/probe code; use "
            "--no-write-latest when the latest report files must not be updated."
        ),
    )


def _require_no_repository_git_filters(*, repository_root: Path = ROOT) -> None:
    """Reject repository controls that can execute or mask content filters."""

    config_names = _git(
        "config",
        "--includes",
        "--null",
        "--name-only",
        "--list",
        repository_root=repository_root,
    )
    if len(config_names) > 16 * 1024 * 1024:
        raise RuntimeError("TAW-08 repository Git filter configuration is invalid")
    if config_names and not config_names.endswith(b"\0"):
        raise RuntimeError("TAW-08 repository Git filter configuration is invalid")
    if any(
        name.lower().startswith(b"filter.")
        for name in config_names.rstrip(b"\0").split(b"\0")
        if name
    ):
        raise RuntimeError("TAW-08 repository Git filters are not permitted")

    tracked_paths = _git("ls-files", "-z", repository_root=repository_root)
    if len(tracked_paths) > 16 * 1024 * 1024 or (
        tracked_paths and not tracked_paths.endswith(b"\0")
    ):
        raise RuntimeError("TAW-08 repository Git path census is invalid")
    paths = tracked_paths.rstrip(b"\0").split(b"\0") if tracked_paths else []
    if len(paths) > 20_000 or any(not path for path in paths):
        raise RuntimeError("TAW-08 repository Git path census is invalid")
    # The raw tree/index/worktree comparison has already established that the
    # index is exactly HEAD.  ``--cached`` therefore checks the same committed
    # attributes without relying on ``check-attr --source``, which is absent
    # from the supported Git 2.39 runtime on hosted macOS.
    for source_args in ((), ("--cached",)):
        attributes = _git(
            "check-attr",
            "-z",
            "--stdin",
            *source_args,
            "filter",
            repository_root=repository_root,
            input_bytes=tracked_paths,
        )
        if len(attributes) > 16 * 1024 * 1024 or (
            attributes and not attributes.endswith(b"\0")
        ):
            raise RuntimeError("TAW-08 repository Git filter attributes are invalid")
        records = attributes.rstrip(b"\0").split(b"\0") if attributes else []
        if len(records) != len(paths) * 3:
            raise RuntimeError("TAW-08 repository Git filter attributes are invalid")
        for index, path in enumerate(paths):
            actual_path, attribute, value = records[index * 3 : index * 3 + 3]
            if actual_path != path or attribute != b"filter":
                raise RuntimeError(
                    "TAW-08 repository Git filter attributes are invalid"
                )
            if value not in {b"unspecified", b"unset"}:
                raise RuntimeError("TAW-08 repository Git filters are not permitted")


def _index_has_hidden_worktree_entries(*, repository_root: Path = ROOT) -> bool:
    entries = _git(
        "ls-files",
        "-v",
        "-z",
        repository_root=repository_root,
    ).split(b"\0")
    return any(
        entry
        and (entry[:1] in {b"S", b"s"} or (entry[:1].isalpha() and entry[:1].islower()))
        for entry in entries
    )


def verify_executing_repository_sources(
    revision: str,
    *,
    repository_root: Path = ROOT,
    source_root: Path = ROOT,
) -> tuple[tuple[str, ...], str]:
    """Bind every loaded repository Python source to the candidate Git tree."""

    current_revision = (
        _git(
            "rev-parse",
            "HEAD",
            repository_root=repository_root,
        )
        .decode("ascii")
        .strip()
    )
    if revision != current_revision:
        raise RuntimeError(
            "TAW-08 executing repository source differs from the candidate"
        )
    resolved_source_root = source_root.resolve()
    source_paths: dict[str, Path] = {}
    for module in tuple(sys.modules.values()):
        module_file = getattr(module, "__file__", None)
        if not isinstance(module_file, str):
            continue
        try:
            source_path = Path(module_file).resolve()
        except OSError:
            continue
        if source_path.suffix != ".py" or not source_path.is_relative_to(
            resolved_source_root
        ):
            continue
        relative_path = source_path.relative_to(resolved_source_root).as_posix()
        if relative_path.startswith((".venv/", ".ci-bootstrap/")):
            continue
        existing = source_paths.get(relative_path)
        if existing is not None and existing != source_path:
            raise RuntimeError("TAW-08 executing repository source census is invalid")
        source_paths[relative_path] = source_path
    tree_entries: dict[str, str] = {}
    for line in (
        _git(
            "ls-tree",
            "-r",
            revision,
            repository_root=repository_root,
        )
        .decode("utf-8")
        .splitlines()
    ):
        metadata, separator, path = line.partition("\t")
        parts = metadata.split()
        if separator and len(parts) == 3 and parts[1] == "blob":
            tree_entries[path] = parts[2]
    if not set(source_paths) <= set(tree_entries):
        raise RuntimeError("TAW-08 executing repository source census is incomplete")
    for path, source_path in source_paths.items():
        if source_path.read_bytes() != _git(
            "show",
            f"{revision}:{path}",
            repository_root=repository_root,
        ):
            raise RuntimeError(
                "TAW-08 executing repository source differs from the candidate"
            )
    sources = {
        f"repo-path-ref:{path}": f"git-blob-ref:{tree_entries[path]}"
        for path in source_paths
    }
    required = {
        TAW08_REPOSITORY_VERIFIER_PATH_REF,
        "repo-path-ref:scripts/run_foundation_gate.py",
        "repo-path-ref:src/ultimate_ai_agent/core/evals/tool_aware_acceptance.py",
    }
    if not required <= set(sources):
        raise RuntimeError("TAW-08 executing repository source census is incomplete")
    path_refs = tuple(sorted(sources))
    return path_refs, canonical_digest(
        {path_ref: sources[path_ref] for path_ref in path_refs}
    )


def _verify_preflight_execution(*, repository_root: Path) -> None:
    preflight = repository_root / "scripts/verify_taw08_environment_preflight.py"
    try:
        expected_digest = "sha256:" + hashlib.sha256(preflight.read_bytes()).hexdigest()
    except OSError as exc:
        raise RuntimeError("TAW-08 evaluator preflight source is unavailable") from exc
    if (
        not sys.flags.isolated
        or not sys.flags.no_site
        or os.environ.get(_PREFLIGHT_COMPLETE_ENV) != "1"
        or os.environ.get(_PREFLIGHT_DIGEST_ENV) != expected_digest
    ):
        raise RuntimeError("TAW-08 evaluator preflight binding is invalid")


def _venv_scripts_directory(platform_name: str = os.name) -> str:
    return "Scripts" if platform_name == "nt" else "bin"


def _python_runtime_identity(
    *,
    executable: Path | None = None,
    standard_library_root: Path | None = None,
) -> tuple[str, int, str]:
    """Bind the exact CPython executable and non-package standard library."""

    executable = (executable or Path(sys.executable)).resolve()
    standard_library_root = (
        standard_library_root or Path(sysconfig.get_path("stdlib"))
    ).resolve()
    try:
        executable_content = executable.read_bytes()
    except OSError as exc:
        raise RuntimeError("TAW-08 CPython executable is unavailable") from exc
    if (
        not executable.is_file()
        or not executable_content
        or len(executable_content) > 256 * 1024 * 1024
        or not standard_library_root.is_dir()
    ):
        raise RuntimeError("TAW-08 CPython runtime census is invalid")
    identities: list[tuple[str, int, str]] = []
    total_bytes = 0
    for path in sorted(standard_library_root.rglob("*")):
        relative = path.relative_to(standard_library_root)
        if "site-packages" in relative.parts:
            continue
        if path.is_dir() and not path.is_symlink():
            continue
        try:
            resolved = path.resolve(strict=True)
            if not resolved.is_file():
                raise OSError
            content = path.read_bytes()
        except OSError as exc:
            raise RuntimeError("TAW-08 CPython runtime census is invalid") from exc
        total_bytes += len(content)
        if (
            len(identities) >= 100_000
            or len(content) > 256 * 1024 * 1024
            or total_bytes > 4 * 1024 * 1024 * 1024
        ):
            raise RuntimeError("TAW-08 CPython runtime census bound exceeded")
        identities.append(
            (
                relative.as_posix(),
                len(content),
                hashlib.sha256(content).hexdigest(),
            )
        )
    if not identities:
        raise RuntimeError("TAW-08 CPython runtime census is invalid")
    return (
        "sha256:" + hashlib.sha256(executable_content).hexdigest(),
        len(identities),
        canonical_digest({"standard_library_files": tuple(identities)}),
    )


def _installed_distribution_content_identity(
    distribution: importlib_metadata.Distribution,
    *,
    environment_root: Path,
) -> tuple[tuple[str, int, str], ...]:
    files = distribution.files
    if not files or len(files) > 100_000:
        raise RuntimeError("TAW-08 evaluator distribution file census is invalid")
    environment_root = environment_root.resolve()
    total_bytes = 0
    identities: list[tuple[str, int, str]] = []
    for entry in sorted(files, key=str):
        entry_ref = str(entry)
        if (
            not entry_ref
            or len(entry_ref) > 1024
            or any(character in entry_ref for character in ("\x00", "\n", "\r"))
        ):
            raise RuntimeError("TAW-08 evaluator distribution file census is invalid")
        path = Path(distribution.locate_file(entry)).resolve()
        if not path.is_relative_to(environment_root) or not path.is_file():
            raise RuntimeError("TAW-08 evaluator distribution file is unavailable")
        content = path.read_bytes()
        total_bytes += len(content)
        if len(content) > 64 * 1024 * 1024 or total_bytes > 1024 * 1024 * 1024:
            raise RuntimeError("TAW-08 evaluator distribution content bound exceeded")
        if entry.size is not None and entry.size != len(content):
            raise RuntimeError("TAW-08 evaluator distribution size differs from RECORD")
        if entry.hash is not None:
            if entry.hash.mode != "sha256":
                raise RuntimeError("TAW-08 evaluator distribution hash mode is invalid")
            actual_record_hash = (
                base64.urlsafe_b64encode(hashlib.sha256(content).digest())
                .rstrip(b"=")
                .decode("ascii")
            )
            if actual_record_hash != entry.hash.value:
                raise RuntimeError(
                    "TAW-08 evaluator distribution content differs from RECORD"
                )
        identities.append(
            (entry_ref, len(content), hashlib.sha256(content).hexdigest())
        )
    return tuple(identities)


def _locked_wheel_distribution_identity(
    *,
    name: str,
    version: str,
    locked_wheels: list[object],
    installed_identity: tuple[tuple[str, int, str], ...],
) -> tuple[str, tuple[tuple[str, int, str], ...]]:
    allowed_wheels: dict[str, tuple[str, int]] = {}
    for item in locked_wheels:
        if not isinstance(item, dict):
            raise RuntimeError("TAW-08 locked wheel census is invalid")
        url = item.get("url")
        digest_ref = item.get("hash")
        size = item.get("size")
        if (
            not isinstance(url, str)
            or not isinstance(digest_ref, str)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest_ref)
            or not isinstance(size, int)
            or size <= 0
        ):
            raise RuntimeError("TAW-08 locked wheel census is invalid")
        filename = url.rsplit("/", 1)[-1]
        if not filename.endswith(".whl") or len(filename) > 512:
            raise RuntimeError("TAW-08 locked wheel census is invalid")
        allowed_wheels[filename] = (
            digest_ref.removeprefix("sha256:"),
            size,
        )
    if not allowed_wheels:
        raise RuntimeError("TAW-08 locked distribution has no wheel artifacts")
    wheelhouse_value = os.environ.get(_LOCKED_WHEELHOUSE_ENV)
    if not wheelhouse_value:
        raise RuntimeError("TAW-08 locked wheelhouse is unavailable")
    wheelhouse = Path(wheelhouse_value).resolve()
    if not wheelhouse.is_dir():
        raise RuntimeError("TAW-08 locked wheelhouse is unavailable")
    matching_identities: list[tuple[str, tuple[tuple[str, int, str], ...]]] = []
    for filename, (expected_hash, expected_size) in allowed_wheels.items():
        wheel_path = (wheelhouse / filename).resolve()
        if not wheel_path.is_relative_to(wheelhouse) or not wheel_path.is_file():
            continue
        wheel_bytes = wheel_path.read_bytes()
        if (
            len(wheel_bytes) != expected_size
            or hashlib.sha256(wheel_bytes).hexdigest() != expected_hash
        ):
            continue
        try:
            parsed_name, parsed_version, _build, _tags = parse_wheel_filename(filename)
        except ValueError:
            continue
        if (
            canonicalize_name(str(parsed_name)) != name
            or str(parsed_version) != version
        ):
            continue
        try:
            with zipfile.ZipFile(io.BytesIO(wheel_bytes)) as wheel:
                members = tuple(item for item in wheel.infolist() if not item.is_dir())
                if (
                    not members
                    or len(members) > 100_000
                    or sum(item.file_size for item in members) > 1024 * 1024 * 1024
                    or any(
                        item.file_size > 64 * 1024 * 1024
                        or not item.filename
                        or len(item.filename) > 1024
                        or item.filename.startswith("/")
                        or ".." in Path(item.filename).parts
                        for item in members
                    )
                ):
                    continue
                member_names = tuple(item.filename for item in members)
                if len(member_names) != len(set(member_names)):
                    continue
                record_names = tuple(
                    item for item in member_names if item.endswith(".dist-info/RECORD")
                )
                if len(record_names) != 1:
                    continue
                try:
                    record_text = wheel.read(record_names[0]).decode("utf-8")
                except (KeyError, UnicodeDecodeError):
                    continue
                rows = tuple(csv.reader(io.StringIO(record_text, newline="")))
                if any(len(row) != 3 for row in rows):
                    continue
                record_by_ref = {row[0]: (row[1], row[2]) for row in rows}
                if set(record_by_ref) != set(member_names):
                    continue
                wheel_identity: list[tuple[str, int, str]] = []
                for member_name in sorted(member_names):
                    content = wheel.read(member_name)
                    hash_value, size_value = record_by_ref[member_name]
                    if member_name != record_names[0]:
                        actual_hash = (
                            base64.urlsafe_b64encode(hashlib.sha256(content).digest())
                            .rstrip(b"=")
                            .decode("ascii")
                        )
                        if hash_value != f"sha256={actual_hash}" or size_value != str(
                            len(content)
                        ):
                            break
                    elif hash_value or size_value:
                        break
                    wheel_identity.append(
                        (
                            member_name,
                            len(content),
                            hashlib.sha256(content).hexdigest(),
                        )
                    )
                else:
                    authenticated_identity = tuple(wheel_identity)
                    wheel_by_ref = {
                        entry[0]: entry[1:] for entry in authenticated_identity
                    }
                    installed_by_ref = {
                        entry[0]: entry[1:] for entry in installed_identity
                    }
                    wheel_payload_refs = {
                        entry_ref
                        for entry_ref in wheel_by_ref
                        if not entry_ref.endswith(".dist-info/RECORD")
                    }
                    installer_metadata_refs = {
                        entry_ref
                        for entry_ref in installed_by_ref
                        if entry_ref.endswith(
                            (
                                ".dist-info/RECORD",
                                ".dist-info/INSTALLER",
                                ".dist-info/REQUESTED",
                                ".dist-info/direct_url.json",
                            )
                        )
                    }
                    installer_script_refs = {
                        entry_ref
                        for entry_ref in installed_by_ref
                        if entry_ref.startswith(
                            f"../../../{_venv_scripts_directory()}/"
                        )
                        and re.fullmatch(
                            r"[A-Za-z0-9_.-]{1,255}",
                            entry_ref.rsplit("/", 1)[-1],
                        )
                    }

                    def installed_entry_matches_wheel(entry_ref: str) -> bool:
                        if ".data/scripts/" not in entry_ref:
                            return (
                                installed_by_ref.get(entry_ref)
                                == wheel_by_ref[entry_ref]
                            )
                        script_name = entry_ref.rsplit("/", 1)[-1]
                        scripts_directory = _venv_scripts_directory()
                        installed_script_ref = (
                            f"../../../{scripts_directory}/{script_name}"
                        )
                        cached_script = wheel.read(entry_ref)
                        try:
                            installed_script = (
                                Path(os.environ.get(_ENVIRONMENT_ROOT_ENV, sys.prefix))
                                / scripts_directory
                                / script_name
                            ).read_bytes()
                        except OSError:
                            return False
                        cached_lines = cached_script.splitlines(keepends=True)
                        installed_lines = installed_script.splitlines(keepends=True)
                        if cached_lines and cached_lines[0] not in {
                            b"#!python\n",
                            b"#!pythonw\n",
                        }:
                            return (
                                installed_script == cached_script
                                and installed_script_ref in installer_script_refs
                            )
                        return (
                            bool(cached_lines)
                            and cached_lines[0] in {b"#!python\n", b"#!pythonw\n"}
                            and bool(installed_lines)
                            and installed_lines[0]
                            == f"#!{sys.executable}\n".encode("utf-8")
                            and installed_lines[1:] == cached_lines[1:]
                            and installed_script_ref in installer_script_refs
                        )

                    if (
                        all(
                            installed_entry_matches_wheel(entry_ref)
                            for entry_ref in wheel_payload_refs
                        )
                        and set(installed_by_ref) - wheel_payload_refs
                        <= installer_metadata_refs | installer_script_refs
                    ):
                        matching_identities.append(
                            (f"sha256:{expected_hash}", authenticated_identity)
                        )
        except (OSError, zipfile.BadZipFile):
            continue
    unique = tuple(dict.fromkeys(matching_identities))
    if len(unique) != 1:
        raise RuntimeError(
            "TAW-08 installed distribution is not bound to one locked wheel "
            f"artifact: {name}"
        )
    return unique[0]


def verify_locked_evaluator_environment(
    *,
    locked_content_by_path_ref: dict[str, bytes],
    repository_root: Path = ROOT,
) -> _EvaluatorEnvironmentReceipt:
    """Bind the exact active interpreter only after an offline frozen lock check."""

    required_paths = {
        "repo-path-ref:pyproject.toml": repository_root / "pyproject.toml",
        "repo-path-ref:uv.lock": repository_root / "uv.lock",
    }
    if set(locked_content_by_path_ref) != set(required_paths):
        raise RuntimeError("TAW-08 evaluator environment lock census is incomplete")
    for path_ref, path in required_paths.items():
        if (
            not path.is_file()
            or path.read_bytes() != locked_content_by_path_ref[path_ref]
        ):
            raise RuntimeError(
                "TAW-08 evaluator environment lock differs from the candidate"
            )
    environment_root_value = os.environ.get(_ENVIRONMENT_ROOT_ENV)
    environment_root = (
        Path(environment_root_value).resolve()
        if environment_root_value
        else Path(sys.prefix).resolve()
    )
    if (
        sys.implementation.name != "cpython"
        or not (environment_root / "pyvenv.cfg").is_file()
    ):
        raise RuntimeError(
            "TAW-08 evaluator environment requires an active CPython project venv"
        )
    venv_configuration = environment_root / "pyvenv.cfg"
    try:
        venv_configuration_text = venv_configuration.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise RuntimeError(
            "TAW-08 evaluator environment venv configuration is unavailable"
        ) from exc
    if not re.search(
        r"(?im)^include-system-site-packages\s*=\s*false\s*$",
        venv_configuration_text,
    ):
        raise RuntimeError(
            "TAW-08 evaluator environment must exclude system site packages"
        )
    try:
        pyproject = tomllib.loads(
            locked_content_by_path_ref["repo-path-ref:pyproject.toml"].decode("utf-8")
        )
        locked = tomllib.loads(
            locked_content_by_path_ref["repo-path-ref:uv.lock"].decode("utf-8")
        )
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise RuntimeError("TAW-08 evaluator lock metadata is invalid") from exc
    project = pyproject.get("project")
    packages = locked.get("package")
    if not isinstance(project, dict) or not isinstance(packages, list):
        raise RuntimeError("TAW-08 evaluator lock metadata is incomplete")
    project_name_value = project.get("name")
    project_dependencies = project.get("dependencies")
    optional_dependencies = project.get("optional-dependencies")
    if (
        not isinstance(project_name_value, str)
        or not isinstance(project_dependencies, list)
        or not isinstance(optional_dependencies, dict)
        or not isinstance(optional_dependencies.get("dev"), list)
        or any(
            not isinstance(item, str)
            for item in (*project_dependencies, *optional_dependencies["dev"])
        )
    ):
        raise RuntimeError("TAW-08 evaluator dependency roots are invalid")
    project_name = canonicalize_name(project_name_value)
    marker_environment = default_environment()
    locked_versions: dict[str, set[str]] = defaultdict(set)
    locked_wheels_by_identity: dict[tuple[str, str], list[object]] = {}
    for item in packages:
        if not isinstance(item, dict):
            raise RuntimeError("TAW-08 uv.lock package census is invalid")
        name = item.get("name")
        version = item.get("version")
        if not isinstance(name, str) or not isinstance(version, str):
            raise RuntimeError("TAW-08 uv.lock package identity is invalid")
        resolution_markers = item.get("resolution-markers", [])
        if not isinstance(resolution_markers, list) or any(
            not isinstance(marker, str) for marker in resolution_markers
        ):
            raise RuntimeError("TAW-08 uv.lock resolution markers are invalid")
        try:
            active_for_environment = not resolution_markers or any(
                Marker(marker).evaluate(marker_environment)
                for marker in resolution_markers
            )
        except InvalidMarker as exc:
            raise RuntimeError("TAW-08 uv.lock resolution markers are invalid") from exc
        if not active_for_environment:
            continue
        canonical_name = canonicalize_name(name)
        locked_versions[canonical_name].add(version)
        wheels = item.get("wheels", [])
        if not isinstance(wheels, list):
            raise RuntimeError("TAW-08 locked wheel census is invalid")
        locked_wheels_by_identity[(canonical_name, version)] = wheels
    installed_by_name: dict[str, importlib_metadata.Distribution] = {}
    for distribution in importlib_metadata.distributions():
        name_value = str(distribution.metadata.get("Name", "")).strip()
        name = canonicalize_name(name_value)
        if not name:
            raise RuntimeError("TAW-08 evaluator distribution census is invalid")
        if name in installed_by_name:
            if name == project_name and str(installed_by_name[name].version) == str(
                distribution.version
            ):
                continue
            raise RuntimeError("TAW-08 evaluator distribution census is invalid")
        installed_by_name[name] = distribution
    if (
        not installed_by_name
        or len(installed_by_name) > 2048
        or any(
            not re.fullmatch(r"[a-z0-9][a-z0-9.-]{0,127}", name)
            or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.+!-]{0,127}", value)
            for name, distribution in installed_by_name.items()
            for value in (str(distribution.version).strip(),)
        )
    ):
        raise RuntimeError("TAW-08 evaluator distribution census is invalid")
    active_extras: dict[str, set[str]] = defaultdict(set)
    reachable: set[str] = set()
    pending: deque[str] = deque()

    def require(requirement_text: str, marker_extras: set[str]) -> None:
        try:
            requirement = Requirement(requirement_text)
        except InvalidRequirement as exc:
            raise RuntimeError("TAW-08 evaluator requirement is invalid") from exc
        contexts = marker_extras or {""}
        if requirement.marker is not None and not any(
            requirement.marker.evaluate({**marker_environment, "extra": extra})
            for extra in contexts
        ):
            return
        name = canonicalize_name(requirement.name)
        distribution = installed_by_name.get(name)
        if distribution is None:
            raise RuntimeError("TAW-08 evaluator dependency closure is incomplete")
        try:
            installed_version = Version(str(distribution.version))
        except InvalidVersion as exc:
            raise RuntimeError(
                "TAW-08 evaluator distribution version is invalid"
            ) from exc
        if installed_version not in requirement.specifier or str(
            distribution.version
        ) not in locked_versions.get(name, set()):
            raise RuntimeError("TAW-08 evaluator environment does not match uv.lock")
        new_extras = set(requirement.extras) - active_extras[name]
        if name not in reachable or new_extras:
            reachable.add(name)
            active_extras[name].update(new_extras)
            pending.append(name)

    for requirement_text in (*project_dependencies, *optional_dependencies["dev"]):
        require(requirement_text, {""})
    processed_extras: dict[str, frozenset[str]] = {}
    while pending:
        name = pending.popleft()
        extras = frozenset(active_extras[name])
        if processed_extras.get(name) == extras:
            continue
        processed_extras[name] = extras
        for requirement_text in installed_by_name[name].requires or ():
            require(requirement_text, {"", *extras})
    unexpected = set(installed_by_name) - reachable - {project_name}
    if unexpected:
        raise RuntimeError("TAW-08 evaluator environment has unlocked distributions")
    distribution_refs = tuple(
        f"{name}=={str(distribution.version).strip()}"
        for name, distribution in sorted(installed_by_name.items())
    )
    distribution_content_identities = []
    for name in sorted(reachable):
        version = str(installed_by_name[name].version).strip()
        installed_identity = _installed_distribution_content_identity(
            installed_by_name[name],
            environment_root=environment_root,
        )
        locked_wheel_identity = _locked_wheel_distribution_identity(
            name=name,
            version=version,
            locked_wheels=locked_wheels_by_identity.get((name, version), []),
            installed_identity=installed_identity,
        )
        distribution_content_identities.append((name, version, locked_wheel_identity))
    distribution_content_identities = tuple(distribution_content_identities)
    (
        python_executable_digest_ref,
        python_standard_library_file_count,
        python_standard_library_digest_ref,
    ) = _python_runtime_identity()
    _git_executable, git_executable_digest_ref, git_provenance_ref = (
        _trusted_git_identity()
    )
    return _bind_evaluator_environment_receipt(
        python_implementation="cpython",
        python_version=".".join(str(item) for item in sys.version_info[:3]),
        platform_system=platform.system().strip().lower(),
        platform_machine=platform.machine().strip().lower(),
        python_executable_digest_ref=python_executable_digest_ref,
        python_standard_library_file_count=python_standard_library_file_count,
        python_standard_library_digest_ref=python_standard_library_digest_ref,
        git_executable_digest_ref=git_executable_digest_ref,
        git_provenance_ref=git_provenance_ref,
        installed_distribution_count=len(distribution_refs),
        installed_distributions_digest_ref=canonical_digest(
            {
                "distributions": distribution_refs,
                "reachable_distribution_contents": (distribution_content_identities),
            }
        ),
        pyproject_digest_ref=(
            "sha256:"
            + hashlib.sha256(
                locked_content_by_path_ref["repo-path-ref:pyproject.toml"]
            ).hexdigest()
        ),
        uv_lock_digest_ref=(
            "sha256:"
            + hashlib.sha256(
                locked_content_by_path_ref["repo-path-ref:uv.lock"]
            ).hexdigest()
        ),
        lock_check_command_ref=(
            "command-ref:python-installed-distribution-lock-closure"
        ),
        independent_lock_closure_verified=True,
        locked_environment_verified=True,
        raw_content_persisted=False,
    )


def derive_revision_path_census(
    revision_ref: str, *, repository_root: Path = ROOT
) -> RevisionPathCensus:
    revision = revision_ref.removeprefix("git-sha:")
    paths = tuple(
        sorted(
            f"repo-path-ref:{path}"
            for path in _git(
                "ls-tree",
                "-r",
                "--name-only",
                revision,
                repository_root=repository_root,
            )
            .decode("utf-8")
            .splitlines()
            if path
        )
    )
    return bind_revision_path_census(
        revision_ref=revision_ref,
        path_refs=paths,
        provenance_ref="provenance-ref:git-ls-tree",
    )


def derive_revision_delta_census(
    candidate_revision_ref: str,
    delta_revision_ref: str,
    *,
    repository_root: Path = ROOT,
) -> RevisionDeltaCensus:
    candidate = candidate_revision_ref.removeprefix("git-sha:")
    delta = delta_revision_ref.removeprefix("git-sha:")
    try:
        _git(
            "merge-base",
            "--is-ancestor",
            candidate,
            delta,
            repository_root=repository_root,
        )
    except subprocess.CalledProcessError as exc:
        raise ValueError(
            "evidence delta must descend from the locked candidate"
        ) from exc
    commits = tuple(
        item
        for item in _git(
            "rev-list",
            "--reverse",
            f"{candidate}..{delta}",
            repository_root=repository_root,
        )
        .decode("ascii")
        .splitlines()
        if item
    )
    if not commits:
        raise ValueError("evidence delta history must contain at least one commit")
    paths = tuple(
        sorted(
            f"repo-path-ref:{path}"
            for path in _git(
                "diff",
                "--name-only",
                "--no-renames",
                candidate,
                delta,
                "--",
                repository_root=repository_root,
            )
            .decode("utf-8")
            .splitlines()
            if path
        )
    )
    history_paths = tuple(
        sorted(
            {
                f"repo-path-ref:{path}"
                for commit in commits
                for path in _git(
                    "diff-tree",
                    "--no-commit-id",
                    "--name-only",
                    "--no-renames",
                    "-r",
                    "-m",
                    commit,
                    repository_root=repository_root,
                )
                .decode("utf-8")
                .splitlines()
                if path
            }
        )
    )
    return bind_revision_delta_census(
        candidate_revision_ref=candidate_revision_ref,
        delta_revision_ref=delta_revision_ref,
        path_refs=paths,
        history_path_refs=history_paths,
        commit_count=len(commits),
        candidate_ancestor_verified=True,
        provenance_ref="provenance-ref:git-history-path-census",
    )


def derive_publication_history_census(
    delta_revision_ref: str,
    publication_revision_ref: str,
    *,
    repository_root: Path = ROOT,
) -> _PublicationHistoryCensus:
    history = derive_revision_delta_census(
        delta_revision_ref,
        publication_revision_ref,
        repository_root=repository_root,
    )
    return _bind_publication_history_census(
        delta_revision_ref=delta_revision_ref,
        publication_revision_ref=publication_revision_ref,
        path_refs=history.path_refs,
        history_path_refs=history.history_path_refs,
        commit_count=history.commit_count,
        delta_ancestor_verified=True,
        provenance_ref="provenance-ref:git-history-path-census",
    )


def _candidate_lock(
    revision: str,
    *,
    repository_root: Path = ROOT,
) -> tuple[CandidateLock, dict[str, bytes]]:
    entries: list[CandidateManifestEntry] = []
    content_by_ref: dict[str, bytes] = {}
    gate_paths = tuple(
        path
        for path in _git(
            "ls-tree",
            "-r",
            "--name-only",
            revision,
            repository_root=repository_root,
        )
        .decode("utf-8")
        .splitlines()
        if f"repo-path-ref:{path}".startswith(TAW08_FOUNDATION_GATE_SOURCE_PREFIX)
        and path.endswith(".py")
    )
    candidate_paths = tuple(sorted({*SLICE_CANDIDATE_PATHS, *gate_paths}))
    for path in candidate_paths:
        content = _git(
            "show",
            f"{revision}:{path}",
            repository_root=repository_root,
        )
        worktree_path = repository_root / path
        try:
            metadata = os.lstat(worktree_path)
            worktree_content = worktree_path.read_bytes()
        except OSError as exc:
            raise RuntimeError(
                f"TAW-08 contract path comparison failed: {path}"
            ) from exc
        if not stat.S_ISREG(metadata.st_mode) or worktree_content != content:
            raise RuntimeError(f"TAW-08 contract path is dirty at {revision}: {path}")
        path_ref = f"repo-path-ref:{path}"
        content_by_ref[path_ref] = content
        entries.append(
            CandidateManifestEntry(
                path_ref=path_ref,
                content_digest_ref=f"sha256:{hashlib.sha256(content).hexdigest()}",
            )
        )
    candidate_ref = "candidate-ref:taw08:contract-slice:v1"
    git_revision_ref = f"git-sha:{revision}"
    evidence_only_delta_path_refs = tuple(
        f"repo-path-ref:{path}" for path in EVIDENCE_ONLY_DELTA_PATHS
    )
    digest_payload = {
        "candidate_ref": candidate_ref,
        "git_revision_ref": git_revision_ref,
        "entries": [entry.model_dump(mode="json") for entry in entries],
        "evidence_only_delta_path_refs": evidence_only_delta_path_refs,
    }
    return (
        CandidateLock(
            candidate_ref=candidate_ref,
            git_revision_ref=git_revision_ref,
            entries=tuple(entries),
            manifest_digest_ref=canonical_digest(digest_payload),
            evidence_only_delta_path_refs=evidence_only_delta_path_refs,
        ),
        content_by_ref,
    )


def _source_evidence_from_git(
    lock: CandidateLock,
    revision_path_census: RevisionPathCensus,
    *,
    repository_root: Path = ROOT,
) -> tuple[SourceProjection, SourceDependencyClosure, dict[str, bytes]]:
    root_entries = tuple(
        item
        for item in lock.entries
        if item.path_ref.startswith("repo-path-ref:src/")
        and item.path_ref.endswith(".py")
    )
    projection_payload = {
        "schema_version": "uaa-taw00-source-projection.v1",
        "projection_ref": "source-projection-ref:taw08:repository-derived",
        "source_revision_ref": lock.git_revision_ref,
        "status": "transitive_dependency_closed",
        "entries": [item.model_dump(mode="json") for item in root_entries],
        "routing_changes_added": False,
        "prompt_changes_added": False,
        "runtime_model_calls_added": False,
        "authority_added": False,
    }
    projection = SourceProjection(
        **projection_payload,
        projection_digest_ref=canonical_digest(projection_payload),
    )
    revision = lock.git_revision_ref.removeprefix("git-sha:")
    available = set(revision_path_census.path_refs)
    content_by_ref: dict[str, bytes] = {}
    dependencies_by_ref: dict[str, tuple[str, ...]] = {}
    frontier = [item.path_ref for item in root_entries]
    while frontier:
        path_ref = frontier.pop()
        if path_ref in content_by_ref:
            continue
        path = path_ref.removeprefix("repo-path-ref:")
        content = _git(
            "show",
            f"{revision}:{path}",
            repository_root=repository_root,
        )
        content_by_ref[path_ref] = content
        dependencies = derive_local_python_dependencies(
            path_ref,
            content,
            available_path_refs=available,
            allow_unresolved_dynamic_imports=(
                path_ref in TAW08_UNRESOLVED_DYNAMIC_IMPORT_PATH_REFS
            ),
        )
        dependencies_by_ref[path_ref] = dependencies
        frontier.extend(ref for ref in dependencies if ref not in content_by_ref)
    closure_entries = tuple(
        SourceDependencyEntry(
            path_ref=path_ref,
            content_digest_ref=(
                f"sha256:{hashlib.sha256(content_by_ref[path_ref]).hexdigest()}"
            ),
            dependency_path_refs=dependencies_by_ref[path_ref],
        )
        for path_ref in sorted(content_by_ref)
    )
    closure_payload = {
        "schema_version": "uaa-taw00-source-dependency-closure.v1",
        "source_revision_ref": lock.git_revision_ref,
        "source_projection_digest_ref": projection.projection_digest_ref,
        "root_path_refs": tuple(item.path_ref for item in root_entries),
        "entries": [item.model_dump(mode="json") for item in closure_entries],
    }
    closure = SourceDependencyClosure(
        **closure_payload,
        closure_digest_ref=canonical_digest(closure_payload),
    )
    return projection, closure, content_by_ref


def verify_repository_candidate(
    lock: CandidateLock,
    *,
    repository_root: Path = ROOT,
) -> _CandidateLockVerificationReceipt:
    revision = lock.git_revision_ref.removeprefix("git-sha:")
    if os.environ.get(_LOCKED_CHILD_REVISION_ENV) != revision:
        raise RuntimeError(
            "TAW-08 candidate receipts require the locked verifier child"
        )
    if _fresh_exact_repository_revision(repository_root) != f"git-sha:{revision}":
        raise RuntimeError(
            "TAW-08 locked verifier child requires the clean candidate checkout"
        )
    if _index_has_hidden_worktree_entries(repository_root=repository_root):
        raise RuntimeError("TAW-08 locked verifier child rejects hidden index entries")
    _load_candidate_foundation_source_for_census(
        repository_root=repository_root,
        revision=revision,
    )
    revision_path_census = derive_revision_path_census(
        lock.git_revision_ref,
        repository_root=repository_root,
    )
    projection, closure, closure_content = _source_evidence_from_git(
        lock,
        revision_path_census,
        repository_root=repository_root,
    )
    content_by_ref = {
        item.path_ref: _git(
            "show",
            f"{revision}:{item.path_ref.removeprefix('repo-path-ref:')}",
            repository_root=repository_root,
        )
        for item in lock.entries
    }
    if (
        Path(__file__).read_bytes()
        != content_by_ref[TAW08_REPOSITORY_VERIFIER_PATH_REF]
    ):
        raise RuntimeError(
            "TAW-08 repository verifier differs from the candidate revision"
        )
    _verify_preflight_execution(repository_root=repository_root)
    evaluator_environment_receipt = verify_locked_evaluator_environment(
        locked_content_by_path_ref={
            path_ref: content_by_ref[path_ref]
            for path_ref in (
                "repo-path-ref:pyproject.toml",
                "repo-path-ref:uv.lock",
            )
        },
        repository_root=repository_root,
    )
    executing_source_path_refs, executing_source_census_digest_ref = (
        verify_executing_repository_sources(
            revision,
            repository_root=repository_root,
        )
    )
    return _bind_candidate_lock_verification_receipt(
        candidate_lock=lock,
        expected_path_refs=tuple(item.path_ref for item in lock.entries),
        revision_content_by_path_ref=content_by_ref,
        source_projection=projection,
        source_closure=closure,
        closure_content_by_path_ref=closure_content,
        revision_path_census=revision_path_census,
        evaluator_environment_receipt=evaluator_environment_receipt,
        executing_source_path_refs=executing_source_path_refs,
        executing_source_census_digest_ref=executing_source_census_digest_ref,
    )


def verify_repository_evidence_delta(
    *,
    candidate_lock: CandidateLock,
    delta: EvidenceOnlyDeltaManifest,
    validated_acceptance_reports_by_path_ref: dict[str, TAW08AcceptanceReport]
    | None = None,
    candidate_repository_root: Path = ROOT,
    delta_repository_root: Path = ROOT,
) -> _EvidenceOnlyDeltaVerificationReceipt:
    candidate_verification_receipt = verify_repository_candidate(
        candidate_lock,
        repository_root=candidate_repository_root,
    )
    if not candidate_verification_receipt.verified:
        raise RuntimeError("TAW-08 delta issuer lacks candidate-bound provenance")
    census = derive_revision_delta_census(
        candidate_lock.git_revision_ref,
        delta.delta_revision_ref,
        repository_root=delta_repository_root,
    )
    delta_revision = delta.delta_revision_ref.removeprefix("git-sha:")
    candidate_revision = candidate_lock.git_revision_ref.removeprefix("git-sha:")
    content_by_ref = {
        path_ref: _git(
            "show",
            f"{delta_revision}:{path_ref.removeprefix('repo-path-ref:')}",
            repository_root=delta_repository_root,
        )
        for path_ref in census.path_refs
    }
    candidate_content_by_ref = {
        path_ref: _git(
            "show",
            f"{candidate_revision}:{path_ref.removeprefix('repo-path-ref:')}",
            repository_root=delta_repository_root,
        )
        for path_ref in census.path_refs
        if path_ref.endswith(".md")
    }
    return _verify_and_bind_evidence_only_delta(
        candidate_lock=candidate_lock,
        delta=delta,
        changed_content_by_path_ref=content_by_ref,
        revision_delta_census=census,
        candidate_content_by_path_ref=candidate_content_by_ref,
        validated_acceptance_reports_by_path_ref=(
            validated_acceptance_reports_by_path_ref
        ),
    )


def verify_repository_foundation_gate(
    *,
    stage: Literal["exact_head", "postmerge"],
    repository_root: Path = ROOT,
) -> FoundationGateReceipt:
    if stage not in {"exact_head", "postmerge"}:
        raise ValueError("Foundation receipt stage is invalid")
    revision_ref, report = _evaluate_foundation_gate_in_fresh_process(repository_root)
    revision = revision_ref.removeprefix("git-sha:")
    verify_executing_repository_sources(
        revision,
        repository_root=repository_root,
    )
    _verify_preflight_execution(repository_root=repository_root)
    evaluator_environment_receipt = verify_locked_evaluator_environment(
        locked_content_by_path_ref={
            path_ref: _git(
                "show",
                f"{revision}:{path_ref.removeprefix('repo-path-ref:')}",
                repository_root=repository_root,
            )
            for path_ref in (
                "repo-path-ref:pyproject.toml",
                "repo-path-ref:uv.lock",
            )
        },
        repository_root=repository_root,
    )
    report = report.model_copy(
        update={
            "command_mode": "report-only",
            "command_receipts": [_report_only_receipt()],
        }
    )
    return _verify_and_bind_foundation_gate_report(
        report=report,
        stage=stage,
        revision_ref=revision_ref,
        evaluator_environment_receipt=evaluator_environment_receipt,
    )


def verify_repository_final_acceptance_publication(
    *,
    publication_revision_ref: str,
    candidate_revision_ref: str,
    candidate_manifest_digest_ref: str,
    founder_evidence_digest_ref: str,
    delta: EvidenceOnlyDeltaManifest,
    delta_verification_receipt: _EvidenceOnlyDeltaVerificationReceipt,
    postmerge_foundation_receipt: FoundationGateReceipt,
    candidate_repository_root: Path = ROOT,
    publication_repository_root: Path = ROOT,
) -> _FinalAcceptancePublicationReceipt:
    candidate_revision = candidate_revision_ref.removeprefix("git-sha:")
    issuer_lock, _candidate_content = _candidate_lock(
        candidate_revision,
        repository_root=candidate_repository_root,
    )
    if issuer_lock.manifest_digest_ref != candidate_manifest_digest_ref:
        raise RuntimeError("TAW-08 publication issuer candidate binding drift")
    candidate_verification_receipt = verify_repository_candidate(
        issuer_lock,
        repository_root=candidate_repository_root,
    )
    if not candidate_verification_receipt.verified:
        raise RuntimeError("TAW-08 publication issuer lacks candidate-bound provenance")
    publication_revision = publication_revision_ref.removeprefix("git-sha:")
    publication_path = TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF.removeprefix(
        "repo-path-ref:"
    )
    publication_content = _git(
        "show",
        f"{publication_revision}:{publication_path}",
        repository_root=publication_repository_root,
    )
    publication_history_census = derive_publication_history_census(
        delta.delta_revision_ref,
        publication_revision_ref,
        repository_root=publication_repository_root,
    )
    return _verify_and_bind_final_acceptance_publication(
        publication_revision_ref=publication_revision_ref,
        publication_path_ref=TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF,
        publication_content=publication_content,
        publication_history_census=publication_history_census,
        candidate_revision_ref=candidate_revision_ref,
        candidate_manifest_digest_ref=candidate_manifest_digest_ref,
        founder_evidence_digest_ref=founder_evidence_digest_ref,
        delta=delta,
        delta_verification_receipt=delta_verification_receipt,
        postmerge_foundation_receipt=postmerge_foundation_receipt,
    )


def verify(*, export_founder_inputs: bool = False) -> dict[str, object] | None:
    revision = _git("rev-parse", "HEAD").decode("ascii").strip()
    lock, content_by_ref = _candidate_lock(revision)
    expected_refs = tuple(item.path_ref for item in lock.entries)
    failures = verify_candidate_lock(
        lock,
        expected_path_refs=expected_refs,
        revision_content_by_path_ref=content_by_ref,
    )
    if failures:
        raise RuntimeError(f"TAW-08 contract candidate lock failed: {failures}")
    candidate_receipt = verify_repository_candidate(lock)
    report = evaluate_taw08_acceptance(
        candidate_lock=lock,
        candidate_verification_receipt=candidate_receipt,
    )
    expected_missing = tuple(
        sorted(
            (
                *(
                    ref
                    for ref in TAW08_FOUNDER_EVIDENCE_MISSING_REFS
                    if ref
                    != "evidence-missing-ref:taw08:candidate-lock-verification-receipt"
                ),
                TAW08_POSTMERGE_EVIDENCE_MISSING_REF,
                TAW08_FINAL_PUBLICATION_MISSING_REF,
            )
            + (TAW08_DELTA_VERIFICATION_MISSING_REF,)
        )
    )
    if (
        report.status != TAW08AcceptanceStatus.blocked_missing_founder_evidence
        or report.founder_private_accepted
        or report.founder_evidence_missing_refs != expected_missing
        or report.independent_promotion_ready
        or report.sealed_holdout_evidence_verified
        or report.public_quality_claims_allowed
    ):
        raise RuntimeError(
            "TAW-08 acceptance contract failed closed-state verification"
        )
    if any(
        (
            report.production_authority_added,
            report.runtime_model_calls_added,
            report.provider_calls_added,
            report.execution_authority_added,
            report.raw_content_persisted,
        )
    ):
        raise RuntimeError("TAW-08 verifier detected authority or content expansion")
    if not export_founder_inputs:
        return None
    foundation_receipt = verify_repository_foundation_gate(stage="exact_head")
    if foundation_receipt.revision_ref != lock.git_revision_ref:
        raise RuntimeError("TAW-08 Foundation export candidate binding drift")
    payload = {
        "schema_version": "uaa-taw08-founder-run-inputs.v1",
        "candidate_lock": lock.model_dump(mode="json"),
        "candidate_verification_receipt": candidate_receipt.model_dump(mode="json"),
        "exact_head_foundation_receipt": foundation_receipt.model_dump(mode="json"),
        "raw_content_persisted": False,
    }
    if _founder_input_export_has_forbidden_fields(payload):
        raise RuntimeError("TAW-08 founder input export contains unsafe fields")
    return {**payload, "bundle_digest_ref": canonical_digest(payload)}


def _locked_reachable_packages(
    *,
    project_name: str,
    packages: list[object],
    marker_environment: dict[str, str],
) -> dict[str, dict[str, object]]:
    """Resolve the project plus dev closure from uv.lock without ambient packages."""

    active_by_name: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in packages:
        if not isinstance(item, dict):
            raise RuntimeError("TAW-08 locked package census is invalid")
        name = item.get("name")
        version = item.get("version")
        markers = item.get("resolution-markers", [])
        if (
            not isinstance(name, str)
            or not isinstance(version, str)
            or not isinstance(markers, list)
            or any(not isinstance(marker, str) for marker in markers)
        ):
            raise RuntimeError("TAW-08 locked package census is invalid")
        try:
            active = not markers or any(
                Marker(marker).evaluate(marker_environment) for marker in markers
            )
        except InvalidMarker as exc:
            raise RuntimeError("TAW-08 locked package marker is invalid") from exc
        if active:
            active_by_name[canonicalize_name(name)].append(item)
    project_candidates = active_by_name.get(project_name, [])
    if len(project_candidates) != 1:
        raise RuntimeError("TAW-08 locked project package is ambiguous")
    selected: dict[str, dict[str, object]] = {project_name: project_candidates[0]}
    active_extras: dict[str, set[str]] = defaultdict(set)
    active_extras[project_name].add("dev")
    pending: deque[str] = deque((project_name,))
    processed_extras: dict[str, frozenset[str]] = {}

    def select_dependency(dependency: object, parent_extras: set[str]) -> None:
        if not isinstance(dependency, dict):
            raise RuntimeError("TAW-08 locked dependency census is invalid")
        name_value = dependency.get("name")
        marker_value = dependency.get("marker")
        version_value = dependency.get("version")
        extras_value = dependency.get("extra", [])
        if (
            not isinstance(name_value, str)
            or (marker_value is not None and not isinstance(marker_value, str))
            or (version_value is not None and not isinstance(version_value, str))
            or not isinstance(extras_value, list)
            or any(not isinstance(extra, str) for extra in extras_value)
        ):
            raise RuntimeError("TAW-08 locked dependency census is invalid")
        if marker_value is not None:
            try:
                contexts = parent_extras or {""}
                if not any(
                    Marker(marker_value).evaluate(
                        {**marker_environment, "extra": extra}
                    )
                    for extra in contexts
                ):
                    return
            except InvalidMarker as exc:
                raise RuntimeError(
                    "TAW-08 locked dependency marker is invalid"
                ) from exc
        name = canonicalize_name(name_value)
        candidates = [
            item
            for item in active_by_name.get(name, [])
            if version_value is None or item.get("version") == version_value
        ]
        identities = {(str(item.get("version")), id(item)): item for item in candidates}
        if len(identities) != 1:
            raise RuntimeError(f"TAW-08 locked dependency is ambiguous: {name}")
        package = next(iter(identities.values()))
        existing = selected.get(name)
        if existing is not None and existing is not package:
            raise RuntimeError(f"TAW-08 locked dependency identity drifts: {name}")
        new_extras = set(extras_value) - active_extras[name]
        if existing is None or new_extras:
            selected[name] = package
            active_extras[name].update(new_extras)
            pending.append(name)

    while pending:
        name = pending.popleft()
        extras = frozenset(active_extras[name])
        if processed_extras.get(name) == extras:
            continue
        processed_extras[name] = extras
        package = selected[name]
        dependencies = package.get("dependencies", [])
        optional_dependencies = package.get("optional-dependencies", {})
        if not isinstance(dependencies, list) or not isinstance(
            optional_dependencies, dict
        ):
            raise RuntimeError("TAW-08 locked dependency census is invalid")
        for dependency in dependencies:
            select_dependency(dependency, set(extras))
        for extra in extras:
            extra_dependencies = optional_dependencies.get(extra, [])
            if not isinstance(extra_dependencies, list):
                raise RuntimeError("TAW-08 locked optional dependency is invalid")
            for dependency in extra_dependencies:
                select_dependency(dependency, {extra})
    selected.pop(project_name)
    return selected


def _materialize_locked_environment(
    *,
    candidate_root: Path,
    environment_root: Path,
    provisioned_wheelhouse: Path,
    selected_wheelhouse: Path,
) -> Path:
    """Build a no-ambient-package venv from exact compatible lock wheels."""

    try:
        pyproject = tomllib.loads(
            (candidate_root / "pyproject.toml").read_text(encoding="utf-8")
        )
        locked = tomllib.loads((candidate_root / "uv.lock").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise RuntimeError("TAW-08 locked environment metadata is invalid") from exc
    project = pyproject.get("project")
    packages = locked.get("package")
    if (
        not isinstance(project, dict)
        or not isinstance(project.get("name"), str)
        or not isinstance(packages, list)
    ):
        raise RuntimeError("TAW-08 locked environment metadata is incomplete")
    project_name = canonicalize_name(project["name"])
    marker_environment = default_environment()
    reachable_packages = _locked_reachable_packages(
        project_name=project_name,
        packages=packages,
        marker_environment=marker_environment,
    )
    active_tags = tuple(sys_tags())
    tag_rank = {tag: index for index, tag in enumerate(active_tags)}
    selected: dict[str, tuple[str, int, str]] = {}
    for name, package in sorted(reachable_packages.items()):
        version = str(package.get("version", ""))
        wheels = package.get("wheels", [])
        if not isinstance(wheels, list):
            raise RuntimeError("TAW-08 locked wheel census is invalid")
        candidates: list[tuple[int, str, str, int, str]] = []
        for wheel in wheels:
            if not isinstance(wheel, dict):
                continue
            url = wheel.get("url")
            digest_ref = wheel.get("hash")
            size = wheel.get("size")
            if (
                not isinstance(url, str)
                or not isinstance(digest_ref, str)
                or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest_ref)
                or not isinstance(size, int)
                or size <= 0
            ):
                continue
            parsed_url = urllib.parse.urlsplit(url)
            filename = urllib.parse.unquote(parsed_url.path.rsplit("/", 1)[-1])
            if (
                parsed_url.scheme != "https"
                or parsed_url.netloc != "files.pythonhosted.org"
                or parsed_url.query
                or parsed_url.fragment
                or not filename.endswith(".whl")
                or len(filename) > 512
            ):
                continue
            try:
                parsed_name, parsed_version, _build, wheel_tags = parse_wheel_filename(
                    filename
                )
            except ValueError:
                continue
            compatible_ranks = tuple(
                tag_rank[tag] for tag in wheel_tags if tag in tag_rank
            )
            if (
                canonicalize_name(str(parsed_name)) != name
                or str(parsed_version) != version
                or not compatible_ranks
            ):
                continue
            candidates.append(
                (
                    min(compatible_ranks),
                    filename,
                    digest_ref.removeprefix("sha256:"),
                    size,
                    url,
                )
            )
        if not candidates:
            raise RuntimeError(
                f"TAW-08 has no compatible locked wheel artifact: {name}"
            )
        _rank, filename, digest, size, url = min(candidates)
        existing = selected.get(filename)
        identity = (digest, size, url)
        if existing is not None and existing != identity:
            raise RuntimeError("TAW-08 locked wheel filename is ambiguous")
        selected[filename] = identity
    if not selected or len(selected) > 2_048:
        raise RuntimeError("TAW-08 locked wheel selection is invalid")
    provisioned_wheelhouse = provisioned_wheelhouse.resolve()
    if not provisioned_wheelhouse.is_dir():
        raise RuntimeError("TAW-08 provisioned wheelhouse is unavailable")
    selected_wheelhouse.mkdir(parents=True)
    wheel_paths: list[Path] = []
    for filename, (expected_hash, expected_size, _url) in sorted(selected.items()):
        provisioned_path = (provisioned_wheelhouse / filename).resolve()
        try:
            if (
                not provisioned_path.is_relative_to(provisioned_wheelhouse)
                or provisioned_path.is_symlink()
            ):
                raise OSError
            content = provisioned_path.read_bytes()
        except OSError as exc:
            raise RuntimeError("TAW-08 locked wheel artifact is unavailable") from exc
        if (
            len(content) != expected_size
            or hashlib.sha256(content).hexdigest() != expected_hash
        ):
            raise RuntimeError("TAW-08 locked wheel artifact differs from uv.lock")
        selected_path = selected_wheelhouse / filename
        shutil.copyfile(provisioned_path, selected_path)
        if selected_path.read_bytes() != content:
            raise RuntimeError("TAW-08 selected wheel copy differs from uv.lock")
        wheel_paths.append(selected_path)
    pip_wheel_paths = []
    remaining_wheel_paths = []
    for wheel_path in wheel_paths:
        try:
            distribution_name, _version, _build, _tags = parse_wheel_filename(
                wheel_path.name
            )
        except ValueError as exc:
            raise RuntimeError("TAW-08 locked wheel filename is invalid") from exc
        if canonicalize_name(str(distribution_name)) == "pip":
            pip_wheel_paths.append(wheel_path)
        else:
            remaining_wheel_paths.append(wheel_path)
    if len(pip_wheel_paths) != 1 or not remaining_wheel_paths:
        raise RuntimeError("TAW-08 locked installer closure is invalid")
    installer_environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith(("PIP_", "PYTHON"))
    }
    installer_environment.update(
        {
            "PIP_CONFIG_FILE": os.devnull,
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_INDEX": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    create_venv = subprocess.run(
        [sys.executable, "-m", "venv", str(environment_root)],
        cwd=candidate_root,
        check=False,
        capture_output=True,
        env=installer_environment,
        timeout=60,
    )
    if create_venv.returncode != 0:
        raise RuntimeError("TAW-08 hermetic evaluator venv creation failed")
    scripts_directory = _venv_scripts_directory()
    environment_python = (
        environment_root
        / scripts_directory
        / ("python.exe" if os.name == "nt" else "python")
    )
    install_locked_pip = subprocess.run(
        [
            str(environment_python),
            "-I",
            "-B",
            "-m",
            "pip",
            "--isolated",
            "install",
            "--force-reinstall",
            "--disable-pip-version-check",
            "--no-index",
            "--no-deps",
            "--no-compile",
            str(pip_wheel_paths[0]),
        ],
        cwd=candidate_root,
        check=False,
        capture_output=True,
        env=installer_environment,
        timeout=300,
    )
    if install_locked_pip.returncode != 0:
        raise RuntimeError("TAW-08 locked pip installation failed")
    install = subprocess.run(
        [
            str(environment_python),
            "-I",
            "-B",
            "-m",
            "pip",
            "--isolated",
            "install",
            "--ignore-installed",
            "--disable-pip-version-check",
            "--no-index",
            "--no-deps",
            "--no-compile",
            *(str(path) for path in remaining_wheel_paths),
        ],
        cwd=candidate_root,
        check=False,
        capture_output=True,
        env=installer_environment,
        timeout=300,
    )
    if install.returncode != 0:
        raise RuntimeError("TAW-08 locked wheel installation failed")
    if "setuptools" not in reachable_packages:
        remove_bootstrap_setuptools = subprocess.run(
            [
                str(environment_python),
                "-I",
                "-B",
                "-m",
                "pip",
                "--isolated",
                "uninstall",
                "--yes",
                "setuptools",
            ],
            cwd=candidate_root,
            check=False,
            capture_output=True,
            env=installer_environment,
            timeout=60,
        )
        if remove_bootstrap_setuptools.returncode != 0:
            raise RuntimeError("TAW-08 bootstrap package removal failed")
    return environment_python


def _locked_child_command(
    *, environment_python: Path, candidate_root: Path
) -> tuple[str, ...]:
    return (
        str(environment_python),
        "-I",
        "-B",
        "-S",
        str(candidate_root / "scripts/verify_taw08_environment_preflight.py"),
        str(candidate_root / "scripts/verify_tool_aware_cognition_taw08.py"),
    )


class _WindowsAclSizeInformation(ctypes.Structure):
    _fields_ = (
        ("AceCount", wintypes.DWORD),
        ("AclBytesInUse", wintypes.DWORD),
        ("AclBytesFree", wintypes.DWORD),
    )


class _WindowsAceHeader(ctypes.Structure):
    _fields_ = (
        ("AceType", ctypes.c_ubyte),
        ("AceFlags", ctypes.c_ubyte),
        ("AceSize", wintypes.WORD),
    )


class _WindowsSidAndAttributes(ctypes.Structure):
    _fields_ = (("Sid", ctypes.c_void_p), ("Attributes", wintypes.DWORD))


class _WindowsTokenUser(ctypes.Structure):
    _fields_ = (("User", _WindowsSidAndAttributes),)


_WINDOWS_DANGEROUS_DIRECTORY_RIGHTS = (
    0x00000002  # FILE_ADD_FILE
    | 0x00000004  # FILE_ADD_SUBDIRECTORY
    | 0x00000010  # FILE_WRITE_EA
    | 0x00000040  # FILE_DELETE_CHILD
    | 0x00000100  # FILE_WRITE_ATTRIBUTES
    | 0x00010000  # DELETE
    | 0x00040000  # WRITE_DAC
    | 0x00080000  # WRITE_OWNER
    | 0x10000000  # GENERIC_ALL
    | 0x40000000  # GENERIC_WRITE
)
_WINDOWS_ALLOW_ACE_TYPES = frozenset({0, 5, 9, 11})


def _windows_parent_acl_grant_is_unsafe(
    *, ace_type: int, access_mask: int, trustee_is_trusted: bool
) -> bool:
    """Return whether one parent ACE grants dangerous authority to a stranger."""

    return (
        ace_type in _WINDOWS_ALLOW_ACE_TYPES
        and not trustee_is_trusted
        and bool(access_mask & _WINDOWS_DANGEROUS_DIRECTORY_RIGHTS)
    )


def _windows_error(message: str) -> RuntimeError:
    return RuntimeError(f"{message} (winerror={ctypes.get_last_error()})")


def _configure_windows_acl_apis(advapi: object, kernel: object) -> None:
    pointer = ctypes.c_void_p
    advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = (  # type: ignore[attr-defined]
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(pointer),
        ctypes.POINTER(wintypes.DWORD),
    )
    advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = wintypes.BOOL  # type: ignore[attr-defined]
    advapi.GetSecurityDescriptorDacl.argtypes = (  # type: ignore[attr-defined]
        pointer,
        ctypes.POINTER(wintypes.BOOL),
        ctypes.POINTER(pointer),
        ctypes.POINTER(wintypes.BOOL),
    )
    advapi.GetSecurityDescriptorDacl.restype = wintypes.BOOL  # type: ignore[attr-defined]
    advapi.SetNamedSecurityInfoW.argtypes = (  # type: ignore[attr-defined]
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        pointer,
        pointer,
        pointer,
        pointer,
    )
    advapi.SetNamedSecurityInfoW.restype = wintypes.DWORD  # type: ignore[attr-defined]
    advapi.OpenProcessToken.argtypes = (  # type: ignore[attr-defined]
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    )
    advapi.OpenProcessToken.restype = wintypes.BOOL  # type: ignore[attr-defined]
    advapi.GetTokenInformation.argtypes = (  # type: ignore[attr-defined]
        wintypes.HANDLE,
        wintypes.DWORD,
        pointer,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    )
    advapi.GetTokenInformation.restype = wintypes.BOOL  # type: ignore[attr-defined]
    advapi.GetNamedSecurityInfoW.argtypes = (  # type: ignore[attr-defined]
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(pointer),
        ctypes.POINTER(pointer),
        ctypes.POINTER(pointer),
        ctypes.POINTER(pointer),
        ctypes.POINTER(pointer),
    )
    advapi.GetNamedSecurityInfoW.restype = wintypes.DWORD  # type: ignore[attr-defined]
    advapi.EqualSid.argtypes = (pointer, pointer)  # type: ignore[attr-defined]
    advapi.EqualSid.restype = wintypes.BOOL  # type: ignore[attr-defined]
    advapi.GetSecurityDescriptorControl.argtypes = (  # type: ignore[attr-defined]
        pointer,
        ctypes.POINTER(wintypes.WORD),
        ctypes.POINTER(wintypes.DWORD),
    )
    advapi.GetSecurityDescriptorControl.restype = wintypes.BOOL  # type: ignore[attr-defined]
    advapi.ConvertStringSidToSidW.argtypes = (  # type: ignore[attr-defined]
        wintypes.LPCWSTR,
        ctypes.POINTER(pointer),
    )
    advapi.ConvertStringSidToSidW.restype = wintypes.BOOL  # type: ignore[attr-defined]
    advapi.GetAclInformation.argtypes = (  # type: ignore[attr-defined]
        pointer,
        pointer,
        wintypes.DWORD,
        wintypes.DWORD,
    )
    advapi.GetAclInformation.restype = wintypes.BOOL  # type: ignore[attr-defined]
    advapi.GetAce.argtypes = (  # type: ignore[attr-defined]
        pointer,
        wintypes.DWORD,
        ctypes.POINTER(pointer),
    )
    advapi.GetAce.restype = wintypes.BOOL  # type: ignore[attr-defined]
    kernel.GetCurrentProcess.restype = wintypes.HANDLE  # type: ignore[attr-defined]
    kernel.LocalFree.argtypes = (pointer,)  # type: ignore[attr-defined]
    kernel.LocalFree.restype = pointer  # type: ignore[attr-defined]
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)  # type: ignore[attr-defined]
    kernel.CloseHandle.restype = wintypes.BOOL  # type: ignore[attr-defined]


def _apply_windows_private_directory_acl(path: Path) -> None:
    if os.name != "nt":
        raise RuntimeError("TAW-08 Windows ACL support is unavailable")
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)  # type: ignore[attr-defined]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
    _configure_windows_acl_apis(advapi, kernel)
    descriptor = ctypes.c_void_p()
    advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(wintypes.DWORD),
    )
    advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = wintypes.BOOL
    if not advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW(
        "D:P(A;OICI;FA;;;OW)(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)",
        1,
        ctypes.byref(descriptor),
        None,
    ):
        raise _windows_error("TAW-08 private ACL creation failed")
    try:
        present = wintypes.BOOL()
        defaulted = wintypes.BOOL()
        dacl = ctypes.c_void_p()
        if (
            not advapi.GetSecurityDescriptorDacl(
                descriptor,
                ctypes.byref(present),
                ctypes.byref(dacl),
                ctypes.byref(defaulted),
            )
            or not present.value
            or not dacl.value
        ):
            raise _windows_error("TAW-08 private ACL creation failed")
        result = advapi.SetNamedSecurityInfoW(
            str(path),
            1,
            0x80000004,
            None,
            None,
            dacl,
            None,
        )
        if result != 0:
            raise RuntimeError(
                f"TAW-08 private ACL application failed (winerror={result})"
            )
    finally:
        kernel.LocalFree(descriptor)


def _validate_windows_private_directory_acl(path: Path) -> None:
    if os.name != "nt":
        raise RuntimeError("TAW-08 Windows ACL support is unavailable")
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)  # type: ignore[attr-defined]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
    _configure_windows_acl_apis(advapi, kernel)
    token = wintypes.HANDLE()
    descriptor = ctypes.c_void_p()
    allowed_sid_handles: list[ctypes.c_void_p] = []
    try:
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        if not advapi.OpenProcessToken(
            kernel.GetCurrentProcess(), 0x0008, ctypes.byref(token)
        ):
            raise _windows_error("TAW-08 private ACL owner lookup failed")
        required = wintypes.DWORD()
        advapi.GetTokenInformation(token, 1, None, 0, ctypes.byref(required))
        if not required.value or required.value > 64 * 1024:
            raise _windows_error("TAW-08 private ACL owner lookup failed")
        token_buffer = ctypes.create_string_buffer(required.value)
        if not advapi.GetTokenInformation(
            token, 1, token_buffer, required, ctypes.byref(required)
        ):
            raise _windows_error("TAW-08 private ACL owner lookup failed")
        current_sid = ctypes.cast(
            token_buffer, ctypes.POINTER(_WindowsTokenUser)
        ).contents.User.Sid
        owner = ctypes.c_void_p()
        dacl = ctypes.c_void_p()
        result = advapi.GetNamedSecurityInfoW(
            str(path),
            1,
            0x00000005,
            ctypes.byref(owner),
            None,
            ctypes.byref(dacl),
            None,
            ctypes.byref(descriptor),
        )
        if result != 0 or not owner.value or not dacl.value or not descriptor.value:
            raise RuntimeError(
                f"TAW-08 private ACL inspection failed (winerror={result})"
            )
        if not advapi.EqualSid(owner, current_sid):
            raise RuntimeError("TAW-08 private ACL owner is invalid")
        control = wintypes.WORD()
        revision = wintypes.DWORD()
        if (
            not advapi.GetSecurityDescriptorControl(
                descriptor, ctypes.byref(control), ctypes.byref(revision)
            )
            or not control.value & 0x1000
        ):
            raise RuntimeError("TAW-08 private ACL is not protected")
        for sid_text in ("S-1-3-4", "S-1-5-18", "S-1-5-32-544"):
            sid = ctypes.c_void_p()
            if not advapi.ConvertStringSidToSidW(sid_text, ctypes.byref(sid)):
                raise _windows_error("TAW-08 private ACL SID lookup failed")
            allowed_sid_handles.append(sid)
        information = _WindowsAclSizeInformation()
        if not advapi.GetAclInformation(
            dacl,
            ctypes.byref(information),
            ctypes.sizeof(information),
            2,
        ) or information.AceCount != len(allowed_sid_handles):
            raise RuntimeError("TAW-08 private ACL grants are invalid")
        observed: set[int] = set()
        for index in range(information.AceCount):
            ace = ctypes.c_void_p()
            if not advapi.GetAce(dacl, index, ctypes.byref(ace)) or not ace.value:
                raise _windows_error("TAW-08 private ACL grant lookup failed")
            header = ctypes.cast(ace, ctypes.POINTER(_WindowsAceHeader)).contents
            mask = ctypes.c_uint32.from_address(ace.value + 4).value
            ace_sid = ctypes.c_void_p(ace.value + 8)
            matches = tuple(
                sid_index
                for sid_index, sid in enumerate(allowed_sid_handles)
                if advapi.EqualSid(ace_sid, sid)
            )
            if (
                header.AceType != 0
                or header.AceFlags != 0x03
                or header.AceSize < 12
                or mask != 0x001F01FF
                or len(matches) != 1
                or matches[0] in observed
            ):
                raise RuntimeError("TAW-08 private ACL grants are invalid")
            observed.add(matches[0])
        if len(observed) != len(allowed_sid_handles):
            raise RuntimeError("TAW-08 private ACL grants are invalid")
    finally:
        if descriptor.value:
            kernel.LocalFree(descriptor)
        for sid in allowed_sid_handles:
            kernel.LocalFree(sid)
        if token.value:
            kernel.CloseHandle(token)


def _validate_windows_private_parent_acl(path: Path) -> None:
    if os.name != "nt":
        raise RuntimeError("TAW-08 Windows ACL support is unavailable")
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)  # type: ignore[attr-defined]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
    _configure_windows_acl_apis(advapi, kernel)
    token = wintypes.HANDLE()
    descriptor = ctypes.c_void_p()
    trusted_sid_handles: list[ctypes.c_void_p] = []
    try:
        if not advapi.OpenProcessToken(
            kernel.GetCurrentProcess(), 0x0008, ctypes.byref(token)
        ):
            raise _windows_error("TAW-08 parent ACL owner lookup failed")
        required = wintypes.DWORD()
        advapi.GetTokenInformation(token, 1, None, 0, ctypes.byref(required))
        if not required.value or required.value > 64 * 1024:
            raise _windows_error("TAW-08 parent ACL owner lookup failed")
        token_buffer = ctypes.create_string_buffer(required.value)
        if not advapi.GetTokenInformation(
            token, 1, token_buffer, required, ctypes.byref(required)
        ):
            raise _windows_error("TAW-08 parent ACL owner lookup failed")
        current_sid = ctypes.cast(
            token_buffer, ctypes.POINTER(_WindowsTokenUser)
        ).contents.User.Sid
        owner = ctypes.c_void_p()
        dacl = ctypes.c_void_p()
        result = advapi.GetNamedSecurityInfoW(
            str(path),
            1,
            0x00000005,
            ctypes.byref(owner),
            None,
            ctypes.byref(dacl),
            None,
            ctypes.byref(descriptor),
        )
        if result != 0 or not owner.value or not dacl.value or not descriptor.value:
            raise RuntimeError(
                f"TAW-08 parent ACL inspection failed (winerror={result})"
            )
        if not advapi.EqualSid(owner, current_sid):
            raise RuntimeError("TAW-08 parent ACL owner is invalid")
        for sid_text in (
            "S-1-3-0",  # Creator Owner
            "S-1-3-4",  # Owner Rights
            "S-1-5-18",  # Local System
            "S-1-5-32-544",  # Builtin Administrators
        ):
            sid = ctypes.c_void_p()
            if not advapi.ConvertStringSidToSidW(sid_text, ctypes.byref(sid)):
                raise _windows_error("TAW-08 parent ACL SID lookup failed")
            trusted_sid_handles.append(sid)
        information = _WindowsAclSizeInformation()
        if (
            not advapi.GetAclInformation(
                dacl,
                ctypes.byref(information),
                ctypes.sizeof(information),
                2,
            )
            or information.AceCount > 1024
        ):
            raise RuntimeError("TAW-08 parent ACL grants are invalid")
        for index in range(information.AceCount):
            ace = ctypes.c_void_p()
            if not advapi.GetAce(dacl, index, ctypes.byref(ace)) or not ace.value:
                raise _windows_error("TAW-08 parent ACL grant lookup failed")
            header = ctypes.cast(ace, ctypes.POINTER(_WindowsAceHeader)).contents
            if header.AceSize < 8:
                raise RuntimeError("TAW-08 parent ACL grants are invalid")
            mask = ctypes.c_uint32.from_address(ace.value + 4).value
            trustee_is_trusted = False
            if header.AceType == 0:
                if header.AceSize < 12:
                    raise RuntimeError("TAW-08 parent ACL grants are invalid")
                ace_sid = ctypes.c_void_p(ace.value + 8)
                trustee_is_trusted = bool(advapi.EqualSid(ace_sid, current_sid)) or any(
                    advapi.EqualSid(ace_sid, sid) for sid in trusted_sid_handles
                )
            if _windows_parent_acl_grant_is_unsafe(
                ace_type=header.AceType,
                access_mask=mask,
                trustee_is_trusted=trustee_is_trusted,
            ):
                raise RuntimeError("TAW-08 parent ACL grants are unsafe")
    finally:
        if descriptor.value:
            kernel.LocalFree(descriptor)
        for sid in trusted_sid_handles:
            kernel.LocalFree(sid)
        if token.value:
            kernel.CloseHandle(token)


def _validate_private_directory(path: Path, *, require_empty: bool) -> None:
    metadata = os.lstat(path)
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise RuntimeError("TAW-08 private directory is unsafe")
    if os.name == "posix":
        if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o700:
            raise RuntimeError("TAW-08 private directory is unsafe")
    elif os.name == "nt":
        _validate_windows_private_directory_acl(path)
    else:
        raise RuntimeError("TAW-08 private directory platform is unsupported")
    if require_empty and any(path.iterdir()):
        raise RuntimeError("TAW-08 private directory is unsafe")


def _harden_private_directory(path: Path, *, require_empty: bool) -> None:
    if os.name == "posix":
        path.chmod(0o700)
    elif os.name == "nt":
        _apply_windows_private_directory_acl(path)
    else:
        raise RuntimeError("TAW-08 private directory platform is unsupported")
    _validate_private_directory(path, require_empty=require_empty)


def _validate_posix_temporary_ancestor_chain(path: Path) -> None:
    if not path.is_absolute():
        raise RuntimeError("TAW-08 temporary directory root is unsafe")
    nofollow_flag = getattr(os, "O_NOFOLLOW", 0)
    if not nofollow_flag:
        raise RuntimeError("TAW-08 temporary directory root is unsafe")
    lexical_components: list[Path] = []
    lexical = Path(path.anchor)
    for part in path.parts[1:]:
        lexical /= part
        lexical_components.append(lexical)
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise RuntimeError("TAW-08 temporary directory root is unsafe") from exc
    components = [
        *((component, True) for component in lexical_components),
        *((component, False) for component in (resolved, *resolved.parents)),
    ]
    for component, allow_root_symlink in components:
        descriptor = -1
        try:
            initial = os.lstat(component)
            if stat.S_ISLNK(initial.st_mode):
                if not allow_root_symlink or initial.st_uid != 0:
                    raise RuntimeError("TAW-08 temporary directory root is unsafe")
                final = os.lstat(component)
                if not os.path.samestat(initial, final):
                    raise RuntimeError("TAW-08 temporary directory root changed")
                continue
            mode = stat.S_IMODE(initial.st_mode)
            if (
                not stat.S_ISDIR(initial.st_mode)
                or initial.st_uid not in {0, os.getuid()}
                or (mode & 0o022 and not mode & stat.S_ISVTX)
            ):
                raise RuntimeError("TAW-08 temporary directory root is unsafe")
            descriptor = os.open(
                component,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_DIRECTORY", 0)
                | nofollow_flag,
            )
            opened = os.fstat(descriptor)
            final = os.lstat(component)
            if (
                not os.path.samestat(initial, opened)
                or not os.path.samestat(opened, final)
                or any(
                    getattr(opened, field) != getattr(final, field)
                    for field in ("st_dev", "st_ino", "st_mode", "st_uid")
                )
            ):
                raise RuntimeError("TAW-08 temporary directory root changed")
        except OSError as exc:
            raise RuntimeError("TAW-08 temporary directory root is unsafe") from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)


def _prepare_private_temporary_directory(
    *, prefix: str, repository_root: Path
) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    unresolved_temporary_parent = Path(tempfile.gettempdir())
    if os.name == "posix":
        _validate_posix_temporary_ancestor_chain(unresolved_temporary_parent)
    temporary_parent = unresolved_temporary_parent.resolve()
    try:
        parent_metadata = temporary_parent.lstat()
    except OSError as exc:
        raise RuntimeError("TAW-08 temporary directory root is unavailable") from exc
    if (
        stat.S_ISLNK(parent_metadata.st_mode)
        or not stat.S_ISDIR(parent_metadata.st_mode)
        or temporary_parent.is_relative_to(repository_root.resolve())
    ):
        raise RuntimeError("TAW-08 temporary directory root is unsafe")
    if os.name == "posix":
        parent_mode = stat.S_IMODE(parent_metadata.st_mode)
        if parent_metadata.st_uid not in {0, os.getuid()} or (
            parent_mode & 0o022 and not parent_mode & stat.S_ISVTX
        ):
            raise RuntimeError("TAW-08 temporary directory root is unsafe")
    elif os.name == "nt":
        _validate_windows_private_parent_acl(temporary_parent)
    else:
        raise RuntimeError("TAW-08 temporary directory root is unsafe")
    handle: tempfile.TemporaryDirectory[str] = tempfile.TemporaryDirectory(
        prefix=prefix,
        dir=temporary_parent,
    )
    try:
        root = Path(handle.name).resolve(strict=True)
        _harden_private_directory(root, require_empty=True)
        final_parent_metadata = os.lstat(temporary_parent)
        if not os.path.samestat(parent_metadata, final_parent_metadata):
            raise RuntimeError("TAW-08 temporary directory root changed")
    except BaseException:
        handle.cleanup()
        raise
    return handle, root


def _read_private_regular_file(path: Path, *, maximum: int) -> bytes:
    try:
        initial = path.lstat()
        if (
            stat.S_ISLNK(initial.st_mode)
            or not stat.S_ISREG(initial.st_mode)
            or initial.st_nlink != 1
            or (os.name == "posix" and initial.st_uid != os.getuid())
        ):
            raise RuntimeError("TAW-08 private evidence file is unsafe")
        descriptor = os.open(
            path,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | (getattr(os, "O_NOFOLLOW_ANY", 0) or getattr(os, "O_NOFOLLOW", 0)),
        )
        try:
            opened = os.fstat(descriptor)
            if not os.path.samestat(initial, opened):
                raise RuntimeError("TAW-08 private evidence file changed")
            if os.name == "posix":
                os.fchmod(descriptor, 0o600)
                hardened = os.fstat(descriptor)
                if (
                    not os.path.samestat(opened, hardened)
                    or stat.S_IMODE(hardened.st_mode) != 0o600
                ):
                    raise RuntimeError("TAW-08 private evidence file is unsafe")
                opened = hardened
            chunks: list[bytes] = []
            observed = 0
            while True:
                chunk = os.read(descriptor, min(1024 * 1024, maximum + 1 - observed))
                if not chunk:
                    break
                chunks.append(chunk)
                observed += len(chunk)
                if observed > maximum:
                    raise RuntimeError("TAW-08 private evidence file is invalid")
            closed_over = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        final = path.lstat()
    except OSError as exc:
        raise RuntimeError("TAW-08 private evidence file is unavailable") from exc
    compared_fields = (
        "st_mode",
        "st_uid",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    if not os.path.samestat(opened, final) or any(
        getattr(opened, field) != getattr(closed_over, field)
        or getattr(opened, field) != getattr(final, field)
        for field in compared_fields
    ):
        raise RuntimeError("TAW-08 private evidence file changed")
    return b"".join(chunks)


def _locked_child_environment(
    *,
    revision: str,
    environment_root: Path,
    selected_wheelhouse: Path,
    runtime_temp: Path,
    platform_name: str = os.name,
) -> dict[str, str]:
    environment = {
        "PATH": os.environ.get("PATH", ""),
        _LOCKED_CHILD_REVISION_ENV: revision,
        _ENVIRONMENT_ROOT_ENV: str(environment_root),
        _LOCKED_WHEELHOUSE_ENV: str(selected_wheelhouse),
        "TMPDIR": str(runtime_temp),
        "TEMP": str(runtime_temp),
        "TMP": str(runtime_temp),
    }
    if os.environ.get(_EXPORT_FOUNDER_INPUTS_ENV) == "1":
        environment[_EXPORT_FOUNDER_INPUTS_ENV] = "1"
    if platform_name == "nt":
        environment["SystemRoot"] = str(_validated_windows_system_root())
    return environment


def _founder_input_export_has_forbidden_fields(
    payload: dict[str, object],
) -> bool:
    """Scan export content while treating validated repo path refs as identifiers."""

    expected_keys = {
        "schema_version",
        "candidate_lock",
        "candidate_verification_receipt",
        "exact_head_foundation_receipt",
        "raw_content_persisted",
    }
    if set(payload) not in (expected_keys, {*expected_keys, "bundle_digest_ref"}):
        raise ValueError("founder input export schema drift")
    candidate_lock = CandidateLock.model_validate(payload["candidate_lock"])
    candidate_receipt = _CandidateLockVerificationReceipt.model_validate(
        payload["candidate_verification_receipt"]
    )
    foundation_receipt = FoundationGateReceipt.model_validate(
        payload["exact_head_foundation_receipt"]
    )
    if (
        candidate_receipt.candidate_revision_ref != candidate_lock.git_revision_ref
        or candidate_receipt.candidate_manifest_digest_ref
        != candidate_lock.manifest_digest_ref
        or foundation_receipt.stage != "exact_head"
        or foundation_receipt.revision_ref != candidate_lock.git_revision_ref
    ):
        raise ValueError("founder input export candidate binding drift")
    candidate_receipt_safety_payload = candidate_receipt.model_dump(mode="json")
    candidate_receipt_safety_payload["executing_source_path_refs"] = ()
    safety_payload = {
        **payload,
        "candidate_lock": candidate_lock.model_dump(mode="json"),
        "candidate_verification_receipt": candidate_receipt_safety_payload,
        "exact_head_foundation_receipt": foundation_receipt.model_dump(mode="json"),
    }
    return durable_payload_has_forbidden_fields(safety_payload)


def _normalize_founder_input_export(child_stdout: bytes) -> bytes:
    """Validate and canonicalize the bounded locked-child export."""

    if not child_stdout or len(child_stdout) > 4 * 1024 * 1024:
        raise RuntimeError("TAW-08 founder input export is invalid")
    expected_keys = {
        "schema_version",
        "candidate_lock",
        "candidate_verification_receipt",
        "exact_head_foundation_receipt",
        "raw_content_persisted",
        "bundle_digest_ref",
    }
    try:
        exported = json.loads(child_stdout)
        if (
            not isinstance(exported, dict)
            or set(exported) != expected_keys
            or exported.get("schema_version") != "uaa-taw08-founder-run-inputs.v1"
            or exported.get("raw_content_persisted") is not False
            or _founder_input_export_has_forbidden_fields(exported)
        ):
            raise ValueError("founder input export schema drift")
        digest_payload = {
            key: value for key, value in exported.items() if key != "bundle_digest_ref"
        }
        if exported.get("bundle_digest_ref") != canonical_digest(digest_payload):
            raise ValueError("founder input export digest drift")
        return (
            json.dumps(
                exported,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("ascii")
            + b"\n"
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        TypeError,
        ValueError,
    ) as exc:
        raise RuntimeError("TAW-08 founder input export is invalid") from exc


def _locked_child_failure_summary(stderr: bytes) -> str:
    if not stderr or len(stderr) > 64 * 1024:
        return "failure detail unavailable"
    try:
        final_line = stderr.decode("ascii").splitlines()[-1]
    except (UnicodeDecodeError, IndexError):
        return "failure detail unavailable"
    match = re.fullmatch(
        r"(?:RuntimeError|ValueError): ([A-Za-z0-9][A-Za-z0-9 ._-]{0,159})",
        final_line,
    )
    if match is None:
        return "failure detail unavailable"
    return match.group(1)


def _run_locked_candidate_verifier() -> bytes | None:
    revision = _fresh_exact_repository_revision(ROOT).removeprefix("git-sha:")
    provisioned_wheelhouse_value = os.environ.get(_LOCKED_WHEELHOUSE_ENV)
    if not provisioned_wheelhouse_value:
        raise RuntimeError("TAW-08 verifier requires a provisioned wheelhouse")
    provisioned_wheelhouse = Path(provisioned_wheelhouse_value).resolve()
    temporary, temporary_root = _prepare_private_temporary_directory(
        prefix="uaa-taw08-locked-",
        repository_root=ROOT,
    )
    try:
        if temporary_root.is_relative_to(ROOT.resolve()):
            raise RuntimeError("TAW-08 locked temporary root is unsafe")
        candidate_root = temporary_root / "candidate"
        environment_root = temporary_root / "environment"
        selected_wheelhouse = temporary_root / "selected-wheelhouse"
        hooks_root = temporary_root / "hooks"
        runtime_temp = temporary_root / "runtime-temp"
        hooks_root.mkdir(mode=0o700)
        runtime_temp.mkdir(mode=0o700)
        _harden_private_directory(hooks_root, require_empty=True)
        _harden_private_directory(runtime_temp, require_empty=True)
        hooks_metadata = os.lstat(hooks_root)
        hooks_config = ("-c", f"core.hooksPath={hooks_root}")
        added = False
        try:
            _require_no_repository_git_filters()
            _git(
                "worktree",
                "add",
                "--detach",
                str(candidate_root),
                revision,
                extra_config=hooks_config,
            )
            added = True
            environment_python = _materialize_locked_environment(
                candidate_root=candidate_root,
                environment_root=environment_root,
                provisioned_wheelhouse=provisioned_wheelhouse,
                selected_wheelhouse=selected_wheelhouse,
            )
            child = subprocess.run(
                _locked_child_command(
                    environment_python=environment_python,
                    candidate_root=candidate_root,
                ),
                cwd=candidate_root,
                check=False,
                capture_output=True,
                env=_locked_child_environment(
                    revision=revision,
                    environment_root=environment_root,
                    selected_wheelhouse=selected_wheelhouse,
                    runtime_temp=runtime_temp,
                ),
                timeout=1_200,
            )
            if child.returncode != 0:
                raise RuntimeError(
                    "TAW-08 locked candidate verifier failed: "
                    + _locked_child_failure_summary(child.stderr)
                )
            if os.environ.get(_EXPORT_FOUNDER_INPUTS_ENV) == "1":
                return _normalize_founder_input_export(child.stdout)
        finally:
            if added:
                current_hooks = os.lstat(hooks_root)
                if not os.path.samestat(hooks_metadata, current_hooks):
                    raise RuntimeError("TAW-08 inert Git hooks directory changed")
                _validate_private_directory(hooks_root, require_empty=True)
                _validate_private_directory(runtime_temp, require_empty=False)
                _git(
                    "worktree",
                    "remove",
                    str(candidate_root),
                    extra_config=hooks_config,
                )
    finally:
        temporary.cleanup()
    return None


def main() -> int:
    export_founder_inputs = os.environ.get(_EXPORT_FOUNDER_INPUTS_ENV) == "1"
    if os.environ.get(_LOCKED_CHILD_REVISION_ENV):
        bundle = verify(export_founder_inputs=export_founder_inputs)
        if bundle is not None:
            print(json.dumps(bundle, sort_keys=True, separators=(",", ":")))
            return 0
    else:
        exported = _run_locked_candidate_verifier()
        if exported is not None:
            sys.stdout.buffer.write(exported)
            return 0
    print(
        "Tool-aware cognition TAW-08 acceptance contract verified; founder-private "
        "acceptance remains blocked on exact measured evidence."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
