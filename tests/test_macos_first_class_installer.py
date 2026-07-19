from __future__ import annotations

import io
import json
import plistlib
import stat
import subprocess
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.macos.build_release_bundle import build_release_bundle
from scripts.macos.release_policy import classify_tag
from scripts.macos.verify_installer_e2e import (
    InstallerE2EError,
    validate_receipts,
    validate_status_payload,
)
from ultimate_ai_agent.distribution.macos.static_policy import (
    MACOS_DISTRIBUTION_EXACT_ADAPTER_FILES,
    macos_distribution_adapter_policy_failures,
    macos_distribution_policy_failures,
)
from ultimate_ai_agent.distribution.macos.contracts import (
    APP_BUNDLE_IDENTIFIER,
    APP_BUNDLE_NAME,
    BUNDLE_MANIFEST_SCHEMA,
    MINIMUM_MACOS,
    PRODUCT_LINE,
    RELEASE_DESCRIPTOR_SCHEMA,
    ReleaseCandidate,
    ReleaseDescriptor,
    select_release,
    sha256_file,
)
from ultimate_ai_agent.distribution.macos.github_releases import GitHubReleaseClient
from ultimate_ai_agent.distribution.macos.installer import (
    APP_MANAGED_MARKER,
    CLI_MARKER,
    InstallError,
    InstallLayout,
    current_manifest,
    current_version_id,
    install_archive,
    rollback,
    safe_extract_archive,
    _select_applications_dir,
)
from ultimate_ai_agent.distribution.macos.runtime import (
    RuntimePaths,
    check_for_update,
)


ROOT = Path(__file__).resolve().parents[1]


def test_newest_channel_compares_stable_and_dev_by_tag_commit_time() -> None:
    stable = _candidate(
        tag="v0.104.0",
        channel="stable",
        source_timestamp="2026-06-23T12:28:59-07:00",
        published_at="2026-07-18T10:00:00Z",
        release_id=10,
    )
    dev = _candidate(
        tag="v0.105.1-web-hybrid",
        channel="dev",
        source_timestamp="2026-07-10T14:36:02-07:00",
        published_at="2026-07-18T09:00:00Z",
        release_id=11,
    )

    newest = select_release([stable, dev], "newest")
    stable_only = select_release([stable, dev], "stable")
    dev_only = select_release([stable, dev], "dev")

    assert newest.selected == dev
    assert newest.stable == stable
    assert newest.dev == dev
    assert stable_only.selected == stable
    assert dev_only.selected == dev


def test_backfilled_older_release_does_not_look_newer() -> None:
    older_but_published_later = _candidate(
        tag="v0.103.0",
        channel="stable",
        source_timestamp="2026-06-01T10:00:00Z",
        published_at="2026-07-18T12:00:00Z",
        release_id=22,
    )
    newer_but_published_earlier = _candidate(
        tag="v0.104.0",
        channel="stable",
        source_timestamp="2026-06-23T10:00:00Z",
        published_at="2026-07-18T11:00:00Z",
        release_id=21,
    )

    selection = select_release(
        [older_but_published_later, newer_but_published_earlier],
        "newest",
    )

    assert selection.selected == newer_but_published_earlier


def test_release_policy_excludes_historical_audit_tags() -> None:
    assert classify_tag("v0.104.0") == "stable"
    assert classify_tag("v0.105.1-web-hybrid") == "dev"
    with pytest.raises(ValueError, match="historical"):
        classify_tag("v2.0.0")
    with pytest.raises(ValueError, match="historical"):
        classify_tag("v1.7.2")
    with pytest.raises(ValueError, match="conflicts"):
        classify_tag("v0.104.0", requested_channel="dev")


def test_github_catalog_requires_active_descriptor_and_matching_assets() -> None:
    repository = "doncazper/ultimate-ai-agent"
    releases_url = (
        f"https://api.github.com/repos/{repository}/releases?per_page=100"
    )
    descriptor_url = (
        f"https://api.github.com/repos/{repository}/releases/assets/101"
    )
    artifact_url = (
        f"https://api.github.com/repos/{repository}/releases/assets/102"
    )
    descriptor = _descriptor(
        tag="v0.105.1-web-hybrid",
        channel="dev",
        source_timestamp="2026-07-10T14:36:02-07:00",
    )
    releases = [
        {
            "id": 55,
            "draft": False,
            "prerelease": True,
            "tag_name": descriptor.tag,
            "published_at": "2026-07-18T11:00:00Z",
            "assets": [
                {
                    "name": "uaa-macos-arm64.release.json",
                    "url": descriptor_url,
                    "size": len(descriptor.to_json_bytes()),
                    "digest": None,
                },
                {
                    "name": "uaa-macos-arm64.tar.gz",
                    "url": artifact_url,
                    "size": descriptor.artifact_size,
                    "digest": f"sha256:{descriptor.artifact_sha256}",
                },
            ],
        },
        {
            "id": 56,
            "draft": False,
            "prerelease": False,
            "tag_name": "v2.0.0",
            "published_at": "2026-07-18T12:00:00Z",
            "assets": [],
        },
    ]
    opener = _FakeOpener(
        {
            releases_url: json.dumps(releases).encode(),
            descriptor_url: descriptor.to_json_bytes(),
        }
    )

    catalog = GitHubReleaseClient(
        repository=repository,
        token="held-in-memory",
        opener=opener,
    ).fetch_catalog("arm64")

    assert len(catalog.candidates) == 1
    assert catalog.candidates[0].descriptor.tag == "v0.105.1-web-hybrid"
    assert catalog.ignored_release_count == 1
    assert catalog.authenticated is True
    assert "held-in-memory" not in repr(catalog)


def test_safe_extract_rejects_traversal_and_links(tmp_path: Path) -> None:
    traversal = tmp_path / "traversal.tar.gz"
    with tarfile.open(traversal, "w:gz") as tar:
        payload = b"unsafe"
        info = tarfile.TarInfo("../outside")
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))
    with pytest.raises(InstallError, match="unsafe path"):
        safe_extract_archive(traversal, tmp_path / "extract-traversal")
    assert not (tmp_path / "outside").exists()

    linked = tmp_path / "linked.tar.gz"
    with tarfile.open(linked, "w:gz") as tar:
        info = tarfile.TarInfo("linked")
        info.type = tarfile.SYMTYPE
        info.linkname = "/tmp/outside"
        tar.addfile(info)
    with pytest.raises(InstallError, match="link or special"):
        safe_extract_archive(linked, tmp_path / "extract-linked")


def test_existing_app_location_wins_over_current_directory_writability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    system_applications = tmp_path / "system-applications"
    installed_app = system_applications / APP_BUNDLE_NAME
    installed_app.mkdir(parents=True)
    monkeypatch.setattr(
        "ultimate_ai_agent.distribution.macos.installer._directory_is_writable",
        lambda path: False,
    )

    selected = _select_applications_dir(
        home=home,
        system_applications=system_applications,
    )

    assert selected == system_applications


def test_atomic_install_idempotency_update_and_rollback(tmp_path: Path) -> None:
    layout = _layout(tmp_path)
    first_archive, first_descriptor = _tiny_release(
        tmp_path / "first",
        tag="v0.104.0",
        channel="stable",
        commit="1" * 40,
        source_timestamp="2026-06-23T12:28:59-07:00",
    )
    second_archive, second_descriptor = _tiny_release(
        tmp_path / "second",
        tag="v0.105.1-web-hybrid",
        channel="dev",
        commit="2" * 40,
        source_timestamp="2026-07-10T14:36:02-07:00",
    )

    def skip_signature(app: Path, descriptor: ReleaseDescriptor) -> None:
        _ = app, descriptor

    first = install_archive(
        first_archive,
        first_descriptor,
        layout,
        code_signature_verifier=skip_signature,
    )
    repeated = install_archive(
        first_archive,
        first_descriptor,
        layout,
        code_signature_verifier=skip_signature,
    )
    second = install_archive(
        second_archive,
        second_descriptor,
        layout,
        code_signature_verifier=skip_signature,
    )

    assert first.status == "installed"
    assert repeated.status == "already-current"
    assert second.status == "installed"
    assert current_version_id(layout) == second.version_id
    assert layout.current_link.is_symlink()
    assert layout.previous_link.is_symlink()
    assert layout.app_link.is_dir()
    assert not layout.app_link.is_symlink()
    assert layout.cli_path.is_file()
    assert CLI_MARKER in layout.cli_path.read_text(encoding="utf-8")
    assert str(tmp_path) not in layout.cli_path.read_text(encoding="utf-8")
    assert current_manifest(layout)["tag"] == second_descriptor.tag

    rolled_back = rollback(
        layout,
        application_verifier=lambda app: None,
    )

    assert rolled_back.version_id == first.version_id
    assert current_version_id(layout) == first.version_id
    assert current_manifest(layout)["tag"] == first_descriptor.tag


def test_entrypoint_failures_restore_install_and_rollback_links(
    tmp_path: Path,
) -> None:
    layout = _layout(tmp_path)
    first_archive, first_descriptor = _tiny_release(
        tmp_path / "first",
        tag="v0.104.0",
        channel="stable",
        commit="1" * 40,
        source_timestamp="2026-06-23T12:28:59-07:00",
    )
    second_archive, second_descriptor = _tiny_release(
        tmp_path / "second",
        tag="v0.105.1-web-hybrid",
        channel="dev",
        commit="2" * 40,
        source_timestamp="2026-07-10T14:36:02-07:00",
    )

    def skip_signature(app: Path, descriptor: ReleaseDescriptor) -> None:
        _ = app, descriptor

    first = install_archive(
        first_archive,
        first_descriptor,
        layout,
        code_signature_verifier=skip_signature,
    )
    original_cli = layout.cli_path.read_bytes()

    def reject_applications_copy(
        app: Path,
        descriptor: ReleaseDescriptor,
    ) -> None:
        _ = descriptor
        if app.name.startswith(".Ultimate AI Agent"):
            raise InstallError("injected Applications promotion failure")

    with pytest.raises(InstallError, match="injected Applications"):
        install_archive(
            second_archive,
            second_descriptor,
            layout,
            code_signature_verifier=reject_applications_copy,
        )

    assert current_version_id(layout) == first.version_id
    assert not layout.previous_link.exists()
    assert layout.app_link.is_dir()
    assert layout.cli_path.read_bytes() == original_cli

    second = install_archive(
        second_archive,
        second_descriptor,
        layout,
        code_signature_verifier=skip_signature,
    )

    def reject_rollback_copy(app: Path) -> None:
        _ = app
        raise InstallError("injected rollback Applications failure")

    with pytest.raises(InstallError, match="injected rollback"):
        rollback(layout, application_verifier=reject_rollback_copy)

    assert current_version_id(layout) == second.version_id
    assert layout.previous_link.resolve().name == first.version_id
    assert layout.app_link.is_dir()
    assert layout.cli_path.read_bytes() == original_cli


def test_installer_refuses_unmanaged_app_or_cli(tmp_path: Path) -> None:
    layout = _layout(tmp_path)
    archive, descriptor = _tiny_release(
        tmp_path / "release",
        tag="v0.104.0",
        channel="stable",
        commit="3" * 40,
        source_timestamp="2026-06-23T12:28:59-07:00",
    )
    layout.applications_dir.mkdir(parents=True)
    layout.app_link.mkdir()

    with pytest.raises(InstallError, match="not owned"):
        install_archive(
            archive,
            descriptor,
            layout,
            code_signature_verifier=lambda app, release: None,
        )


def test_installer_migrates_only_the_exact_legacy_repo_cli(tmp_path: Path) -> None:
    layout = _layout(tmp_path)
    archive, descriptor = _tiny_release(
        tmp_path / "release",
        tag="v0.104.0",
        channel="stable",
        commit="6" * 40,
        source_timestamp="2026-06-23T12:28:59-07:00",
    )
    layout.bin_dir.mkdir(parents=True)
    layout.cli_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'exec "/workspace/ultimate-ai-agent/scripts/dev/uaa" "$@"\n',
        encoding="utf-8",
    )

    result = install_archive(
        archive,
        descriptor,
        layout,
        code_signature_verifier=lambda app, release: None,
    )

    assert result.status == "installed"
    assert CLI_MARKER in layout.cli_path.read_text(encoding="utf-8")
    assert "/workspace/" not in layout.cli_path.read_text(encoding="utf-8")


def test_installer_refuses_arbitrary_existing_cli(tmp_path: Path) -> None:
    layout = _layout(tmp_path)
    archive, descriptor = _tiny_release(
        tmp_path / "release",
        tag="v0.104.0",
        channel="stable",
        commit="7" * 40,
        source_timestamp="2026-06-23T12:28:59-07:00",
    )
    layout.bin_dir.mkdir(parents=True)
    layout.cli_path.write_text("#!/bin/sh\necho unrelated\n", encoding="utf-8")

    with pytest.raises(InstallError, match="not owned"):
        install_archive(
            archive,
            descriptor,
            layout,
            code_signature_verifier=lambda app, release: None,
        )


def test_packaged_bundle_has_native_app_verified_manifest_and_no_checkout_path(
    tmp_path: Path,
) -> None:
    runtime = tmp_path / "runtime"
    (runtime / "bin").mkdir(parents=True)
    fake_python = runtime / "bin" / "python3"
    fake_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_python.chmod(0o755)
    frontend = tmp_path / "frontend"
    (frontend / "assets").mkdir(parents=True)
    (frontend / "index.html").write_text("<!doctype html><title>UAA</title>\n")
    output = tmp_path / "output"

    receipt = build_release_bundle(
        source_root=ROOT,
        python_runtime=runtime,
        output_dir=output,
        tag="local-test-build",
        channel="dev",
        source_commit="4" * 40,
        source_timestamp="2026-07-10T14:36:02-07:00",
        version="0.104.0",
        architecture="arm64",
        frontend_dist=frontend,
        signing_identity=None,
        notary_profile=None,
        skip_dependency_install=True,
        allow_dirty_local=True,
    )
    descriptor = ReleaseDescriptor.from_json_bytes(
        (output / "uaa-macos-arm64.release.json").read_bytes(),
        expected_architecture="arm64",
    )
    install_layout = _layout(tmp_path / "installed")

    result = install_archive(
        output / "uaa-macos-arm64.tar.gz",
        descriptor,
        install_layout,
    )
    executable = (
        install_layout.current_link
        / APP_BUNDLE_NAME
        / "Contents"
        / "MacOS"
        / APP_BUNDLE_NAME.removesuffix(".app")
    )
    installed_app = executable.parents[2]
    icon = installed_app / "Contents" / "Resources" / "UltimateAI-Agent.icns"
    with (installed_app / "Contents" / "Info.plist").open("rb") as handle:
        installed_plist = plistlib.load(handle)
    file_result = subprocess.run(
        ["/usr/bin/file", "-b", str(executable)],
        text=True,
        capture_output=True,
        check=True,
    )

    assert receipt["status"] == "built"
    assert receipt["signing_kind"] == "ad-hoc"
    assert result.status == "installed"
    assert "Mach-O" in file_result.stdout
    assert icon.is_file()
    assert icon.stat().st_size > 100_000
    assert installed_plist["CFBundleIconFile"] == "UltimateAI-Agent.icns"
    assert subprocess.run(
        ["/usr/bin/codesign", "--verify", "--deep", "--strict", str(installed_app)],
        capture_output=True,
        check=False,
    ).returncode == 0
    for path in output.iterdir():
        if path.is_file() and path.stat().st_size < 10 * 1024 * 1024:
            assert str(ROOT).encode() not in path.read_bytes()
            assert b"/Users/" not in path.read_bytes()


def test_update_check_never_downgrades_a_newer_local_install(tmp_path: Path) -> None:
    layout = _layout(tmp_path)
    archive, descriptor = _tiny_release(
        tmp_path / "local",
        tag="worktree-local",
        channel="dev",
        commit="5" * 40,
        source_timestamp="2026-07-17T14:43:26-07:00",
    )
    install_archive(
        archive,
        descriptor,
        layout,
        code_signature_verifier=lambda app, release: None,
    )
    remote = _candidate(
        tag="v0.105.1-web-hybrid",
        channel="dev",
        source_timestamp="2026-07-10T14:36:02-07:00",
        published_at="2026-07-18T12:00:00Z",
        release_id=77,
    )
    client = SimpleNamespace(
        fetch_catalog=lambda architecture: SimpleNamespace(
            candidates=(remote,),
            ignored_release_count=0,
            authenticated=True,
        )
    )

    check = check_for_update(
        RuntimePaths(layout),
        client=client,
        channel="newest",
    )

    assert check.update_available is False
    assert check.reason_ref == "reason-ref:update:installed-is-current-or-newer"


def test_workflow_is_tag_bound_checksum_verified_and_does_not_move_tags() -> None:
    workflow = (ROOT / ".github" / "workflows" / "macos-release.yml").read_text(
        encoding="utf-8"
    )

    assert "refs/tags/${{ steps.source.outputs.tag }}" in workflow
    assert 'git rev-parse "refs/tags/$RELEASE_TAG^{commit}"' in workflow
    assert "scripts/macos/release_policy.py" in workflow
    assert "scripts/macos/prepare_python_runtime.sh" in workflow
    assert "build_release_bundle.py" in workflow
    assert "uaa-macos-arm64.release.json" in workflow
    assert "gh release upload" in workflow
    assert "scripts/macos/verify_installer_e2e.py" in workflow
    assert "git tag -f" not in workflow
    assert "git push --force" not in workflow
    assert "actions/setup-python" not in workflow
    assert "runs-on: [self-hosted, macOS, ARM64, uaa-ci]" in workflow
    builder = (ROOT / "scripts" / "macos" / "build_release_bundle.py").read_text(
        encoding="utf-8"
    )
    assert "--no-build-isolation" in builder
    assert "setuptools==79.0.1" in builder
    assert "--require-hashes" in builder


def test_installer_e2e_validators_fail_closed_on_status_and_receipt_drift(
    tmp_path: Path,
) -> None:
    valid_status = {
        "schema_version": "uaa.macos.status.v1",
        "installed": True,
        "tag_ref": "git-tag:v0.104.0",
        "version": "0.104.0",
        "runtime_status": "stopped",
        "raw_paths_included": False,
        "credentials_included": False,
    }
    validate_status_payload(
        valid_status,
        expected_tag="v0.104.0",
        expected_version="0.104.0",
        expected_runtime_status="stopped",
    )
    with pytest.raises(InstallerE2EError, match="status payload"):
        validate_status_payload(
            {**valid_status, "runtime_status": "unknown"},
            expected_tag="v0.104.0",
            expected_version="0.104.0",
            expected_runtime_status="stopped",
        )

    receipts = tmp_path / "receipts"
    receipts.mkdir()
    receipt = {
        "schema_version": "uaa.macos.install-receipt.v1",
        "status": "installed",
        "raw_paths_included": False,
        "credentials_included": False,
    }
    target = receipts / "one.json"
    target.write_text(json.dumps(receipt), encoding="utf-8")
    validate_receipts(receipts, forbidden_text=str(tmp_path))

    target.write_text(
        json.dumps({**receipt, "unsafe": str(tmp_path)}),
        encoding="utf-8",
    )
    with pytest.raises(InstallerE2EError, match="redaction"):
        validate_receipts(receipts, forbidden_text=str(tmp_path))


def test_macos_distribution_adapters_remain_exact_scoped() -> None:
    assert macos_distribution_policy_failures(ROOT) == []
    assert MACOS_DISTRIBUTION_EXACT_ADAPTER_FILES == {
        "src/ultimate_ai_agent/distribution/macos/github_releases.py",
        "src/ultimate_ai_agent/distribution/macos/installer.py",
        "src/ultimate_ai_agent/distribution/macos/runtime.py",
    }


def test_macos_distribution_policy_rejects_shell_broadening() -> None:
    rel_path = "src/ultimate_ai_agent/distribution/macos/runtime.py"
    source = (ROOT / rel_path).read_text(encoding="utf-8")

    failures = macos_distribution_adapter_policy_failures(
        rel_path,
        source + "\nsubprocess.run(user_command, shell=True)\n",
    )

    assert failures
    assert any(
        "shell execution" in failure or "forbidden broad" in failure
        for failure in failures
    )


def test_macos_distribution_policy_ignores_unrelated_fixture_roots_but_fails_partial_lane(
    tmp_path: Path,
) -> None:
    assert macos_distribution_policy_failures(tmp_path) == []

    lane_root = (
        tmp_path / "src" / "ultimate_ai_agent" / "distribution" / "macos"
    )
    lane_root.mkdir(parents=True)

    failures = macos_distribution_policy_failures(tmp_path)

    assert failures
    assert any("unavailable" in failure for failure in failures)

    partial = tmp_path / next(iter(MACOS_DISTRIBUTION_EXACT_ADAPTER_FILES))
    partial.write_text("# partial distribution lane\n", encoding="utf-8")
    partial_failures = macos_distribution_policy_failures(tmp_path)

    assert partial_failures
    assert any("unavailable" in failure for failure in partial_failures)


def _layout(root: Path) -> InstallLayout:
    return InstallLayout(
        root=root / "Library" / "Ultimate AI Agent",
        applications_dir=root / "Applications",
        bin_dir=root / "bin",
    )


def _descriptor(
    *,
    tag: str,
    channel: str,
    source_timestamp: str,
    commit: str = "a" * 40,
    artifact_sha256: str = "b" * 64,
    artifact_size: int = 123,
) -> ReleaseDescriptor:
    return ReleaseDescriptor(
        schema_version=RELEASE_DESCRIPTOR_SCHEMA,
        product_line=PRODUCT_LINE,
        tag=tag,
        version="0.104.0",
        channel=channel,  # type: ignore[arg-type]
        source_commit=commit,
        source_timestamp=source_timestamp,
        platform="macos",
        architecture="arm64",
        artifact_name="uaa-macos-arm64.tar.gz",
        artifact_sha256=artifact_sha256,
        artifact_size=artifact_size,
        minimum_macos=MINIMUM_MACOS,
        signing_kind="ad-hoc",
        notarized=False,
    )


def _candidate(
    *,
    tag: str,
    channel: str,
    source_timestamp: str,
    published_at: str,
    release_id: int,
) -> ReleaseCandidate:
    descriptor = _descriptor(
        tag=tag,
        channel=channel,
        source_timestamp=source_timestamp,
    )
    return ReleaseCandidate(
        descriptor=descriptor,
        release_id=release_id,
        published_at=published_at,
        artifact_api_url=(
            f"https://api.github.com/repos/doncazper/ultimate-ai-agent/"
            f"releases/assets/{release_id * 10 + 1}"
        ),
        descriptor_api_url=(
            f"https://api.github.com/repos/doncazper/ultimate-ai-agent/"
            f"releases/assets/{release_id * 10 + 2}"
        ),
        github_asset_digest=f"sha256:{descriptor.artifact_sha256}",
    )


def _tiny_release(
    root: Path,
    *,
    tag: str,
    channel: str,
    commit: str,
    source_timestamp: str,
) -> tuple[Path, ReleaseDescriptor]:
    payload = root / "payload"
    app = payload / APP_BUNDLE_NAME
    executable = app / "Contents" / "MacOS" / APP_BUNDLE_NAME.removesuffix(".app")
    resources = app / "Contents" / "Resources"
    resources.mkdir(parents=True)
    executable.parent.mkdir(parents=True)
    shutil_source = Path("/usr/bin/true")
    executable.write_bytes(shutil_source.read_bytes())
    executable.chmod(0o755)
    with (app / "Contents" / "Info.plist").open("wb") as handle:
        plistlib.dump(
            {
                "CFBundleIdentifier": APP_BUNDLE_IDENTIFIER,
                "CFBundleShortVersionString": "0.104.0",
                "CFBundleExecutable": APP_BUNDLE_NAME.removesuffix(".app"),
                "CFBundlePackageType": "APPL",
            },
            handle,
        )
    (resources / APP_MANAGED_MARKER).write_text(
        json.dumps(
            {
                "schema_version": "uaa.macos.install-ownership.v1",
                "product_line": PRODUCT_LINE,
            }
        )
    )
    files = []
    for path in sorted(item for item in payload.rglob("*") if item.is_file()):
        files.append(
            {
                "path": path.relative_to(payload).as_posix(),
                "sha256": sha256_file(path),
                "size": path.stat().st_size,
                "mode": 0o755 if stat.S_IMODE(path.stat().st_mode) & 0o111 else 0o644,
            }
        )
    manifest = {
        "schema_version": BUNDLE_MANIFEST_SCHEMA,
        "product_line": PRODUCT_LINE,
        "tag": tag,
        "version": "0.104.0",
        "channel": channel,
        "source_commit": commit,
        "source_timestamp": source_timestamp,
        "platform": "macos",
        "architecture": "arm64",
        "app_bundle": APP_BUNDLE_NAME,
        "signing_kind": "ad-hoc",
        "notarized": False,
        "files": files,
    }
    (payload / "bundle-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    archive = root / "uaa-macos-arm64.tar.gz"
    archive.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "w:gz") as tar:
        for path in sorted(payload.rglob("*")):
            tar.add(
                path,
                arcname=path.relative_to(payload).as_posix(),
                recursive=False,
            )
    descriptor = _descriptor(
        tag=tag,
        channel=channel,
        source_timestamp=source_timestamp,
        commit=commit,
        artifact_sha256=sha256_file(archive),
        artifact_size=archive.stat().st_size,
    )
    return archive, descriptor


class _FakeResponse(io.BytesIO):
    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class _FakeOpener:
    def __init__(self, responses: dict[str, bytes]) -> None:
        self.responses = responses

    def open(self, request: object, timeout: float) -> _FakeResponse:
        _ = timeout
        url = getattr(request, "full_url")
        return _FakeResponse(self.responses[url])
