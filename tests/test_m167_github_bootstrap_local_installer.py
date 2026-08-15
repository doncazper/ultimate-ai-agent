from typing import Any
import hashlib
import importlib.util
import io
import json
import re
import stat
import sys
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parent.parent
BOOTSTRAP_DOC = ROOT / "docs" / "production" / "M167_GITHUB_BOOTSTRAP_LOCAL_INSTALLER.md"
TRUST_ROOT_DOC = ROOT / "docs" / "production" / "UAA_BOOTSTRAP_TRUST_ROOT.md"
MINISIGN_KEY = ROOT / "docs" / "production" / "UAA_BOOTSTRAP_MINISIGN.pub"
BOOTSTRAP_DOC_REF = "docs/production/M167_GITHUB_BOOTSTRAP_LOCAL_INSTALLER.md"
TRUST_ROOT_DOC_REF = "docs/production/UAA_BOOTSTRAP_TRUST_ROOT.md"
MINISIGN_KEY_REF = "docs/production/UAA_BOOTSTRAP_MINISIGN.pub"
PINNED_OPENWEBUI_IMAGE = (
    "ghcr.io/open-webui/open-webui@"
    "sha256:7f1b0a1a50cfbac23da3b16f96bc968fd757b26dc9e54e93813d61768ea9184e"
)


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _shell_blocks(markdown: str) -> list[str]:
    blocks: list[str] = []
    for match in re.finditer(r"```([^\n`]*)\n(.*?)```", markdown, flags=re.DOTALL):
        language = match.group(1).strip().lower()
        if language in {"", "bash", "sh", "shell", "text"}:
            blocks.append(match.group(2))
    return blocks


def _implementation_surface_files() -> list[Path]:
    roots = [
        ROOT / "scripts",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "src" / "ultimate_ai_agent" / "api",
        ROOT / ".github" / "workflows",
    ]
    suffixes = {".py", ".ts", ".tsx", ".js", ".jsx", ".sh", ".yml", ".yaml", ""}
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            candidates = [root]
        elif root.exists():
            candidates = [path for path in root.rglob("*") if path.is_file()]
        else:
            candidates = []
        for path in candidates:
            if path.name in {"run_all_legacy.py", "provision_self_hosted_macos_runners.sh"}:
                continue
            if any(part in {"node_modules", "__pycache__"} for part in path.parts):
                continue
            if path.name.startswith("verify_"):
                continue
            if path.suffix in suffixes:
                files.append(path)
    return sorted(files)


def _load_setup() -> Any:
    setup_path = ROOT / "scripts" / "dev" / "uaa_setup.py"
    spec = importlib.util.spec_from_file_location("uaa_setup_bootstrap_guard_test", setup_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_launcher() -> Any:
    launcher_path = ROOT / "scripts" / "dev" / "uaa_launcher.py"
    spec = importlib.util.spec_from_file_location("uaa_launcher_bootstrap_guard_test", launcher_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _bootstrap_args(tmp_path: Path, **overrides: Any) -> Any:
    home = tmp_path / "home"
    values = {
        "setup_action": "bootstrap",
        "release_tag": "v0.102.0-m167",
        "asset": "uaa-bootstrap-darwin-arm64.tar.gz",
        "sha256": "0" * 64,
        "signature": "uaa-bootstrap-darwin-arm64.tar.gz.provenance.json",
        "target": "openwebui",
        "bin_dir": str(home / ".local" / "bin"),
        "install_dir": str(home / ".local" / "share" / "uaa"),
        "receipt": str(home / ".local" / "state" / "uaa" / "bootstrap-receipt.json"),
        "yes": False,
        "approval_token": None,
        "write_approval_token": None,
        "provenance_mode": "local-dev-json",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _tar_bytes() -> bytes:
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as archive:
        content = b"#!/bin/sh\nexit 0\n"
        info = tarfile.TarInfo("uaa-bootstrap")
        info.size = len(content)
        info.mode = 0o755
        archive.addfile(info, io.BytesIO(content))
    return stream.getvalue()


def _provenance(*, digest: str, release_tag: str = "v0.102.0-m167", asset: str = "uaa-bootstrap-darwin-arm64.tar.gz") -> bytes:
    return (
        json.dumps(
            {
                "schema": "uaa.bootstrap.provenance.v1",
                "repo": "https://github.com/doncazper/ultimate-ai-agent",
                "release_tag": release_tag,
                "asset": asset,
                "sha256": digest,
                "target": "openwebui",
                "installer": "uaa-bootstrap",
                "trust_root": TRUST_ROOT_DOC_REF,
                "authority": "openwebui-local-dev-bootstrap-only",
            },
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _minisign_signature() -> bytes:
    return (
        b"untrusted comment: UAA M167 bootstrap minisign detached signature\n"
        b"RURVQUFNMTY3AejkqxQBxQH4fTMmnF7a4vD5wZ8iGTx0dj3p2pWAGmBeUAA=\n"
    )


def _patch_supported_home(setup: Any, monkeypatch: pytest.MonkeyPatch, home: Path) -> None:
    monkeypatch.setattr(setup, "_bootstrap_platform_status", lambda: (True, "macOS arm64 supported"))
    monkeypatch.setattr(setup, "_bootstrap_user_home", lambda: home)


def _approve_interactively(setup: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(f"{setup.SETUP_BOOTSTRAP_CONFIRMATION}\n"))


def test_github_bootstrap_milestone_defines_required_boundary() -> None:
    text = BOOTSTRAP_DOC.read_text(encoding="utf-8")
    lower = text.lower()
    normalized = " ".join(lower.replace("`", "").split())

    required_markers = [
        "Status: scoped implementation slice",
        "https://github.com/doncazper/ultimate-ai-agent",
        "main is denied",
        "latest is denied",
        "detached minisign signature",
        MINISIGN_KEY_REF,
        "minisign -Vm",
        "minisign signature verification passes",
        "cryptographic verification",
        TRUST_ROOT_DOC_REF,
        "uaa setup bootstrap --release-tag",
        "--approval-token",
        "unattended bootstrap approval is disabled",
        "interactive_operator_confirmation_required",
        "--provenance-mode local-dev-json",
        "./uaa-bootstrap install --target openwebui --bin-dir",
        "uaa setup install --target openwebui",
        PINNED_OPENWEBUI_IMAGE,
        "canonicalized user-scope path validation",
        "docker desktop installer",
        "live PyPI/npm/Homebrew dependency resolution",
        "raw.githubusercontent.com script execution",
        "UAA tool/function authority",
        "install uaa openwebui bootstrap",
        "chmod `0600` receipt",
        "macOS arm64",
        "No Foundation Gate or OpenAPI update is required",
    ]
    for marker in required_markers:
        assert " ".join(marker.lower().replace("`", "").split()) in normalized

    denied_markers = [
        "curl | bash",
        "pipe-to-shell execution",
        "execution from mutable `main`",
        "execution from `latest`",
        "arbitrary GitHub repo or script URL execution",
        "secret or environment dumping",
        "broad system install claims",
        "OpenWebUI plugin/admin mutation",
        "model/provider authority",
        "memory writes",
        "context injection",
        "autonomous background authority",
    ]
    for marker in denied_markers:
        assert " ".join(marker.lower().replace("`", "").split()) in normalized


def test_trust_root_doc_exists_and_defines_fail_closed_verification() -> None:
    text = TRUST_ROOT_DOC.read_text(encoding="utf-8")
    normalized = " ".join(text.lower().replace("`", "").split())
    for marker in [
        "uaa.bootstrap.provenance.v1",
        "uaa.bootstrap.minisign_statement.v1",
        "local-dev-json",
        "minisign",
        MINISIGN_KEY_REF,
        "minisign -Vm",
        "https://github.com/doncazper/ultimate-ai-agent",
        "explicit immutable release tag",
        "sha-256",
        "openwebui-local-dev-bootstrap-only",
        "any mismatch must abort before installer code runs",
        "raw.githubusercontent.com",
        "curl | bash",
        "chmod 0600",
        "receipt-bound or marker-owned",
    ]:
        assert " ".join(marker.lower().replace("`", "").split()) in normalized


def test_minisign_public_key_exists_and_is_pinned_by_setup_and_docs() -> None:
    setup = _load_setup()
    key_text = MINISIGN_KEY.read_text(encoding="utf-8")
    trust_text = TRUST_ROOT_DOC.read_text(encoding="utf-8")
    bootstrap_text = BOOTSTRAP_DOC.read_text(encoding="utf-8")

    assert setup.BOOTSTRAP_MINISIGN_PUBLIC_KEY_REF == MINISIGN_KEY_REF
    assert setup.BOOTSTRAP_MINISIGN_PUBLIC_KEY_SHA256 == hashlib.sha256(key_text.encode("utf-8")).hexdigest()
    assert key_text.startswith("untrusted comment: UAA M167 bootstrap minisign public key")
    assert setup.BOOTSTRAP_MINISIGN_PUBLIC_KEY_SHA256 in trust_text
    assert MINISIGN_KEY_REF in trust_text
    assert MINISIGN_KEY_REF in bootstrap_text


def test_github_bootstrap_shell_examples_do_not_execute_unverified_remote_code() -> None:
    text = "\n".join(
        [
            BOOTSTRAP_DOC.read_text(encoding="utf-8"),
            TRUST_ROOT_DOC.read_text(encoding="utf-8"),
        ]
    )
    shell_text = "\n".join(_shell_blocks(text)).lower()

    forbidden_shell_fragments = [
        "| bash",
        "| sh",
        "bash <(",
        "sh <(",
        "raw.githubusercontent.com",
        "refs/heads/main",
        "/main/",
        "sudo",
        "launchctl",
    ]
    for fragment in forbidden_shell_fragments:
        assert fragment not in shell_text


def test_github_bootstrap_doc_is_linked_from_active_catalogs() -> None:
    for path in [
        "docs/production/M167_OPENWEBUI_LOCAL_INSTALLER.md",
        "docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING.md",
        "docs/production/LOCAL_RUNTIME_PACKAGING.md",
        "docs/DOCUMENTATION_INDEX.md",
        "docs/README.md",
        "docs/canonical/CANONICAL_DOC_MAP.md",
    ]:
        assert BOOTSTRAP_DOC_REF in _text(path)
    assert TRUST_ROOT_DOC_REF in BOOTSTRAP_DOC.read_text(encoding="utf-8")


def test_bootstrap_implementation_surface_denies_unsafe_remote_execution_patterns() -> None:
    forbidden_fragments = [
        "raw.githubusercontent.com",
        "| bash",
        "| sh",
        "bash <(",
        "sh <(",
        "urlretrieve",
        "shell=True",
        "sudo ",
        "launchctl",
    ]
    for path in _implementation_surface_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for fragment in forbidden_fragments:
            assert fragment not in text, f"{fragment!r} found in {path.relative_to(ROOT)}"

    setup_text = _text("scripts/dev/uaa_setup.py")
    assert '"pull", OPENWEBUI_IMAGE' in setup_text
    assert "uaa setup install --target openwebui" in setup_text


def test_openwebui_image_is_digest_pinned_across_runtime_surfaces() -> None:
    launcher = _load_launcher()
    setup = _load_setup()
    runtime_files = [
        ROOT / "scripts" / "dev" / "uaa_setup.py",
        ROOT / "scripts" / "dev" / "uaa_launcher.py",
    ]

    assert setup.OPENWEBUI_IMAGE == PINNED_OPENWEBUI_IMAGE
    assert launcher.OPENWEBUI_IMAGE == PINNED_OPENWEBUI_IMAGE
    assert "@sha256:" in setup.OPENWEBUI_IMAGE
    assert ":main" not in setup.OPENWEBUI_IMAGE
    for path in runtime_files:
        assert "ghcr.io/open-webui/open-webui:main" not in path.read_text(encoding="utf-8")


def test_bootstrap_parser_requires_explicit_release_asset_checksum_and_signature() -> None:
    launcher = _load_launcher()

    with pytest.raises(SystemExit):
        launcher.parse_args(["setup", "bootstrap"])
    with pytest.raises(SystemExit):
        launcher.parse_args(
            [
                "setup",
                "bootstrap",
                "--release-tag",
                "v0.102.0-m167",
                "--asset",
                "uaa-bootstrap-darwin-arm64.tar.gz",
                "--sha256",
                "0" * 64,
                "--target",
                "openwebui",
            ]
        )

    parsed = launcher.parse_args(
        [
            "setup",
            "bootstrap",
            "--release-tag",
            "v0.102.0-m167",
            "--asset",
            "uaa-bootstrap-darwin-arm64.tar.gz",
            "--sha256",
            "0" * 64,
            "--signature",
            "uaa-bootstrap-darwin-arm64.tar.gz.provenance.json",
            "--provenance-mode",
            "local-dev-json",
            "--target",
            "openwebui",
        ]
    )
    assert parsed.command == "setup"
    assert parsed.setup_action == "bootstrap"
    assert parsed.target == "openwebui"
    assert parsed.provenance_mode == "local-dev-json"


def test_bootstrap_parser_denies_mutable_refs_latest_and_arbitrary_urls() -> None:
    launcher = _load_launcher()
    base = [
        "setup",
        "bootstrap",
        "--asset",
        "uaa-bootstrap-darwin-arm64.tar.gz",
        "--sha256",
        "0" * 64,
        "--signature",
        "uaa-bootstrap-darwin-arm64.tar.gz.provenance.json",
        "--target",
        "openwebui",
    ]

    for release_tag in ["main", "master", "latest", "refs/heads/main", "feature/test"]:
        with pytest.raises(SystemExit):
            launcher.parse_args([*base, "--release-tag", release_tag])

    with pytest.raises(SystemExit):
        launcher.parse_args(
            [
                "setup",
                "bootstrap",
                "--release-tag",
                "v0.102.0-m167",
                "--asset",
                "https://github.com/other/repo/releases/download/v1/x.tar.gz",
                "--sha256",
                "0" * 64,
                "--signature",
                "uaa-bootstrap-darwin-arm64.tar.gz.provenance.json",
                "--target",
                "openwebui",
            ]
        )


def test_bootstrap_path_validation_rejects_system_world_writable_symlink_and_conflicts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    setup = _load_setup()
    home = tmp_path / "home"
    home.mkdir()
    _patch_supported_home(setup, monkeypatch, home)

    with pytest.raises(ValueError, match="user-scope"):
        setup._validate_bootstrap_dir_path(ROOT, "/usr/local/bin", option_name="--bin-dir")

    world = home / "world"
    world.mkdir()
    world.chmod(0o777)
    with pytest.raises(ValueError, match="world-writable"):
        setup._validate_bootstrap_dir_path(ROOT, world / "bin", option_name="--bin-dir")

    outside = tmp_path / "outside"
    outside.mkdir()
    link = home / "link"
    link.symlink_to(outside)
    with pytest.raises(ValueError, match="user-scope"):
        setup._validate_bootstrap_dir_path(ROOT, link / "bin", option_name="--bin-dir")

    safe_bin = home / ".local" / "bin"
    safe_bin.mkdir(parents=True)
    (safe_bin / "uaa").write_text("existing", encoding="utf-8")
    with pytest.raises(ValueError, match="existing uaa"):
        setup._validate_bootstrap_launcher_slot(safe_bin)

    receipt = home / ".local" / "state" / "uaa" / "receipt.json"
    receipt.parent.mkdir(parents=True)
    receipt.write_text("existing", encoding="utf-8")
    with pytest.raises(ValueError, match="already exists"):
        setup._validate_bootstrap_receipt_path(ROOT, receipt)


def test_bootstrap_unsupported_platform_fails_before_download(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    setup = _load_setup()
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(setup, "_bootstrap_user_home", lambda: home)
    monkeypatch.setattr(setup, "_bootstrap_platform_status", lambda: (False, "unsupported platform"))
    _approve_interactively(setup, monkeypatch)
    monkeypatch.setattr(setup, "_download_bootstrap_file", lambda *args, **kwargs: pytest.fail("download should not run"))
    monkeypatch.setattr(setup, "_run_bootstrap_installer_command", lambda command: pytest.fail("installer should not run"))

    exit_code = setup.command_setup(tmp_path, _bootstrap_args(tmp_path))
    captured = capsys.readouterr()
    payload = json.loads((home / ".local/state/uaa/bootstrap-receipt.json").read_text(encoding="utf-8"))

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["result"] == "unsupported-platform"
    assert "unsupported platform" in captured.out


def test_bootstrap_refusal_runs_nothing_and_writes_redacted_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    setup = _load_setup()
    home = tmp_path / "home"
    home.mkdir()
    _patch_supported_home(setup, monkeypatch, home)
    monkeypatch.setattr(sys, "stdin", io.StringIO("no\n"))
    monkeypatch.setattr(setup, "_download_bootstrap_file", lambda *args, **kwargs: pytest.fail("download should not run"))
    monkeypatch.setattr(setup, "_run_bootstrap_installer_command", lambda command: pytest.fail("installer should not run"))

    exit_code = setup.command_setup(tmp_path, _bootstrap_args(tmp_path, yes=False))
    captured = capsys.readouterr()
    receipt_path = home / ".local" / "state" / "uaa" / "bootstrap-receipt.json"
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert stat.S_IMODE(receipt_path.stat().st_mode) == 0o600
    assert payload["schema"] == "uaa.setup_bootstrap_receipt.v1"
    assert payload["status"] == "refused"
    assert payload["release_tag"] == "v0.102.0-m167"
    assert "No download or install command was run" in captured.out
    assert "secret-value" not in captured.out
    assert "secret-value" not in receipt_path.read_text(encoding="utf-8")


def test_bootstrap_checksum_mismatch_fails_closed_before_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    setup = _load_setup()
    home = tmp_path / "home"
    home.mkdir()
    _patch_supported_home(setup, monkeypatch, home)
    _approve_interactively(setup, monkeypatch)
    calls = []

    def fake_download(url: str, destination: Any) -> None:
        calls.append(url)
        destination.write_bytes(b"wrong artifact")

    monkeypatch.setattr(setup, "_download_bootstrap_file", fake_download)
    monkeypatch.setattr(setup, "_run_bootstrap_installer_command", lambda command: pytest.fail("installer should not run"))

    exit_code = setup.command_setup(tmp_path, _bootstrap_args(tmp_path, sha256=hashlib.sha256(b"expected").hexdigest()))
    captured = capsys.readouterr()
    payload = json.loads((home / ".local/state/uaa/bootstrap-receipt.json").read_text(encoding="utf-8"))

    assert exit_code == 1
    assert calls == [
        "https://github.com/doncazper/ultimate-ai-agent/releases/download/v0.102.0-m167/uaa-bootstrap-darwin-arm64.tar.gz"
    ]
    assert payload["status"] == "failed"
    assert payload["checksum_status"] == "mismatch"
    assert "checksum verification failed" in captured.out.lower()


def test_bootstrap_provenance_mismatch_fails_closed_before_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    setup = _load_setup()
    home = tmp_path / "home"
    home.mkdir()
    _patch_supported_home(setup, monkeypatch, home)
    _approve_interactively(setup, monkeypatch)
    artifact = _tar_bytes()
    digest = hashlib.sha256(artifact).hexdigest()

    def fake_download(url: str, destination: Any) -> None:
        if url.endswith(".provenance.json"):
            destination.write_bytes(_provenance(digest=digest, release_tag="v0.0.0-wrong"))
        else:
            destination.write_bytes(artifact)

    monkeypatch.setattr(setup, "_download_bootstrap_file", fake_download)
    monkeypatch.setattr(setup, "_run_bootstrap_installer_command", lambda command: pytest.fail("installer should not run"))

    exit_code = setup.command_setup(tmp_path, _bootstrap_args(tmp_path, sha256=digest))
    captured = capsys.readouterr()
    payload = json.loads((home / ".local/state/uaa/bootstrap-receipt.json").read_text(encoding="utf-8"))

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["provenance_status"] == "mismatch"
    assert "provenance verification failed" in captured.out.lower()


def test_bootstrap_yes_fails_without_interactive_confirmation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    setup = _load_setup()
    home = tmp_path / "home"
    home.mkdir()
    _patch_supported_home(setup, monkeypatch, home)
    monkeypatch.setattr(setup, "_download_bootstrap_file", lambda *args, **kwargs: pytest.fail("download should not run"))
    monkeypatch.setattr(setup, "_run_bootstrap_installer_command", lambda command: pytest.fail("installer should not run"))

    exit_code = setup.command_setup(tmp_path, _bootstrap_args(tmp_path, yes=True, approval_token=None))
    captured = capsys.readouterr()
    payload = json.loads((home / ".local/state/uaa/bootstrap-receipt.json").read_text(encoding="utf-8"))

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["result"] == "unattended-approval-disabled"
    assert payload["approval_mode"] == "unattended-disabled"
    assert "unattended setup approval is disabled" in captured.out.lower()


def test_bootstrap_forged_legacy_token_cannot_create_operator_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    setup = _load_setup()
    home = tmp_path / "home"
    home.mkdir()
    _patch_supported_home(setup, monkeypatch, home)
    token_path = home / "forged-bootstrap-approval.json"
    plan = setup._bootstrap_plan(tmp_path, _bootstrap_args(tmp_path))
    forged_payload = {
        "schema": "uaa.setup_bootstrap_approval_token.v1",
        "milestone_ref": plan["milestone_ref"],
        "target": plan["target"],
        "release_tag": plan["release_tag"],
        "asset": plan["asset"],
        "provenance_mode": plan["provenance_mode"],
        "preview_hash": plan["preview_hash"],
        "expires_at_epoch": 4_102_444_800,
        "created_at": "20260815T010203Z",
        "used_at": None,
        "redaction": "structurally valid forged legacy metadata",
    }
    token_path.write_text(json.dumps(forged_payload, sort_keys=True) + "\n", encoding="utf-8")
    token_path.chmod(0o600)
    monkeypatch.setattr(
        setup,
        "_download_bootstrap_file",
        lambda *args, **kwargs: pytest.fail("download must not run for a legacy token"),
    )

    exit_code = setup.command_setup(
        tmp_path,
        _bootstrap_args(tmp_path, yes=True, approval_token=str(token_path)),
    )
    captured = capsys.readouterr()
    denial_receipt = next(
        (tmp_path / setup.SETUP_APPROVAL_RECEIPT_DIR).glob(
            "github-bootstrap-*.json"
        )
    )
    denial_payload = json.loads(denial_receipt.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert "unattended setup approval is disabled" in captured.out.lower()
    assert json.loads(token_path.read_text(encoding="utf-8")) == forged_payload
    assert denial_payload["status"] == "denied"
    assert denial_payload["actor"] == "untrusted-caller-input"
    assert denial_payload["reason_codes"] == [
        "INTERACTIVE_OPERATOR_CONFIRMATION_REQUIRED"
    ]
    assert denial_payload["replay"]["unattended_token_authority"] == "disabled"
    decision = setup._policy_engine_approval_decision(
        tmp_path,
        plan,
        action_ref="github-bootstrap",
        approval_mode="preview-token",
    )
    assert decision["allowed"] is False
    assert decision["reason_codes"] == ["INTERACTIVE_OPERATOR_CONFIRMATION_REQUIRED"]


def test_bootstrap_interactive_exact_confirmation_allows_verified_install(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    setup = _load_setup()
    home = tmp_path / "home"
    home.mkdir()
    _patch_supported_home(setup, monkeypatch, home)
    _approve_interactively(setup, monkeypatch)
    artifact = _tar_bytes()
    digest = hashlib.sha256(artifact).hexdigest()
    commands = []
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_KEY", "secret-value")
    receipt_path = home / ".local" / "state" / "uaa" / "bootstrap-receipt.json"
    receipt_path.parent.mkdir(parents=True)

    def fake_download(url: str, destination: Any) -> None:
        if url.endswith(".provenance.json"):
            destination.write_bytes(_provenance(digest=digest))
        else:
            destination.write_bytes(artifact)

    def fake_run(command: str) -> dict[str, Any]:
        commands.append(command)
        return {"returncode": 0, "summary": "completed"}

    monkeypatch.setattr(setup, "_download_bootstrap_file", fake_download)
    monkeypatch.setattr(setup, "_run_bootstrap_installer_command", fake_run)

    exit_code = setup.command_setup(
        tmp_path,
        _bootstrap_args(tmp_path, sha256=digest, receipt=str(receipt_path)),
    )
    captured = capsys.readouterr()
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert len(commands) == 1
    assert payload["status"] == "installed"
    assert payload["approval_mode"] == "typed"
    assert "Running approved verified local installer command:" in captured.out
    assert "secret-value" not in captured.out
    assert "secret-value" not in receipt_path.read_text(encoding="utf-8")


def test_bootstrap_deprecated_token_writer_never_creates_requested_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    setup = _load_setup()
    home = tmp_path / "home"
    home.mkdir()
    _patch_supported_home(setup, monkeypatch, home)
    token_path = home / ".local" / "state" / "uaa" / "bootstrap-approval.json"
    monkeypatch.setattr(setup, "_download_bootstrap_file", lambda *args, **kwargs: pytest.fail("download should not run"))
    monkeypatch.setattr(setup, "_run_bootstrap_installer_command", lambda command: pytest.fail("installer should not run"))

    exit_code = setup.command_setup(
        tmp_path,
        _bootstrap_args(
            tmp_path,
            write_approval_token=str(token_path),
        ),
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "unattended setup approval is disabled" in captured.out.lower()
    assert not token_path.exists()


@pytest.mark.parametrize(
    "legacy_payload",
    [
        {"expires_at_epoch": 0},
        {"preview_hash": "f" * 64},
        {"used_at": "20260620T010203Z"},
    ],
)
def test_bootstrap_stale_mismatched_and_replayed_legacy_tokens_are_equally_non_authorizing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    legacy_payload: dict[str, Any],
) -> None:
    setup = _load_setup()
    home = tmp_path / "home"
    home.mkdir()
    _patch_supported_home(setup, monkeypatch, home)
    token_path = home / ".local" / "state" / "uaa" / "bootstrap-approval.json"
    token_path.parent.mkdir(parents=True)
    receipt_path = home / ".local" / "state" / "uaa" / "bootstrap-denied-receipt.json"
    token_path.write_text(json.dumps(legacy_payload, sort_keys=True) + "\n", encoding="utf-8")
    token_path.chmod(0o600)
    monkeypatch.setattr(setup, "_download_bootstrap_file", lambda *args, **kwargs: pytest.fail("download should not run"))
    monkeypatch.setattr(setup, "_run_bootstrap_installer_command", lambda command: pytest.fail("installer should not run"))

    exit_code = setup.command_setup(
        tmp_path,
        _bootstrap_args(tmp_path, receipt=str(receipt_path), approval_token=str(token_path), yes=True),
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "unattended setup approval is disabled" in captured.out.lower()
    assert json.loads(token_path.read_text(encoding="utf-8")) == legacy_payload


def test_bootstrap_public_crypto_mode_rejects_json_only_provenance_before_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    setup = _load_setup()
    home = tmp_path / "home"
    home.mkdir()
    _patch_supported_home(setup, monkeypatch, home)
    _approve_interactively(setup, monkeypatch)
    artifact = _tar_bytes()
    digest = hashlib.sha256(artifact).hexdigest()

    def fake_download(url: str, destination: Any) -> None:
        if url.endswith(".provenance.json"):
            destination.write_bytes(_provenance(digest=digest))
        else:
            destination.write_bytes(artifact)

    monkeypatch.setattr(setup, "_download_bootstrap_file", fake_download)
    monkeypatch.setattr(setup, "_run_bootstrap_installer_command", lambda command: pytest.fail("installer should not run"))

    exit_code = setup.command_setup(
        tmp_path,
        _bootstrap_args(tmp_path, sha256=digest, provenance_mode="minisign"),
    )
    captured = capsys.readouterr()
    payload = json.loads((home / ".local/state/uaa/bootstrap-receipt.json").read_text(encoding="utf-8"))

    assert exit_code == 1
    assert payload["provenance_mode"] == "minisign"
    assert payload["provenance_status"] == "mismatch"
    assert "cryptographic" in captured.out.lower()


def test_bootstrap_minisign_statement_binds_tag_asset_digest_target_and_trust_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    setup = _load_setup()
    home = tmp_path / "home"
    home.mkdir()
    _patch_supported_home(setup, monkeypatch, home)

    plan = setup._bootstrap_plan(
        tmp_path,
        _bootstrap_args(
            tmp_path,
            sha256=hashlib.sha256(b"artifact").hexdigest(),
            signature="uaa-bootstrap-darwin-arm64.tar.gz.minisig",
            provenance_mode="minisign",
        ),
    )
    statement = json.loads(setup._bootstrap_minisign_statement(plan).decode("utf-8"))

    assert statement == {
        "schema": "uaa.bootstrap.minisign_statement.v1",
        "repo": "https://github.com/doncazper/ultimate-ai-agent",
        "release_tag": "v0.102.0-m167",
        "asset": "uaa-bootstrap-darwin-arm64.tar.gz",
        "sha256": hashlib.sha256(b"artifact").hexdigest(),
        "target": "openwebui",
        "installer": "uaa-bootstrap",
        "trust_root": TRUST_ROOT_DOC_REF,
        "trust_root_identity": setup.BOOTSTRAP_MINISIGN_TRUST_ROOT_IDENTITY,
        "public_key_ref": MINISIGN_KEY_REF,
        "public_key_sha256": setup.BOOTSTRAP_MINISIGN_PUBLIC_KEY_SHA256,
        "authority": "openwebui-local-dev-bootstrap-only",
        "provenance_mode": "minisign",
    }

    changed = dict(plan)
    changed["asset"] = "uaa-bootstrap-darwin-arm64-alt.tar.gz"
    assert setup._bootstrap_minisign_statement(changed) != setup._bootstrap_minisign_statement(plan)
    changed = dict(plan)
    changed["release_tag"] = "v0.102.1-m167"
    assert setup._bootstrap_minisign_statement(changed) != setup._bootstrap_minisign_statement(plan)
    changed = dict(plan)
    changed["target"] = "other"
    assert setup._bootstrap_minisign_statement(changed) != setup._bootstrap_minisign_statement(plan)


def test_bootstrap_public_minisign_mode_verifies_statement_before_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    setup = _load_setup()
    home = tmp_path / "home"
    home.mkdir()
    _patch_supported_home(setup, monkeypatch, home)
    _approve_interactively(setup, monkeypatch)
    artifact = _tar_bytes()
    digest = hashlib.sha256(artifact).hexdigest()
    statements = []
    commands = []

    def fake_download(url: str, destination: Any) -> None:
        if url.endswith(".minisig"):
            destination.write_bytes(_minisign_signature())
        else:
            destination.write_bytes(artifact)

    def fake_verify(statement_path: Any, signature_path: Any, public_key: Any) -> dict[str, Any]:
        statement = json.loads(statement_path.read_text(encoding="utf-8"))
        statements.append(statement)
        assert signature_path.name == "uaa-bootstrap-darwin-arm64.tar.gz.minisig"
        assert public_key == setup._bootstrap_minisign_public_key(ROOT)
        return {"verifier": "minisign", "raw_output_retained": False}

    def fake_run(command: str) -> dict[str, Any]:
        commands.append(command)
        return {"returncode": 0, "summary": "completed"}

    monkeypatch.setattr(setup, "_download_bootstrap_file", fake_download)
    monkeypatch.setattr(setup, "_run_minisign_verify", fake_verify)
    monkeypatch.setattr(setup, "_run_bootstrap_installer_command", fake_run)

    exit_code = setup.command_setup(
        tmp_path,
        _bootstrap_args(
            tmp_path,
            sha256=digest,
            signature="uaa-bootstrap-darwin-arm64.tar.gz.minisig",
            provenance_mode="minisign",
        ),
    )
    captured = capsys.readouterr()
    payload = json.loads((home / ".local/state/uaa/bootstrap-receipt.json").read_text(encoding="utf-8"))
    approval_receipt = next((tmp_path / setup.SETUP_APPROVAL_RECEIPT_DIR).glob("github-bootstrap-*.json"))
    approval_payload = json.loads(approval_receipt.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert len(statements) == 1
    assert statements[0]["release_tag"] == "v0.102.0-m167"
    assert statements[0]["asset"] == "uaa-bootstrap-darwin-arm64.tar.gz"
    assert statements[0]["sha256"] == digest
    assert statements[0]["target"] == "openwebui"
    assert statements[0]["public_key_ref"] == MINISIGN_KEY_REF
    assert len(commands) == 1
    assert payload["provenance_mode"] == "minisign"
    assert payload["provenance_status"] == "verified"
    assert payload["approval_authority"] == "PolicyEngine+LocalApprovalAuthority"
    assert approval_payload["scope"]["release_tag"] == "v0.102.0-m167"
    assert approval_payload["scope"]["asset"] == "uaa-bootstrap-darwin-arm64.tar.gz"
    assert approval_payload["scope"]["provenance_mode"] == "minisign"
    assert stat.S_IMODE(approval_receipt.stat().st_mode) == 0o600
    assert "raw verifier" not in captured.out.lower()


def test_bootstrap_public_minisign_missing_verifier_fails_before_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    setup = _load_setup()
    home = tmp_path / "home"
    home.mkdir()
    _patch_supported_home(setup, monkeypatch, home)
    _approve_interactively(setup, monkeypatch)
    artifact = _tar_bytes()
    digest = hashlib.sha256(artifact).hexdigest()

    def fake_download(url: str, destination: Any) -> None:
        if url.endswith(".minisig"):
            destination.write_bytes(_minisign_signature())
        else:
            destination.write_bytes(artifact)

    monkeypatch.setattr(setup, "_download_bootstrap_file", fake_download)
    monkeypatch.setattr(setup, "_resolve_command", lambda command: None if command == "minisign" else Path(f"/tmp/{command}"))
    monkeypatch.setattr(setup, "_run_bootstrap_installer_command", lambda command: pytest.fail("installer should not run"))

    exit_code = setup.command_setup(
        tmp_path,
        _bootstrap_args(
            tmp_path,
            sha256=digest,
            signature="uaa-bootstrap-darwin-arm64.tar.gz.minisig",
            provenance_mode="minisign",
        ),
    )
    captured = capsys.readouterr()
    payload = json.loads((home / ".local/state/uaa/bootstrap-receipt.json").read_text(encoding="utf-8"))

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["provenance_status"] == "mismatch"
    assert "minisign verifier is unavailable" in captured.out.lower()


def test_bootstrap_approval_runs_only_verified_local_installer_and_writes_redacted_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    setup = _load_setup()
    home = tmp_path / "home"
    home.mkdir()
    _patch_supported_home(setup, monkeypatch, home)
    _approve_interactively(setup, monkeypatch)
    artifact = _tar_bytes()
    digest = hashlib.sha256(artifact).hexdigest()
    commands = []
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_KEY", "secret-value")

    def fake_download(url: str, destination: Any) -> None:
        if url.endswith(".provenance.json"):
            destination.write_bytes(_provenance(digest=digest))
        else:
            destination.write_bytes(artifact)

    def fake_run(command: str) -> dict[str, Any]:
        commands.append(command)
        return {"returncode": 0, "summary": "completed"}

    monkeypatch.setattr(setup, "_download_bootstrap_file", fake_download)
    monkeypatch.setattr(setup, "_run_bootstrap_installer_command", fake_run)

    receipt_path = home / ".local" / "state" / "uaa" / "bootstrap-receipt.json"
    exit_code = setup.command_setup(tmp_path, _bootstrap_args(tmp_path, sha256=digest, receipt=str(receipt_path)))
    captured = capsys.readouterr()
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    approval_receipt = next((tmp_path / setup.SETUP_APPROVAL_RECEIPT_DIR).glob("github-bootstrap-*.json"))
    approval_payload = json.loads(approval_receipt.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert len(commands) == 1
    command = commands[0]
    assert isinstance(command, list)
    assert Path(command[0]).name == "uaa-bootstrap"
    assert command[1:] == [
        "install",
        "--target",
        "openwebui",
        "--bin-dir",
        str(home / ".local" / "bin"),
        "--install-dir",
        str(home / ".local" / "share" / "uaa"),
        "--receipt",
        str(receipt_path),
        "--yes",
    ]
    assert stat.S_IMODE(receipt_path.stat().st_mode) == 0o600
    assert payload["status"] == "installed"
    assert payload["checksum_status"] == "verified"
    assert payload["provenance_status"] == "verified"
    assert payload["approval_mode"] == "typed"
    assert payload["approval_authority"] == "PolicyEngine+LocalApprovalAuthority"
    assert payload["approval_decision_ref"] == approval_payload["decision_ref"]
    assert payload["target"] == "openwebui"
    assert payload["bin_dir"] == "~/.local/bin"
    assert payload["install_dir"] == "~/.local/share/uaa"
    assert "receipt-bound or marker-owned" in "\n".join(payload["rollback_hints"])
    assert "Running approved verified local installer command:" in captured.out
    assert "secret-value" not in captured.out
    assert "secret-value" not in receipt_path.read_text(encoding="utf-8")
    assert "secret-value" not in approval_receipt.read_text(encoding="utf-8")


def test_plain_setup_stays_diagnostic_and_openwebui_image_installer_stays_separate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    setup = _load_setup()
    monkeypatch.setattr(setup, "build_setup_report", lambda root, **kwargs: _stable_report(setup))
    monkeypatch.setattr(setup, "command_setup_bootstrap", lambda root, args: pytest.fail("plain setup must not bootstrap"))

    exit_code = setup.command_setup(tmp_path, SimpleNamespace(**_plain_setup_args()))

    assert exit_code == 0
    plan = setup._openwebui_install_plan(tmp_path)
    assert plan["commands"] == [["docker", "pull", setup.OPENWEBUI_IMAGE]]
    assert plan["image_ref"] == PINNED_OPENWEBUI_IMAGE
    assert plan["action"] == "docker-image-pull"


def _stable_report(setup: Any) -> Any:
    return setup.SetupReport(
        mode="local-llama",
        profile="minimal",
        system_summary={"os": "test", "architecture": "test", "python": "3.11.0"},
        findings=[setup.SetupFinding("python environment", "pass", "ready", "No action needed.")],
        model_id="uaa-llama-cpp-local",
        selected_model_alias="uaa-llama-cpp-local",
        next_steps=["Run: uaa start"],
        repair_plan=[],
        plan_commands=["uaa start"],
        platform_hints=[],
    )


def _plain_setup_args() -> dict[str, Any]:
    return {
        "setup_action": None,
        "mode": "local-llama",
        "profile": "minimal",
        "provider": None,
        "model_id": "uaa-llama-cpp-local",
        "hf_repo": "ggml-org/gemma-3-1b-it-GGUF",
        "hf_file": "gemma-3-1b-it-Q4_K_M.gguf",
        "write_env": False,
        "overwrite_env": False,
        "check_env": None,
        "write_report": None,
        "explain": False,
        "plan": False,
        "json": True,
    }
