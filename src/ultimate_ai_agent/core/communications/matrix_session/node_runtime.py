from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import stat
import struct
from dataclasses import dataclass, field
from pathlib import Path


MATRIX_NODE_RUNTIME_FILE_MAX_BYTES = 256 * 1024 * 1024
MATRIX_NODE_RUNTIME_COMMAND_BYTES_MAX = 8 * 1024 * 1024
MATRIX_NODE_RUNTIME_FILE_COUNT_MAX = 64
MATRIX_NODE_RUNTIME_TOTAL_BYTES_MAX = 1024 * 1024 * 1024
MATRIX_NODE_RUNTIME_VERSION_OUTPUT_MAX_BYTES = 128
MATRIX_NODE_RUNTIME_TRUST_MANIFEST_MAX_BYTES = 16 * 1024
MATRIX_NODE_RUNTIME_VERSION_REF = "version-ref:node:22"
MATRIX_NODE_RUNTIME_PROBE_OUTPUT = b"node22-permission-enforced\n"
MATRIX_NODE_RUNTIME_TRUST_SCHEMA_VERSION = "uaa-matrix-node-runtime-trust.v1"
_MACHO_64_MAGIC = 0xFEEDFACF
_MACHO_HEADER = struct.Struct("<IiiIIIII")
_MACHO_ARM64_CPU_TYPE = 0x0100000C
_MACHO_EXECUTE_FILE_TYPE = 2
_MACHO_DYLIB_FILE_TYPE = 6
_LOAD_DYLIB_COMMANDS = {0x0C, 0x18, 0x1F, 0x20, 0x23}
_RPATH_COMMAND = 0x1C
_SYSTEM_LIBRARY_PREFIXES = ("/System/Library/", "/usr/lib/")
_NODE_22_VERSION_PATTERN = re.compile(rb"v22\.[0-9]+\.[0-9]+\n?")
_CLONEFILE = getattr(ctypes.CDLL(None, use_errno=True), "clonefile", None)
if _CLONEFILE is not None:
    _CLONEFILE.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
    _CLONEFILE.restype = ctypes.c_int


@dataclass(frozen=True, repr=False)
class MatrixNodeRuntimeFileBinding:
    source_path: Path = field(repr=False)
    snapshot_relative_path: Path
    expected_sha256: str
    size_bytes: int


@dataclass(frozen=True, repr=False)
class MatrixNodeRuntimeBinding:
    files: tuple[MatrixNodeRuntimeFileBinding, ...] = field(repr=False)
    binding_ref: str
    version_ref: str = MATRIX_NODE_RUNTIME_VERSION_REF
    trust_profile_ref: str | None = None

    @property
    def executable(self) -> MatrixNodeRuntimeFileBinding:
        return self.files[0]

    @property
    def dependencies(self) -> tuple[MatrixNodeRuntimeFileBinding, ...]:
        return self.files[1:]


@dataclass(frozen=True, repr=False)
class _MatrixNodeRuntimeImage:
    source_path: Path = field(repr=False)
    expected_sha256: str
    size_bytes: int
    load_paths: tuple[str, ...]
    rpaths: tuple[str, ...]


def resolve_matrix_node_runtime_binding(
    node_binary: Path,
    *,
    expected_node_sha256: str,
    expected: MatrixNodeRuntimeBinding | None = None,
) -> MatrixNodeRuntimeBinding:
    return _resolve_matrix_node_runtime_binding(
        node_binary,
        expected_node_sha256=expected_node_sha256,
        expected=expected,
    )


def resolve_approved_matrix_node_runtime_binding(
    node_binary: Path,
    *,
    trust_manifest_path: Path,
) -> MatrixNodeRuntimeBinding:
    resolved = _resolve_matrix_node_runtime_binding(
        node_binary,
        expected_node_sha256=None,
        expected=None,
    )
    manifest = _read_node_runtime_trust_manifest(trust_manifest_path)
    approved = manifest["approved_runtime_bindings"]
    assert isinstance(approved, list)
    for item in approved:
        if (
            item["root_sha256"] == resolved.executable.expected_sha256
            and item["binding_ref"] == resolved.binding_ref
            and item["version_ref"] == resolved.version_ref
        ):
            return MatrixNodeRuntimeBinding(
                files=resolved.files,
                binding_ref=resolved.binding_ref,
                version_ref=resolved.version_ref,
                trust_profile_ref=str(item["profile_ref"]),
            )
    raise ValueError("MATRIX_SESSION_NODE_RUNTIME_NOT_APPROVED")


def _resolve_matrix_node_runtime_binding(
    node_binary: Path,
    *,
    expected_node_sha256: str | None,
    expected: MatrixNodeRuntimeBinding | None,
) -> MatrixNodeRuntimeBinding:
    if not node_binary.is_absolute():
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_ABSOLUTE_PATH_REQUIRED")
    executable_image = _inspect_runtime_image(
        node_binary,
        expected_sha256=expected_node_sha256,
        executable=True,
    )
    executable = _runtime_file_binding(
        executable_image,
        snapshot_relative_path=Path("bin") / "node-runtime",
    )
    pending = [executable_image]
    visited: set[Path] = set()
    inspected: dict[Path, _MatrixNodeRuntimeImage] = {
        executable_image.source_path: executable_image
    }
    dependencies: dict[str, MatrixNodeRuntimeFileBinding] = {}
    total_bytes = executable.size_bytes
    while pending:
        current = pending.pop()
        if current.source_path in visited:
            continue
        visited.add(current.source_path)
        for snapshot_name, dependency in _resolve_non_system_dependencies(
            current,
            executable_path=executable_image.source_path,
        ):
            image = inspected.get(dependency)
            if image is None:
                image = _inspect_runtime_image(
                    dependency,
                    expected_sha256=None,
                    executable=False,
                )
                inspected[image.source_path] = image
            existing = dependencies.get(snapshot_name)
            binding = _runtime_file_binding(
                image,
                snapshot_relative_path=Path("lib") / snapshot_name,
            )
            if existing is not None:
                if (
                    existing.source_path != binding.source_path
                    or existing.expected_sha256 != binding.expected_sha256
                ):
                    raise ValueError("MATRIX_SESSION_NODE_RUNTIME_DEPENDENCY_AMBIGUOUS")
                continue
            dependencies[snapshot_name] = binding
            total_bytes += binding.size_bytes
            if (
                len(dependencies) + 1 > MATRIX_NODE_RUNTIME_FILE_COUNT_MAX
                or total_bytes > MATRIX_NODE_RUNTIME_TOTAL_BYTES_MAX
            ):
                raise ValueError("MATRIX_SESSION_NODE_RUNTIME_CLOSURE_TOO_LARGE")
            pending.append(image)
    files = (executable, *sorted(dependencies.values(), key=_binding_sort_key))
    binding_ref = _runtime_binding_ref(files)
    resolved = MatrixNodeRuntimeBinding(files=files, binding_ref=binding_ref)
    if expected is not None and (
        resolved.binding_ref != expected.binding_ref
        or tuple(
            (item.source_path, item.snapshot_relative_path) for item in resolved.files
        )
        != tuple(
            (item.source_path, item.snapshot_relative_path) for item in expected.files
        )
    ):
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_BINDING_CHANGED")
    return resolved


def _read_node_runtime_trust_manifest(path: Path) -> dict[str, object]:
    descriptor, metadata = _open_safe_runtime_file(path)
    try:
        if metadata.st_size > MATRIX_NODE_RUNTIME_TRUST_MANIFEST_MAX_BYTES:
            raise ValueError("MATRIX_SESSION_NODE_RUNTIME_TRUST_INVALID")
        payload = bytearray()
        while chunk := os.read(descriptor, 16 * 1024):
            payload.extend(chunk)
            if len(payload) > MATRIX_NODE_RUNTIME_TRUST_MANIFEST_MAX_BYTES:
                raise ValueError("MATRIX_SESSION_NODE_RUNTIME_TRUST_INVALID")
    finally:
        os.close(descriptor)
    try:
        manifest = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_TRUST_INVALID") from None
    if (
        not isinstance(manifest, dict)
        or set(manifest)
        != {
            "approved_runtime_bindings",
            "credential_material_included",
            "raw_paths_included",
            "schema_version",
        }
        or manifest.get("schema_version") != MATRIX_NODE_RUNTIME_TRUST_SCHEMA_VERSION
        or manifest.get("raw_paths_included") is not False
        or manifest.get("credential_material_included") is not False
    ):
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_TRUST_INVALID")
    approved = manifest.get("approved_runtime_bindings")
    if not isinstance(approved, list) or not approved or len(approved) > 8:
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_TRUST_INVALID")
    seen: set[tuple[str, str]] = set()
    seen_profiles: set[str] = set()
    for item in approved:
        if not isinstance(item, dict) or set(item) != {
            "binding_ref",
            "profile_ref",
            "root_sha256",
            "version_ref",
        }:
            raise ValueError("MATRIX_SESSION_NODE_RUNTIME_TRUST_INVALID")
        profile_ref = item.get("profile_ref")
        root_sha256 = item.get("root_sha256")
        binding_ref = item.get("binding_ref")
        version_ref = item.get("version_ref")
        if (
            not isinstance(profile_ref, str)
            or re.fullmatch(
                (
                    r"node-runtime-profile-ref:"
                    r"[a-z0-9][a-z0-9.-]{0,63}:"
                    r"[0-9]+\.[0-9]+\.[0-9]+:arm64"
                ),
                profile_ref,
            )
            is None
            or not isinstance(root_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", root_sha256) is None
            or not isinstance(binding_ref, str)
            or re.fullmatch(
                r"node-runtime-binding-ref:sha256:[0-9a-f]{64}",
                binding_ref,
            )
            is None
            or not isinstance(version_ref, str)
            or version_ref != MATRIX_NODE_RUNTIME_VERSION_REF
            or (root_sha256, binding_ref) in seen
            or profile_ref in seen_profiles
        ):
            raise ValueError("MATRIX_SESSION_NODE_RUNTIME_TRUST_INVALID")
        seen.add((root_sha256, binding_ref))
        seen_profiles.add(profile_ref)
    return manifest


def copy_matrix_node_runtime_binding(
    binding: MatrixNodeRuntimeBinding,
    *,
    target_root: Path,
) -> Path:
    target_root.mkdir(mode=0o700, parents=True)
    (target_root / "lib").mkdir(mode=0o700)
    for item in binding.files:
        target = target_root / item.snapshot_relative_path
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        _copy_bound_runtime_file(item, target)
    return target_root / binding.executable.snapshot_relative_path


def matrix_node_runtime_environment(target_root: Path) -> dict[str, str]:
    return {
        "DYLD_LIBRARY_PATH": os.fspath(target_root / "lib"),
        "HOME": "/var/empty",
        "LANG": "C",
        "PATH": "/usr/bin:/bin",
        "TMPDIR": "/tmp",
    }


def validate_matrix_node_runtime_version(output: bytes) -> str:
    if (
        len(output) > MATRIX_NODE_RUNTIME_VERSION_OUTPUT_MAX_BYTES
        or _NODE_22_VERSION_PATTERN.fullmatch(output) is None
    ):
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_VERSION_UNSUPPORTED")
    return MATRIX_NODE_RUNTIME_VERSION_REF


def validate_matrix_node_runtime_probe(output: bytes) -> str:
    if output != MATRIX_NODE_RUNTIME_PROBE_OUTPUT:
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_PERMISSION_PROBE_FAILED")
    return MATRIX_NODE_RUNTIME_VERSION_REF


def _binding_sort_key(
    binding: MatrixNodeRuntimeFileBinding,
) -> tuple[str, str]:
    return (binding.snapshot_relative_path.as_posix(), binding.expected_sha256)


def _runtime_binding_ref(
    files: tuple[MatrixNodeRuntimeFileBinding, ...],
) -> str:
    payload = {
        "version_ref": MATRIX_NODE_RUNTIME_VERSION_REF,
        "files": [
            {
                "relative_path": item.snapshot_relative_path.as_posix(),
                "sha256": item.expected_sha256,
                "size_bytes": item.size_bytes,
            }
            for item in files
        ],
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"node-runtime-binding-ref:sha256:{digest}"


def _inspect_runtime_image(
    path: Path,
    *,
    expected_sha256: str | None,
    executable: bool,
) -> _MatrixNodeRuntimeImage:
    try:
        resolved = path.resolve(strict=True)
    except OSError:
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_DEPENDENCY_MISSING") from None
    descriptor, metadata = _open_safe_runtime_file(resolved)
    try:
        digest, command_prefix = _hash_and_capture_descriptor(descriptor)
        load_paths, rpaths = _macho_load_commands(
            command_prefix,
            metadata,
            executable=executable,
        )
    finally:
        os.close(descriptor)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError("MATRIX_SESSION_RUNTIME_HASH_MISMATCH")
    return _MatrixNodeRuntimeImage(
        source_path=resolved,
        expected_sha256=digest,
        size_bytes=metadata.st_size,
        load_paths=load_paths,
        rpaths=rpaths,
    )


def _runtime_file_binding(
    image: _MatrixNodeRuntimeImage,
    *,
    snapshot_relative_path: Path,
) -> MatrixNodeRuntimeFileBinding:
    return MatrixNodeRuntimeFileBinding(
        source_path=image.source_path,
        snapshot_relative_path=snapshot_relative_path,
        expected_sha256=image.expected_sha256,
        size_bytes=image.size_bytes,
    )


def _copy_bound_runtime_file(
    binding: MatrixNodeRuntimeFileBinding,
    target: Path,
) -> None:
    source_descriptor, source_metadata = _open_safe_runtime_file(binding.source_path)
    target_descriptor: int | None = None
    try:
        if (
            source_metadata.st_size != binding.size_bytes
            or _hash_descriptor(source_descriptor) != binding.expected_sha256
        ):
            raise ValueError("MATRIX_SESSION_NODE_RUNTIME_BINDING_CHANGED")
        os.lseek(source_descriptor, 0, os.SEEK_SET)
        if (
            _CLONEFILE is not None
            and _CLONEFILE(
                os.fsencode(binding.source_path),
                os.fsencode(target),
                0,
            )
            == 0
        ):
            copied_image = _inspect_runtime_image(
                target,
                expected_sha256=binding.expected_sha256,
                executable=binding.snapshot_relative_path.parts[0] == "bin",
            )
            copied = _runtime_file_binding(
                copied_image,
                snapshot_relative_path=binding.snapshot_relative_path,
            )
            if copied.size_bytes != binding.size_bytes:
                raise ValueError("MATRIX_SESSION_NODE_RUNTIME_BINDING_CHANGED")
            return
        target.unlink(missing_ok=True)
        target_descriptor = os.open(
            target,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        digest = hashlib.sha256()
        copied = 0
        while chunk := os.read(source_descriptor, 1024 * 1024):
            copied += len(chunk)
            if copied > binding.size_bytes:
                raise ValueError("MATRIX_SESSION_NODE_RUNTIME_BINDING_CHANGED")
            digest.update(chunk)
            view = memoryview(chunk)
            while view:
                written = os.write(target_descriptor, view)
                view = view[written:]
        if (
            copied != binding.size_bytes
            or digest.hexdigest() != binding.expected_sha256
        ):
            raise ValueError("MATRIX_SESSION_NODE_RUNTIME_BINDING_CHANGED")
        os.fsync(target_descriptor)
    except BaseException:
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    finally:
        if target_descriptor is not None:
            os.close(target_descriptor)
        os.close(source_descriptor)


def _open_safe_runtime_file(path: Path) -> tuple[int, os.stat_result]:
    try:
        path_metadata = os.lstat(path)
    except OSError:
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_DEPENDENCY_UNSAFE") from None
    if (
        not stat.S_ISREG(path_metadata.st_mode)
        or stat.S_ISLNK(path_metadata.st_mode)
        or path_metadata.st_size > MATRIX_NODE_RUNTIME_FILE_MAX_BYTES
        or path_metadata.st_mode & 0o022
    ):
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_DEPENDENCY_UNSAFE")
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY
            | os.O_NONBLOCK
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError:
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_DEPENDENCY_UNSAFE") from None
    try:
        metadata = os.fstat(descriptor)
        current_path_metadata = os.lstat(path)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_size > MATRIX_NODE_RUNTIME_FILE_MAX_BYTES
            or metadata.st_mode & 0o022
            or (metadata.st_dev, metadata.st_ino)
            != (current_path_metadata.st_dev, current_path_metadata.st_ino)
        ):
            raise ValueError("MATRIX_SESSION_NODE_RUNTIME_DEPENDENCY_UNSAFE")
        return descriptor, metadata
    except BaseException:
        os.close(descriptor)
        raise


def _hash_descriptor(descriptor: int) -> str:
    digest, _command_prefix = _hash_and_capture_descriptor(descriptor)
    return digest


def _hash_and_capture_descriptor(descriptor: int) -> tuple[str, bytes]:
    os.lseek(descriptor, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    command_prefix = bytearray()
    capture_limit = _MACHO_HEADER.size + MATRIX_NODE_RUNTIME_COMMAND_BYTES_MAX
    while chunk := os.read(descriptor, 1024 * 1024):
        digest.update(chunk)
        if len(command_prefix) < capture_limit:
            remaining = capture_limit - len(command_prefix)
            command_prefix.extend(chunk[:remaining])
    return digest.hexdigest(), bytes(command_prefix)


def _resolve_non_system_dependencies(
    image: _MatrixNodeRuntimeImage,
    *,
    executable_path: Path,
) -> tuple[tuple[str, Path], ...]:
    dependencies: list[tuple[str, Path]] = []
    for load_path in image.load_paths:
        if load_path.startswith("/") and os.path.normpath(load_path) != load_path:
            raise ValueError("MATRIX_SESSION_NODE_RUNTIME_LOAD_PATH_UNSUPPORTED")
        if _is_system_library(load_path):
            continue
        snapshot_name = Path(load_path).name
        if (
            not snapshot_name
            or snapshot_name in {".", ".."}
            or len(snapshot_name.encode("utf-8")) > 240
            or not snapshot_name.endswith(".dylib")
        ):
            raise ValueError("MATRIX_SESSION_NODE_RUNTIME_LOAD_PATH_UNSUPPORTED")
        candidates = _resolve_load_path_candidates(
            load_path,
            loader_path=image.source_path.parent,
            executable_path=executable_path.parent,
            rpaths=image.rpaths,
        )
        try:
            existing = {
                candidate.resolve(strict=True)
                for candidate in candidates
                if candidate.exists()
            }
        except OSError:
            raise ValueError("MATRIX_SESSION_NODE_RUNTIME_DEPENDENCY_MISSING") from None
        existing = {
            candidate
            for candidate in existing
            if not _is_system_library(str(candidate))
        }
        if not existing:
            raise ValueError("MATRIX_SESSION_NODE_RUNTIME_DEPENDENCY_MISSING")
        if len(existing) != 1:
            raise ValueError("MATRIX_SESSION_NODE_RUNTIME_DEPENDENCY_AMBIGUOUS")
        dependencies.append((snapshot_name, next(iter(existing))))
    return tuple(sorted(set(dependencies)))


def _resolve_load_path_candidates(
    load_path: str,
    *,
    loader_path: Path,
    executable_path: Path,
    rpaths: tuple[str, ...],
) -> tuple[Path, ...]:
    if load_path.startswith("@rpath/"):
        suffix = load_path.removeprefix("@rpath/")
        return tuple(
            _expand_loader_token(
                rpath,
                loader_path=loader_path,
                executable_path=executable_path,
            )
            / suffix
            for rpath in rpaths
        )
    return (
        _expand_loader_token(
            load_path,
            loader_path=loader_path,
            executable_path=executable_path,
        ),
    )


def _expand_loader_token(
    value: str,
    *,
    loader_path: Path,
    executable_path: Path,
) -> Path:
    if value == "@loader_path":
        return loader_path
    if value.startswith("@loader_path/"):
        return loader_path / value.removeprefix("@loader_path/")
    if value == "@executable_path":
        return executable_path
    if value.startswith("@executable_path/"):
        return executable_path / value.removeprefix("@executable_path/")
    if value.startswith("@"):
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_LOAD_PATH_UNSUPPORTED")
    candidate = Path(value)
    return candidate if candidate.is_absolute() else loader_path / candidate


def _is_system_library(value: str) -> bool:
    return value.startswith(_SYSTEM_LIBRARY_PREFIXES)


def _macho_load_commands(
    command_prefix: bytes,
    metadata: os.stat_result,
    *,
    executable: bool,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    header = command_prefix[: _MACHO_HEADER.size]
    if len(header) < 4:
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_FORMAT_UNSUPPORTED")
    magic = struct.unpack_from("<I", header)[0]
    if magic != _MACHO_64_MAGIC:
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_FORMAT_UNSUPPORTED")
    if len(header) != _MACHO_HEADER.size:
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_FORMAT_INVALID")
    (
        _magic,
        cpu_type,
        _subtype,
        file_type,
        command_count,
        command_bytes,
        _flags,
        _reserved,
    ) = _MACHO_HEADER.unpack(header)
    if cpu_type != _MACHO_ARM64_CPU_TYPE or file_type != (
        _MACHO_EXECUTE_FILE_TYPE if executable else _MACHO_DYLIB_FILE_TYPE
    ):
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_FORMAT_UNSUPPORTED")
    if (
        command_count > 4096
        or command_bytes > MATRIX_NODE_RUNTIME_COMMAND_BYTES_MAX
        or _MACHO_HEADER.size + command_bytes > metadata.st_size
    ):
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_FORMAT_INVALID")
    payload = command_prefix[_MACHO_HEADER.size : _MACHO_HEADER.size + command_bytes]
    if len(payload) != command_bytes:
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_FORMAT_INVALID")
    load_paths: list[str] = []
    rpaths: list[str] = []
    offset = 0
    for _index in range(command_count):
        if offset + 8 > len(payload):
            raise ValueError("MATRIX_SESSION_NODE_RUNTIME_FORMAT_INVALID")
        command, command_size = struct.unpack_from("<II", payload, offset)
        if command_size < 8 or offset + command_size > len(payload):
            raise ValueError("MATRIX_SESSION_NODE_RUNTIME_FORMAT_INVALID")
        base_command = command & 0x7FFFFFFF
        if base_command in _LOAD_DYLIB_COMMANDS or base_command == _RPATH_COMMAND:
            if command_size < 12:
                raise ValueError("MATRIX_SESSION_NODE_RUNTIME_FORMAT_INVALID")
            string_offset = struct.unpack_from("<I", payload, offset + 8)[0]
            if string_offset < 8 or string_offset >= command_size:
                raise ValueError("MATRIX_SESSION_NODE_RUNTIME_FORMAT_INVALID")
            raw = payload[offset + string_offset : offset + command_size]
            try:
                value = raw.split(b"\0", 1)[0].decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError("MATRIX_SESSION_NODE_RUNTIME_FORMAT_INVALID") from exc
            if not value or len(value) > 4096:
                raise ValueError("MATRIX_SESSION_NODE_RUNTIME_FORMAT_INVALID")
            if base_command == _RPATH_COMMAND:
                rpaths.append(value)
            else:
                load_paths.append(value)
        offset += command_size
    if offset != len(payload):
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_FORMAT_INVALID")
    return tuple(load_paths), tuple(rpaths)


__all__ = (
    "MATRIX_NODE_RUNTIME_PROBE_OUTPUT",
    "MATRIX_NODE_RUNTIME_VERSION_OUTPUT_MAX_BYTES",
    "MATRIX_NODE_RUNTIME_VERSION_REF",
    "MatrixNodeRuntimeBinding",
    "MatrixNodeRuntimeFileBinding",
    "copy_matrix_node_runtime_binding",
    "matrix_node_runtime_environment",
    "resolve_matrix_node_runtime_binding",
    "validate_matrix_node_runtime_probe",
    "validate_matrix_node_runtime_version",
)
