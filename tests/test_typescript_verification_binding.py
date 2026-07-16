from __future__ import annotations

import dataclasses
import json
import os
import re
from pathlib import Path

import pytest

from scripts.verification import typescript_binding
from scripts.verification.typescript_binding import (
    MACHO_ARM64_HEADER,
    REDACTION_STATUS,
    TypeScriptBindingError,
    build_declared_typescript_binding,
    resolve_typescript_runtime_binding,
)


VERSION = "7.0.2"
INTEGRITY = "sha512-QUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUE="


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _package_manifest(*, version: str = VERSION) -> dict[str, object]:
    return {
        "name": "@ultimate-ai-agent/control-center",
        "private": True,
        "scripts": {
            "build": "tsc -b && vite build",
            "lint": "tsc -b --pretty false",
            "typecheck": "tsc -b --pretty false",
        },
        "dependencies": {"react": "19.2.7"},
        "devDependencies": {"typescript": version},
    }


def _package_lock(*, version: str = VERSION) -> dict[str, object]:
    return {
        "name": "@ultimate-ai-agent/control-center",
        "lockfileVersion": 3,
        "requires": True,
        "packages": {
            "": {
                "name": "@ultimate-ai-agent/control-center",
                "dependencies": {"react": "19.2.7"},
                "devDependencies": {"typescript": version},
            },
            "node_modules/typescript": {
                "version": version,
                "resolved": (
                    "https://registry.npmjs.org/typescript/-/"
                    f"typescript-{version}.tgz"
                ),
                "integrity": INTEGRITY,
                "dev": True,
                "bin": {"tsc": "bin/tsc"},
                "optionalDependencies": {
                    "@typescript/typescript-darwin-arm64": version,
                },
            },
            "node_modules/@typescript/typescript-darwin-arm64": {
                "version": version,
                "resolved": (
                    "https://registry.npmjs.org/@typescript/"
                    "typescript-darwin-arm64/-/"
                    f"typescript-darwin-arm64-{version}.tgz"
                ),
                "integrity": INTEGRITY,
                "cpu": ["arm64"],
                "dev": True,
                "optional": True,
                "os": ["darwin"],
            },
        },
    }


def _declared_project(tmp_path: Path) -> Path:
    app = tmp_path / "control-center"
    app.mkdir(parents=True)
    _write_json(app / "package.json", _package_manifest())
    _write_json(app / "package-lock.json", _package_lock())
    _write_json(
        app / "tsconfig.json",
        {
            "files": [],
            "references": [
                {"path": "./tsconfig.app.json"},
                {"path": "./tsconfig.node.json"},
            ],
        },
    )
    _write_json(app / "tsconfig.app.json", {"compilerOptions": {"noEmit": True}})
    _write_json(app / "tsconfig.node.json", {"compilerOptions": {"noEmit": True}})
    return app


def _runtime_project(tmp_path: Path) -> tuple[Path, object]:
    app = _declared_project(tmp_path)
    declared = build_declared_typescript_binding(app)
    _write_json(
        app / "node_modules/typescript/package.json",
        {
            "name": "typescript",
            "version": VERSION,
            "bin": {"tsc": "./bin/tsc"},
            "imports": {"#getExePath": "./lib/getExePath.js"},
        },
    )
    launcher_target = app / "node_modules/typescript/bin/tsc"
    launcher_target.parent.mkdir(parents=True, exist_ok=True)
    launcher_target.write_bytes(typescript_binding.EXPECTED_LAUNCHER_BYTES)
    launcher_target.chmod(0o755)
    (app / "node_modules/typescript/lib").mkdir(parents=True, exist_ok=True)
    (app / "node_modules/typescript/lib/tsc.js").write_text(
        "import getExePath from '#getExePath';\ngetExePath();\n",
        encoding="utf-8",
    )
    (app / "node_modules/typescript/lib/getExePath.js").write_text(
        "export default function getExePath() { return 'bound'; }\n",
        encoding="utf-8",
    )
    launcher = app / "node_modules/.bin/tsc"
    launcher.parent.mkdir(parents=True, exist_ok=True)
    launcher.symlink_to("../typescript/bin/tsc")
    _write_json(
        app / "node_modules/@typescript/typescript-darwin-arm64/package.json",
        {
            "name": "@typescript/typescript-darwin-arm64",
            "version": VERSION,
            "os": ["darwin"],
            "cpu": ["arm64"],
        },
    )
    platform_binary = (
        app / "node_modules/@typescript/typescript-darwin-arm64/lib/tsc"
    )
    platform_binary.parent.mkdir(parents=True, exist_ok=True)
    platform_binary.write_bytes(MACHO_ARM64_HEADER + (b"\0" * 64))
    platform_binary.chmod(0o755)
    return app, declared


def _enable_test_macos_runtime(
    monkeypatch: pytest.MonkeyPatch,
    app: Path,
) -> None:
    monkeypatch.setattr(typescript_binding.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(typescript_binding.platform, "machine", lambda: "arm64")
    node_directory = app.parent / "node-bin"
    node_directory.mkdir(exist_ok=True)
    node_binary = node_directory / "node"
    node_binary.write_bytes(MACHO_ARM64_HEADER + (b"\0" * 64))
    node_binary.chmod(0o755)
    monkeypatch.setenv("PATH", os.fspath(node_directory))
    monkeypatch.setattr(
        typescript_binding,
        "_run_bounded_node_version_probe",
        lambda _application_directory, _node_binary: b"v22.23.1\n",
    )
    monkeypatch.setattr(
        typescript_binding,
        "_run_bounded_version_probe",
        lambda _application_directory, _node_binary: b"Version 7.0.2\n",
    )


def test_current_control_center_declaration_is_exact_and_deterministic() -> None:
    app = Path(__file__).resolve().parents[1] / "apps/control-center"

    first = build_declared_typescript_binding(app)
    second = build_declared_typescript_binding(app)

    assert first == second
    assert first.typescript_version == "7.0.2"
    assert first.expected_platform_package_version == "7.0.2"
    assert first.config_graph.config_count == 3
    assert first.config_graph.edge_count == 2
    assert len(first.declared_project_fingerprint) == 64
    assert len(first.declared_command_fingerprint) == 64
    assert first.redaction_status == REDACTION_STATUS
    with pytest.raises(dataclasses.FrozenInstanceError):
        first.typescript_version = "7.0.3"  # type: ignore[misc]


def test_declared_fingerprints_change_for_command_and_config_content(tmp_path: Path) -> None:
    app = _declared_project(tmp_path)
    baseline = build_declared_typescript_binding(app)
    manifest = _package_manifest()
    scripts = manifest["scripts"]
    assert isinstance(scripts, dict)
    scripts["lint"] = "tsc -b --pretty false --verbose"
    _write_json(app / "package.json", manifest)

    changed_command = build_declared_typescript_binding(app)

    assert changed_command.declared_command_fingerprint != baseline.declared_command_fingerprint
    assert changed_command.declared_project_fingerprint != baseline.declared_project_fingerprint
    _write_json(app / "package.json", _package_manifest())
    _write_json(
        app / "tsconfig.app.json",
        {"compilerOptions": {"noEmit": True, "strict": True}},
    )

    changed_config = build_declared_typescript_binding(app)

    assert changed_config.config_graph.graph_fingerprint != baseline.config_graph.graph_fingerprint
    assert changed_config.declared_project_fingerprint != baseline.declared_project_fingerprint


@pytest.mark.parametrize(
    "version",
    ("^7.0.2", "~7.0.2", ">=7", "latest", "next", "7.0.2-beta.1", "7.0.2+build", "6.0.3", "07.0.2"),
)
def test_declaration_rejects_ranges_tags_prereleases_and_non_v7(
    tmp_path: Path,
    version: str,
) -> None:
    app = _declared_project(tmp_path)
    _write_json(app / "package.json", _package_manifest(version=version))

    with pytest.raises(TypeScriptBindingError) as exc_info:
        build_declared_typescript_binding(app)

    assert exc_info.value.reason_ref == "typescript-declaration:version-not-exact-stable"


@pytest.mark.parametrize(
    ("package_name", "package_spec"),
    (
        ("@typescript/native-preview", VERSION),
        ("@typescript/typescript-compat", VERSION),
        ("typescript-compat", VERSION),
        ("typescript-v6", VERSION),
        ("ts-compiler-legacy", "npm:typescript@6.0.3"),
    ),
)
def test_declaration_rejects_native_preview_and_compatibility_packages(
    tmp_path: Path,
    package_name: str,
    package_spec: str,
) -> None:
    app = _declared_project(tmp_path)
    manifest = _package_manifest()
    dev_dependencies = manifest["devDependencies"]
    assert isinstance(dev_dependencies, dict)
    dev_dependencies[package_name] = package_spec
    _write_json(app / "package.json", manifest)

    with pytest.raises(TypeScriptBindingError) as exc_info:
        build_declared_typescript_binding(app)

    assert exc_info.value.reason_ref == "typescript-declaration:compatibility-package-denied"


@pytest.mark.parametrize("entry_ref", ("", "node_modules/typescript"))
def test_declaration_rejects_lock_version_mismatches(
    tmp_path: Path,
    entry_ref: str,
) -> None:
    app = _declared_project(tmp_path)
    lock = _package_lock()
    packages = lock["packages"]
    assert isinstance(packages, dict)
    entry = packages[entry_ref]
    assert isinstance(entry, dict)
    if entry_ref:
        entry["version"] = "7.0.3"
    else:
        dev_dependencies = entry["devDependencies"]
        assert isinstance(dev_dependencies, dict)
        dev_dependencies["typescript"] = "7.0.3"
    _write_json(app / "package-lock.json", lock)

    with pytest.raises(TypeScriptBindingError):
        build_declared_typescript_binding(app)


def test_declaration_rejects_wrong_platform_optional_version(tmp_path: Path) -> None:
    app = _declared_project(tmp_path)
    lock = _package_lock()
    packages = lock["packages"]
    assert isinstance(packages, dict)
    entry = packages["node_modules/typescript"]
    assert isinstance(entry, dict)
    optional = entry["optionalDependencies"]
    assert isinstance(optional, dict)
    optional["@typescript/typescript-darwin-arm64"] = "7.0.3"
    _write_json(app / "package-lock.json", lock)

    with pytest.raises(TypeScriptBindingError) as exc_info:
        build_declared_typescript_binding(app)

    assert exc_info.value.reason_ref == "typescript-declaration:platform-version-mismatch"


def test_declaration_rejects_symlink_fifo_and_hardlinked_json(
    tmp_path: Path,
) -> None:
    for unsafe_kind in ("symlink", "fifo", "hardlink"):
        app = _declared_project(tmp_path / unsafe_kind)
        target = app / "tsconfig.app.json"
        if unsafe_kind == "symlink":
            outside = tmp_path / f"{unsafe_kind}-outside.json"
            _write_json(outside, {})
            target.unlink()
            target.symlink_to(outside)
        elif unsafe_kind == "fifo":
            target.unlink()
            os.mkfifo(target)
        else:
            os.link(target, app / "tsconfig.app.duplicate.json")

        with pytest.raises(TypeScriptBindingError) as exc_info:
            build_declared_typescript_binding(app)

        assert exc_info.value.reason_ref == "typescript-declaration:tsconfig-file-invalid"


@pytest.mark.parametrize(
    ("references", "reason_ref"),
    (
        ([{"path": "../outside.json"}], "typescript-declaration:tsconfig-reference-invalid"),
        ([{"path": "/tmp/outside.json"}], "typescript-declaration:tsconfig-reference-invalid"),
        ([{"path": "tsconfig.json"}], "typescript-declaration:tsconfig-self-reference"),
        (
            [{"path": "./tsconfig.app.json"}, {"path": "tsconfig.app.json"}],
            "typescript-declaration:tsconfig-duplicate-reference",
        ),
    ),
)
def test_declaration_rejects_unsafe_self_and_duplicate_config_references(
    tmp_path: Path,
    references: list[dict[str, str]],
    reason_ref: str,
) -> None:
    app = _declared_project(tmp_path)
    _write_json(app / "tsconfig.json", {"files": [], "references": references})

    with pytest.raises(TypeScriptBindingError) as exc_info:
        build_declared_typescript_binding(app)

    assert exc_info.value.reason_ref == reason_ref


def test_declaration_rejects_config_cycles_before_returning_a_binding(
    tmp_path: Path,
) -> None:
    app = _declared_project(tmp_path)
    _write_json(app / "tsconfig.json", {"references": [{"path": "./a.json"}]})
    _write_json(app / "a.json", {"references": [{"path": "./b.json"}]})
    _write_json(app / "b.json", {"references": [{"path": "./a.json"}]})

    with pytest.raises(TypeScriptBindingError) as exc_info:
        build_declared_typescript_binding(app)

    assert exc_info.value.reason_ref == "typescript-declaration:tsconfig-cycle"


def test_declaration_rejects_unbound_extends(tmp_path: Path) -> None:
    app = _declared_project(tmp_path)
    _write_json(app / "tsconfig.app.json", {"extends": "../shared.json"})

    with pytest.raises(TypeScriptBindingError) as exc_info:
        build_declared_typescript_binding(app)

    assert exc_info.value.reason_ref == "typescript-declaration:tsconfig-extends-unsupported"


def test_runtime_binding_is_exact_hash_bound_and_content_free(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, declared = _runtime_project(tmp_path)
    _enable_test_macos_runtime(monkeypatch, app)

    runtime = resolve_typescript_runtime_binding(app, declared)  # type: ignore[arg-type]
    payload = json.dumps(dataclasses.asdict(runtime), sort_keys=True)

    assert runtime.typescript_version == VERSION
    assert runtime.declared_project_fingerprint == declared.declared_project_fingerprint
    assert len(runtime.resolved_runtime_fingerprint) == 64
    assert runtime.runtime_file_count == 8
    assert runtime.node_version == "22.23.1"
    assert len(runtime.node_runtime_fingerprint) == 64
    assert len(runtime.runtime_tsc_loader_fingerprint) == 64
    assert len(runtime.runtime_platform_resolver_fingerprint) == 64
    assert runtime.runtime_byte_count > 0
    assert runtime.redaction_status == REDACTION_STATUS
    assert "Version 7.0.2" not in payload
    assert str(tmp_path) not in payload
    assert "node_modules" not in payload


def test_runtime_binding_rejects_non_macos_arm64(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, declared = _runtime_project(tmp_path)
    monkeypatch.setattr(typescript_binding.platform, "system", lambda: "Linux")
    monkeypatch.setattr(typescript_binding.platform, "machine", lambda: "x86_64")

    with pytest.raises(TypeScriptBindingError) as exc_info:
        resolve_typescript_runtime_binding(app, declared)  # type: ignore[arg-type]

    assert exc_info.value.reason_ref == "typescript-runtime:platform-mismatch"


@pytest.mark.parametrize("spoof_kind", ("regular", "wrong-target", "wrong-content"))
def test_runtime_binding_rejects_spoofed_launchers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    spoof_kind: str,
) -> None:
    app, declared = _runtime_project(tmp_path)
    _enable_test_macos_runtime(monkeypatch, app)
    launcher = app / "node_modules/.bin/tsc"
    if spoof_kind == "regular":
        launcher.unlink()
        launcher.write_bytes(typescript_binding.EXPECTED_LAUNCHER_BYTES)
        launcher.chmod(0o755)
    elif spoof_kind == "wrong-target":
        launcher.unlink()
        launcher.symlink_to("../typescript/bin/not-tsc")
    else:
        target = app / "node_modules/typescript/bin/tsc"
        target.write_text("#!/bin/sh\necho Version 7.0.2\n", encoding="utf-8")
        target.chmod(0o755)

    with pytest.raises(TypeScriptBindingError) as exc_info:
        resolve_typescript_runtime_binding(app, declared)  # type: ignore[arg-type]

    assert exc_info.value.reason_ref.startswith("typescript-runtime:launcher")


def test_runtime_binding_rejects_wrong_package_version(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, declared = _runtime_project(tmp_path)
    _enable_test_macos_runtime(monkeypatch, app)
    _write_json(
        app / "node_modules/typescript/package.json",
        {
            "name": "typescript",
            "version": "7.0.3",
            "bin": {"tsc": "./bin/tsc"},
            "imports": {"#getExePath": "./lib/getExePath.js"},
        },
    )

    with pytest.raises(TypeScriptBindingError) as exc_info:
        resolve_typescript_runtime_binding(app, declared)  # type: ignore[arg-type]

    assert exc_info.value.reason_ref == "typescript-runtime:package-mismatch"


def test_runtime_binding_rejects_wrong_platform_binary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, declared = _runtime_project(tmp_path)
    _enable_test_macos_runtime(monkeypatch, app)
    binary = app / "node_modules/@typescript/typescript-darwin-arm64/lib/tsc"
    binary.write_bytes(b"#!/bin/sh\necho Version 7.0.2\n")
    binary.chmod(0o755)

    with pytest.raises(TypeScriptBindingError) as exc_info:
        resolve_typescript_runtime_binding(app, declared)  # type: ignore[arg-type]

    assert (
        exc_info.value.reason_ref
        == "typescript-runtime:platform-binary-architecture-mismatch"
    )


@pytest.mark.parametrize(
    ("probe_output", "reason_ref"),
    (
        (b"Version 7.0.3\n", "typescript-runtime:version-probe-version-mismatch"),
        (b"7.0.2\n", "typescript-runtime:version-probe-output-invalid"),
        (b"Version 7.0.2\nsecret", "typescript-runtime:version-probe-output-invalid"),
        (b"x" * 129, "typescript-runtime:version-probe-output-bound"),
    ),
)
def test_runtime_binding_rejects_wrong_or_unbounded_probe_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    probe_output: bytes,
    reason_ref: str,
) -> None:
    app, declared = _runtime_project(tmp_path)
    _enable_test_macos_runtime(monkeypatch, app)
    monkeypatch.setattr(
        typescript_binding,
        "_run_bounded_version_probe",
        lambda _application_directory, _node_binary: probe_output,
    )

    with pytest.raises(TypeScriptBindingError) as exc_info:
        resolve_typescript_runtime_binding(app, declared)  # type: ignore[arg-type]

    assert exc_info.value.reason_ref == reason_ref


def test_runtime_binding_rejects_declaration_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, declared = _runtime_project(tmp_path)
    _enable_test_macos_runtime(monkeypatch, app)
    _write_json(
        app / "tsconfig.app.json",
        {"compilerOptions": {"noEmit": True, "strict": True}},
    )

    with pytest.raises(TypeScriptBindingError) as exc_info:
        resolve_typescript_runtime_binding(app, declared)  # type: ignore[arg-type]

    assert exc_info.value.reason_ref == "typescript-runtime:declaration-drift"


@pytest.mark.parametrize(
    ("relative_ref", "reason_ref"),
    (
        (
            "node_modules/typescript/lib/tsc.js",
            "typescript-runtime:tsc-loader-invalid",
        ),
        (
            "node_modules/typescript/lib/getExePath.js",
            "typescript-runtime:platform-resolver-invalid",
        ),
    ),
)
def test_runtime_binding_rejects_symlinked_intermediary_modules(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative_ref: str,
    reason_ref: str,
) -> None:
    app, declared = _runtime_project(tmp_path)
    _enable_test_macos_runtime(monkeypatch, app)
    target = app / relative_ref
    outside = tmp_path / "intermediary.js"
    outside.write_text("export default 'unsafe';\n", encoding="utf-8")
    target.unlink()
    target.symlink_to(outside)

    with pytest.raises(TypeScriptBindingError) as exc_info:
        resolve_typescript_runtime_binding(app, declared)  # type: ignore[arg-type]

    assert exc_info.value.reason_ref == reason_ref


@pytest.mark.parametrize(
    "relative_ref",
    (
        "node_modules/typescript/lib/tsc.js",
        "node_modules/typescript/lib/getExePath.js",
        "node_modules/typescript/package.json",
        "node_modules/@typescript/typescript-darwin-arm64/package.json",
    ),
)
def test_runtime_binding_rejects_any_pre_post_runtime_tamper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative_ref: str,
) -> None:
    app, declared = _runtime_project(tmp_path)
    _enable_test_macos_runtime(monkeypatch, app)

    def tampering_probe(_application_directory: Path, _node_binary: Path) -> bytes:
        target = app / relative_ref
        if target.suffix == ".json":
            payload = json.loads(target.read_text(encoding="utf-8"))
            payload["tampered"] = True
            _write_json(target, payload)
        else:
            target.write_text("tampered intermediary\n", encoding="utf-8")
        return b"Version 7.0.2\n"

    monkeypatch.setattr(
        typescript_binding,
        "_run_bounded_version_probe",
        tampering_probe,
    )

    with pytest.raises(TypeScriptBindingError) as exc_info:
        resolve_typescript_runtime_binding(app, declared)  # type: ignore[arg-type]

    assert exc_info.value.reason_ref in {
        "typescript-runtime:runtime-drift",
        "typescript-runtime:package-mismatch",
        "typescript-runtime:platform-package-mismatch",
    }


def test_declaration_rejects_duplicate_json_keys(tmp_path: Path) -> None:
    app = _declared_project(tmp_path)
    (app / "package.json").write_text(
        '{"scripts": {}, "devDependencies": {"typescript": "7.0.2"}, '
        '"devDependencies": {"typescript": "7.0.2"}}',
        encoding="utf-8",
    )

    with pytest.raises(TypeScriptBindingError) as exc_info:
        build_declared_typescript_binding(app)

    assert exc_info.value.reason_ref == "typescript-declaration:package-manifest-invalid"


def test_runtime_rejects_duplicate_json_keys(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app, declared = _runtime_project(tmp_path)
    _enable_test_macos_runtime(monkeypatch, app)
    (app / "node_modules/typescript/package.json").write_text(
        '{"name":"typescript","name":"typescript","version":"7.0.2",'
        '"bin":{"tsc":"./bin/tsc"},'
        '"imports":{"#getExePath":"./lib/getExePath.js"}}',
        encoding="utf-8",
    )

    with pytest.raises(TypeScriptBindingError) as exc_info:
        resolve_typescript_runtime_binding(app, declared)  # type: ignore[arg-type]

    assert exc_info.value.reason_ref == "typescript-runtime:package-invalid"


@pytest.mark.parametrize("unsafe_path", ("relative/bin", ":/usr/bin", "/usr/bin:"))
def test_runtime_rejects_relative_or_empty_path_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    unsafe_path: str,
) -> None:
    app, declared = _runtime_project(tmp_path)
    _enable_test_macos_runtime(monkeypatch, app)
    monkeypatch.setenv("PATH", unsafe_path)

    with pytest.raises(TypeScriptBindingError) as exc_info:
        resolve_typescript_runtime_binding(app, declared)  # type: ignore[arg-type]

    assert exc_info.value.reason_ref == "typescript-runtime:node-path-invalid"


def test_runtime_rejects_path_selected_non_macho_node(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, declared = _runtime_project(tmp_path)
    _enable_test_macos_runtime(monkeypatch, app)
    unsafe_bin = tmp_path / "unsafe-node-bin"
    unsafe_bin.mkdir()
    node = unsafe_bin / "node"
    node.write_text("#!/bin/sh\necho v22.23.1\n", encoding="utf-8")
    node.chmod(0o755)
    monkeypatch.setenv("PATH", os.fspath(unsafe_bin))

    with pytest.raises(TypeScriptBindingError) as exc_info:
        resolve_typescript_runtime_binding(app, declared)  # type: ignore[arg-type]

    assert exc_info.value.reason_ref == "typescript-runtime:node-binary-architecture-mismatch"


def test_runtime_rejects_node_path_identity_change_during_probe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, declared = _runtime_project(tmp_path)
    _enable_test_macos_runtime(monkeypatch, app)
    replacement_dir = tmp_path / "replacement-node-bin"
    replacement_dir.mkdir()
    replacement_node = replacement_dir / "node"
    replacement_node.write_bytes(MACHO_ARM64_HEADER + (b"replacement" * 8))
    replacement_node.chmod(0o755)

    def changing_probe(_application_directory: Path, _node_binary: Path) -> bytes:
        monkeypatch.setenv("PATH", os.fspath(replacement_dir))
        return b"Version 7.0.2\n"

    monkeypatch.setattr(
        typescript_binding,
        "_run_bounded_version_probe",
        changing_probe,
    )

    with pytest.raises(TypeScriptBindingError) as exc_info:
        resolve_typescript_runtime_binding(app, declared)  # type: ignore[arg-type]

    assert exc_info.value.reason_ref == "typescript-runtime:runtime-drift"


def test_binding_errors_never_include_path_or_unsafe_payload(
    tmp_path: Path,
) -> None:
    secret_marker = "raw-secret-marker-must-not-escape"
    app = tmp_path / secret_marker / "control-center"
    app.mkdir(parents=True)
    (app / "package.json").write_text(secret_marker, encoding="utf-8")

    with pytest.raises(TypeScriptBindingError) as exc_info:
        build_declared_typescript_binding(app)

    rendered = str(exc_info.value)
    assert secret_marker not in rendered
    assert str(tmp_path) not in rendered
    assert re.fullmatch(r"[a-z0-9][a-z0-9:._-]{0,191}", exc_info.value.reason_ref)
