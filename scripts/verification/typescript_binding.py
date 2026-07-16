from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import selectors
import signal
import shutil
import stat
import subprocess
import time
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterator


SCHEMA_VERSION = "uaa_typescript_verification_binding.v1"
APPLICATION_REF = "application-ref:control-center"
PACKAGE_REF = "package-ref:typescript"
PLATFORM_PACKAGE_REF = "package-ref:typescript-darwin-arm64"
PLATFORM_REF = "platform-ref:darwin-arm64"
LAUNCHER_REF = "runtime-ref:control-center-tsc-launcher"
PLATFORM_BINARY_REF = "runtime-ref:typescript-darwin-arm64-tsc"
REDACTION_STATUS = "content-free-refs-hashes-counts-only"

PACKAGE_JSON_REF = "package.json"
PACKAGE_LOCK_REF = "package-lock.json"
ROOT_TSCONFIG_REF = "tsconfig.json"
TYPESCRIPT_PACKAGE_LOCK_REF = "node_modules/typescript"
PLATFORM_PACKAGE_NAME = "@typescript/typescript-darwin-arm64"
PLATFORM_PACKAGE_LOCK_REF = f"node_modules/{PLATFORM_PACKAGE_NAME}"
RUNTIME_PACKAGE_JSON_REF = "node_modules/typescript/package.json"
RUNTIME_LAUNCHER_REF = "node_modules/.bin/tsc"
RUNTIME_LAUNCHER_TARGET = "../typescript/bin/tsc"
RUNTIME_LAUNCHER_TARGET_REF = "node_modules/typescript/bin/tsc"
RUNTIME_TSC_LOADER_REF = "node_modules/typescript/lib/tsc.js"
RUNTIME_PLATFORM_RESOLVER_REF = "node_modules/typescript/lib/getExePath.js"
RUNTIME_PLATFORM_PACKAGE_JSON_REF = (
    "node_modules/@typescript/typescript-darwin-arm64/package.json"
)
RUNTIME_PLATFORM_BINARY_REF = "node_modules/@typescript/typescript-darwin-arm64/lib/tsc"

MAX_PACKAGE_JSON_BYTES = 256 * 1024
MAX_PACKAGE_LOCK_BYTES = 8 * 1024 * 1024
MAX_TSCONFIG_BYTES = 256 * 1024
MAX_RUNTIME_BINARY_BYTES = 64 * 1024 * 1024
MAX_NODE_BINARY_BYTES = 256 * 1024 * 1024
MAX_CONFIG_NODES = 32
MAX_CONFIG_EDGES = 128
MAX_DEPENDENCY_ENTRIES = 10_000
MAX_COMMAND_BYTES = 512
MAX_PROBE_BYTES = 128
MAX_PATH_BYTES = 16 * 1024
MAX_PATH_ENTRIES = 128
PROBE_TIMEOUT_SECONDS = 10.0

STABLE_TYPESCRIPT_VERSION_PATTERN = re.compile(
    r"^(?P<major>0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)
SAFE_REASON_REF_PATTERN = re.compile(r"^[a-z0-9][a-z0-9:._-]{0,191}$")
INTEGRITY_PATTERN = re.compile(r"^sha512-[A-Za-z0-9+/]+={0,2}$")
PROBE_OUTPUT_PATTERN = re.compile(rb"^Version ([0-9]+\.[0-9]+\.[0-9]+)\r?\n?$")
NODE_PROBE_OUTPUT_PATTERN = re.compile(rb"^v(22\.[0-9]+\.[0-9]+)\r?\n?$")
EXPECTED_LAUNCHER_BYTES = b'#!/usr/bin/env node\nimport "../lib/tsc.js";\n'
MACHO_ARM64_HEADER = bytes.fromhex("cffaedfe0c000001")

DECLARED_COMMAND_KEYS = ("build", "lint", "typecheck")
DECLARED_COMMAND_REFS = tuple(
    f"command:frontend.{key}" for key in DECLARED_COMMAND_KEYS
)


class TypeScriptBindingError(RuntimeError):
    """A content-free fail-closed TypeScript verification error."""

    def __init__(self, reason_ref: str) -> None:
        if SAFE_REASON_REF_PATTERN.fullmatch(reason_ref) is None:
            reason_ref = "typescript-binding:invalid-error-ref"
        self.reason_ref = reason_ref
        super().__init__(f"TypeScript verification binding denied: {reason_ref}")


@dataclass(frozen=True)
class TypeScriptConfigGraphBinding:
    node_refs: tuple[str, ...]
    dependency_edges: tuple[tuple[str, str], ...]
    config_count: int
    edge_count: int
    graph_fingerprint: str


@dataclass(frozen=True)
class TypeScriptDeclaredProjectBinding:
    schema_version: str
    application_ref: str
    package_ref: str
    platform_package_ref: str
    expected_platform_ref: str
    expected_launcher_ref: str
    expected_platform_binary_ref: str
    typescript_version: str
    expected_platform_package_version: str
    package_manifest_fingerprint: str
    package_lock_fingerprint: str
    config_graph: TypeScriptConfigGraphBinding
    declared_command_refs: tuple[str, ...]
    declared_command_fingerprint: str
    declared_project_fingerprint: str
    redaction_status: str


@dataclass(frozen=True)
class TypeScriptRuntimeBinding:
    schema_version: str
    application_ref: str
    package_ref: str
    platform_package_ref: str
    platform_ref: str
    launcher_ref: str
    platform_binary_ref: str
    typescript_version: str
    declared_project_fingerprint: str
    runtime_package_fingerprint: str
    runtime_platform_package_fingerprint: str
    runtime_launcher_fingerprint: str
    runtime_tsc_loader_fingerprint: str
    runtime_platform_resolver_fingerprint: str
    runtime_platform_binary_fingerprint: str
    node_version: str
    node_binary_fingerprint: str
    node_path_identity_fingerprint: str
    node_runtime_fingerprint: str
    runtime_version_probe_fingerprint: str
    runtime_file_count: int
    runtime_byte_count: int
    resolved_runtime_fingerprint: str
    redaction_status: str


@dataclass(frozen=True)
class _NodeRuntimeSnapshot:
    binary_path: Path
    version: str
    binary_fingerprint: str
    path_identity_fingerprint: str
    runtime_fingerprint: str
    byte_count: int


@dataclass(frozen=True)
class _TypeScriptRuntimeSnapshot:
    runtime_package_fingerprint: str
    runtime_platform_package_fingerprint: str
    launcher_fingerprint: str
    launcher_target_fingerprint: str
    tsc_loader_fingerprint: str
    platform_resolver_fingerprint: str
    platform_binary_fingerprint: str
    node_runtime: _NodeRuntimeSnapshot
    runtime_byte_count: int


class _DuplicateJsonKey(ValueError):
    pass


def _deny(reason_ref: str) -> None:
    raise TypeScriptBindingError(reason_ref)


def _fingerprint(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _bytes_fingerprint(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _validated_relative_ref(ref: str, *, reason_ref: str) -> tuple[str, ...]:
    if (
        not isinstance(ref, str)
        or not ref
        or len(ref) > 512
        or ref.startswith("./")
        or "\\" in ref
        or unicodedata.normalize("NFC", ref) != ref
        or any(
            unicodedata.category(character) in {"Cc", "Cf", "Cs"}
            for character in ref
        )
    ):
        _deny(reason_ref)
    path = PurePosixPath(ref)
    if (
        path.is_absolute()
        or path.as_posix() != ref
        or path.as_posix() in {"", "."}
        or ".." in path.parts
        or any(
            not part or len(part) > 255 or part != part.strip() for part in path.parts
        )
    ):
        _deny(reason_ref)
    return path.parts


def _open_flags(*, directory: bool = False) -> int:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    if directory:
        flags |= getattr(os, "O_DIRECTORY", 0)
    else:
        flags |= getattr(os, "O_NONBLOCK", 0)
    return flags


@contextmanager
def _open_parent_directory(
    application_directory: Path,
    ref: str,
) -> Iterator[tuple[int, str]]:
    parts = _validated_relative_ref(
        ref,
        reason_ref="typescript-binding:unsafe-repository-ref",
    )
    descriptors: list[int] = []
    try:
        try:
            descriptor = os.open(application_directory, _open_flags(directory=True))
        except (OSError, TypeError, ValueError):
            _deny("typescript-binding:unsafe-application-directory")
        descriptors.append(descriptor)
        root_info = os.fstat(descriptor)
        if not stat.S_ISDIR(root_info.st_mode):
            _deny("typescript-binding:unsafe-application-directory")
        for part in parts[:-1]:
            try:
                next_descriptor = os.open(
                    part,
                    _open_flags(directory=True),
                    dir_fd=descriptor,
                )
            except (OSError, TypeError, ValueError):
                _deny("typescript-binding:unsafe-parent-directory")
            descriptors.append(next_descriptor)
            descriptor = next_descriptor
            if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
                _deny("typescript-binding:unsafe-parent-directory")
        yield descriptor, parts[-1]
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _read_bounded_bytes(
    application_directory: Path,
    ref: str,
    *,
    limit: int,
    executable: bool = False,
    invalid_reason_ref: str = "typescript-binding:unsafe-file",
) -> bytes:
    with _open_parent_directory(application_directory, ref) as (parent_fd, leaf):
        try:
            descriptor = os.open(leaf, _open_flags(), dir_fd=parent_fd)
        except (OSError, TypeError, ValueError):
            _deny(invalid_reason_ref)
        try:
            before = os.fstat(descriptor)
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
                or before.st_size < 0
                or before.st_size > limit
                or (executable and before.st_mode & 0o111 == 0)
            ):
                _deny(invalid_reason_ref)
            chunks: list[bytes] = []
            remaining = limit + 1
            while remaining > 0:
                chunk = os.read(descriptor, min(64 * 1024, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            payload = b"".join(chunks)
            after = os.fstat(descriptor)
            if (
                len(payload) > limit
                or len(payload) != before.st_size
                or (
                    before.st_dev,
                    before.st_ino,
                    before.st_size,
                    before.st_mtime_ns,
                )
                != (
                    after.st_dev,
                    after.st_ino,
                    after.st_size,
                    after.st_mtime_ns,
                )
            ):
                _deny(invalid_reason_ref)
            return payload
        except OSError:
            _deny(invalid_reason_ref)
        finally:
            try:
                os.close(descriptor)
            except OSError:
                pass


def _read_bounded_json(
    application_directory: Path,
    ref: str,
    *,
    limit: int,
    invalid_reason_ref: str,
) -> tuple[dict[str, Any], str]:
    payload = _read_bounded_bytes(
        application_directory,
        ref,
        limit=limit,
        invalid_reason_ref=invalid_reason_ref,
    )

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise _DuplicateJsonKey
            value[key] = item
        return value

    def reject_non_finite_constant(_value: str) -> None:
        raise ValueError

    try:
        decoded = payload.decode("utf-8")
        value = json.loads(
            decoded,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_non_finite_constant,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        _DuplicateJsonKey,
        RecursionError,
        ValueError,
    ):
        _deny(invalid_reason_ref)
    if not isinstance(value, dict):
        _deny(invalid_reason_ref)
    return value, _bytes_fingerprint(payload)


def _read_exact_symlink(
    application_directory: Path,
    ref: str,
    *,
    expected_target: str,
) -> str:
    with _open_parent_directory(application_directory, ref) as (parent_fd, leaf):
        try:
            before = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
            if not stat.S_ISLNK(before.st_mode):
                _deny("typescript-runtime:launcher-not-exact-symlink")
            target = os.readlink(leaf, dir_fd=parent_fd)
            after = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        except (OSError, TypeError, ValueError):
            _deny("typescript-runtime:launcher-not-exact-symlink")
    if (
        target != expected_target
        or len(target) > 128
        or (before.st_dev, before.st_ino, before.st_mtime_ns)
        != (after.st_dev, after.st_ino, after.st_mtime_ns)
    ):
        _deny("typescript-runtime:launcher-target-mismatch")
    return _fingerprint({"target_ref": LAUNCHER_REF, "target": expected_target})


def _mapping(value: object, *, reason_ref: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        _deny(reason_ref)
    return value


def _dependency_mapping(value: object, *, reason_ref: str) -> dict[str, str]:
    mapping = _mapping(value, reason_ref=reason_ref)
    if len(mapping) > MAX_DEPENDENCY_ENTRIES or not all(
        isinstance(item, str) for item in mapping.values()
    ):
        _deny(reason_ref)
    return mapping  # type: ignore[return-value]


def _is_forbidden_typescript_package(name: str) -> bool:
    normalized = name.casefold()
    compact = re.sub(r"[^a-z0-9]", "", normalized)
    return (
        "typescript" in normalized
        and ("native-preview" in normalized or "compat" in normalized)
    ) or compact in {
        "typescript6",
        "typescriptv6",
        "typescriptlegacy",
        "typescriptts6",
    }


def _is_forbidden_typescript_spec(spec: str) -> bool:
    normalized = spec.casefold().replace(" ", "")
    return (
        "native-preview" in normalized
        or "typescript-compat" in normalized
        or re.search(r"(?:^|:)typescript@[^0-9]*6(?:\.|$)", normalized) is not None
    )


def _assert_no_compatibility_packages(
    package_manifest: dict[str, Any],
    package_lock: dict[str, Any],
) -> None:
    dependency_names: set[str] = set()
    dependency_specs: set[str] = set()
    for key in (
        "dependencies",
        "devDependencies",
        "optionalDependencies",
        "peerDependencies",
    ):
        raw = package_manifest.get(key, {})
        dependencies = _dependency_mapping(
            raw,
            reason_ref="typescript-declaration:dependencies-invalid",
        )
        dependency_names.update(dependencies)
        dependency_specs.update(dependencies.values())
    packages = _mapping(
        package_lock.get("packages"),
        reason_ref="typescript-declaration:lock-packages-invalid",
    )
    if len(packages) > MAX_DEPENDENCY_ENTRIES:
        _deny("typescript-declaration:lock-packages-invalid")
    for package_path, package_value in packages.items():
        if package_path:
            dependency_names.add(package_path.rsplit("node_modules/", maxsplit=1)[-1])
        if isinstance(package_value, dict) and isinstance(package_value.get("name"), str):
            dependency_names.add(package_value["name"])
    if any(
        _is_forbidden_typescript_package(name) for name in dependency_names
    ) or any(_is_forbidden_typescript_spec(spec) for spec in dependency_specs):
        _deny("typescript-declaration:compatibility-package-denied")


def _stable_typescript_version(value: object) -> str:
    if not isinstance(value, str):
        _deny("typescript-declaration:version-not-exact-stable")
    match = STABLE_TYPESCRIPT_VERSION_PATTERN.fullmatch(value)
    if match is None or int(match.group("major")) != 7:
        _deny("typescript-declaration:version-not-exact-stable")
    return value


def _assert_registry_lock_entry(
    entry: dict[str, Any],
    *,
    version: str,
    expected_resolved: str,
) -> None:
    if (
        entry.get("version") != version
        or entry.get("resolved") != expected_resolved
        or not isinstance(entry.get("integrity"), str)
        or INTEGRITY_PATTERN.fullmatch(entry["integrity"]) is None
        or entry.get("link") is not None
    ):
        _deny("typescript-declaration:lock-entry-invalid")


def _declared_commands(package_manifest: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    scripts = _mapping(
        package_manifest.get("scripts"),
        reason_ref="typescript-declaration:scripts-invalid",
    )
    selected: list[tuple[str, str]] = []
    for key in DECLARED_COMMAND_KEYS:
        value = scripts.get(key)
        if (
            not isinstance(value, str)
            or not value
            or len(value.encode("utf-8")) > MAX_COMMAND_BYTES
            or any(unicodedata.category(character) in {"Cc", "Cf", "Cs"} for character in value)
        ):
            _deny("typescript-declaration:script-invalid")
        selected.append((key, value))
    if not scripts["typecheck"].startswith("tsc -b"):
        _deny("typescript-declaration:typecheck-command-invalid")
    if not scripts["lint"].startswith("tsc -b"):
        _deny("typescript-declaration:lint-command-invalid")
    if scripts["build"].split("&&", maxsplit=1)[0].strip() != "tsc -b":
        _deny("typescript-declaration:build-command-invalid")
    return tuple(selected)


def _canonical_config_reference(current_ref: str, raw_ref: object) -> str:
    if not isinstance(raw_ref, str):
        _deny("typescript-declaration:tsconfig-reference-invalid")
    candidate = raw_ref[2:] if raw_ref.startswith("./") else raw_ref
    _validated_relative_ref(
        candidate,
        reason_ref="typescript-declaration:tsconfig-reference-invalid",
    )
    if not candidate.endswith(".json"):
        _deny("typescript-declaration:tsconfig-reference-invalid")
    current_parent = PurePosixPath(current_ref).parent
    canonical = (current_parent / PurePosixPath(candidate)).as_posix()
    _validated_relative_ref(
        canonical,
        reason_ref="typescript-declaration:tsconfig-reference-invalid",
    )
    return canonical


def _config_node_ref(config_ref: str) -> str:
    digest = _bytes_fingerprint(config_ref.encode("utf-8"))
    return f"typescript-config-ref:{digest}"


def _build_config_graph(
    application_directory: Path,
) -> tuple[TypeScriptConfigGraphBinding, tuple[tuple[str, str], ...]]:
    pending = [ROOT_TSCONFIG_REF]
    visit_state: dict[str, int] = {}
    ordered_refs: list[str] = []
    references_by_config: dict[str, tuple[str, ...]] = {}
    config_fingerprints: dict[str, str] = {}

    def visit(config_ref: str) -> None:
        state = visit_state.get(config_ref, 0)
        if state == 1:
            _deny("typescript-declaration:tsconfig-cycle")
        if state == 2:
            return
        if len(visit_state) >= MAX_CONFIG_NODES and config_ref not in visit_state:
            _deny("typescript-declaration:tsconfig-node-bound-exceeded")
        visit_state[config_ref] = 1
        config, config_fingerprint = _read_bounded_json(
            application_directory,
            config_ref,
            limit=MAX_TSCONFIG_BYTES,
            invalid_reason_ref="typescript-declaration:tsconfig-file-invalid",
        )
        if "extends" in config:
            _deny("typescript-declaration:tsconfig-extends-unsupported")
        raw_references = config.get("references", [])
        if not isinstance(raw_references, list) or len(raw_references) > MAX_CONFIG_EDGES:
            _deny("typescript-declaration:tsconfig-references-invalid")
        canonical_references: list[str] = []
        for raw_reference in raw_references:
            reference = _mapping(
                raw_reference,
                reason_ref="typescript-declaration:tsconfig-reference-invalid",
            )
            if set(reference) != {"path"}:
                _deny("typescript-declaration:tsconfig-reference-invalid")
            canonical_ref = _canonical_config_reference(config_ref, reference["path"])
            if canonical_ref == config_ref:
                _deny("typescript-declaration:tsconfig-self-reference")
            canonical_references.append(canonical_ref)
        if len(canonical_references) != len(set(canonical_references)):
            _deny("typescript-declaration:tsconfig-duplicate-reference")
        references_by_config[config_ref] = tuple(canonical_references)
        config_fingerprints[config_ref] = config_fingerprint
        for referenced_config in canonical_references:
            visit(referenced_config)
        visit_state[config_ref] = 2
        ordered_refs.append(config_ref)

    visit(pending[0])
    edge_count = sum(len(refs) for refs in references_by_config.values())
    if edge_count > MAX_CONFIG_EDGES:
        _deny("typescript-declaration:tsconfig-edge-bound-exceeded")
    canonical_node_order = tuple(sorted(ordered_refs))
    node_refs = tuple(_config_node_ref(ref) for ref in canonical_node_order)
    edges = tuple(
        (
            _config_node_ref(config_ref),
            _config_node_ref(dependency_ref),
        )
        for config_ref in canonical_node_order
        for dependency_ref in references_by_config[config_ref]
    )
    graph_payload = {
        "nodes": [
            {
                "config_ref_hash": _bytes_fingerprint(ref.encode("utf-8")),
                "content_fingerprint": config_fingerprints[ref],
                "dependency_ref_hashes": [
                    _bytes_fingerprint(dependency.encode("utf-8"))
                    for dependency in references_by_config[ref]
                ],
            }
            for ref in canonical_node_order
        ]
    }
    graph = TypeScriptConfigGraphBinding(
        node_refs=node_refs,
        dependency_edges=edges,
        config_count=len(node_refs),
        edge_count=edge_count,
        graph_fingerprint=_fingerprint(graph_payload),
    )
    file_fingerprints = tuple(
        (
            _bytes_fingerprint(ref.encode("utf-8")),
            config_fingerprints[ref],
        )
        for ref in canonical_node_order
    )
    return graph, file_fingerprints


def build_declared_typescript_binding(
    application_directory: Path,
) -> TypeScriptDeclaredProjectBinding:
    """Bind the exact declared Control Center TypeScript project without executing it."""

    package_manifest, package_manifest_fingerprint = _read_bounded_json(
        application_directory,
        PACKAGE_JSON_REF,
        limit=MAX_PACKAGE_JSON_BYTES,
        invalid_reason_ref="typescript-declaration:package-manifest-invalid",
    )
    package_lock, package_lock_fingerprint = _read_bounded_json(
        application_directory,
        PACKAGE_LOCK_REF,
        limit=MAX_PACKAGE_LOCK_BYTES,
        invalid_reason_ref="typescript-declaration:package-lock-invalid",
    )
    _assert_no_compatibility_packages(package_manifest, package_lock)

    dependencies = _dependency_mapping(
        package_manifest.get("dependencies", {}),
        reason_ref="typescript-declaration:dependencies-invalid",
    )
    optional_dependencies = _dependency_mapping(
        package_manifest.get("optionalDependencies", {}),
        reason_ref="typescript-declaration:dependencies-invalid",
    )
    peer_dependencies = _dependency_mapping(
        package_manifest.get("peerDependencies", {}),
        reason_ref="typescript-declaration:dependencies-invalid",
    )
    dev_dependencies = _dependency_mapping(
        package_manifest.get("devDependencies"),
        reason_ref="typescript-declaration:dev-dependencies-invalid",
    )
    if "typescript" in dependencies | optional_dependencies | peer_dependencies:
        _deny("typescript-declaration:typescript-not-dev-only")
    version = _stable_typescript_version(dev_dependencies.get("typescript"))

    if package_lock.get("lockfileVersion") != 3:
        _deny("typescript-declaration:lock-version-invalid")
    lock_packages = _mapping(
        package_lock.get("packages"),
        reason_ref="typescript-declaration:lock-packages-invalid",
    )
    root_entry = _mapping(
        lock_packages.get(""),
        reason_ref="typescript-declaration:lock-root-invalid",
    )
    root_dev_dependencies = _dependency_mapping(
        root_entry.get("devDependencies"),
        reason_ref="typescript-declaration:lock-root-invalid",
    )
    for key in ("dependencies", "optionalDependencies", "peerDependencies"):
        if "typescript" in _dependency_mapping(
            root_entry.get(key, {}),
            reason_ref="typescript-declaration:lock-root-invalid",
        ):
            _deny("typescript-declaration:typescript-not-dev-only")
    if root_dev_dependencies.get("typescript") != version:
        _deny("typescript-declaration:lock-root-version-mismatch")

    typescript_entry = _mapping(
        lock_packages.get(TYPESCRIPT_PACKAGE_LOCK_REF),
        reason_ref="typescript-declaration:typescript-lock-entry-missing",
    )
    _assert_registry_lock_entry(
        typescript_entry,
        version=version,
        expected_resolved=(
            f"https://registry.npmjs.org/typescript/-/typescript-{version}.tgz"
        ),
    )
    if typescript_entry.get("bin") != {"tsc": "bin/tsc"}:
        _deny("typescript-declaration:typescript-bin-invalid")
    package_optional_dependencies = _dependency_mapping(
        typescript_entry.get("optionalDependencies"),
        reason_ref="typescript-declaration:platform-optional-dependencies-invalid",
    )
    if package_optional_dependencies.get(PLATFORM_PACKAGE_NAME) != version:
        _deny("typescript-declaration:platform-version-mismatch")

    platform_entry = _mapping(
        lock_packages.get(PLATFORM_PACKAGE_LOCK_REF),
        reason_ref="typescript-declaration:platform-lock-entry-missing",
    )
    _assert_registry_lock_entry(
        platform_entry,
        version=version,
        expected_resolved=(
            "https://registry.npmjs.org/@typescript/typescript-darwin-arm64/-/"
            f"typescript-darwin-arm64-{version}.tgz"
        ),
    )
    if (
        platform_entry.get("optional") is not True
        or platform_entry.get("os") != ["darwin"]
        or platform_entry.get("cpu") != ["arm64"]
    ):
        _deny("typescript-declaration:platform-lock-posture-invalid")

    declared_commands = _declared_commands(package_manifest)
    command_fingerprint = _fingerprint({"commands": declared_commands})
    config_graph, config_file_fingerprints = _build_config_graph(application_directory)
    project_fingerprint = _fingerprint(
        {
            "schema_version": SCHEMA_VERSION,
            "application_ref": APPLICATION_REF,
            "typescript_version": version,
            "package_manifest_fingerprint": package_manifest_fingerprint,
            "package_lock_fingerprint": package_lock_fingerprint,
            "config_file_fingerprints": config_file_fingerprints,
            "config_graph_fingerprint": config_graph.graph_fingerprint,
            "declared_command_fingerprint": command_fingerprint,
            "expected_platform_ref": PLATFORM_REF,
            "expected_platform_package_version": version,
        }
    )
    return TypeScriptDeclaredProjectBinding(
        schema_version=SCHEMA_VERSION,
        application_ref=APPLICATION_REF,
        package_ref=PACKAGE_REF,
        platform_package_ref=PLATFORM_PACKAGE_REF,
        expected_platform_ref=PLATFORM_REF,
        expected_launcher_ref=LAUNCHER_REF,
        expected_platform_binary_ref=PLATFORM_BINARY_REF,
        typescript_version=version,
        expected_platform_package_version=version,
        package_manifest_fingerprint=package_manifest_fingerprint,
        package_lock_fingerprint=package_lock_fingerprint,
        config_graph=config_graph,
        declared_command_refs=DECLARED_COMMAND_REFS,
        declared_command_fingerprint=command_fingerprint,
        declared_project_fingerprint=project_fingerprint,
        redaction_status=REDACTION_STATUS,
    )


def _terminate_probe(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (OSError, ProcessLookupError):
        try:
            process.kill()
        except (OSError, ProcessLookupError):
            pass
    try:
        process.wait(timeout=1)
    except (OSError, subprocess.TimeoutExpired):
        pass


def _run_bounded_probe(
    argv: tuple[str, ...],
    *,
    application_directory: Path,
    reason_stem: str,
) -> bytes:
    environment = {
        "CI": "1",
        "LANG": "C",
        "LC_ALL": "C",
        "NO_COLOR": "1",
        "PATH": "/usr/bin:/bin",
        "TERM": "dumb",
    }
    try:
        process = subprocess.Popen(
            argv,
            cwd=application_directory,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    except (OSError, TypeError, ValueError):
        _deny(f"typescript-runtime:{reason_stem}-probe-start-failed")
    assert process.stdout is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    output = bytearray()
    deadline = time.monotonic() + PROBE_TIMEOUT_SECONDS
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                _terminate_probe(process)
                _deny(f"typescript-runtime:{reason_stem}-probe-timeout")
            events = selector.select(timeout=min(0.1, remaining))
            for key, _ in events:
                try:
                    chunk = os.read(key.fileobj.fileno(), 64)
                except OSError:
                    _terminate_probe(process)
                    _deny(f"typescript-runtime:{reason_stem}-probe-failed")
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                output.extend(chunk)
                if len(output) > MAX_PROBE_BYTES:
                    _terminate_probe(process)
                    _deny(f"typescript-runtime:{reason_stem}-probe-output-bound")
        try:
            return_code = process.wait(timeout=max(0.1, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            _terminate_probe(process)
            _deny(f"typescript-runtime:{reason_stem}-probe-timeout")
        if return_code != 0:
            _deny(f"typescript-runtime:{reason_stem}-probe-failed")
        return bytes(output)
    finally:
        selector.close()
        if process.poll() is None:
            _terminate_probe(process)


def _run_bounded_node_version_probe(
    application_directory: Path,
    node_binary: Path,
) -> bytes:
    return _run_bounded_probe(
        (os.fspath(node_binary), "--version"),
        application_directory=application_directory,
        reason_stem="node-version",
    )


def _run_bounded_version_probe(
    application_directory: Path,
    node_binary: Path,
) -> bytes:
    return _run_bounded_probe(
        (
            os.fspath(node_binary),
            f"./{RUNTIME_LAUNCHER_TARGET_REF}",
            "--version",
        ),
        application_directory=application_directory,
        reason_stem="version",
    )


def _read_external_binary(path: Path) -> bytes:
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        descriptor = os.open(path, flags)
    except (OSError, TypeError, ValueError):
        _deny("typescript-runtime:node-binary-invalid")
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_mode & 0o111 == 0
            or before.st_size <= 0
            or before.st_size > MAX_NODE_BINARY_BYTES
        ):
            _deny("typescript-runtime:node-binary-invalid")
        chunks: list[bytes] = []
        remaining = MAX_NODE_BINARY_BYTES + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        after = os.fstat(descriptor)
        if (
            len(payload) > MAX_NODE_BINARY_BYTES
            or len(payload) != before.st_size
            or (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
            )
            != (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
            )
        ):
            _deny("typescript-runtime:node-binary-invalid")
        return payload
    except OSError:
        _deny("typescript-runtime:node-binary-invalid")
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass


def _validated_node_version(output: bytes) -> str:
    if len(output) > MAX_PROBE_BYTES:
        _deny("typescript-runtime:node-version-probe-output-bound")
    match = NODE_PROBE_OUTPUT_PATTERN.fullmatch(output)
    if match is None:
        _deny("typescript-runtime:node-version-probe-output-invalid")
    try:
        return match.group(1).decode("ascii")
    except UnicodeDecodeError:
        _deny("typescript-runtime:node-version-probe-output-invalid")


def _safe_runtime_path_text(value: str) -> bool:
    return (
        bool(value)
        and len(value.encode("utf-8")) <= MAX_PATH_BYTES
        and unicodedata.normalize("NFC", value) == value
        and not any(
            unicodedata.category(character) in {"Cc", "Cf", "Cs"}
            for character in value
        )
    )


def _capture_node_runtime(application_directory: Path) -> _NodeRuntimeSnapshot:
    path_value = os.environ.get("PATH")
    if not isinstance(path_value, str) or not _safe_runtime_path_text(path_value):
        _deny("typescript-runtime:node-path-invalid")
    path_entries = path_value.split(os.pathsep)
    if not path_entries or len(path_entries) > MAX_PATH_ENTRIES:
        _deny("typescript-runtime:node-path-invalid")
    for path_entry in path_entries:
        if (
            not _safe_runtime_path_text(path_entry)
            or not Path(path_entry).is_absolute()
            or ".." in Path(path_entry).parts
        ):
            _deny("typescript-runtime:node-path-invalid")
    candidate_text = shutil.which("node", path=path_value)
    if candidate_text is None or not _safe_runtime_path_text(candidate_text):
        _deny("typescript-runtime:node-not-found")
    candidate = Path(candidate_text)
    if not candidate.is_absolute():
        _deny("typescript-runtime:node-path-invalid")
    try:
        candidate_info = candidate.lstat()
    except OSError:
        _deny("typescript-runtime:node-binary-invalid")
    symlink_target_hash: str | None = None
    if stat.S_ISLNK(candidate_info.st_mode):
        try:
            target_text = os.readlink(candidate)
        except OSError:
            _deny("typescript-runtime:node-binary-invalid")
        if not _safe_runtime_path_text(target_text):
            _deny("typescript-runtime:node-path-invalid")
        symlink_target_hash = _bytes_fingerprint(target_text.encode("utf-8"))
    elif not stat.S_ISREG(candidate_info.st_mode):
        _deny("typescript-runtime:node-binary-invalid")
    try:
        resolved = candidate.resolve(strict=True)
        resolved_info = resolved.lstat()
    except (OSError, RuntimeError):
        _deny("typescript-runtime:node-binary-invalid")
    if (
        not resolved.is_absolute()
        or not _safe_runtime_path_text(os.fspath(resolved))
        or not stat.S_ISREG(resolved_info.st_mode)
        or resolved_info.st_nlink != 1
        or resolved_info.st_mode & 0o111 == 0
    ):
        _deny("typescript-runtime:node-binary-invalid")
    node_binary = _read_external_binary(resolved)
    if not node_binary.startswith(MACHO_ARM64_HEADER):
        _deny("typescript-runtime:node-binary-architecture-mismatch")
    version_output = _run_bounded_node_version_probe(application_directory, resolved)
    version = _validated_node_version(version_output)
    binary_fingerprint = _bytes_fingerprint(node_binary)
    path_identity_fingerprint = _fingerprint(
        {
            "candidate_path_hash": _bytes_fingerprint(candidate_text.encode("utf-8")),
            "resolved_path_hash": _bytes_fingerprint(os.fsencode(resolved)),
            "symlink_target_hash": symlink_target_hash,
        }
    )
    runtime_fingerprint = _fingerprint(
        {
            "version": version,
            "binary_fingerprint": binary_fingerprint,
            "path_identity_fingerprint": path_identity_fingerprint,
            "byte_count": len(node_binary),
        }
    )
    return _NodeRuntimeSnapshot(
        binary_path=resolved,
        version=version,
        binary_fingerprint=binary_fingerprint,
        path_identity_fingerprint=path_identity_fingerprint,
        runtime_fingerprint=runtime_fingerprint,
        byte_count=len(node_binary),
    )


def _validated_probe_version(output: bytes, *, expected_version: str) -> str:
    if len(output) > MAX_PROBE_BYTES:
        _deny("typescript-runtime:version-probe-output-bound")
    match = PROBE_OUTPUT_PATTERN.fullmatch(output)
    if match is None:
        _deny("typescript-runtime:version-probe-output-invalid")
    try:
        version = match.group(1).decode("ascii")
    except UnicodeDecodeError:
        _deny("typescript-runtime:version-probe-output-invalid")
    if version != expected_version:
        _deny("typescript-runtime:version-probe-version-mismatch")
    return version


def _capture_typescript_runtime(
    application_directory: Path,
    declared_binding: TypeScriptDeclaredProjectBinding,
) -> _TypeScriptRuntimeSnapshot:
    runtime_package, runtime_package_fingerprint = _read_bounded_json(
        application_directory,
        RUNTIME_PACKAGE_JSON_REF,
        limit=MAX_PACKAGE_JSON_BYTES,
        invalid_reason_ref="typescript-runtime:package-invalid",
    )
    imports = runtime_package.get("imports")
    if (
        runtime_package.get("name") != "typescript"
        or runtime_package.get("version") != declared_binding.typescript_version
        or runtime_package.get("bin")
        not in ({"tsc": "bin/tsc"}, {"tsc": "./bin/tsc"})
        or not isinstance(imports, dict)
        or imports.get("#getExePath") != "./lib/getExePath.js"
    ):
        _deny("typescript-runtime:package-mismatch")

    runtime_platform_package, runtime_platform_package_fingerprint = (
        _read_bounded_json(
            application_directory,
            RUNTIME_PLATFORM_PACKAGE_JSON_REF,
            limit=MAX_PACKAGE_JSON_BYTES,
            invalid_reason_ref="typescript-runtime:platform-package-invalid",
        )
    )
    if (
        runtime_platform_package.get("name") != PLATFORM_PACKAGE_NAME
        or runtime_platform_package.get("version")
        != declared_binding.expected_platform_package_version
        or runtime_platform_package.get("os") != ["darwin"]
        or runtime_platform_package.get("cpu") != ["arm64"]
    ):
        _deny("typescript-runtime:platform-package-mismatch")

    symlink_fingerprint = _read_exact_symlink(
        application_directory,
        RUNTIME_LAUNCHER_REF,
        expected_target=RUNTIME_LAUNCHER_TARGET,
    )
    launcher_bytes = _read_bounded_bytes(
        application_directory,
        RUNTIME_LAUNCHER_TARGET_REF,
        limit=MAX_PACKAGE_JSON_BYTES,
        executable=True,
        invalid_reason_ref="typescript-runtime:launcher-target-invalid",
    )
    if launcher_bytes != EXPECTED_LAUNCHER_BYTES:
        _deny("typescript-runtime:launcher-content-mismatch")
    launcher_target_fingerprint = _bytes_fingerprint(launcher_bytes)

    tsc_loader = _read_bounded_bytes(
        application_directory,
        RUNTIME_TSC_LOADER_REF,
        limit=MAX_PACKAGE_JSON_BYTES,
        invalid_reason_ref="typescript-runtime:tsc-loader-invalid",
    )
    platform_resolver = _read_bounded_bytes(
        application_directory,
        RUNTIME_PLATFORM_RESOLVER_REF,
        limit=MAX_PACKAGE_JSON_BYTES,
        invalid_reason_ref="typescript-runtime:platform-resolver-invalid",
    )
    if not tsc_loader or not platform_resolver:
        _deny("typescript-runtime:intermediary-module-invalid")

    platform_binary = _read_bounded_bytes(
        application_directory,
        RUNTIME_PLATFORM_BINARY_REF,
        limit=MAX_RUNTIME_BINARY_BYTES,
        executable=True,
        invalid_reason_ref="typescript-runtime:platform-binary-invalid",
    )
    if len(platform_binary) < len(MACHO_ARM64_HEADER) or not platform_binary.startswith(
        MACHO_ARM64_HEADER
    ):
        _deny("typescript-runtime:platform-binary-architecture-mismatch")
    node_runtime = _capture_node_runtime(application_directory)
    return _TypeScriptRuntimeSnapshot(
        runtime_package_fingerprint=runtime_package_fingerprint,
        runtime_platform_package_fingerprint=runtime_platform_package_fingerprint,
        launcher_fingerprint=symlink_fingerprint,
        launcher_target_fingerprint=launcher_target_fingerprint,
        tsc_loader_fingerprint=_bytes_fingerprint(tsc_loader),
        platform_resolver_fingerprint=_bytes_fingerprint(platform_resolver),
        platform_binary_fingerprint=_bytes_fingerprint(platform_binary),
        node_runtime=node_runtime,
        runtime_byte_count=(
            len(launcher_bytes)
            + len(tsc_loader)
            + len(platform_resolver)
            + len(platform_binary)
            + node_runtime.byte_count
        ),
    )


def resolve_typescript_runtime_binding(
    application_directory: Path,
    declared_binding: TypeScriptDeclaredProjectBinding,
) -> TypeScriptRuntimeBinding:
    """Validate an npm-ci runtime with a bounded version-only probe.

    This does not typecheck, load the compiler API, or persist process output.
    """

    if not isinstance(declared_binding, TypeScriptDeclaredProjectBinding):
        _deny("typescript-runtime:declared-binding-invalid")
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        _deny("typescript-runtime:platform-mismatch")
    current_declaration = build_declared_typescript_binding(application_directory)
    if current_declaration != declared_binding:
        _deny("typescript-runtime:declaration-drift")

    before = _capture_typescript_runtime(application_directory, declared_binding)
    runtime_launcher_fingerprint = _fingerprint(
        {
            "symlink_fingerprint": before.launcher_fingerprint,
            "target_fingerprint": before.launcher_target_fingerprint,
        }
    )
    probe_output = _run_bounded_version_probe(
        application_directory,
        before.node_runtime.binary_path,
    )
    _validated_probe_version(
        probe_output,
        expected_version=declared_binding.typescript_version,
    )

    after = _capture_typescript_runtime(application_directory, declared_binding)
    if (
        after != before
        or build_declared_typescript_binding(application_directory) != declared_binding
    ):
        _deny("typescript-runtime:runtime-drift")

    probe_fingerprint = _bytes_fingerprint(probe_output)
    runtime_byte_count = before.runtime_byte_count
    runtime_fingerprint = _fingerprint(
        {
            "schema_version": SCHEMA_VERSION,
            "declared_project_fingerprint": declared_binding.declared_project_fingerprint,
            "runtime_package_fingerprint": before.runtime_package_fingerprint,
            "runtime_platform_package_fingerprint": before.runtime_platform_package_fingerprint,
            "runtime_launcher_fingerprint": runtime_launcher_fingerprint,
            "runtime_tsc_loader_fingerprint": before.tsc_loader_fingerprint,
            "runtime_platform_resolver_fingerprint": before.platform_resolver_fingerprint,
            "runtime_platform_binary_fingerprint": before.platform_binary_fingerprint,
            "node_runtime_fingerprint": before.node_runtime.runtime_fingerprint,
            "runtime_version_probe_fingerprint": probe_fingerprint,
            "runtime_file_count": 8,
            "runtime_byte_count": runtime_byte_count,
            "platform_ref": PLATFORM_REF,
        }
    )
    return TypeScriptRuntimeBinding(
        schema_version=SCHEMA_VERSION,
        application_ref=APPLICATION_REF,
        package_ref=PACKAGE_REF,
        platform_package_ref=PLATFORM_PACKAGE_REF,
        platform_ref=PLATFORM_REF,
        launcher_ref=LAUNCHER_REF,
        platform_binary_ref=PLATFORM_BINARY_REF,
        typescript_version=declared_binding.typescript_version,
        declared_project_fingerprint=declared_binding.declared_project_fingerprint,
        runtime_package_fingerprint=before.runtime_package_fingerprint,
        runtime_platform_package_fingerprint=before.runtime_platform_package_fingerprint,
        runtime_launcher_fingerprint=runtime_launcher_fingerprint,
        runtime_tsc_loader_fingerprint=before.tsc_loader_fingerprint,
        runtime_platform_resolver_fingerprint=before.platform_resolver_fingerprint,
        runtime_platform_binary_fingerprint=before.platform_binary_fingerprint,
        node_version=before.node_runtime.version,
        node_binary_fingerprint=before.node_runtime.binary_fingerprint,
        node_path_identity_fingerprint=before.node_runtime.path_identity_fingerprint,
        node_runtime_fingerprint=before.node_runtime.runtime_fingerprint,
        runtime_version_probe_fingerprint=probe_fingerprint,
        runtime_file_count=8,
        runtime_byte_count=runtime_byte_count,
        resolved_runtime_fingerprint=runtime_fingerprint,
        redaction_status=REDACTION_STATUS,
    )
