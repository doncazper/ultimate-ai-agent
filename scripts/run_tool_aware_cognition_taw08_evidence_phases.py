from __future__ import annotations

import argparse
import base64
import ctypes
import errno
import hashlib
import importlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.parse
from collections import defaultdict, deque
from pathlib import Path
from types import ModuleType
from typing import Any

MAX_JSON_BYTES = 16 * 1024 * 1024
MAX_ARTIFACT_BYTES = 4 * 1024 * 1024
MAX_BOOTSTRAP_WHEEL_BYTES = MAX_JSON_BYTES
GIT_READ_CONFIG = (
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
)
WORKER_PATH = Path(__file__).with_name("taw08_evidence_phase_worker.py")
PREFLIGHT_PATH = Path(__file__).with_name("verify_taw08_environment_preflight.py")
DRIVER_PATH_REF = (
    "repo-path-ref:scripts/run_tool_aware_cognition_taw08_evidence_phases.py"
)
WORKER_PATH_REF = "repo-path-ref:scripts/taw08_evidence_phase_worker.py"
PREFLIGHT_PATH_REF = "repo-path-ref:scripts/verify_taw08_environment_preflight.py"
PYPROJECT_PATH_REF = "repo-path-ref:pyproject.toml"
UV_LOCK_PATH_REF = "repo-path-ref:uv.lock"
PREPARE_PATHS = {
    "repo-path-ref:docs/evals/tool_aware_cognition_taw08_acceptance_report_v1.json": (
        "acceptance_report"
    ),
    "repo-path-ref:docs/kanban/current_board.md": "claim_reconciliation",
    "repo-path-ref:docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md": (
        "claim_reconciliation"
    ),
}
FINAL_PATHS = {
    "repo-path-ref:docs/evals/"
    "tool_aware_cognition_taw08_final_acceptance_report_v1.json": (
        "final_acceptance_report"
    )
}
OUTPUT_NAMES = {
    **{
        path_ref: path_ref.removeprefix("repo-path-ref:").rsplit("/", 1)[-1]
        for path_ref in PREPARE_PATHS
    },
    **{
        path_ref: path_ref.removeprefix("repo-path-ref:").rsplit("/", 1)[-1]
        for path_ref in FINAL_PATHS
    },
}

# The operational entrypoint starts with the standard library only. These
# bindings are populated from the authenticated, candidate-locked pip wheel
# before any owner-private evidence is read.
tomllib: ModuleType | None = None
InvalidMarker: type[Exception] | None = None
Marker: Any = None
default_environment: Any = None
sys_tags: Any = None
canonicalize_name: Any = None
parse_wheel_filename: Any = None
_BOOTSTRAP_PIP_IDENTITY: tuple[str, int, str, str] | None = None


def _require_posix_private_path_support() -> None:
    if os.name != "posix" or not hasattr(os, "getuid"):
        raise ValueError("private path enforcement is unavailable on this platform")


def _darwin_extended_acl_tags(
    descriptor: int,
    *,
    purpose: str,
) -> tuple[int, ...]:
    if sys.platform != "darwin":
        return ()
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        acl_get_fd_np = libc.acl_get_fd_np
        acl_get_fd_np.argtypes = (ctypes.c_int, ctypes.c_int)
        acl_get_fd_np.restype = ctypes.c_void_p
        acl_get_entry = libc.acl_get_entry
        acl_get_entry.argtypes = (
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_void_p),
        )
        acl_get_entry.restype = ctypes.c_int
        acl_get_tag_type = libc.acl_get_tag_type
        acl_get_tag_type.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_int),
        )
        acl_get_tag_type.restype = ctypes.c_int
        acl_free = libc.acl_free
        acl_free.argtypes = (ctypes.c_void_p,)
        acl_free.restype = ctypes.c_int
    except (AttributeError, OSError) as exc:
        raise ValueError(f"{purpose} access controls cannot be verified") from exc
    ctypes.set_errno(0)
    acl = acl_get_fd_np(descriptor, 0x100)
    if not acl:
        if ctypes.get_errno() == errno.ENOENT:
            return ()
        raise ValueError(f"{purpose} access controls cannot be verified")
    try:
        tags: list[int] = []
        for index in range(170):
            ctypes.set_errno(0)
            entry = ctypes.c_void_p()
            entry_selector = 0 if index == 0 else -1  # FIRST, then NEXT
            entry_result = acl_get_entry(acl, entry_selector, ctypes.byref(entry))
            if entry_result == -1 and ctypes.get_errno() == errno.EINVAL and index:
                break
            if entry_result != 0 or entry.value is None:
                raise ValueError(f"{purpose} access controls cannot be verified")
            tag = ctypes.c_int()
            if acl_get_tag_type(entry, ctypes.byref(tag)) != 0:
                raise ValueError(f"{purpose} access controls cannot be verified")
            tags.append(tag.value)
        else:
            raise ValueError(f"{purpose} access controls cannot be verified")
    finally:
        free_result = acl_free(acl)
    if free_result != 0:
        raise ValueError(f"{purpose} access controls cannot be verified")
    return tuple(tags)


def _require_no_extended_acl_fd(descriptor: int, *, purpose: str) -> None:
    if _darwin_extended_acl_tags(descriptor, purpose=purpose):
        raise ValueError(f"{purpose} must not have an extended ACL")


def _require_no_extended_acl_grants_fd(
    descriptor: int,
    *,
    purpose: str,
) -> None:
    if any(
        tag != 2 for tag in _darwin_extended_acl_tags(descriptor, purpose=purpose)
    ):
        raise ValueError(f"{purpose} has unsafe extended ACL grants")


def _private_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_uid,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _require_root_owned_lexical_symlinks(path: Path, *, purpose: str) -> None:
    if not path.is_absolute():
        raise ValueError(f"{purpose} must be absolute")
    nofollow_flag = getattr(os, "O_NOFOLLOW", 0)
    if not nofollow_flag:
        raise ValueError("private path enforcement is unavailable on this platform")
    lexical = Path(path.anchor)
    try:
        for component in path.parent.parts[1:]:
            lexical /= component
            metadata = os.lstat(lexical)
            if stat.S_ISLNK(metadata.st_mode):
                if metadata.st_uid != 0:
                    raise ValueError(
                        f"{purpose} contains an unsafe linked ancestor"
                    )
                continue
            if (
                not stat.S_ISDIR(metadata.st_mode)
                or metadata.st_uid not in {0, os.getuid()}
                or (
                    stat.S_IMODE(metadata.st_mode) & 0o022
                    and not stat.S_IMODE(metadata.st_mode) & stat.S_ISVTX
                )
            ):
                raise ValueError(f"{purpose} has an unsafe lexical ancestor")
            descriptor = os.open(
                lexical,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_DIRECTORY", 0)
                | nofollow_flag,
            )
            try:
                opened = os.fstat(descriptor)
                if not os.path.samestat(metadata, opened):
                    raise ValueError(
                        f"{purpose} lexical ancestor changed during inspection"
                    )
                _require_no_extended_acl_grants_fd(descriptor, purpose=purpose)
                closed_over = os.fstat(descriptor)
                final = os.lstat(lexical)
            finally:
                os.close(descriptor)
            if (
                _private_identity(opened) != _private_identity(closed_over)
                or _private_identity(opened) != _private_identity(final)
                or not os.path.samestat(opened, final)
            ):
                raise ValueError(
                    f"{purpose} lexical ancestor changed during inspection"
                )
    except OSError as exc:
        raise ValueError(f"{purpose} ancestor is unavailable") from exc


def _require_safe_private_ancestor_chain(path: Path, *, purpose: str) -> None:
    _require_root_owned_lexical_symlinks(path, purpose=purpose)
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"{purpose} is unavailable") from exc
    nofollow_flag = getattr(os, "O_NOFOLLOW_ANY", 0) or getattr(
        os, "O_NOFOLLOW", 0
    )
    if not nofollow_flag:
        raise ValueError("private path enforcement is unavailable on this platform")
    ancestor = resolved.parent
    while True:
        descriptor = -1
        try:
            initial = os.lstat(ancestor)
            if (
                not stat.S_ISDIR(initial.st_mode)
                or initial.st_uid not in {0, os.getuid()}
                or (
                    stat.S_IMODE(initial.st_mode) & 0o022
                    and not stat.S_IMODE(initial.st_mode) & stat.S_ISVTX
                )
            ):
                raise ValueError(f"{purpose} has an unsafe ancestor")
            descriptor = os.open(
                ancestor,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_DIRECTORY", 0)
                | nofollow_flag,
            )
            opened = os.fstat(descriptor)
            if not os.path.samestat(initial, opened):
                raise ValueError(f"{purpose} ancestor changed during inspection")
            _require_no_extended_acl_grants_fd(descriptor, purpose=purpose)
            closed_over = os.fstat(descriptor)
            final = os.lstat(ancestor)
        except OSError as exc:
            raise ValueError(f"{purpose} ancestor is unavailable") from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        if (
            _private_identity(opened) != _private_identity(closed_over)
            or _private_identity(opened) != _private_identity(final)
            or not os.path.samestat(opened, final)
        ):
            raise ValueError(f"{purpose} ancestor changed during inspection")
        if ancestor.parent == ancestor:
            break
        ancestor = ancestor.parent
RECEIPT_NAMES = {
    "prepare_delta": "prepare_delta_phase_receipt.json",
    "verify_delta": "verified_delta_phase_receipt.json",
    "verify_publication": "final_publication_phase_receipt.json",
}
STATUS_BY_PHASE = {
    "prepare_delta": "founder_private_accepted_postmerge_pending",
    "verify_delta": "founder_private_accepted_final_publication_pending",
    "verify_publication": "founder_private_accepted_promotion_blocked",
}
FALSE_AUTHORITY_FIELDS = (
    "independent_promotion_ready",
    "public_quality_claims_allowed",
    "production_authority_added",
    "runtime_model_calls_added",
    "provider_calls_added",
    "execution_authority_added",
    "raw_content_persisted",
)


def _canonical_digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _require_absolute_directory(path: Path, *, purpose: str) -> Path:
    if not path.is_absolute() or path.is_symlink():
        raise ValueError(f"{purpose} must be an absolute regular directory")
    resolved = path.resolve()
    if not resolved.is_dir():
        raise ValueError(f"{purpose} must be an absolute regular directory")
    return resolved


def _read_owner_only_file(path: Path, *, purpose: str) -> tuple[Path, bytes]:
    _require_posix_private_path_support()
    if not path.is_absolute() or path.is_symlink():
        raise ValueError(f"{purpose} must be an absolute regular file")
    _require_safe_private_ancestor_chain(path, purpose=purpose)
    resolved = path.resolve(strict=True)
    initial = os.lstat(resolved)
    if (
        not stat.S_ISREG(initial.st_mode)
        or initial.st_uid != os.getuid()
        or stat.S_IMODE(initial.st_mode) & 0o077
        or initial.st_nlink != 1
        or initial.st_size <= 0
        or initial.st_size > MAX_JSON_BYTES
    ):
        raise ValueError(f"{purpose} must be owner-only")
    nofollow_flag = getattr(os, "O_NOFOLLOW_ANY", 0) or getattr(
        os, "O_NOFOLLOW", 0
    )
    if not nofollow_flag:
        raise ValueError("private path enforcement is unavailable on this platform")
    descriptor = os.open(
        resolved,
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | nofollow_flag,
    )
    try:
        opened = os.fstat(descriptor)
        if not os.path.samestat(initial, opened):
            raise ValueError(f"{purpose} changed during inspection")
        _require_no_extended_acl_fd(descriptor, purpose=purpose)
        chunks: list[bytes] = []
        observed = 0
        while observed <= MAX_JSON_BYTES:
            chunk = os.read(
                descriptor,
                min(64 * 1024, MAX_JSON_BYTES + 1 - observed),
            )
            if not chunk:
                break
            chunks.append(chunk)
            observed += len(chunk)
        closed_over = os.fstat(descriptor)
        final = os.lstat(resolved)
    finally:
        os.close(descriptor)
    if (
        observed != opened.st_size
        or observed > MAX_JSON_BYTES
        or _private_identity(opened) != _private_identity(closed_over)
        or _private_identity(opened) != _private_identity(final)
        or not os.path.samestat(opened, final)
    ):
        raise ValueError(f"{purpose} changed during inspection")
    return resolved, b"".join(chunks)


def _require_owner_only_file(path: Path, *, purpose: str) -> Path:
    resolved, _content = _read_owner_only_file(path, purpose=purpose)
    return resolved


def _prepare_output_directory(path: Path) -> Path:
    _require_posix_private_path_support()
    if not path.is_absolute() or path.is_symlink():
        raise ValueError("output directory must be absolute and owner-only")
    if not path.exists():
        parent = path.parent
        if not parent.exists() or parent.is_symlink():
            raise ValueError("output directory parent must already exist")
        _require_safe_private_ancestor_chain(parent, purpose="output directory parent")
        parent_resolved = parent.resolve(strict=True)
        if path.name in {"", ".", ".."}:
            raise ValueError("output directory name is invalid")
        parent_metadata = os.lstat(parent_resolved)
        if (
            not stat.S_ISDIR(parent_metadata.st_mode)
            or parent_metadata.st_uid not in {0, os.getuid()}
            or (
                stat.S_IMODE(parent_metadata.st_mode) & 0o022
                and not stat.S_IMODE(parent_metadata.st_mode) & stat.S_ISVTX
            )
        ):
            raise ValueError("output directory parent is unsafe")
        nofollow_flag = getattr(os, "O_NOFOLLOW_ANY", 0) or getattr(
            os, "O_NOFOLLOW", 0
        )
        if not nofollow_flag:
            raise ValueError("private path enforcement is unavailable on this platform")
        parent_descriptor = -1
        try:
            parent_descriptor = os.open(
                parent_resolved,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_DIRECTORY", 0)
                | nofollow_flag,
            )
            opened_parent = os.fstat(parent_descriptor)
            if not os.path.samestat(parent_metadata, opened_parent):
                raise ValueError("output directory parent changed during inspection")
            _require_no_extended_acl_grants_fd(
                parent_descriptor,
                purpose="output directory parent",
            )
            os.mkdir(path.name, mode=0o700, dir_fd=parent_descriptor)
        except OSError as exc:
            raise ValueError("output directory is unavailable") from exc
        finally:
            if parent_descriptor >= 0:
                os.close(parent_descriptor)
        path = parent_resolved / path.name
    _require_safe_private_ancestor_chain(path, purpose="output directory")
    resolved = path.resolve(strict=True)
    metadata = os.lstat(resolved)
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) & 0o077
    ):
        raise ValueError("output directory must be absolute and owner-only")
    nofollow_flag = getattr(os, "O_NOFOLLOW_ANY", 0) or getattr(
        os, "O_NOFOLLOW", 0
    )
    if not nofollow_flag:
        raise ValueError("private path enforcement is unavailable on this platform")
    descriptor = -1
    try:
        descriptor = os.open(
            resolved,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_DIRECTORY", 0)
            | nofollow_flag,
        )
        opened = os.fstat(descriptor)
        if not os.path.samestat(metadata, opened):
            raise ValueError("output directory changed during inspection")
        _require_no_extended_acl_fd(descriptor, purpose="output directory")
        closed_over = os.fstat(descriptor)
        final = os.lstat(resolved)
    except OSError as exc:
        raise ValueError("output directory is unavailable") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if (
        _private_identity(opened) != _private_identity(closed_over)
        or _private_identity(opened) != _private_identity(final)
        or not os.path.samestat(opened, final)
    ):
        raise ValueError("output directory changed during inspection")
    return resolved


def _sanitized_environment() -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith(("GIT_", "PIP_", "PYTHON"))
    }
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
            "PIP_CONFIG_FILE": os.devnull,
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_INDEX": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    return environment


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


def _trusted_git_executable() -> Path:
    """Resolve Git across the same OS-administrator trust boundary as the verifier."""

    _require_posix_private_path_support()
    executable_value = shutil.which("git")
    if not executable_value:
        raise RuntimeError("TAW-08 trusted Git executable is unavailable")
    try:
        resolved = Path(executable_value).resolve(strict=True)
        content = resolved.read_bytes()
    except OSError as exc:
        raise RuntimeError("TAW-08 trusted Git executable is unavailable") from exc
    if not resolved.is_file() or not content or len(content) > 256 * 1024 * 1024:
        raise RuntimeError("TAW-08 trusted Git executable is invalid")
    _validate_posix_admin_path(resolved)
    if sys.platform == "darwin":
        if resolved != Path("/usr/bin/git"):
            raise RuntimeError("TAW-08 Git executable lacks trusted provenance")
        signature = subprocess.run(
            (
                "/usr/bin/codesign",
                "--verify",
                "--strict",
                "-R=anchor apple",
                str(resolved),
            ),
            check=False,
            capture_output=True,
            timeout=30,
        )
        if signature.returncode != 0:
            raise RuntimeError("TAW-08 Git executable lacks trusted provenance")
    return resolved


def _git(repository_root: Path, *args: str) -> bytes:
    executable = _trusted_git_executable()
    completed = subprocess.run(
        (str(executable), "--no-replace-objects", *GIT_READ_CONFIG, *args),
        cwd=repository_root,
        env=_sanitized_environment(),
        check=True,
        capture_output=True,
        timeout=120,
    )
    return completed.stdout


def _candidate_source_bytes(
    *,
    candidate_root: Path,
    candidate_revision: str,
    source_path: Path,
    path_ref: str,
) -> bytes:
    relative_path = path_ref.removeprefix("repo-path-ref:")
    expected = (candidate_root / relative_path).resolve()
    if (
        source_path.resolve() != expected
        or source_path.is_symlink()
        or not source_path.is_file()
    ):
        raise ValueError("TAW-08 phase source is outside the candidate")
    content = source_path.read_bytes()
    committed = _git(
        candidate_root,
        "show",
        f"{candidate_revision}:{relative_path}",
    )
    if not content or content != committed:
        raise ValueError("TAW-08 phase source differs from the candidate")
    return content


def _require_isolated_bootstrap() -> None:
    if not (sys.flags.isolated and sys.flags.no_site and sys.flags.dont_write_bytecode):
        raise RuntimeError("TAW-08 phase driver requires -I -B -S")


def _bootstrap_pip_identity(uv_lock: bytes) -> tuple[str, int, str, str]:
    if not uv_lock or len(uv_lock) > 64 * 1024 * 1024:
        raise ValueError("bootstrap lock metadata size is invalid")
    try:
        lock_text = uv_lock.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("bootstrap lock metadata is invalid") from exc
    package_blocks = lock_text.split("\n[[package]]\n")[1:]
    pip_blocks = [
        block
        for block in package_blocks
        if re.search(r'(?m)^name = "pip"$', block) is not None
    ]
    if len(pip_blocks) != 1:
        raise ValueError("bootstrap pip package is ambiguous")
    block = pip_blocks[0]
    versions = re.findall(r'(?m)^version = "([A-Za-z0-9.!+_-]+)"$', block)
    wheel_sections = re.findall(r"(?ms)^wheels = \[\n(.*?)^\]$", block)
    if len(versions) != 1 or len(wheel_sections) != 1:
        raise ValueError("bootstrap pip package is invalid")
    records = [line.strip() for line in wheel_sections[0].splitlines() if line.strip()]
    if len(records) != 1:
        raise ValueError("bootstrap pip wheel is ambiguous")
    record = re.fullmatch(
        r'\{ url = "([^"]+)", hash = "sha256:([0-9a-f]{64})", '
        r'size = ([1-9][0-9]*), upload-time = "[^"]+" \},',
        records[0],
    )
    if record is None:
        raise ValueError("bootstrap pip wheel identity is invalid")
    url, digest, size_value = record.groups()
    parsed = urllib.parse.urlsplit(url)
    filename = urllib.parse.unquote(parsed.path.rsplit("/", 1)[-1])
    expected_filename = f"pip-{versions[0]}-py3-none-any.whl"
    size = int(size_value)
    if (
        parsed.scheme != "https"
        or parsed.netloc != "files.pythonhosted.org"
        or parsed.query
        or parsed.fragment
        or filename != expected_filename
        or size > MAX_BOOTSTRAP_WHEEL_BYTES
    ):
        raise ValueError("bootstrap pip wheel identity is invalid")
    return filename, size, digest, url


def _stage_bootstrap_pip_wheel(
    *,
    locked_wheelhouse: Path,
    identity: tuple[str, int, str, str],
) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    filename, expected_size, expected_digest, _url = identity
    wheel_candidates = tuple(
        path
        for path in locked_wheelhouse.iterdir()
        if re.fullmatch(r"pip-[^-]+-py3-none-any\.whl", path.name)
    )
    if len(wheel_candidates) != 1 or wheel_candidates[0].name != filename:
        raise ValueError("bootstrap pip wheel is unavailable or ambiguous")
    source = wheel_candidates[0]
    if (
        source.is_symlink()
        or not source.is_file()
        or source.parent != locked_wheelhouse
    ):
        raise ValueError("bootstrap pip wheel is unavailable")
    content = source.read_bytes()
    if (
        len(content) != expected_size
        or hashlib.sha256(content).hexdigest() != expected_digest
    ):
        raise ValueError("bootstrap pip wheel differs from uv.lock")
    temporary: tempfile.TemporaryDirectory[str] = tempfile.TemporaryDirectory(
        prefix="uaa-taw08-bootstrap-"
    )
    try:
        root = Path(temporary.name).resolve(strict=True)
        root.chmod(0o700)
        staged = root / filename
        descriptor = os.open(
            staged,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0)
            | (getattr(os, "O_NOFOLLOW_ANY", 0) or getattr(os, "O_NOFOLLOW", 0)),
            0o600,
        )
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                descriptor = -1
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        _verify_staged_bootstrap_pip_wheel(staged, identity=identity)
    except BaseException:
        temporary.cleanup()
        raise
    return temporary, staged


def _verify_staged_bootstrap_pip_wheel(
    staged_pip_wheel: Path,
    *,
    identity: tuple[str, int, str, str],
) -> None:
    filename, expected_size, expected_digest, _url = identity
    resolved, content = _read_owner_only_file(
        staged_pip_wheel,
        purpose="staged bootstrap pip wheel",
    )
    if (
        resolved != staged_pip_wheel.resolve()
        or staged_pip_wheel.name != filename
        or len(content) != expected_size
        or hashlib.sha256(content).hexdigest() != expected_digest
    ):
        raise RuntimeError("bootstrap pip wheel staging drift")


def _install_bootstrap_lock_tooling(staged_pip_wheel: Path) -> None:
    global InvalidMarker
    global Marker
    global canonicalize_name
    global default_environment
    global parse_wheel_filename
    global sys_tags
    global tomllib

    staged_prefix = f"{staged_pip_wheel}{os.sep}"
    sys.path.insert(0, str(staged_pip_wheel))
    importlib.invalidate_caches()
    try:
        toml_module = importlib.import_module("pip._vendor.tomli")
        markers_module = importlib.import_module("pip._vendor.packaging.markers")
        tags_module = importlib.import_module("pip._vendor.packaging.tags")
        utils_module = importlib.import_module("pip._vendor.packaging.utils")
    except (ImportError, OSError) as exc:
        raise RuntimeError("authenticated bootstrap tooling is unavailable") from exc
    for module in (toml_module, markers_module, tags_module, utils_module):
        origin = getattr(module, "__file__", None)
        if not isinstance(origin, str) or not origin.startswith(staged_prefix):
            raise RuntimeError("authenticated bootstrap tooling provenance drift")
    tomllib = toml_module
    InvalidMarker = markers_module.InvalidMarker
    Marker = markers_module.Marker
    default_environment = markers_module.default_environment
    sys_tags = tags_module.sys_tags
    canonicalize_name = utils_module.canonicalize_name
    parse_wheel_filename = utils_module.parse_wheel_filename


def _bootstrap_lock_tooling(
    *,
    candidate_root: Path,
    candidate_revision: str,
    locked_wheelhouse: Path,
) -> tempfile.TemporaryDirectory[str]:
    global _BOOTSTRAP_PIP_IDENTITY

    _candidate_source_bytes(
        candidate_root=candidate_root,
        candidate_revision=candidate_revision,
        source_path=Path(__file__),
        path_ref=DRIVER_PATH_REF,
    )
    _candidate_source_bytes(
        candidate_root=candidate_root,
        candidate_revision=candidate_revision,
        source_path=candidate_root / "pyproject.toml",
        path_ref=PYPROJECT_PATH_REF,
    )
    uv_lock = _candidate_source_bytes(
        candidate_root=candidate_root,
        candidate_revision=candidate_revision,
        source_path=candidate_root / "uv.lock",
        path_ref=UV_LOCK_PATH_REF,
    )
    identity = _bootstrap_pip_identity(uv_lock)
    temporary, staged = _stage_bootstrap_pip_wheel(
        locked_wheelhouse=locked_wheelhouse,
        identity=identity,
    )
    try:
        _verify_staged_bootstrap_pip_wheel(staged, identity=identity)
        _install_bootstrap_lock_tooling(staged)
    except BaseException:
        temporary.cleanup()
        raise
    _BOOTSTRAP_PIP_IDENTITY = identity
    return temporary


def _precheck_clean_worktree(path: Path) -> tuple[Path, str]:
    root = _require_absolute_directory(path, purpose="repository worktree")
    top_level = Path(
        _git(root, "rev-parse", "--show-toplevel").decode("utf-8").strip()
    ).resolve()
    if top_level != root:
        raise ValueError("repository worktree root drift")
    if _git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("repository worktree must be clean")
    hidden = _git(root, "ls-files", "-v", "-z").split(b"\0")
    if any(
        entry
        and (entry[:1] in {b"S", b"s"} or (entry[:1].isalpha() and entry[:1].islower()))
        for entry in hidden
    ):
        raise ValueError("repository worktree contains hidden index entries")
    revision = _git(root, "rev-parse", "HEAD").decode("ascii").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("repository worktree revision is invalid")
    return root, revision


def _require_lock_tooling() -> None:
    if any(
        binding is None
        for binding in (
            tomllib,
            InvalidMarker,
            Marker,
            default_environment,
            sys_tags,
            canonicalize_name,
            parse_wheel_filename,
        )
    ):
        raise RuntimeError("authenticated bootstrap tooling is unavailable")


def _locked_reachable_packages(
    *,
    project_name: str,
    packages: list[object],
    marker_environment: dict[str, str],
) -> dict[str, dict[str, object]]:
    _require_lock_tooling()
    active_by_name: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in packages:
        if not isinstance(item, dict):
            raise ValueError("uv.lock package census is invalid")
        name = item.get("name")
        version = item.get("version")
        markers = item.get("resolution-markers", [])
        if (
            not isinstance(name, str)
            or not isinstance(version, str)
            or not isinstance(markers, list)
            or any(not isinstance(marker, str) for marker in markers)
        ):
            raise ValueError("uv.lock package census is invalid")
        try:
            active = not markers or any(
                Marker(marker).evaluate(marker_environment) for marker in markers
            )
        except InvalidMarker as exc:
            raise ValueError("uv.lock package marker is invalid") from exc
        if active:
            active_by_name[canonicalize_name(name)].append(item)
    project_candidates = active_by_name.get(project_name, [])
    if len(project_candidates) != 1:
        raise ValueError("uv.lock project package is ambiguous")
    selected: dict[str, dict[str, object]] = {project_name: project_candidates[0]}
    active_extras: dict[str, set[str]] = defaultdict(set)
    active_extras[project_name].add("dev")
    pending: deque[str] = deque((project_name,))
    processed_extras: dict[str, frozenset[str]] = {}

    def select_dependency(dependency: object, parent_extras: set[str]) -> None:
        if not isinstance(dependency, dict):
            raise ValueError("uv.lock dependency census is invalid")
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
            raise ValueError("uv.lock dependency census is invalid")
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
                raise ValueError("uv.lock dependency marker is invalid") from exc
        name = canonicalize_name(name_value)
        candidates = [
            item
            for item in active_by_name.get(name, [])
            if version_value is None or item.get("version") == version_value
        ]
        identities = {(str(item.get("version")), id(item)): item for item in candidates}
        if len(identities) != 1:
            raise ValueError(f"uv.lock dependency is ambiguous: {name}")
        package = next(iter(identities.values()))
        existing = selected.get(name)
        if existing is not None and existing is not package:
            raise ValueError(f"uv.lock dependency identity drifts: {name}")
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
            raise ValueError("uv.lock dependency census is invalid")
        for dependency in dependencies:
            select_dependency(dependency, set(extras))
        for extra in extras:
            extra_dependencies = optional_dependencies.get(extra, [])
            if not isinstance(extra_dependencies, list):
                raise ValueError("uv.lock optional dependency is invalid")
            for dependency in extra_dependencies:
                select_dependency(dependency, {extra})
    selected.pop(project_name)
    return selected


def _compatible_locked_wheel_identities(
    *,
    pyproject: bytes,
    uv_lock: bytes,
) -> dict[str, tuple[int, str, str]]:
    _require_lock_tooling()
    if (
        not pyproject
        or len(pyproject) > 4 * 1024 * 1024
        or not uv_lock
        or len(uv_lock) > 64 * 1024 * 1024
    ):
        raise ValueError("locked environment metadata size is invalid")
    try:
        project_payload = tomllib.loads(pyproject.decode("utf-8"))
        lock_payload = tomllib.loads(uv_lock.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ValueError("locked environment metadata is invalid") from exc
    project = project_payload.get("project")
    packages = lock_payload.get("package")
    if (
        not isinstance(project, dict)
        or not isinstance(project.get("name"), str)
        or not isinstance(packages, list)
    ):
        raise ValueError("locked environment metadata is incomplete")
    reachable = _locked_reachable_packages(
        project_name=canonicalize_name(project["name"]),
        packages=packages,
        marker_environment=default_environment(),
    )
    tag_rank = {tag: index for index, tag in enumerate(sys_tags())}
    selected: dict[str, tuple[int, str, str]] = {}
    for name, package in sorted(reachable.items()):
        version = str(package.get("version", ""))
        wheels = package.get("wheels", [])
        if not isinstance(wheels, list):
            raise ValueError("uv.lock wheel census is invalid")
        candidates: list[tuple[int, str, int, str, str]] = []
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
            parsed = urllib.parse.urlsplit(url)
            filename = urllib.parse.unquote(parsed.path.rsplit("/", 1)[-1])
            if (
                parsed.scheme != "https"
                or parsed.netloc != "files.pythonhosted.org"
                or parsed.query
                or parsed.fragment
                or not filename.endswith(".whl")
                or len(filename) > 512
            ):
                continue
            try:
                parsed_name, parsed_version, _build, wheel_tags = (
                    parse_wheel_filename(filename)
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
                    size,
                    digest_ref.removeprefix("sha256:"),
                    url,
                )
            )
        if not candidates:
            raise ValueError(f"no compatible locked wheel artifact: {name}")
        _rank, filename, size, digest, url = min(candidates)
        identity = (size, digest, url)
        existing = selected.get(filename)
        if existing is not None and existing != identity:
            raise ValueError("locked wheel filename is ambiguous")
        selected[filename] = identity
    if not selected or len(selected) > 2_048:
        raise ValueError("locked wheel selection is invalid")
    return selected


def _copy_locked_wheelhouse(
    *, provisioned: Path, selected: Path, pyproject: bytes, uv_lock: bytes
) -> tuple[Path, ...]:
    wheelhouse = _require_absolute_directory(provisioned, purpose="locked wheelhouse")
    locked = _compatible_locked_wheel_identities(
        pyproject=pyproject,
        uv_lock=uv_lock,
    )
    if _BOOTSTRAP_PIP_IDENTITY is not None:
        bootstrap_filename, bootstrap_size, bootstrap_digest, bootstrap_url = (
            _BOOTSTRAP_PIP_IDENTITY
        )
        if locked.get(bootstrap_filename) != (
            bootstrap_size,
            bootstrap_digest,
            bootstrap_url,
        ):
            raise ValueError("bootstrap pip wheel is outside the locked closure")
    selected.mkdir(mode=0o700)
    copied: list[Path] = []
    for filename, (expected_size, expected_digest, _url) in sorted(locked.items()):
        source = wheelhouse / filename
        if source.is_symlink() or not source.is_file() or source.parent != wheelhouse:
            raise ValueError("locked wheel artifact is unavailable")
        content = source.read_bytes()
        if (
            len(content) != expected_size
            or hashlib.sha256(content).hexdigest() != expected_digest
        ):
            raise ValueError("locked wheel artifact differs from uv.lock")
        destination = selected / filename
        shutil.copyfile(source, destination)
        if destination.read_bytes() != content:
            raise RuntimeError("locked wheel copy drift")
        copied.append(destination)
    return tuple(copied)


def _materialize_environment(
    *,
    environment_root: Path,
    selected_wheelhouse: Path,
    wheels: tuple[Path, ...],
) -> Path:
    _require_lock_tooling()
    pip_wheels: list[Path] = []
    remaining: list[Path] = []
    for path in wheels:
        try:
            name, _version, _build, _tags = parse_wheel_filename(path.name)
        except ValueError as exc:
            raise ValueError("locked installer wheel filename is invalid") from exc
        if canonicalize_name(str(name)) == "pip":
            pip_wheels.append(path)
        else:
            remaining.append(path)
    if len(pip_wheels) != 1 or not remaining:
        raise ValueError("locked installer closure is invalid")
    environment = _sanitized_environment()
    create = subprocess.run(
        (sys.executable, "-I", "-B", "-S", "-m", "venv", str(environment_root)),
        env=environment,
        check=False,
        capture_output=True,
        timeout=120,
    )
    if create.returncode != 0:
        raise RuntimeError("locked evaluator environment creation failed")
    scripts = "Scripts" if os.name == "nt" else "bin"
    python_name = "python.exe" if os.name == "nt" else "python"
    environment_python = environment_root / scripts / python_name
    install_pip = subprocess.run(
        (
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
            str(pip_wheels[0]),
        ),
        cwd=selected_wheelhouse,
        env=environment,
        check=False,
        capture_output=True,
        timeout=300,
    )
    if install_pip.returncode != 0:
        raise RuntimeError("locked pip installation failed")
    install = subprocess.run(
        (
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
            *(str(path) for path in remaining),
        ),
        cwd=selected_wheelhouse,
        env=environment,
        check=False,
        capture_output=True,
        timeout=600,
    )
    if install.returncode != 0:
        raise RuntimeError("locked dependency installation failed")
    if not any(path.name.startswith("setuptools-") for path in wheels):
        remove_setuptools = subprocess.run(
            (
                str(environment_python),
                "-I",
                "-B",
                "-m",
                "pip",
                "--isolated",
                "uninstall",
                "--yes",
                "setuptools",
            ),
            cwd=selected_wheelhouse,
            env=environment,
            check=False,
            capture_output=True,
            timeout=120,
        )
        if remove_setuptools.returncode != 0:
            raise RuntimeError("bootstrap setuptools removal failed")
    return environment_python


def _write_private(path: Path, content: bytes) -> None:
    if path.exists():
        _existing, existing_content = _read_owner_only_file(
            path, purpose="existing output"
        )
        if existing_content == content:
            return
        raise FileExistsError(f"refusing to overwrite existing output: {path.name}")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(
        temporary,
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | (getattr(os, "O_NOFOLLOW_ANY", 0) or getattr(os, "O_NOFOLLOW", 0)),
        0o600,
    )
    try:
        os.fchmod(descriptor, 0o600)
        _require_no_extended_acl_fd(descriptor, purpose="new output")
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path, follow_symlinks=False)
        temporary.unlink()
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary.exists():
            temporary.unlink()


def _request_for(
    arguments: argparse.Namespace, roots: dict[str, Path]
) -> dict[str, object]:
    request: dict[str, object] = {
        "schema_version": "uaa-taw08-phase-request.v1",
        "phase": arguments.phase,
        "candidate_repository": str(roots["candidate"]),
        "founder_evidence_path": str(arguments.founder_evidence),
    }
    if arguments.phase in {"verify_delta", "verify_publication"}:
        request["delta_repository"] = str(roots["delta"])
    if arguments.phase == "verify_publication":
        request["publication_repository"] = str(roots["publication"])
        request["verified_delta_receipt_path"] = str(arguments.verified_delta_receipt)
    return request


def _bind_existing_verify_delta_receipt(
    request: dict[str, object], *, output_dir: Path
) -> dict[str, object]:
    existing_receipt = output_dir / RECEIPT_NAMES["verify_delta"]
    existing_artifact = output_dir / next(iter(FINAL_PATHS)).rsplit("/", 1)[-1]
    if existing_artifact.exists() and not existing_receipt.exists():
        raise ValueError("verify_delta output is incomplete")
    if existing_receipt.exists():
        return {
            **request,
            "existing_verified_delta_receipt_path": str(
                _require_owner_only_file(
                    existing_receipt,
                    purpose="existing verified delta phase receipt",
                )
            ),
        }
    return request


def _validate_response(
    response: object,
    *,
    expected_phase: str,
    expected_source_digests: dict[str, str],
) -> tuple[dict[str, object], list[tuple[str, bytes]]]:
    if not isinstance(response, dict) or set(response) != {
        "schema_version",
        "phase",
        "receipt",
        "artifacts",
    }:
        raise ValueError("phase response schema drift")
    if (
        response.get("schema_version") != "uaa-taw08-phase-worker-response.v1"
        or response.get("phase") != expected_phase
        or not isinstance(response.get("receipt"), dict)
        or not isinstance(response.get("artifacts"), list)
    ):
        raise ValueError("phase response schema drift")
    receipt = response["receipt"]
    assert isinstance(receipt, dict)
    digest_payload = {
        key: value for key, value in receipt.items() if key != "receipt_digest_ref"
    }
    if (
        receipt.get("phase") != expected_phase
        or receipt.get("status") != STATUS_BY_PHASE[expected_phase]
        or receipt.get("driver_source_digest_ref")
        != expected_source_digests.get("driver_source_digest_ref")
        or receipt.get("worker_source_digest_ref")
        != expected_source_digests.get("worker_source_digest_ref")
        or receipt.get("receipt_digest_ref") != _canonical_digest(digest_payload)
        or any(receipt.get(field) is not False for field in FALSE_AUTHORITY_FIELDS)
    ):
        raise ValueError("phase receipt status, digest, or authority drift")
    expected_paths = (
        PREPARE_PATHS
        if expected_phase == "prepare_delta"
        else FINAL_PATHS
        if expected_phase == "verify_delta"
        else {}
    )
    artifacts = response["artifacts"]
    assert isinstance(artifacts, list)
    decoded: list[tuple[str, bytes]] = []
    observed: dict[str, str] = {}
    for item in artifacts:
        if not isinstance(item, dict) or set(item) != {
            "path_ref",
            "artifact_kind",
            "content_digest_ref",
            "content_base64",
        }:
            raise ValueError("phase artifact schema drift")
        path_ref = item["path_ref"]
        artifact_kind = item["artifact_kind"]
        if not isinstance(path_ref, str) or not isinstance(artifact_kind, str):
            raise ValueError("phase artifact identity drift")
        try:
            content = base64.b64decode(item["content_base64"], validate=True)
        except (TypeError, ValueError) as exc:
            raise ValueError("phase artifact encoding drift") from exc
        digest_ref = f"sha256:{hashlib.sha256(content).hexdigest()}"
        if (
            not content
            or len(content) > MAX_ARTIFACT_BYTES
            or item["content_digest_ref"] != digest_ref
            or path_ref in observed
        ):
            raise ValueError("phase artifact content drift")
        observed[path_ref] = artifact_kind
        decoded.append((path_ref, content))
    if observed != expected_paths:
        raise ValueError("phase artifact census drift")
    return receipt, decoded


def _invoke_locked_worker(
    *,
    request: dict[str, object],
    candidate_root: Path,
    candidate_revision: str,
    locked_wheelhouse: Path,
) -> tuple[dict[str, object], dict[str, str]]:
    driver_source = _candidate_source_bytes(
        candidate_root=candidate_root,
        candidate_revision=candidate_revision,
        source_path=Path(__file__),
        path_ref=DRIVER_PATH_REF,
    )
    worker_source = _candidate_source_bytes(
        candidate_root=candidate_root,
        candidate_revision=candidate_revision,
        source_path=WORKER_PATH,
        path_ref=WORKER_PATH_REF,
    )
    preflight_source = _candidate_source_bytes(
        candidate_root=candidate_root,
        candidate_revision=candidate_revision,
        source_path=PREFLIGHT_PATH,
        path_ref=PREFLIGHT_PATH_REF,
    )
    source_digests = {
        "driver_source_digest_ref": (
            f"sha256:{hashlib.sha256(driver_source).hexdigest()}"
        ),
        "worker_source_digest_ref": (
            f"sha256:{hashlib.sha256(worker_source).hexdigest()}"
        ),
    }
    request = {**request, **source_digests}
    with tempfile.TemporaryDirectory(prefix="uaa-taw08-phases-") as temporary_value:
        temporary = Path(temporary_value).resolve(strict=True)
        temporary.chmod(0o700)
        worker_root = temporary / "worker-root"
        scripts_root = worker_root / "scripts"
        scripts_root.mkdir(parents=True, mode=0o700)
        staged_worker = scripts_root / WORKER_PATH.name
        staged_worker.write_bytes(worker_source)
        staged_worker.chmod(0o600)
        staged_preflight = scripts_root / PREFLIGHT_PATH.name
        staged_preflight.write_bytes(preflight_source)
        staged_preflight.chmod(0o600)
        pyproject = _candidate_source_bytes(
            candidate_root=candidate_root,
            candidate_revision=candidate_revision,
            source_path=candidate_root / "pyproject.toml",
            path_ref=PYPROJECT_PATH_REF,
        )
        uv_lock = _candidate_source_bytes(
            candidate_root=candidate_root,
            candidate_revision=candidate_revision,
            source_path=candidate_root / "uv.lock",
            path_ref=UV_LOCK_PATH_REF,
        )
        staged_uv_lock = worker_root / "uv.lock"
        staged_uv_lock.write_bytes(uv_lock)
        staged_uv_lock.chmod(0o600)
        selected_wheelhouse = temporary / "selected-wheelhouse"
        wheels = _copy_locked_wheelhouse(
            provisioned=locked_wheelhouse,
            selected=selected_wheelhouse,
            pyproject=pyproject,
            uv_lock=uv_lock,
        )
        environment_root = temporary / "environment"
        environment_python = _materialize_environment(
            environment_root=environment_root,
            selected_wheelhouse=selected_wheelhouse,
            wheels=wheels,
        )
        request_path = temporary / "phase-request.json"
        request_content = (
            json.dumps(request, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        )
        descriptor = os.open(
            request_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(request_content)
        rechecked_root, rechecked_revision = _precheck_clean_worktree(candidate_root)
        if rechecked_root != candidate_root or rechecked_revision != candidate_revision:
            raise ValueError("repository worktree revision drift")
        environment = {
            "PATH": os.environ.get("PATH", ""),
            "UAA_TAW08_LOCKED_CHILD_REVISION": candidate_revision,
            "UAA_TAW08_ENVIRONMENT_ROOT": str(environment_root),
            "UAA_TAW08_LOCKED_WHEELHOUSE": str(selected_wheelhouse),
            "UAA_TAW08_PHASE_REQUEST": str(request_path),
            "UAA_TAW08_PHASE_WORKER_DIGEST": (
                f"sha256:{hashlib.sha256(worker_source).hexdigest()}"
            ),
        }
        if os.name == "nt":
            system_root = os.environ.get("SystemRoot")
            if not system_root:
                raise ValueError("Windows SystemRoot is unavailable")
            environment["SystemRoot"] = system_root
        completed = subprocess.run(
            (
                str(environment_python),
                "-I",
                "-B",
                "-S",
                str(staged_preflight),
                str(staged_worker),
            ),
            cwd=candidate_root,
            env=environment,
            check=False,
            capture_output=True,
            timeout=1_800,
        )
        if completed.returncode != 0:
            raise RuntimeError("locked TAW-08 phase worker failed")
        if not completed.stdout or len(completed.stdout) > MAX_JSON_BYTES:
            raise RuntimeError("locked TAW-08 phase response size is invalid")
        try:
            response = json.loads(completed.stdout)
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
            raise RuntimeError("locked TAW-08 phase response is invalid") from exc
        if not isinstance(response, dict):
            raise RuntimeError("locked TAW-08 phase response is invalid")
        return response, source_digests


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare and verify the exact owner-private TAW-08 M1/M2/M3 "
            "evidence publication phases without modifying a repository."
        )
    )
    subparsers = parser.add_subparsers(dest="phase", required=True)

    def common(command: argparse.ArgumentParser) -> None:
        command.add_argument("--candidate-worktree", type=Path, required=True)
        command.add_argument("--founder-evidence", type=Path, required=True)
        command.add_argument("--locked-wheelhouse", type=Path, required=True)
        command.add_argument("--output-dir", type=Path, required=True)

    prepare = subparsers.add_parser("prepare_delta")
    common(prepare)
    verify_delta = subparsers.add_parser("verify_delta")
    common(verify_delta)
    verify_delta.add_argument("--delta-worktree", type=Path, required=True)
    verify_publication = subparsers.add_parser("verify_publication")
    common(verify_publication)
    verify_publication.add_argument("--delta-worktree", type=Path, required=True)
    verify_publication.add_argument("--publication-worktree", type=Path, required=True)
    verify_publication.add_argument(
        "--verified-delta-receipt", type=Path, required=True
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    bootstrap_temporary: tempfile.TemporaryDirectory[str] | None = None
    try:
        _require_isolated_bootstrap()
        _require_posix_private_path_support()
        arguments = _parser().parse_args(argv)
        locked_wheelhouse = _require_absolute_directory(
            arguments.locked_wheelhouse, purpose="locked wheelhouse"
        )
        candidate_root, candidate_revision = _precheck_clean_worktree(
            arguments.candidate_worktree
        )
        bootstrap_temporary = _bootstrap_lock_tooling(
            candidate_root=candidate_root,
            candidate_revision=candidate_revision,
            locked_wheelhouse=locked_wheelhouse,
        )
        founder_evidence = _require_owner_only_file(
            arguments.founder_evidence, purpose="founder evidence"
        )
        arguments.founder_evidence = founder_evidence
        output_dir = _prepare_output_directory(arguments.output_dir)
        roots = {"candidate": candidate_root}
        if arguments.phase in {"verify_delta", "verify_publication"}:
            delta_root, _delta_revision = _precheck_clean_worktree(
                arguments.delta_worktree
            )
            roots["delta"] = delta_root
        if arguments.phase == "verify_publication":
            publication_root, _publication_revision = _precheck_clean_worktree(
                arguments.publication_worktree
            )
            roots["publication"] = publication_root
            arguments.verified_delta_receipt = _require_owner_only_file(
                arguments.verified_delta_receipt,
                purpose="verified delta phase receipt",
            )
        request = _request_for(arguments, roots)
        if arguments.phase == "verify_delta":
            request = _bind_existing_verify_delta_receipt(
                request,
                output_dir=output_dir,
            )
        response, source_digests = _invoke_locked_worker(
            request=request,
            candidate_root=candidate_root,
            candidate_revision=candidate_revision,
            locked_wheelhouse=locked_wheelhouse,
        )
        receipt, artifacts = _validate_response(
            response,
            expected_phase=arguments.phase,
            expected_source_digests=source_digests,
        )
        receipt_content = (
            json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        )
        _write_private(output_dir / RECEIPT_NAMES[arguments.phase], receipt_content)
        for path_ref, content in artifacts:
            _write_private(output_dir / OUTPUT_NAMES[path_ref], content)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        print("TAW-08 evidence phase blocked: bounded failure", file=sys.stderr)
        return 1
    finally:
        if bootstrap_temporary is not None:
            bootstrap_temporary.cleanup()
    summary = {
        "schema_version": "uaa-taw08-phase-driver-summary.v1",
        "phase": arguments.phase,
        "status": receipt["status"],
        "receipt_digest_ref": receipt["receipt_digest_ref"],
        "artifact_count": len(artifacts),
        "repository_modified": False,
        "independent_promotion_ready": False,
        "public_quality_claims_allowed": False,
        "production_authority_added": False,
    }
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
