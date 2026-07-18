#!/usr/bin/env python3
"""Build a self-contained, signed macOS app and verified release archive."""
from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from ultimate_ai_agent.distribution.macos.contracts import (
    APP_BUNDLE_IDENTIFIER,
    APP_BUNDLE_NAME,
    BUNDLE_MANIFEST_SCHEMA,
    MINIMUM_MACOS,
    PRODUCT_LINE,
    RELEASE_DESCRIPTOR_SCHEMA,
    ReleaseDescriptor,
    artifact_name,
    current_architecture,
    descriptor_name,
    sha256_file,
)
from ultimate_ai_agent.distribution.macos.installer import APP_MANAGED_MARKER


ROOT = Path(__file__).resolve().parents[2]
APP_EXECUTABLE_NAME = APP_BUNDLE_NAME.removesuffix(".app")
BUILD_RECEIPT_SCHEMA = "uaa.macos.build-receipt.v1"
BOUNDARY_SCHEMA = "uaa.macos.distribution-boundary.v1"
APP_ICON_FILENAME = "UltimateAI-Agent.icns"
SETUPTOOLS_BUILD_REQUIREMENT = (
    "setuptools==79.0.1 "
    "--hash=sha256:e147c0549f27767ba362f9da434eab9c5dc0045d5304feb602a0af001089fc51"
)


def build_release_bundle(
    *,
    source_root: Path,
    python_runtime: Path,
    output_dir: Path,
    tag: str,
    channel: str,
    source_commit: str,
    source_timestamp: str,
    version: str,
    architecture: str,
    frontend_dist: Path,
    signing_identity: str | None,
    notary_profile: str | None,
    skip_dependency_install: bool = False,
    allow_dirty_local: bool = False,
) -> dict[str, Any]:
    """Build the complete app, sign it, archive it, and emit release metadata."""

    _validate_build_inputs(
        source_root=source_root,
        python_runtime=python_runtime,
        tag=tag,
        channel=channel,
        source_commit=source_commit,
        source_timestamp=source_timestamp,
        version=version,
        architecture=architecture,
        frontend_dist=frontend_dist,
        signing_identity=signing_identity,
        notary_profile=notary_profile,
    )
    _validate_source_identity(
        source_root=source_root,
        tag=tag,
        channel=channel,
        source_commit=source_commit,
        allow_dirty_local=allow_dirty_local,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact = output_dir / artifact_name(architecture)
    descriptor_path = output_dir / descriptor_name(architecture)
    checksum_path = output_dir / f"{artifact.name}.sha256"
    for path in (artifact, descriptor_path, checksum_path):
        path.unlink(missing_ok=True)

    with tempfile.TemporaryDirectory(prefix="uaa-macos-release-") as temporary:
        stage_root = Path(temporary)
        payload_root = stage_root / "payload"
        app_bundle = payload_root / APP_BUNDLE_NAME
        resources = app_bundle / "Contents" / "Resources"
        runtime_python = resources / "runtime" / "python"
        macos_dir = app_bundle / "Contents" / "MacOS"
        macos_dir.mkdir(parents=True)
        resources.mkdir(parents=True)
        shutil.copytree(python_runtime, runtime_python, symlinks=False)
        baseline_bin_files = _relative_files(runtime_python / "bin")
        if not skip_dependency_install:
            _install_locked_runtime(
                source_root=source_root,
                runtime_python=runtime_python,
                baseline_bin_files=baseline_bin_files,
                build_root=stage_root,
            )
        shutil.copytree(frontend_dist, resources / "control-center")
        _write_app_files(
            source_root=source_root,
            app_bundle=app_bundle,
            tag=tag,
            channel=channel,
            source_commit=source_commit,
            source_timestamp=source_timestamp,
            version=version,
            architecture=architecture,
        )
        _remove_python_caches(runtime_python)
        _remove_non_runtime_package_metadata(runtime_python)
        _scan_for_forbidden_durable_text(
            payload_root,
            additional_fragments=(
                str(source_root),
                str(stage_root),
                str(Path.home()),
            ),
        )
        signing_kind = "developer-id" if signing_identity else "ad-hoc"
        _sign_app(app_bundle, signing_identity=signing_identity)
        notarized = False
        if notary_profile:
            _notarize_and_staple(app_bundle, notary_profile=notary_profile)
            notarized = True
        _verify_signature(
            app_bundle,
            developer_id=signing_identity is not None,
            notarized=notarized,
        )
        bundle_manifest = _build_bundle_manifest(
            payload_root=payload_root,
            tag=tag,
            channel=channel,
            source_commit=source_commit,
            source_timestamp=source_timestamp,
            version=version,
            architecture=architecture,
            signing_kind=signing_kind,
            notarized=notarized,
        )
        (payload_root / "bundle-manifest.json").write_text(
            json.dumps(bundle_manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _create_deterministic_archive(
            payload_root,
            artifact,
            source_timestamp=source_timestamp,
        )

    descriptor = ReleaseDescriptor(
        schema_version=RELEASE_DESCRIPTOR_SCHEMA,
        product_line=PRODUCT_LINE,
        tag=tag,
        version=version,
        channel=channel,  # type: ignore[arg-type]
        source_commit=source_commit,
        source_timestamp=source_timestamp,
        platform="macos",
        architecture=architecture,
        artifact_name=artifact.name,
        artifact_sha256=sha256_file(artifact),
        artifact_size=artifact.stat().st_size,
        minimum_macos=MINIMUM_MACOS,
        signing_kind="developer-id" if signing_identity else "ad-hoc",
        notarized=bool(notary_profile),
    )
    descriptor.validate(expected_architecture=architecture)
    descriptor_path.write_bytes(descriptor.to_json_bytes())
    checksum_path.write_text(
        f"{descriptor.artifact_sha256}  {artifact.name}\n",
        encoding="utf-8",
    )
    receipt = {
        "schema_version": BUILD_RECEIPT_SCHEMA,
        "status": "built",
        "tag_ref": f"git-tag:{tag}",
        "source_commit_ref": f"git-commit:{source_commit}",
        "channel": channel,
        "architecture": architecture,
        "artifact_ref": f"github-release-asset:{artifact.name}",
        "descriptor_ref": f"github-release-asset:{descriptor_path.name}",
        "checksum_ref": f"sha256:{descriptor.artifact_sha256}",
        "signing_kind": descriptor.signing_kind,
        "notarized": descriptor.notarized,
        "raw_paths_included": False,
        "credentials_included": False,
    }
    (output_dir / "build-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


def _validate_build_inputs(
    *,
    source_root: Path,
    python_runtime: Path,
    tag: str,
    channel: str,
    source_commit: str,
    source_timestamp: str,
    version: str,
    architecture: str,
    frontend_dist: Path,
    signing_identity: str | None,
    notary_profile: str | None,
) -> None:
    if not (source_root / "pyproject.toml").is_file():
        raise ValueError("source root is not an Ultimate AI Agent checkout")
    if not (
        source_root / "packaging" / "macos" / "assets" / APP_ICON_FILENAME
    ).is_file():
        raise ValueError("macOS application icon asset is missing")
    if not (python_runtime / "bin" / "python3").is_file():
        raise ValueError("relocatable Python runtime is missing bin/python3")
    if not (frontend_dist / "index.html").is_file():
        raise ValueError("Control Center production build is missing index.html")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,127}", tag):
        raise ValueError("release tag is not safe")
    if channel not in {"stable", "dev"}:
        raise ValueError("release channel must be stable or dev")
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError("source commit must be an exact lowercase SHA")
    parsed_timestamp = datetime.fromisoformat(source_timestamp.replace("Z", "+00:00"))
    if parsed_timestamp.tzinfo is None:
        raise ValueError("source timestamp must include a timezone")
    if not re.fullmatch(
        r"[0-9]+(?:\.[0-9]+){1,3}(?:[-+][A-Za-z0-9._-]+)?",
        version,
    ):
        raise ValueError("app version is invalid")
    if architecture not in {"arm64", "x86_64"}:
        raise ValueError("release architecture is unsupported")
    if notary_profile and not signing_identity:
        raise ValueError("notarization requires a Developer ID signing identity")


def _install_locked_runtime(
    *,
    source_root: Path,
    runtime_python: Path,
    baseline_bin_files: set[str],
    build_root: Path,
) -> None:
    python = runtime_python / "bin" / "python3"
    requirements = build_root / "requirements.locked.txt"
    _run(
        [
            _find_tool("uv"),
            "export",
            "--frozen",
            "--no-dev",
            "--no-emit-project",
            "--format",
            "requirements.txt",
            "--output-file",
            str(requirements),
        ],
        cwd=source_root,
        timeout=120.0,
    )
    _run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-cache-dir",
            "--no-compile",
            "--require-hashes",
            "--requirement",
            str(requirements),
        ],
        cwd=source_root,
        timeout=900.0,
    )
    wheel_dir = build_root / "wheel"
    wheel_dir.mkdir()
    wheel_environment = build_root / "wheel-build-environment"
    _run(
        [
            str(python),
            "-m",
            "venv",
            str(wheel_environment),
        ],
        cwd=source_root,
        timeout=120.0,
    )
    build_requirements = build_root / "build-backend.locked.txt"
    build_requirements.write_text(
        SETUPTOOLS_BUILD_REQUIREMENT + "\n",
        encoding="utf-8",
    )
    wheel_python = wheel_environment / "bin" / "python3"
    _run(
        [
            str(wheel_python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-cache-dir",
            "--require-hashes",
            "--requirement",
            str(build_requirements),
        ],
        cwd=source_root,
        timeout=300.0,
    )
    _run(
        [
            str(wheel_python),
            "-m",
            "pip",
            "wheel",
            "--disable-pip-version-check",
            "--no-cache-dir",
            "--no-build-isolation",
            "--no-deps",
            "--wheel-dir",
            str(wheel_dir),
            str(source_root),
        ],
        cwd=source_root,
        timeout=300.0,
    )
    wheels = sorted(wheel_dir.glob("ultimate_ai_agent-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError("UAA wheel build did not produce exactly one wheel")
    _run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-cache-dir",
            "--no-compile",
            "--no-deps",
            "--force-reinstall",
            str(wheels[0]),
        ],
        cwd=source_root,
        timeout=300.0,
    )
    for relative in _relative_files(runtime_python / "bin") - baseline_bin_files:
        path = runtime_python / "bin" / relative
        if path.is_file() or path.is_symlink():
            path.unlink()


def _write_app_files(
    *,
    source_root: Path,
    app_bundle: Path,
    tag: str,
    channel: str,
    source_commit: str,
    source_timestamp: str,
    version: str,
    architecture: str,
) -> None:
    contents = app_bundle / "Contents"
    resources = contents / "Resources"
    executable = contents / "MacOS" / APP_EXECUTABLE_NAME
    shutil.copy2(
        source_root / "packaging" / "macos" / "assets" / APP_ICON_FILENAME,
        resources / APP_ICON_FILENAME,
    )
    launcher_source = resources / ".uaa-launcher.c"
    launcher_source.write_text(_launcher_source(), encoding="utf-8")
    _run(
        [
            "/usr/bin/clang",
            "-Os",
            "-Wall",
            "-Wextra",
            "-mmacosx-version-min=13.0",
            "-o",
            str(executable),
            str(launcher_source),
        ],
        timeout=120.0,
    )
    launcher_source.unlink()
    with (contents / "Info.plist").open("wb") as handle:
        plistlib.dump(
            {
                "CFBundleDevelopmentRegion": "en",
                "CFBundleDisplayName": APP_EXECUTABLE_NAME,
                "CFBundleExecutable": APP_EXECUTABLE_NAME,
                "CFBundleIdentifier": APP_BUNDLE_IDENTIFIER,
                "CFBundleIconFile": APP_ICON_FILENAME,
                "CFBundleName": APP_EXECUTABLE_NAME,
                "CFBundlePackageType": "APPL",
                "CFBundleShortVersionString": version,
                "CFBundleVersion": _bundle_build_version(source_timestamp),
                "LSMinimumSystemVersion": MINIMUM_MACOS,
                "LSMultipleInstancesProhibited": True,
                "NSHighResolutionCapable": True,
                "UAAReleaseTag": tag,
                "UAAUpdateChannel": channel,
            },
            handle,
            sort_keys=True,
        )
    managed_marker = {
        "schema_version": "uaa.macos.install-ownership.v1",
        "product_line": PRODUCT_LINE,
        "managed_by": "uaa-macos-installer",
    }
    (resources / APP_MANAGED_MARKER).write_text(
        json.dumps(managed_marker, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    boundary = {
        "schema_version": BOUNDARY_SCHEMA,
        "product_line": PRODUCT_LINE,
        "tag_ref": f"git-tag:{tag}",
        "source_commit_ref": f"git-commit:{source_commit}",
        "source_timestamp": source_timestamp,
        "channel": channel,
        "architecture": architecture,
        "network_scope": [
            "api.github.com exact repository release metadata",
            "GitHub release asset download hosts",
        ],
        "agent_web_authority_added": False,
        "provider_model_authority_added": False,
        "connector_write_authority_added": False,
        "browser_automation_added": False,
        "background_daemon_added": False,
        "raw_paths_included": False,
        "credentials_included": False,
    }
    (resources / "distribution-boundary.json").write_text(
        json.dumps(boundary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _launcher_source() -> str:
    return r"""#include <errno.h>
#include <limits.h>
#include <mach-o/dyld.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static int parent_directory(char *path) {
    char *slash = strrchr(path, '/');
    if (slash == NULL || slash == path) {
        return -1;
    }
    *slash = '\0';
    return 0;
}

int main(int argc, char **argv) {
    char executable_path[PATH_MAX];
    uint32_t executable_size = (uint32_t)sizeof(executable_path);
    if (_NSGetExecutablePath(executable_path, &executable_size) != 0) {
        fputs("Ultimate AI Agent could not resolve its application path.\n", stderr);
        return 1;
    }

    char contents_path[PATH_MAX];
    if (realpath(executable_path, contents_path) == NULL ||
        parent_directory(contents_path) != 0 ||
        parent_directory(contents_path) != 0) {
        fputs("Ultimate AI Agent application path is invalid.\n", stderr);
        return 1;
    }

    char resources_path[PATH_MAX];
    char bundle_path[PATH_MAX];
    char python_path[PATH_MAX];
    if (snprintf(resources_path, sizeof(resources_path), "%s/Resources", contents_path) >=
            (int)sizeof(resources_path) ||
        snprintf(bundle_path, sizeof(bundle_path), "%s/..", contents_path) >=
            (int)sizeof(bundle_path) ||
        snprintf(python_path, sizeof(python_path),
                 "%s/runtime/python/bin/python3", resources_path) >=
            (int)sizeof(python_path)) {
        fputs("Ultimate AI Agent application path is too long.\n", stderr);
        return 1;
    }
    if (access(python_path, X_OK) != 0) {
        fputs("Ultimate AI Agent runtime is missing. Run installer repair.\n", stderr);
        return 1;
    }
    if (setenv("UAA_APP_BUNDLE", bundle_path, 1) != 0 ||
        setenv("UAA_APP_RESOURCES", resources_path, 1) != 0 ||
        setenv("PYTHONDONTWRITEBYTECODE", "1", 1) != 0) {
        fputs("Ultimate AI Agent could not configure its packaged runtime.\n", stderr);
        return 1;
    }

    int forwarded = argc > 1 ? argc - 1 : 0;
    if (forwarded == 1 && strncmp(argv[1], "-psn_", 5) == 0) {
        forwarded = 0;
    }
    size_t new_count = (size_t)forwarded + 4;
    char **new_argv = calloc(new_count, sizeof(char *));
    if (new_argv == NULL) {
        fputs("Ultimate AI Agent could not allocate launcher arguments.\n", stderr);
        return 1;
    }
    new_argv[0] = python_path;
    new_argv[1] = "-m";
    new_argv[2] = "ultimate_ai_agent.distribution.macos.runtime";
    for (int index = 0; index < forwarded; index++) {
        new_argv[index + 3] = argv[index + 1];
    }
    new_argv[forwarded + 3] = NULL;
    execv(python_path, new_argv);
    fputs("Ultimate AI Agent could not start its packaged runtime.\n", stderr);
    free(new_argv);
    return errno == 0 ? 1 : errno;
}
"""


def _build_bundle_manifest(
    *,
    payload_root: Path,
    tag: str,
    channel: str,
    source_commit: str,
    source_timestamp: str,
    version: str,
    architecture: str,
    signing_kind: str,
    notarized: bool,
) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for path in sorted(item for item in payload_root.rglob("*") if item.is_file()):
        if path.is_symlink():
            raise RuntimeError("release payload contains an unexpected symlink")
        relative = path.relative_to(payload_root).as_posix()
        files.append(
            {
                "path": relative,
                "sha256": sha256_file(path),
                "size": path.stat().st_size,
                "mode": (
                    0o755
                    if stat.S_IMODE(path.stat().st_mode) & 0o111
                    else 0o644
                ),
            }
        )
    return {
        "schema_version": BUNDLE_MANIFEST_SCHEMA,
        "product_line": PRODUCT_LINE,
        "tag": tag,
        "version": version,
        "channel": channel,
        "source_commit": source_commit,
        "source_timestamp": source_timestamp,
        "platform": "macos",
        "architecture": architecture,
        "app_bundle": APP_BUNDLE_NAME,
        "signing_kind": signing_kind,
        "notarized": notarized,
        "files": files,
    }


def _sign_app(app_bundle: Path, *, signing_identity: str | None) -> None:
    identity = signing_identity or "-"
    macho_files = sorted(
        (
            path
            for path in app_bundle.rglob("*")
            if path.is_file() and _is_macho(path)
        ),
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for path in macho_files:
        command = ["/usr/bin/codesign", "--force", "--sign", identity]
        if signing_identity:
            command.extend(["--options", "runtime", "--timestamp"])
        else:
            command.append("--timestamp=none")
        command.append(str(path))
        _run(command, timeout=60.0)
    command = ["/usr/bin/codesign", "--force", "--sign", identity]
    if signing_identity:
        command.extend(["--options", "runtime", "--timestamp"])
    else:
        command.append("--timestamp=none")
    command.append(str(app_bundle))
    _run(command, timeout=120.0)


def _verify_signature(
    app_bundle: Path,
    *,
    developer_id: bool,
    notarized: bool,
) -> None:
    _run(
        ["/usr/bin/codesign", "--verify", "--deep", "--strict", str(app_bundle)],
        timeout=120.0,
    )
    details = _run(
        ["/usr/bin/codesign", "-d", "--verbose=4", str(app_bundle)],
        timeout=30.0,
        capture_output=True,
    )
    if developer_id and (
        "Authority=Developer ID Application:" not in details
        or "runtime" not in details.lower()
    ):
        raise RuntimeError("Developer ID signature or hardened runtime is missing")
    if notarized:
        _run(
            ["/usr/sbin/spctl", "-a", "-t", "exec", "-vv", str(app_bundle)],
            timeout=30.0,
        )


def _notarize_and_staple(app_bundle: Path, *, notary_profile: str) -> None:
    with tempfile.TemporaryDirectory(prefix="uaa-notary-") as temporary:
        archive = Path(temporary) / "Ultimate-AI-Agent.zip"
        _run(
            [
                "/usr/bin/ditto",
                "-c",
                "-k",
                "--keepParent",
                str(app_bundle),
                str(archive),
            ],
            timeout=300.0,
        )
        _run(
            [
                "/usr/bin/xcrun",
                "notarytool",
                "submit",
                str(archive),
                "--keychain-profile",
                notary_profile,
                "--wait",
            ],
            timeout=1800.0,
        )
    _run(
        ["/usr/bin/xcrun", "stapler", "staple", str(app_bundle)],
        timeout=300.0,
    )
    _run(
        ["/usr/bin/xcrun", "stapler", "validate", str(app_bundle)],
        timeout=120.0,
    )


def _create_deterministic_archive(
    payload_root: Path,
    target: Path,
    *,
    source_timestamp: str,
) -> None:
    epoch = int(
        datetime.fromisoformat(source_timestamp.replace("Z", "+00:00")).timestamp()
    )

    def normalize(info: tarfile.TarInfo) -> tarfile.TarInfo:
        info.uid = 0
        info.gid = 0
        info.uname = ""
        info.gname = ""
        info.mtime = epoch
        if info.isfile():
            info.mode = 0o755 if info.mode & 0o111 else 0o644
        elif info.isdir():
            info.mode = 0o755
        return info

    with tarfile.open(target, mode="w:gz", format=tarfile.PAX_FORMAT) as tar:
        tar.dereference = True
        for path in sorted(payload_root.rglob("*")):
            tar.add(
                path,
                arcname=path.relative_to(payload_root).as_posix(),
                recursive=False,
                filter=normalize,
            )


def _scan_for_forbidden_durable_text(
    root: Path,
    *,
    additional_fragments: Iterable[str],
) -> None:
    fragments = tuple(fragment for fragment in additional_fragments if fragment)
    for path in root.rglob("*"):
        if not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
            continue
        payload = path.read_bytes()
        if b"\x00" in payload[:4096]:
            continue
        text = payload.decode("utf-8", errors="ignore")
        lowered = text.lower()
        for fragment in fragments:
            if fragment.lower() in lowered:
                raise RuntimeError(
                    "release payload contains a forbidden durable-text fragment in "
                    + path.relative_to(root).as_posix()
                )


def _remove_python_caches(root: Path) -> None:
    for path in sorted(root.rglob("__pycache__"), reverse=True):
        if path.is_dir():
            shutil.rmtree(path)
    for path in root.rglob("*.pyc"):
        path.unlink()


def _remove_non_runtime_package_metadata(root: Path) -> None:
    for path in sorted(root.rglob("sboms"), reverse=True):
        if path.is_dir() and ".dist-info" in path.parent.name:
            shutil.rmtree(path)
    for path in root.rglob("direct_url.json"):
        if ".dist-info" in path.parent.name:
            path.unlink()


def _is_macho(path: Path) -> bool:
    completed = subprocess.run(
        ["/usr/bin/file", "-b", str(path)],
        text=True,
        capture_output=True,
        timeout=10.0,
        check=False,
    )
    return completed.returncode == 0 and "Mach-O" in completed.stdout


def _relative_files(root: Path) -> set[str]:
    if not root.is_dir():
        return set()
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() or path.is_symlink()
    }


def _bundle_build_version(source_timestamp: str) -> str:
    timestamp = datetime.fromisoformat(source_timestamp.replace("Z", "+00:00"))
    return timestamp.strftime("%Y%m%d%H%M%S")


def _find_tool(name: str) -> str:
    discovered = shutil.which(name)
    if not discovered:
        raise RuntimeError(f"required build tool is missing: {name}")
    return discovered


def _validate_source_identity(
    *,
    source_root: Path,
    tag: str,
    channel: str,
    source_commit: str,
    allow_dirty_local: bool,
) -> None:
    if allow_dirty_local:
        if channel != "dev" or not tag.startswith("local-"):
            raise ValueError(
                "dirty local builds require a local-* tag and the dev channel"
            )
        return
    head = _git_output(source_root, ["rev-parse", "HEAD"])
    if head != source_commit:
        raise ValueError("source commit does not match checkout HEAD")
    tagged_commit = _git_output(
        source_root,
        ["rev-parse", f"refs/tags/{tag}^{{commit}}"],
    )
    if tagged_commit != source_commit:
        raise ValueError("release tag does not resolve to the source commit")
    status = _git_output(
        source_root,
        ["status", "--porcelain", "--untracked-files=no"],
    )
    if status:
        raise ValueError("release source checkout contains tracked modifications")


def _git_output(source_root: Path, arguments: list[str]) -> str:
    completed = subprocess.run(
        ["/usr/bin/git", "-C", str(source_root), *arguments],
        text=True,
        capture_output=True,
        timeout=30.0,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError("release source identity could not be verified")
    return completed.stdout.strip()


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    timeout: float,
    capture_output: bool = False,
) -> str:
    environment = os.environ.copy()
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        environment.pop(name, None)
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        text=True,
        stdout=subprocess.PIPE if capture_output else subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"build command failed: {Path(command[0]).name}")
    if capture_output:
        return (completed.stdout or "") + (completed.stderr or "")
    return ""


def _default_version(source_root: Path) -> str:
    pyproject = (source_root / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'(?m)^version = "([^"]+)"$', pyproject)
    if match is None:
        raise RuntimeError("pyproject.toml does not declare a version")
    return match.group(1)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the self-contained Ultimate AI Agent macOS release bundle"
    )
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--python-runtime", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--channel", choices=["stable", "dev"], required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--source-timestamp", required=True)
    parser.add_argument("--version", default=None)
    parser.add_argument(
        "--architecture",
        choices=["arm64", "x86_64"],
        default=current_architecture(),
    )
    parser.add_argument("--frontend-dist", type=Path, default=None)
    parser.add_argument("--signing-identity", default=None)
    parser.add_argument("--notary-profile", default=None)
    parser.add_argument(
        "--skip-dependency-install",
        action="store_true",
        help="Test-only: use a prepared runtime without installing locked dependencies.",
    )
    parser.add_argument(
        "--allow-dirty-local",
        action="store_true",
        help="Local smoke only: require a local-* dev tag and bypass clean-tag verification.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_root = args.source_root.resolve()
    frontend_dist = (
        args.frontend_dist.resolve()
        if args.frontend_dist is not None
        else source_root / "apps" / "control-center" / "dist"
    )
    receipt = build_release_bundle(
        source_root=source_root,
        python_runtime=args.python_runtime.resolve(),
        output_dir=args.output_dir.resolve(),
        tag=args.tag,
        channel=args.channel,
        source_commit=args.source_commit,
        source_timestamp=args.source_timestamp,
        version=args.version or _default_version(source_root),
        architecture=args.architecture,
        frontend_dist=frontend_dist,
        signing_identity=args.signing_identity,
        notary_profile=args.notary_profile,
        skip_dependency_install=args.skip_dependency_install,
        allow_dirty_local=args.allow_dirty_local,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
