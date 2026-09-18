#!/usr/bin/env python3
"""Explicit local build recipe for the fixed FIN003 developer artifact.

Runtime setup never imports or invokes this script. The manifest records local
source consistency and an ad-hoc signature, not publisher/source attestation.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import tempfile
from dataclasses import replace
from pathlib import Path

from ultimate_ai_agent.core.finance_managed_profile import (
    MANAGED_BUILDER_SOURCE_REF,
    MANAGED_HELPER_MAX_BYTES,
    MANAGED_HELPER_NAME,
    DeveloperHelperBuildManifestV1,
    ManagedSourceFileDigestV1,
    managed_ref,
    managed_wire_payload,
    serialize_helper_build_manifest,
)
from ultimate_ai_agent.distribution.macos.contracts import current_architecture
from ultimate_ai_agent.distribution.macos.installer import (
    InstallError,
    _FINANCE_PACKAGE,
    _FINANCE_SOURCE_FILES,
    _FinanceSourceCapture,
    _finance_macho_architecture,
    _finance_signature_kind,
    _finance_source_inputs,
)

ROOT = Path(__file__).resolve().parents[2]
# SwiftPM manifests execute during compilation. This finite recipe has no
# dependencies, plugins or arbitrary manifest actions; changes need review.
_PACKAGE_RECIPE_SHA256 = (
    "6ddc397e4f019ab81cbe20c05deadd702b923b20fd054fcd96b6189e930d6e5d"
)


def _run(command: list[str], *, timeout: float, scratch: Path) -> None:
    environment = {
        name: value
        for name, value in os.environ.items()
        if name in {"DEVELOPER_DIR", "SDKROOT"}
    }
    environment.update(
        {
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
            "HOME": str(scratch / "home"),
            "CFFIXED_USER_HOME": str(scratch / "home"),
            "TMPDIR": str(scratch / "tmp"),
            "CLANG_MODULE_CACHE_PATH": str(scratch / "module-cache"),
        }
    )
    result = subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=timeout,
        check=False,
        env=environment,
    )
    if result.returncode:
        raise InstallError("FIN003_HELPER_BUILD_FAILED")


def _capture_inputs(source_root: Path) -> tuple[tuple[bytes, ...], bytes]:
    with _FinanceSourceCapture(source_root) as capture:
        inputs = _finance_source_inputs(capture)
        capture.recheck()
        return inputs


def _compile(
    source_root: Path, *, architecture: str
) -> tuple[bytes, tuple[bytes, ...], bytes]:
    if architecture not in {"arm64", "x86_64"}:
        raise InstallError("FIN003_HELPER_ARCHITECTURE_INVALID")
    source_bytes, builder_bytes = _capture_inputs(source_root)
    if builder_bytes != Path(__file__).read_bytes():
        raise InstallError("FIN003_BUILD_RECIPE_CHANGED")
    if hashlib.sha256(source_bytes[0]).hexdigest() != _PACKAGE_RECIPE_SHA256:
        raise InstallError("FIN003_BUILD_RECIPE_CHANGED")
    with tempfile.TemporaryDirectory(prefix="uaa-fin003-build-") as temporary:
        scratch = Path(temporary).resolve()
        for name in ("home", "tmp", "module-cache", "cache", "config", "security"):
            (scratch / name).mkdir(mode=0o700)
        package = scratch / "package"
        for name, raw in zip(_FINANCE_SOURCE_FILES, source_bytes, strict=True):
            destination = package / Path(name).relative_to(_FINANCE_PACKAGE)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
        output = scratch / "output"
        _run(
            [
                "/usr/bin/xcrun",
                "swift",
                "build",
                "--package-path",
                str(package),
                "--scratch-path",
                str(output),
                "--cache-path",
                str(scratch / "cache"),
                "--config-path",
                str(scratch / "config"),
                "--security-path",
                str(scratch / "security"),
                "--configuration",
                "release",
                "--arch",
                architecture,
                "--product",
                MANAGED_HELPER_NAME,
                "--disable-automatic-resolution",
                "--skip-update",
                "-Xswiftc",
                "-debug-prefix-map",
                "-Xswiftc",
                f"{scratch}=/uaa-build",
                "-Xswiftc",
                "-file-prefix-map",
                "-Xswiftc",
                f"{scratch}=/uaa-build",
            ],
            timeout=600.0,
            scratch=scratch,
        )
        # SwiftPM's release link is a build-system output, not an enrolled source.
        # Resolve it only inside our exclusive scratch tree, then require a
        # retained regular executable before accepting final bytes.
        compiled = (output / "release" / MANAGED_HELPER_NAME).resolve(strict=True)
        if not compiled.is_relative_to(output) or compiled.is_symlink():
            raise InstallError("FIN003_HELPER_BUILD_FAILED")
        _run(
            ["/usr/bin/xcrun", "strip", "-S", "-x", str(compiled)],
            timeout=60.0,
            scratch=scratch,
        )
        _run(
            [
                "/usr/bin/codesign",
                "--force",
                "--sign",
                "-",
                "--timestamp=none",
                str(compiled),
            ],
            timeout=60.0,
            scratch=scratch,
        )
        if _finance_signature_kind(compiled) != "ad-hoc":
            raise InstallError("FIN003_SOURCE_SIGNATURE_INVALID")
        with _FinanceSourceCapture(compiled.parent) as capture:
            raw = capture.read(compiled.name, MANAGED_HELPER_MAX_BYTES, executable=True)
            capture.recheck()
        if _finance_macho_architecture(raw) != architecture:
            raise InstallError("FIN003_HELPER_ARCHITECTURE_INVALID")
        forbidden = (source_root, scratch, Path(temporary), Path.home())
        if any(str(path).encode("utf-8") in raw for path in forbidden):
            raise InstallError("FIN003_HELPER_BUILD_PATH_CONTENT")
    if _capture_inputs(source_root) != (source_bytes, builder_bytes):
        raise InstallError("FIN003_BUILD_SOURCE_CHANGED")
    return raw, source_bytes, builder_bytes


def _manifest(
    raw: bytes,
    source_bytes: tuple[bytes, ...],
    builder_bytes: bytes,
    *,
    architecture: str,
) -> DeveloperHelperBuildManifestV1:
    source_files = tuple(
        ManagedSourceFileDigestV1(
            source_ref="repo-ref:" + name, sha256=hashlib.sha256(content).hexdigest()
        )
        for name, content in zip(_FINANCE_SOURCE_FILES, source_bytes, strict=True)
    )
    manifest = DeveloperHelperBuildManifestV1(
        manifest_ref="pending:manifest",
        artifact_selector_ref=f"artifact-selector-ref:finance/FIN-003/native-helper:{architecture}:v1",
        source_files=source_files,
        source_fingerprint_ref=managed_ref(
            "source-files", [managed_wire_payload(item) for item in source_files]
        ),
        builder_source_ref=MANAGED_BUILDER_SOURCE_REF,
        builder_sha256=hashlib.sha256(builder_bytes).hexdigest(),
        helper_sha256=hashlib.sha256(raw).hexdigest(),
        helper_size_bytes=len(raw),
        architecture=architecture,
    )
    payload = managed_wire_payload(manifest)
    del payload["manifest_ref"]
    return replace(manifest, manifest_ref=managed_ref("build-manifest", payload))


def _publish(
    source_root: Path, raw: bytes, manifest: bytes, *, architecture: str
) -> None:
    # Fixed paths only. Refuse preexisting aliases, hardlinks, nonregular leaves
    # or unsafe directories; publish helper first and manifest last so any
    # interruption yields either a consistent pair or explicit stale evidence.
    with _FinanceSourceCapture(source_root) as capture:
        descriptor = capture._directory(_FINANCE_PACKAGE)
        opened: list[int] = []
        bindings: list[tuple[int, str, int, os.stat_result]] = []
        try:
            for name in (".uaa-artifacts", architecture):
                try:
                    os.mkdir(name, mode=0o700, dir_fd=descriptor)
                except FileExistsError:
                    pass
                before = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
                capture._metadata(before, directory=True)
                child = os.open(
                    name,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                    dir_fd=descriptor,
                )
                if capture._identity(before) != capture._identity(os.fstat(child)):
                    os.close(child)
                    raise InstallError("FIN003_BUILD_DESTINATION_CHANGED")
                opened.append(child)
                bindings.append((descriptor, name, child, before))
                descriptor = child
            from ultimate_ai_agent.core.private_path_security import (
                require_no_extended_acl_fd,
            )

            def same_directory(before: os.stat_result, after: os.stat_result) -> bool:
                # Our own publication changes directory timestamps/link count;
                # identity, owner and permissions must remain the same.
                return (
                    before.st_dev,
                    before.st_ino,
                    before.st_uid,
                    before.st_mode,
                ) == (after.st_dev, after.st_ino, after.st_uid, after.st_mode)

            def recheck_destination() -> None:
                for relative, (fd, before) in capture.directories.items():
                    lexical = source_root / relative
                    if not same_directory(
                        before, os.lstat(lexical)
                    ) or not same_directory(before, os.fstat(fd)):
                        raise InstallError("FIN003_BUILD_DESTINATION_CHANGED")
                for parent, name, fd, before in bindings:
                    current = os.stat(name, dir_fd=parent, follow_symlinks=False)
                    if not same_directory(before, current) or not same_directory(
                        before, os.fstat(fd)
                    ):
                        raise InstallError("FIN003_BUILD_DESTINATION_CHANGED")
                    require_no_extended_acl_fd(fd, purpose="Finance artifact")

            recheck_destination()
            for name, content, mode in (
                ("helper", raw, 0o755),
                ("helper-manifest-v1.json", manifest, 0o644),
            ):
                try:
                    existing = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
                except FileNotFoundError:
                    existing = None
                if existing is not None:
                    capture._metadata(existing, directory=False)
                    if existing.st_uid != os.getuid():
                        raise InstallError("FIN003_BUILD_DESTINATION_INVALID")
                temporary = ".new-" + name
                fd = os.open(
                    temporary,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                    mode,
                    dir_fd=descriptor,
                )
                created = os.fstat(fd)
                try:
                    with os.fdopen(fd, "wb", closefd=False) as handle:
                        handle.write(content)
                        handle.flush()
                        os.fchmod(handle.fileno(), mode)
                        os.fsync(handle.fileno())
                    recheck_destination()
                    if capture._identity(os.fstat(fd)) != capture._identity(
                        os.stat(temporary, dir_fd=descriptor, follow_symlinks=False)
                    ):
                        raise InstallError("FIN003_BUILD_DESTINATION_CHANGED")
                    try:
                        current = os.stat(
                            name, dir_fd=descriptor, follow_symlinks=False
                        )
                    except FileNotFoundError:
                        current = None
                    if (existing is None) != (current is None) or (
                        existing is not None
                        and current is not None
                        and capture._identity(existing) != capture._identity(current)
                    ):
                        raise InstallError("FIN003_BUILD_DESTINATION_CHANGED")
                    os.replace(
                        temporary, name, src_dir_fd=descriptor, dst_dir_fd=descriptor
                    )
                    os.fsync(descriptor)
                    recheck_destination()
                finally:
                    os.close(fd)
                    try:
                        remaining = os.stat(
                            temporary, dir_fd=descriptor, follow_symlinks=False
                        )
                        if os.path.samestat(created, remaining):
                            os.unlink(temporary, dir_fd=descriptor)
                    except FileNotFoundError:
                        pass
        finally:
            for item in reversed(opened):
                os.close(item)


def build_finance_helper(
    *, source_root: Path, architecture: str
) -> DeveloperHelperBuildManifestV1:
    """Fresh explicit developer build; atomically publish the fixed artifact pair."""
    raw, source_bytes, builder_bytes = _compile(source_root, architecture=architecture)
    manifest = _manifest(raw, source_bytes, builder_bytes, architecture=architecture)
    _publish(
        source_root,
        raw,
        serialize_helper_build_manifest(manifest),
        architecture=architecture,
    )
    return manifest


def stage_finance_helper(
    *, source_root: Path, app_bundle: Path, architecture: str
) -> None:
    """Fresh helper for an owned release stage; outer signing owns final bytes."""
    raw, _source_bytes, _builder_bytes = _compile(
        source_root, architecture=architecture
    )
    destination = app_bundle / "Contents" / "Helpers" / MANAGED_HELPER_NAME
    destination.parent.mkdir(mode=0o755)
    with destination.open("xb") as handle:
        handle.write(raw)
    destination.chmod(0o755)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--architecture", choices=("arm64", "x86_64"), default=current_architecture()
    )
    args = parser.parse_args()
    try:
        manifest = build_finance_helper(
            source_root=ROOT, architecture=args.architecture
        )
    except (OSError, ValueError, InstallError, subprocess.SubprocessError):
        print("FIN003_HELPER_BUILD_FAILED")
        return 1
    print(manifest.manifest_ref)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
