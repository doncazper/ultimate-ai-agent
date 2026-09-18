"""Fixed FIN003 build/source artifacts; mocked signatures are unit tests only."""

from __future__ import annotations

import hashlib
import json
import os
import plistlib
import shutil
import struct
from pathlib import Path

import pytest

from scripts.macos import build_finance_helper as builder
from scripts.macos import build_release_bundle as release
from ultimate_ai_agent.core import finance_managed_profile as profile
from ultimate_ai_agent.distribution.macos import contracts, installer

ROOT = Path(__file__).resolve().parents[1]


def _macho(architecture: str = "arm64") -> bytes:
    cpu = 0x0100000C if architecture == "arm64" else 0x01000007
    return (
        b"\xcf\xfa\xed\xfe"
        + struct.pack("<IIIIIII", cpu, 0, 2, 0, 0, 0, 0)
        + b"unit-helper"
    )


@pytest.fixture
def source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "source"
    for name in (*installer._FINANCE_SOURCE_FILES, installer._FINANCE_BUILDER):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    monkeypatch.setattr(contracts, "current_architecture", lambda: "arm64")
    monkeypatch.setattr(installer, "_finance_signature_kind", lambda _path: "ad-hoc")
    return root


def _artifact(
    source: Path, raw: bytes | None = None
) -> profile.DeveloperHelperBuildManifestV1:
    raw = _macho() if raw is None else raw
    inputs, build_bytes = builder._capture_inputs(source)
    manifest = builder._manifest(raw, inputs, build_bytes, architecture="arm64")
    builder._publish(
        source,
        raw,
        profile.serialize_helper_build_manifest(manifest),
        architecture="arm64",
    )
    return manifest


def test_developer_source_returns_exact_immutable_bytes_and_manifest_bindings(
    source: Path,
) -> None:
    manifest = _artifact(source)
    verified = installer.verified_developer_finance_helper(source)
    assert verified.executable_bytes == _macho()
    assert verified.identity.helper_sha256 == manifest.helper_sha256
    assert verified.identity.source.build_manifest_ref == manifest.manifest_ref
    assert verified.identity.source.builder_fingerprint_ref == profile.managed_ref(
        "builder",
        {
            "builder_source_ref": manifest.builder_source_ref,
            "builder_sha256": manifest.builder_sha256,
        },
    )
    assert verified.identity.publisher_verified is False
    assert verified.identity.source_attestation_verified is False
    (source / installer._FINANCE_PACKAGE / ".uaa-artifacts/arm64/helper").unlink()
    assert verified.executable_bytes == _macho()


@pytest.mark.parametrize(
    "changed",
    [
        "swift",
        "package",
        "builder",
        "helper",
        "manifest",
        "architecture",
        "mode",
        "symlink",
        "hardlink",
        "extra-source",
    ],
)
def test_developer_source_rejects_stale_or_unsafe_artifact(
    source: Path, changed: str
) -> None:
    _artifact(source)
    artifact = source / installer._FINANCE_PACKAGE / ".uaa-artifacts/arm64"
    helper = artifact / "helper"
    if changed in {"swift", "package", "builder"}:
        selected = {
            "swift": installer._FINANCE_SOURCE_FILES[1],
            "package": installer._FINANCE_SOURCE_FILES[0],
            "builder": installer._FINANCE_BUILDER,
        }[changed]
        path = source / selected
        path.write_bytes(path.read_bytes() + b"\n")
    elif changed == "helper":
        helper.write_bytes(_macho() + b"changed")
    elif changed == "manifest":
        (artifact / "helper-manifest-v1.json").write_bytes(b"{}")
    elif changed == "architecture":
        _artifact(source, _macho("x86_64"))
    elif changed == "mode":
        helper.chmod(0o644)
    elif changed == "symlink":
        target = helper.with_name("other")
        helper.rename(target)
        helper.symlink_to(target.name)
    elif changed == "hardlink":
        os.link(helper, helper.with_name("other"))
    else:
        (
            source
            / installer._FINANCE_PACKAGE
            / "Sources/UAAMatrixProtectedCacheHelper/extra.swift"
        ).write_bytes(b"")
    with pytest.raises(installer.InstallError, match="FIN003_"):
        installer.verified_developer_finance_helper(source)


def test_developer_signature_bracket_detects_same_byte_leaf_replacement(
    source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _artifact(source)

    def replace_helper(path: Path) -> str:
        raw = path.read_bytes()
        path.unlink()
        path.write_bytes(raw)
        path.chmod(0o755)
        return "ad-hoc"

    monkeypatch.setattr(installer, "_finance_signature_kind", replace_helper)
    with pytest.raises(installer.InstallError, match="FIN003_SOURCE_CHANGED"):
        installer.verified_developer_finance_helper(source)


@pytest.fixture
def installed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> installer.InstallLayout:
    root = tmp_path / "installed"
    version = root / "versions" / "local+unit"
    app = version / contracts.APP_BUNDLE_NAME
    contents = app / "Contents"
    (contents / "Helpers").mkdir(parents=True)
    (contents / "Resources").mkdir()
    plist = {
        "CFBundleIdentifier": contracts.APP_BUNDLE_IDENTIFIER,
        "UAASourceCommit": "a" * 40,
        "CFBundleShortVersionString": "0.1.0",
        "UAAReleaseTag": "v0.1.0",
        "UAAUpdateChannel": "dev",
    }
    (contents / "Info.plist").write_bytes(plistlib.dumps(plist))
    boundary = {
        "schema_version": "uaa.macos.distribution-boundary.v1",
        "product_line": contracts.PRODUCT_LINE,
        "architecture": "arm64",
        "source_commit_ref": "git-commit:" + "a" * 40,
        "tag_ref": "git-tag:v0.1.0",
        "channel": "dev",
    }
    (contents / "Resources/distribution-boundary.json").write_text(json.dumps(boundary))
    helper = app / installer._FINANCE_HELPER
    helper.write_bytes(_macho())
    helper.chmod(0o755)
    inventory = release._build_bundle_manifest(
        payload_root=version,
        tag="v0.1.0",
        channel="dev",
        source_commit="a" * 40,
        source_timestamp="2026-01-01T00:00:00Z",
        version="0.1.0",
        architecture="arm64",
        signing_kind="ad-hoc",
        notarized=False,
    )
    (version / "bundle-manifest.json").write_text(json.dumps(inventory))
    (root / "current").symlink_to("versions/local+unit")
    monkeypatch.setattr(contracts, "current_architecture", lambda: "arm64")
    monkeypatch.setattr(installer, "_finance_signature_kind", lambda _path: "ad-hoc")
    return installer.InstallLayout(
        root=root, applications_dir=tmp_path / "applications", bin_dir=tmp_path / "bin"
    )


def test_installed_source_binds_signed_metadata_and_inventory_between_two_signatures(
    installed: installer.InstallLayout, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed: list[Path] = []
    monkeypatch.setattr(
        installer,
        "_finance_signature_kind",
        lambda path: observed.append(path) or "ad-hoc",
    )
    verified = installer.verified_installed_finance_helper(installed)
    assert len(observed) == 2 and observed[0] == observed[1]
    assert verified.executable_bytes == _macho()
    source = verified.identity.source
    assert source.source_commit_ref == "git-commit:" + "a" * 40
    assert (
        source.source_version_ref
        == "macos-version-ref:sha256:" + hashlib.sha256(b"local+unit").hexdigest()
    )
    assert source.bundle_ref.startswith("macos-bundle-ref:sha256:")
    assert source.bundle_inventory_ref.startswith("bundle-inventory-ref:sha256:")
    assert verified.identity.signing_kind == "ad-hoc"
    assert not verified.identity.publisher_verified


@pytest.mark.parametrize("phase", [1, 2])
@pytest.mark.parametrize(
    "changed", ["current", "app", "plist", "helper", "inventory", "boundary"]
)
def test_installed_source_rejects_identity_replacement_in_either_signature_bracket(
    installed: installer.InstallLayout,
    monkeypatch: pytest.MonkeyPatch,
    phase: int,
    changed: str,
) -> None:
    calls = 0

    def signature(app: Path) -> str:
        nonlocal calls
        calls += 1
        if calls != phase:
            return "ad-hoc"
        if changed == "current":
            installed.current_link.unlink()
            installed.current_link.symlink_to("versions/local+unit")
        elif changed == "app":
            other = app.with_name("replaced")
            app.rename(other)
            shutil.copytree(other, app)
        else:
            path = {
                "plist": app / "Contents/Info.plist",
                "helper": app / installer._FINANCE_HELPER,
                "inventory": app.parent / "bundle-manifest.json",
                "boundary": app / "Contents/Resources/distribution-boundary.json",
            }[changed]
            mode = path.stat().st_mode & 0o777
            raw = path.read_bytes()
            path.unlink()
            path.write_bytes(raw)
            path.chmod(mode)
        return "ad-hoc"

    monkeypatch.setattr(installer, "_finance_signature_kind", signature)
    with pytest.raises(installer.InstallError, match="FIN003_SOURCE_CHANGED"):
        installer.verified_installed_finance_helper(installed)


@pytest.mark.parametrize(
    "changed",
    [
        "signature",
        "signing-kind",
        "inventory-digest",
        "duplicate-json",
        "metadata-commit",
        "missing-helper",
        "linked-contents",
        "oversize-metadata",
        "non-executable",
    ],
)
def test_installed_source_rejects_unverified_source(
    installed: installer.InstallLayout, monkeypatch: pytest.MonkeyPatch, changed: str
) -> None:
    version = installed.root / "versions/local+unit"
    app = version / contracts.APP_BUNDLE_NAME
    if changed == "signature":

        def invalid(_path: Path) -> str:
            raise installer.InstallError("FIN003_SOURCE_SIGNATURE_INVALID")

        monkeypatch.setattr(installer, "_finance_signature_kind", invalid)
    elif changed == "signing-kind":
        kinds = iter(("ad-hoc", "developer-id"))
        monkeypatch.setattr(
            installer, "_finance_signature_kind", lambda _path: next(kinds)
        )
    elif changed == "inventory-digest":
        path = version / "bundle-manifest.json"
        value = json.loads(path.read_bytes())
        value["files"][0]["sha256"] = "0" * 64
        path.write_text(json.dumps(value))
    elif changed == "duplicate-json":
        (version / "bundle-manifest.json").write_bytes(b'{"files":[],"files":[]}')
    elif changed == "metadata-commit":
        path = app / "Contents/Info.plist"
        value = plistlib.loads(path.read_bytes())
        value["UAASourceCommit"] = "b" * 40
        path.write_bytes(plistlib.dumps(value))
    elif changed == "missing-helper":
        (app / installer._FINANCE_HELPER).unlink()
    elif changed == "linked-contents":
        contents = app / "Contents"
        contents.rename(app / "other")
        contents.symlink_to("other")
    elif changed == "oversize-metadata":
        (app / "Contents/Info.plist").write_bytes(
            b"a" * (installer._FINANCE_METADATA_MAX_BYTES + 1)
        )
    else:
        (app / installer._FINANCE_HELPER).chmod(0o644)
    with pytest.raises(installer.InstallError, match="FIN003_"):
        installer.verified_installed_finance_helper(installed)


def test_build_uses_fresh_copy_and_final_signed_bytes(
    source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    commands: list[list[str]] = []
    unsigned, signed = _macho(), _macho() + b"signed"

    def run(command: list[str], *, timeout: float, scratch: Path) -> None:
        assert timeout > 0 and scratch.is_dir()
        commands.append(command)
        if "build" in command:
            copied = Path(command[command.index("--package-path") + 1])
            assert not copied.is_relative_to(source)
            assert (copied / "Package.swift").read_bytes() == (
                source / installer._FINANCE_SOURCE_FILES[0]
            ).read_bytes()
            output = (
                Path(command[command.index("--scratch-path") + 1])
                / "release"
                / profile.MANAGED_HELPER_NAME
            )
            output.parent.mkdir(parents=True)
            output.write_bytes(unsigned)
            output.chmod(0o755)
        elif command[0] == "/usr/bin/codesign":
            Path(command[-1]).write_bytes(signed)

    monkeypatch.setattr(builder, "_run", run)
    monkeypatch.setattr(builder, "_finance_signature_kind", lambda _path: "ad-hoc")
    manifest = builder.build_finance_helper(source_root=source, architecture="arm64")
    assert manifest.helper_sha256 == hashlib.sha256(signed).hexdigest()
    assert manifest.helper_sha256 != hashlib.sha256(unsigned).hexdigest()
    assert commands[0][0:3] == ["/usr/bin/xcrun", "swift", "build"]
    assert "--disable-automatic-resolution" in commands[0]
    assert "--skip-update" in commands[0]
    assert len(commands) == 3
    artifact = source / installer._FINANCE_PACKAGE / ".uaa-artifacts/arm64"
    assert (artifact / "helper").read_bytes() == signed
    assert (
        profile.parse_helper_build_manifest(
            (artifact / "helper-manifest-v1.json").read_bytes()
        )
        == manifest
    )
    assert not (source / installer._FINANCE_PACKAGE / ".build").exists()


def test_build_rejects_changed_dependency_recipe_before_compiler(
    source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (source / installer._FINANCE_SOURCE_FILES[0]).write_bytes(
        b"import PackageDescription\n"
    )
    monkeypatch.setattr(
        builder, "_run", lambda *_args, **_kwargs: pytest.fail("compiler must not run")
    )
    with pytest.raises(installer.InstallError, match="FIN003_BUILD_RECIPE_CHANGED"):
        builder.build_finance_helper(source_root=source, architecture="arm64")


def test_build_publication_refuses_linked_output_without_modifying_target(
    source: Path,
) -> None:
    _artifact(source)
    path = source / installer._FINANCE_PACKAGE / ".uaa-artifacts/arm64/helper"
    other = source / "unowned"
    other.write_bytes(b"preserve")
    path.unlink()
    path.symlink_to(other)
    with pytest.raises(installer.InstallError, match="FIN003_SOURCE_INVALID"):
        _artifact(source)
    assert other.read_bytes() == b"preserve"


def test_release_stage_uses_fixed_nested_helper_then_final_inventory(
    source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = tmp_path / "payload" / contracts.APP_BUNDLE_NAME
    (app / "Contents").mkdir(parents=True)
    monkeypatch.setattr(
        builder, "_compile", lambda *_args, **_kwargs: (_macho(), (), b"")
    )
    builder.stage_finance_helper(
        source_root=source, app_bundle=app, architecture="arm64"
    )
    helper = app / installer._FINANCE_HELPER
    assert helper.read_bytes() == _macho()
    signed = _macho() + b"outer-signature"
    helper.write_bytes(signed)
    inventory = release._build_bundle_manifest(
        payload_root=app.parent,
        tag="v0.1.0",
        channel="dev",
        source_commit="a" * 40,
        source_timestamp="2026-01-01T00:00:00Z",
        version="0.1.0",
        architecture="arm64",
        signing_kind="ad-hoc",
        notarized=False,
    )
    (entry,) = inventory["files"]
    assert entry["path"] == f"{contracts.APP_BUNDLE_NAME}/{installer._FINANCE_HELPER}"
    assert entry["sha256"] == hashlib.sha256(signed).hexdigest()
    assert entry["mode"] == 0o755


@pytest.mark.parametrize(
    "raw",
    [b"", b"not-macho", _macho().replace(b"\x02\x00\x00\x00", b"\x06\x00\x00\x00", 1)],
    ids=["empty", "invalid-magic", "library-not-executable"],
)
def test_helper_requires_thin_supported_executable_macho(raw: bytes) -> None:
    with pytest.raises(
        installer.InstallError, match="FIN003_HELPER_ARCHITECTURE_INVALID"
    ):
        installer._finance_macho_architecture(raw)


@pytest.mark.parametrize(
    "details,expected",
    [
        (b"Signature=adhoc\n", "ad-hoc"),
        (
            b"Authority=Developer ID Application: fixture\nCodeDirectory v=20500 flags=0x10000(runtime)\n",
            "developer-id",
        ),
        (b"Authority=Developer ID Application: fixture\n", None),
        (b"Signature=unknown\n", None),
        (b"x" * (installer._FINANCE_METADATA_MAX_BYTES + 1), None),
    ],
    ids=["adhoc", "developer-id", "missing-runtime", "unknown", "oversize"],
)
def test_signature_details_are_fixed_bounded_and_classified(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    details: bytes,
    expected: str | None,
) -> None:
    import selectors

    output = tmp_path / "unit-details"
    output.write_bytes(details)
    stream = output.open("rb")
    commands: list[list[str]] = []

    class Child:
        stdout = stream

        def wait(self, *, timeout: float) -> int:
            assert timeout > 0
            return 0

        def poll(self) -> int:
            return 0

    class Selector:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def register(self, *_args):
            return None

        def select(self, remaining: float):
            assert remaining > 0
            return [True]

    app = tmp_path / "unit-app"
    monkeypatch.setattr(
        installer,
        "_verify_installed_application",
        lambda path: (
            None if path == app else pytest.fail("unexpected signature target")
        ),
    )
    monkeypatch.setattr(
        installer.subprocess,
        "Popen",
        lambda command, **_kwargs: commands.append(command) or Child(),
    )
    monkeypatch.setattr(selectors, "DefaultSelector", Selector)
    if expected is None:
        with pytest.raises(
            installer.InstallError, match="FIN003_SOURCE_SIGNATURE_INVALID"
        ):
            installer._finance_signature_kind(app)
    else:
        assert installer._finance_signature_kind(app) == expected
    assert commands == [["/usr/bin/codesign", "-d", "--verbose=4", str(app)]]
    assert stream.closed


def test_signature_deadline_kills_and_reaps_only_owned_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import selectors
    from types import SimpleNamespace

    output = tmp_path / "unit-details"
    output.write_bytes(b"")
    stream = output.open("rb")
    events: list[object] = []

    class Child:
        stdout = stream

        def poll(self):
            return None

        def kill(self):
            events.append("kill")

        def wait(self, *, timeout: float):
            events.append(("wait", timeout))
            return -9

    class Selector:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def register(self, *_args):
            return None

        def select(self, _remaining):
            pytest.fail("expired deadline must not wait")

    clock = iter((0.0, 31.0))
    monkeypatch.setattr(
        installer, "time", SimpleNamespace(monotonic=lambda: next(clock))
    )
    monkeypatch.setattr(installer, "_verify_installed_application", lambda _path: None)
    monkeypatch.setattr(
        installer.subprocess, "Popen", lambda *_args, **_kwargs: Child()
    )
    monkeypatch.setattr(selectors, "DefaultSelector", Selector)
    with pytest.raises(installer.InstallError, match="FIN003_SOURCE_SIGNATURE_INVALID"):
        installer._finance_signature_kind(tmp_path / "unit-app")
    assert events == ["kill", ("wait", 5.0)]
    assert stream.closed


def test_build_rejects_source_change_during_compile(
    source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def run(command: list[str], **_kwargs) -> None:
        if "build" in command:
            output = (
                Path(command[command.index("--scratch-path") + 1])
                / "release"
                / profile.MANAGED_HELPER_NAME
            )
            output.parent.mkdir(parents=True)
            output.write_bytes(_macho())
            output.chmod(0o755)
            path = source / installer._FINANCE_SOURCE_FILES[1]
            path.write_bytes(path.read_bytes() + b"\n")

    monkeypatch.setattr(builder, "_run", run)
    monkeypatch.setattr(builder, "_finance_signature_kind", lambda _path: "ad-hoc")
    with pytest.raises(installer.InstallError, match="FIN003_BUILD_SOURCE_CHANGED"):
        builder.build_finance_helper(source_root=source, architecture="arm64")
    assert not (source / installer._FINANCE_PACKAGE / ".uaa-artifacts").exists()


def test_source_json_rejects_deep_objects_before_decode_and_duplicate_keys() -> None:
    with pytest.raises(installer.InstallError, match="FIN003_SOURCE_METADATA_INVALID"):
        installer._finance_json(b'{"nested":' + b"[" * 33 + b"0" + b"]" * 33 + b"}")
    with pytest.raises(installer.InstallError, match="FIN003_SOURCE_METADATA_INVALID"):
        installer._finance_json(b'{"field":1,"field":2}')
    assert installer._finance_json(b'{"quoted":"[[[{{{\\""}') == {"quoted": '[[[{{{"'}


def test_installed_capture_retains_leaves_before_first_signature_and_reads_between_brackets(
    installed: installer.InstallLayout, monkeypatch: pytest.MonkeyPatch
) -> None:
    signature_count = 0
    captures: list[int] = []
    original_read = installer._FinanceSourceCapture.read

    def read(self, *args, **kwargs):
        captures.append(signature_count)
        assert args[0] in self.files
        return original_read(self, *args, **kwargs)

    def signature(_app: Path) -> str:
        nonlocal signature_count
        signature_count += 1
        return "ad-hoc"

    monkeypatch.setattr(installer._FinanceSourceCapture, "read", read)
    monkeypatch.setattr(installer, "_finance_signature_kind", signature)
    installer.verified_installed_finance_helper(installed)
    assert captures == [1, 1, 1, 1]
    assert signature_count == 2


def test_signature_verifier_failure_has_fixed_fin003_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failure(_path):
        raise installer.InstallError(
            "staged Applications bundle signature verification failed"
        )

    monkeypatch.setattr(installer, "_verify_installed_application", failure)
    monkeypatch.setattr(
        installer.subprocess,
        "Popen",
        lambda *_args, **_kwargs: pytest.fail(
            "details must not run after verification failure"
        ),
    )
    with pytest.raises(
        installer.InstallError, match="^FIN003_SOURCE_SIGNATURE_INVALID$"
    ):
        installer._finance_signature_kind(Path("/unused-unit-signature-target"))
