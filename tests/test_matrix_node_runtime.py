from __future__ import annotations

import hashlib
import json
import os
import struct
from pathlib import Path

import pytest

import ultimate_ai_agent.core.communications.matrix_session.node_runtime as node_runtime_module
from ultimate_ai_agent.core.communications.matrix_session.node_runtime import (
    copy_matrix_node_runtime_binding,
    resolve_approved_matrix_node_runtime_binding,
    resolve_matrix_node_runtime_binding,
    validate_matrix_node_runtime_version,
)


_MACHO_64_MAGIC = 0xFEEDFACF
_MACHO_ARM64_CPU_TYPE = 0x0100000C
_MACHO_EXECUTE_FILE_TYPE = 2
_MACHO_DYLIB_FILE_TYPE = 6
_LC_LOAD_DYLIB = 0x0C
_LC_RPATH = 0x8000001C


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _command(command: int, value: str) -> bytes:
    encoded = value.encode("utf-8") + b"\0"
    fixed_size = 24 if command == _LC_LOAD_DYLIB else 12
    command_size = fixed_size + len(encoded)
    command_size += (-command_size) % 8
    if command == _LC_LOAD_DYLIB:
        header = struct.pack(
            "<IIIIII",
            command,
            command_size,
            fixed_size,
            0,
            0,
            0,
        )
    else:
        header = struct.pack("<III", command, command_size, fixed_size)
    return header + encoded + (b"\0" * (command_size - fixed_size - len(encoded)))


def _write_macho(
    path: Path,
    *,
    rpaths: tuple[str, ...],
    loads: tuple[str, ...],
    cpu_type: int = _MACHO_ARM64_CPU_TYPE,
    file_type: int = _MACHO_EXECUTE_FILE_TYPE,
    suffix: bytes = b"",
) -> None:
    commands = b"".join(
        [
            *(_command(_LC_RPATH, value) for value in rpaths),
            *(_command(_LC_LOAD_DYLIB, value) for value in loads),
        ]
    )
    header = struct.pack(
        "<IiiIIIII",
        _MACHO_64_MAGIC,
        cpu_type,
        0,
        file_type,
        len(rpaths) + len(loads),
        len(commands),
        0,
        0,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + commands + suffix)
    os.chmod(path, 0o700)


def test_runtime_binding_covers_dependency_bytes_and_detects_change(
    tmp_path: Path,
) -> None:
    node = tmp_path / "runtime" / "bin" / "node"
    dependency = tmp_path / "runtime" / "lib" / "libnode.test.dylib"
    dependency.parent.mkdir(parents=True)
    _write_macho(
        dependency,
        rpaths=(),
        loads=(),
        file_type=_MACHO_DYLIB_FILE_TYPE,
        suffix=b"first-runtime",
    )
    _write_macho(
        node,
        rpaths=("@loader_path/../lib",),
        loads=("@rpath/libnode.test.dylib",),
    )

    first = resolve_matrix_node_runtime_binding(
        node,
        expected_node_sha256=_digest(node),
    )
    _write_macho(
        dependency,
        rpaths=(),
        loads=(),
        file_type=_MACHO_DYLIB_FILE_TYPE,
        suffix=b"second-runtime",
    )
    second = resolve_matrix_node_runtime_binding(
        node,
        expected_node_sha256=_digest(node),
    )

    assert first.binding_ref != second.binding_ref
    with pytest.raises(
        ValueError,
        match="MATRIX_SESSION_NODE_RUNTIME_BINDING_CHANGED",
    ):
        resolve_matrix_node_runtime_binding(
            node,
            expected_node_sha256=_digest(node),
            expected=first,
        )


def test_runtime_binding_rejects_ambiguous_loader_resolution(
    tmp_path: Path,
) -> None:
    node = tmp_path / "runtime" / "bin" / "node"
    first = tmp_path / "runtime" / "lib-first" / "libnode.test.dylib"
    second = tmp_path / "runtime" / "lib-second" / "libnode.test.dylib"
    first.parent.mkdir(parents=True)
    second.parent.mkdir(parents=True)
    _write_macho(
        first,
        rpaths=(),
        loads=(),
        file_type=_MACHO_DYLIB_FILE_TYPE,
        suffix=b"first-runtime",
    )
    _write_macho(
        second,
        rpaths=(),
        loads=(),
        file_type=_MACHO_DYLIB_FILE_TYPE,
        suffix=b"second-runtime",
    )
    _write_macho(
        node,
        rpaths=(
            "@loader_path/../lib-first",
            "@loader_path/../lib-second",
        ),
        loads=("@rpath/libnode.test.dylib",),
    )

    with pytest.raises(
        ValueError,
        match="MATRIX_SESSION_NODE_RUNTIME_DEPENDENCY_AMBIGUOUS",
    ):
        resolve_matrix_node_runtime_binding(
            node,
            expected_node_sha256=_digest(node),
        )


def test_runtime_binding_rejects_script_launcher(tmp_path: Path) -> None:
    node = tmp_path / "node"
    node.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    os.chmod(node, 0o700)

    with pytest.raises(
        ValueError,
        match="MATRIX_SESSION_NODE_RUNTIME_FORMAT_UNSUPPORTED",
    ):
        resolve_matrix_node_runtime_binding(
            node,
            expected_node_sha256=_digest(node),
        )


@pytest.mark.parametrize(
    "load_path",
    (
        "/usr/lib/../local/libuaa-untrusted.dylib",
        "/System/Library/../PrivateFrameworks/libuaa-untrusted.dylib",
    ),
)
def test_runtime_binding_rejects_noncanonical_system_looking_load_path(
    tmp_path: Path,
    load_path: str,
) -> None:
    node = tmp_path / "node"
    _write_macho(node, rpaths=(), loads=(load_path,))

    with pytest.raises(
        ValueError,
        match="MATRIX_SESSION_NODE_RUNTIME_LOAD_PATH_UNSUPPORTED",
    ):
        resolve_matrix_node_runtime_binding(
            node,
            expected_node_sha256=_digest(node),
        )


def test_approved_runtime_requires_exact_repository_binding(
    tmp_path: Path,
) -> None:
    node = tmp_path / "node"
    _write_macho(node, rpaths=(), loads=(), suffix=b"approved")
    binding = resolve_matrix_node_runtime_binding(
        node,
        expected_node_sha256=_digest(node),
    )
    manifest = tmp_path / "node-runtime.json"
    manifest.write_text(
        json.dumps(
            {
                "approved_runtime_bindings": [
                    {
                        "binding_ref": binding.binding_ref,
                        "profile_ref": ("node-runtime-profile-ref:test:22.0.0:arm64"),
                        "root_sha256": binding.executable.expected_sha256,
                        "version_ref": binding.version_ref,
                    }
                ],
                "credential_material_included": False,
                "raw_paths_included": False,
                "schema_version": "uaa-matrix-node-runtime-trust.v1",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    os.chmod(manifest, 0o600)

    assert (
        resolve_approved_matrix_node_runtime_binding(
            node,
            trust_manifest_path=manifest,
        ).binding_ref
        == binding.binding_ref
    )
    _write_macho(node, rpaths=(), loads=(), suffix=b"unapproved")
    with pytest.raises(
        ValueError,
        match="MATRIX_SESSION_NODE_RUNTIME_NOT_APPROVED",
    ):
        resolve_approved_matrix_node_runtime_binding(
            node,
            trust_manifest_path=manifest,
        )


def test_runtime_trust_manifest_rejects_duplicate_binding(
    tmp_path: Path,
) -> None:
    node = tmp_path / "node"
    _write_macho(node, rpaths=(), loads=())
    binding = resolve_matrix_node_runtime_binding(
        node,
        expected_node_sha256=_digest(node),
    )
    item = {
        "binding_ref": binding.binding_ref,
        "profile_ref": "node-runtime-profile-ref:test:22.0.0:arm64",
        "root_sha256": binding.executable.expected_sha256,
        "version_ref": binding.version_ref,
    }
    manifest = tmp_path / "node-runtime.json"
    manifest.write_text(
        json.dumps(
            {
                "approved_runtime_bindings": [item, item],
                "credential_material_included": False,
                "raw_paths_included": False,
                "schema_version": "uaa-matrix-node-runtime-trust.v1",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    os.chmod(manifest, 0o600)

    with pytest.raises(
        ValueError,
        match="MATRIX_SESSION_NODE_RUNTIME_TRUST_INVALID",
    ):
        resolve_approved_matrix_node_runtime_binding(
            node,
            trust_manifest_path=manifest,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("binding_ref", "node-runtime-binding-ref:sha256:not-a-digest"),
        ("profile_ref", "node-runtime-profile-ref:unsafe-path"),
        ("root_sha256", "not-a-digest"),
    ],
)
def test_runtime_trust_manifest_rejects_malformed_refs(
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    node = tmp_path / "node"
    _write_macho(node, rpaths=(), loads=())
    binding = resolve_matrix_node_runtime_binding(
        node,
        expected_node_sha256=_digest(node),
    )
    item = {
        "binding_ref": binding.binding_ref,
        "profile_ref": "node-runtime-profile-ref:test:22.0.0:arm64",
        "root_sha256": binding.executable.expected_sha256,
        "version_ref": binding.version_ref,
    }
    item[field] = value
    manifest = tmp_path / "node-runtime.json"
    manifest.write_text(
        json.dumps(
            {
                "approved_runtime_bindings": [item],
                "credential_material_included": False,
                "raw_paths_included": False,
                "schema_version": "uaa-matrix-node-runtime-trust.v1",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    os.chmod(manifest, 0o600)

    with pytest.raises(
        ValueError,
        match="MATRIX_SESSION_NODE_RUNTIME_TRUST_INVALID",
    ):
        resolve_approved_matrix_node_runtime_binding(
            node,
            trust_manifest_path=manifest,
        )


@pytest.mark.parametrize("unsafe_kind", ["symlink", "fifo", "writable"])
def test_runtime_trust_manifest_rejects_unsafe_file_types_and_modes(
    tmp_path: Path,
    unsafe_kind: str,
) -> None:
    node = tmp_path / "node"
    _write_macho(node, rpaths=(), loads=())
    manifest = tmp_path / "node-runtime.json"
    if unsafe_kind == "symlink":
        target = tmp_path / "target.json"
        target.write_text("{}\n", encoding="utf-8")
        manifest.symlink_to(target)
    elif unsafe_kind == "fifo":
        os.mkfifo(manifest)
    else:
        manifest.write_text("{}\n", encoding="utf-8")
        os.chmod(manifest, 0o666)

    with pytest.raises(
        ValueError,
        match="MATRIX_SESSION_NODE_RUNTIME_DEPENDENCY_UNSAFE",
    ):
        resolve_approved_matrix_node_runtime_binding(
            node,
            trust_manifest_path=manifest,
        )


@pytest.mark.parametrize(
    ("cpu_type", "file_type"),
    [
        (0x01000007, _MACHO_EXECUTE_FILE_TYPE),
        (_MACHO_ARM64_CPU_TYPE, _MACHO_DYLIB_FILE_TYPE),
    ],
)
def test_runtime_binding_rejects_wrong_executable_identity(
    tmp_path: Path,
    cpu_type: int,
    file_type: int,
) -> None:
    node = tmp_path / "node"
    _write_macho(
        node,
        rpaths=(),
        loads=(),
        cpu_type=cpu_type,
        file_type=file_type,
    )

    with pytest.raises(
        ValueError,
        match="MATRIX_SESSION_NODE_RUNTIME_FORMAT_UNSUPPORTED",
    ):
        resolve_matrix_node_runtime_binding(
            node,
            expected_node_sha256=_digest(node),
        )


@pytest.mark.parametrize(
    "output",
    [
        b"v21.9.0\n",
        b"v23.0.0\n",
        b"22.23.1\n",
        b"v22.1\n",
        b"not-node\n",
        b"v22.1.0\n" + (b"x" * 129),
    ],
)
def test_node_runtime_version_rejects_unsupported_output(output: bytes) -> None:
    with pytest.raises(
        ValueError,
        match="MATRIX_SESSION_NODE_RUNTIME_VERSION_UNSUPPORTED",
    ):
        validate_matrix_node_runtime_version(output)


def test_node_runtime_version_accepts_exact_node_22_semver() -> None:
    assert validate_matrix_node_runtime_version(b"v22.23.1\n") == "version-ref:node:22"


def test_runtime_hash_and_graph_are_derived_from_same_descriptor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    node = tmp_path / "runtime" / "bin" / "node"
    replacement = tmp_path / "runtime" / "bin" / "replacement-node"
    dependency = tmp_path / "runtime" / "lib" / "libnode.127.dylib"
    dependency.parent.mkdir(parents=True)
    _write_macho(
        dependency,
        rpaths=(),
        loads=(),
        file_type=_MACHO_DYLIB_FILE_TYPE,
        suffix=b"bound-dependency",
    )
    _write_macho(
        node,
        rpaths=("@loader_path/../lib",),
        loads=("@rpath/libnode.127.dylib",),
        suffix=b"first-generation",
    )
    first_digest = _digest(node)
    _write_macho(
        replacement,
        rpaths=("@loader_path/../lib",),
        loads=("@rpath/libnode.missing.dylib",),
        suffix=b"second-generation",
    )
    node_path = node.resolve()
    original_open = node_runtime_module._open_safe_runtime_file
    swapped = False

    def swap_after_open(path: Path):  # type: ignore[no-untyped-def]
        nonlocal swapped
        descriptor, metadata = original_open(path)
        if path == node_path and not swapped:
            os.replace(replacement, node)
            swapped = True
        return descriptor, metadata

    monkeypatch.setattr(
        node_runtime_module,
        "_open_safe_runtime_file",
        swap_after_open,
    )
    binding = resolve_matrix_node_runtime_binding(
        node,
        expected_node_sha256=first_digest,
    )

    assert swapped is True
    assert binding.executable.expected_sha256 == first_digest
    assert [item.snapshot_relative_path.name for item in binding.dependencies] == [
        "libnode.127.dylib"
    ]
    with pytest.raises(
        ValueError,
        match="MATRIX_SESSION_NODE_RUNTIME_BINDING_CHANGED",
    ):
        copy_matrix_node_runtime_binding(
            binding,
            target_root=tmp_path / "snapshot",
        )


def test_runtime_in_place_mutation_cannot_mix_hash_and_graph(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    node = tmp_path / "runtime" / "bin" / "node"
    replacement = tmp_path / "runtime" / "bin" / "replacement-node"
    dependency = tmp_path / "runtime" / "lib" / "libnode.127.dylib"
    dependency.parent.mkdir(parents=True)
    _write_macho(
        dependency,
        rpaths=(),
        loads=(),
        file_type=_MACHO_DYLIB_FILE_TYPE,
        suffix=b"bound-dependency",
    )
    _write_macho(
        node,
        rpaths=("@loader_path/../lib",),
        loads=("@rpath/libnode.127.dylib",),
        suffix=b"first-generation",
    )
    _write_macho(
        replacement,
        rpaths=("@loader_path/../lib",),
        loads=("@rpath/libnode.missing.dylib",),
        suffix=b"second-generation",
    )
    first_digest = _digest(node)
    node_inode = node.stat().st_ino
    replacement_bytes = replacement.read_bytes()
    original_hash_and_capture = node_runtime_module._hash_and_capture_descriptor
    mutated = False

    def mutate_after_bound_read(descriptor: int):  # type: ignore[no-untyped-def]
        nonlocal mutated
        result = original_hash_and_capture(descriptor)
        if os.fstat(descriptor).st_ino == node_inode and not mutated:
            node.write_bytes(replacement_bytes)
            os.chmod(node, 0o700)
            mutated = True
        return result

    monkeypatch.setattr(
        node_runtime_module,
        "_hash_and_capture_descriptor",
        mutate_after_bound_read,
    )
    binding = resolve_matrix_node_runtime_binding(
        node,
        expected_node_sha256=first_digest,
    )

    assert mutated is True
    assert binding.executable.expected_sha256 == first_digest
    assert [item.snapshot_relative_path.name for item in binding.dependencies] == [
        "libnode.127.dylib"
    ]
    with pytest.raises(
        ValueError,
        match="MATRIX_SESSION_NODE_RUNTIME_BINDING_CHANGED",
    ):
        copy_matrix_node_runtime_binding(
            binding,
            target_root=tmp_path / "snapshot",
        )


def test_runtime_binding_rejects_fifo_dependency_without_blocking(
    tmp_path: Path,
) -> None:
    node = tmp_path / "runtime" / "bin" / "node"
    dependency = tmp_path / "runtime" / "lib" / "libnode.test.dylib"
    dependency.parent.mkdir(parents=True)
    os.mkfifo(dependency)
    _write_macho(
        node,
        rpaths=("@loader_path/../lib",),
        loads=("@rpath/libnode.test.dylib",),
    )

    with pytest.raises(
        ValueError,
        match="MATRIX_SESSION_NODE_RUNTIME_DEPENDENCY_UNSAFE",
    ):
        resolve_matrix_node_runtime_binding(
            node,
            expected_node_sha256=_digest(node),
        )
