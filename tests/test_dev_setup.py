from typing import Any
import importlib.util
import io
import json
import stat
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
SETUP_PATH = ROOT / "scripts" / "dev" / "uaa_setup.py"
LAUNCHER_PATH = ROOT / "scripts" / "dev" / "uaa_launcher.py"


def load_setup() -> Any:
    spec = importlib.util.spec_from_file_location("uaa_setup_test", SETUP_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_launcher() -> Any:
    spec = importlib.util.spec_from_file_location("uaa_launcher_setup_test", LAUNCHER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_setup_writes_local_llama_env_template(tmp_path: Path) -> None:
    setup = load_setup()

    target = setup.write_local_llama_env(tmp_path, model_id="uaa-llama-cpp-local")

    content = target.read_text(encoding="utf-8")
    assert target.relative_to(tmp_path) == Path(".uaa/dev/local-llama.env")
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert "UAA_LLAMA_CPP_GATEWAY_ENABLED=1" in content
    assert "UAA_LLAMA_CPP_MODEL_ID=uaa-llama-cpp-local" in content
    assert 'HF_HOME="${HF_HOME:-$HOME/Models/huggingface}"' in content
    assert 'HF_HUB_CACHE="${HF_HUB_CACHE:-$HF_HOME/hub}"' in content
    assert 'OLLAMA_MODELS="${OLLAMA_MODELS:-$HOME/Models/ollama/models}"' in content
    assert (
        'UAA_LLAMA_CPP_MODEL_CACHE_ROOT="${UAA_LLAMA_CPP_MODEL_CACHE_ROOT:-$HOME/Models/llama.cpp/model-cache}"'
        in content
    )
    assert 'UAA_LLAMA_CPP_MODEL_PATH="$UAA_LLAMA_CPP_MODEL_CACHE_ROOT/path/to/model.gguf"' in content
    assert "sk-" not in content
    assert "ANTHROPIC" not in content
    assert "GEMINI" not in content


def test_frontier_setup_is_reported_as_not_scoped(monkeypatch: pytest.MonkeyPatch) -> None:
    setup = load_setup()
    safe_finding = setup.SetupFinding("safe prerequisite", "pass", "present", "No action needed.")
    monkeypatch.setattr(setup, "_probe_python", lambda root: safe_finding)
    monkeypatch.setattr(setup, "_probe_frontend_deps", lambda root: safe_finding)
    monkeypatch.setattr(setup, "_probe_uaa_shell_command", lambda root: safe_finding)
    monkeypatch.setattr(setup, "_probe_docker", lambda: safe_finding)
    monkeypatch.setattr(setup, "_probe_backend_port", lambda: safe_finding)
    monkeypatch.setattr(setup, "_probe_frontend_port", lambda: safe_finding)
    monkeypatch.setattr(setup, "_probe_openwebui_port", lambda: safe_finding)
    monkeypatch.setattr(setup, "_probe_openwebui_image", lambda docker_finding: safe_finding)

    report = setup.build_setup_report(
        ROOT,
        mode="frontier",
        profile="minimal",
        provider="openai",
        model_id="uaa-llama-cpp-local",
        hf_repo=setup.DEFAULT_HF_REPO,
        hf_file=setup.DEFAULT_HF_FILE,
    )

    assert report.overall_status == "manual"
    assert any(finding.status == "not-scoped" for finding in report.findings)
    rendered = setup.render_report(report, hf_repo=setup.DEFAULT_HF_REPO, hf_file=setup.DEFAULT_HF_FILE)
    assert "does not install packages, download models, collect provider credentials" in rendered
    assert "multi-provider UAA routing needs a later scoped milestone" in rendered


def test_minimal_profile_skips_docker_and_frontend(monkeypatch: pytest.MonkeyPatch) -> None:
    setup = load_setup()
    safe_finding = setup.SetupFinding("safe prerequisite", "pass", "present", "No action needed.")
    called = {"docker": False, "frontend": False}
    monkeypatch.setattr(setup, "_probe_python", lambda root: safe_finding)
    monkeypatch.setattr(setup, "_probe_uaa_shell_command", lambda root: safe_finding)
    monkeypatch.setattr(setup, "_probe_backend_port", lambda: setup.SetupFinding("backend port", "pass", "free", "No action needed."))

    def fail_docker() -> None:
        called["docker"] = True
        raise AssertionError("Docker should not be probed for minimal profile")

    def fail_frontend(root: Any) -> None:
        called["frontend"] = True
        raise AssertionError("Frontend should not be probed for minimal profile")

    monkeypatch.setattr(setup, "_probe_docker", fail_docker)
    monkeypatch.setattr(setup, "_probe_frontend_deps", fail_frontend)

    report = setup.build_setup_report(
        ROOT,
        mode="local-llama",
        profile="minimal",
        provider=None,
        model_id="uaa-llama-cpp-local",
        hf_repo=setup.DEFAULT_HF_REPO,
        hf_file=setup.DEFAULT_HF_FILE,
    )

    assert report.profile == "minimal"
    assert [finding.name for finding in report.findings] == ["safe prerequisite", "safe prerequisite", "backend port"]
    assert not called["docker"]
    assert not called["frontend"]
    assert report.next_steps == [
        "Resolve blocked Python or launcher checks first.",
        "Run: uaa doctor",
        "Run: uaa start",
    ]


def test_profiles_run_only_their_scoped_probes(monkeypatch: pytest.MonkeyPatch) -> None:
    setup = load_setup()
    calls = []

    def finding(name: str) -> Any:
        def _inner(*args: Any, **kwargs: Any) -> Any:
            calls.append(name)
            return setup.SetupFinding(name, "pass", "safe", "No action needed.")

        return _inner

    monkeypatch.setattr(setup, "_probe_python", finding("python environment"))
    monkeypatch.setattr(setup, "_probe_frontend_deps", finding("frontend dependencies"))
    monkeypatch.setattr(setup, "_probe_uaa_shell_command", finding("uaa shell command"))
    monkeypatch.setattr(setup, "_probe_docker", finding("docker"))
    monkeypatch.setattr(setup, "_probe_backend_port", finding("backend port"))
    monkeypatch.setattr(setup, "_probe_frontend_port", finding("frontend port"))
    monkeypatch.setattr(setup, "_probe_openwebui_port", finding("OpenWebUI port"))
    monkeypatch.setattr(setup, "_probe_openwebui_data_dir", finding("OpenWebUI data directory"))
    monkeypatch.setattr(setup, "_probe_openwebui_image", finding("OpenWebUI image"))
    monkeypatch.setattr(setup, "_probe_smoke_gateway_env", finding("local gateway env"))
    monkeypatch.setattr(setup, "_probe_local_llama_gateway_env", finding("local gateway env"))
    monkeypatch.setattr(setup, "_probe_model_alias", finding("selected model alias"))
    monkeypatch.setattr(setup, "_probe_uaa_gateway_status", finding("UAA local gateway"))
    monkeypatch.setattr(setup, "_probe_llama_server", finding("llama-server"))
    monkeypatch.setattr(setup, "_probe_llama_server_port", finding("llama.cpp port"))

    expected = {
        "minimal": [
            "python environment",
            "uaa shell command",
            "backend port",
        ],
        "frontend-only": [
            "python environment",
            "uaa shell command",
            "frontend dependencies",
            "backend port",
            "frontend port",
        ],
        "openwebui-smoke": [
            "docker",
            "python environment",
            "uaa shell command",
            "backend port",
            "OpenWebUI port",
            "OpenWebUI data directory",
            "OpenWebUI image",
            "local gateway env",
            "selected model alias",
            "UAA local gateway",
        ],
        "local-llama": [
            "docker",
            "python environment",
            "uaa shell command",
            "frontend dependencies",
            "backend port",
            "frontend port",
            "OpenWebUI port",
            "OpenWebUI data directory",
            "OpenWebUI image",
            "local gateway env",
            "selected model alias",
            "UAA local gateway",
            "llama-server",
            "llama.cpp port",
        ],
    }

    for profile, expected_calls in expected.items():
        calls.clear()
        setup.build_setup_report(
            ROOT,
            mode="local-llama",
            profile=profile,
            provider=None,
            model_id="uaa-llama-cpp-local",
            hf_repo=setup.DEFAULT_HF_REPO,
            hf_file=setup.DEFAULT_HF_FILE,
        )

        assert calls == expected_calls


def test_command_setup_writes_redacted_report_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    setup = load_setup()
    monkeypatch.setattr(setup, "build_setup_report", lambda root, **kwargs: _stable_report(setup))

    exit_code = setup.command_setup(
        tmp_path,
        _setup_args(profile="minimal", json=True, write_report=".uaa/dev/setup-report.json"),
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    report_path = tmp_path / ".uaa" / "dev" / "setup-report.json"
    file_payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["report_path"] == ".uaa/dev/setup-report.json"
    assert file_payload["report_path"] == ".uaa/dev/setup-report.json"
    assert stat.S_IMODE(report_path.stat().st_mode) == 0o600
    assert "secret" not in captured.out.lower()
    assert "secret" not in report_path.read_text(encoding="utf-8").lower()


def test_command_setup_write_env_existing_file_keeps_template(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    setup = load_setup()
    target = tmp_path / setup.LOCAL_ENV_PATH
    target.parent.mkdir(parents=True)
    original = (
        "export UAA_LLAMA_CPP_GATEWAY_KEY=secret-gateway\n"
        "export UAA_LLAMA_CPP_API_KEY=secret-backend\n"
    )
    target.write_text(original, encoding="utf-8")
    monkeypatch.setattr(setup, "build_setup_report", lambda root, **kwargs: _stable_report(setup))

    exit_code = setup.command_setup(
        tmp_path,
        _setup_args(profile="local-llama", json=True, write_env=True),
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert target.read_text(encoding="utf-8") == original
    assert payload["env_template"] == ".uaa/dev/local-llama.env"
    assert any(finding["name"] == "local env template" and finding["status"] == "manual" for finding in payload["findings"])
    assert "Existing local env template kept" in captured.out
    assert "secret-gateway" not in captured.out
    assert "secret-backend" not in captured.out


def test_setup_install_refusal_writes_redacted_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    setup = load_setup()
    monkeypatch.setattr(setup, "_utc_timestamp", lambda: "20260620T010203Z")
    monkeypatch.setattr(sys, "stdin", io.StringIO("no\n"))

    def fail_resolve(command: str) -> None:
        raise AssertionError("Docker should not be resolved when install approval is refused")

    monkeypatch.setattr(setup, "_resolve_command", fail_resolve)

    exit_code = setup.command_setup(
        tmp_path,
        _setup_args(setup_action="install", target="openwebui", yes=False),
    )
    captured = capsys.readouterr()
    receipt_path = tmp_path / setup.SETUP_INSTALL_RECEIPT_DIR / "openwebui-20260620T010203Z.json"
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert stat.S_IMODE(receipt_path.stat().st_mode) == 0o600
    assert payload["schema"] == "uaa.setup_install_receipt.v1"
    assert payload["target"] == "openwebui"
    assert payload["status"] == "refused"
    assert payload["image_ref"] == setup.OPENWEBUI_IMAGE
    assert payload["exact_commands"] == [f"docker pull {setup.OPENWEBUI_IMAGE}"]
    assert "No download or install command was run" in captured.out
    assert "docker pull" in captured.out
    assert "secret-value" not in captured.out
    assert "secret-value" not in receipt_path.read_text(encoding="utf-8")


def test_setup_install_yes_without_preview_token_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    setup = load_setup()
    monkeypatch.setattr(setup, "_utc_timestamp", lambda: "20260620T010203Z")

    def fail_resolve(command: str) -> None:
        raise AssertionError("Docker should not be resolved without a preview-bound approval token")

    monkeypatch.setattr(setup, "_resolve_command", fail_resolve)

    exit_code = setup.command_setup(
        tmp_path,
        _setup_args(setup_action="install", target="openwebui", yes=True, approval_token=None),
    )
    captured = capsys.readouterr()
    receipt_path = tmp_path / setup.SETUP_INSTALL_RECEIPT_DIR / "openwebui-20260620T010203Z.json"
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["approval_mode"] == "not-approved"
    assert "approval token" in captured.out.lower()
    assert "docker pull" in captured.out


def test_setup_install_approved_pulls_openwebui_image_and_writes_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    setup = load_setup()
    calls = []
    home = tmp_path / "home"
    home.mkdir()
    token_path = home / ".local" / "state" / "uaa" / "install-approval.json"
    token_path.parent.mkdir(parents=True)
    monkeypatch.setattr(setup, "_bootstrap_user_home", lambda: home)
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_KEY", "secret-value")
    monkeypatch.setattr(setup, "_utc_timestamp", lambda: "20260620T010203Z")
    monkeypatch.setattr(setup, "_resolve_command", lambda command: Path("/tmp/docker") if command == "docker" else None)
    monkeypatch.setattr(setup, "_run_probe", lambda command, **kwargs: {"returncode": 0, "stdout": "27.0.0\n", "stderr": ""})
    setup.write_setup_install_approval_token(tmp_path, setup._openwebui_install_plan(tmp_path), token_path)

    def fake_install(command: str) -> dict[str, Any]:
        calls.append(command)
        return {"returncode": 0, "summary": "completed"}

    monkeypatch.setattr(setup, "_run_install_command", fake_install)

    exit_code = setup.command_setup(
        tmp_path,
        _setup_args(setup_action="install", target="openwebui", yes=True, approval_token=str(token_path)),
    )
    captured = capsys.readouterr()
    receipt_path = tmp_path / setup.SETUP_INSTALL_RECEIPT_DIR / "openwebui-20260620T010203Z.json"
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    approval_receipt = next((tmp_path / setup.SETUP_APPROVAL_RECEIPT_DIR).glob("openwebui-image-pull-*.json"))
    approval_payload = json.loads(approval_receipt.read_text(encoding="utf-8"))
    token_payload = json.loads(token_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert calls == [[str(Path("/tmp/docker")), "pull", setup.OPENWEBUI_IMAGE]]
    assert payload["status"] == "installed"
    assert payload["action"] == "docker-image-pull"
    assert payload["approval_mode"] == "preview-token"
    assert payload["approval_authority"] == "PolicyEngine+LocalApprovalAuthority"
    assert payload["approval_decision_ref"] == approval_payload["decision_ref"]
    assert payload["preview_hash"] == token_payload["preview_hash"]
    assert approval_payload["schema"] == "uaa.setup_approval_receipt.v1"
    assert approval_payload["status"] == "allowed"
    assert approval_payload["scope"]["image_ref"] == setup.OPENWEBUI_IMAGE
    assert approval_payload["scope"]["preview_hash"] == payload["preview_hash"]
    assert stat.S_IMODE(approval_receipt.stat().st_mode) == 0o600
    assert token_payload["used_at"]
    assert payload["side_effects_allowed"] == [
        "Docker may download and store the configured OpenWebUI image in the local Docker image cache.",
        "A redacted local receipt may be written under .uaa/dev/setup-install-receipts by default, or to --receipt.",
    ]
    assert "docker image rm" in "\n".join(payload["rollback_steps"])
    assert "explicit canonical-path review" in captured.out
    assert "rm -rf .uaa/dev/openwebui-data" not in captured.out
    assert "secret-value" not in captured.out
    assert "secret-value" not in receipt_path.read_text(encoding="utf-8")
    assert "secret-value" not in approval_receipt.read_text(encoding="utf-8")


def test_setup_install_custom_receipt_is_preview_bound_and_redacted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    setup = load_setup()
    home = tmp_path / "home"
    receipt_path = home / ".local" / "state" / "uaa" / "openwebui-receipt.json"
    token_path = home / ".local" / "state" / "uaa" / "install-approval.json"
    receipt_path.parent.mkdir(parents=True)
    monkeypatch.setattr(setup, "_bootstrap_user_home", lambda: home)
    monkeypatch.setattr(setup, "_utc_timestamp", lambda: "20260620T010203Z")
    monkeypatch.setattr(sys, "stdin", io.StringIO("install openwebui\n"))

    token_exit = setup.command_setup(
        tmp_path,
        _setup_args(
            setup_action="install",
            target="openwebui",
            receipt=str(receipt_path),
            write_approval_token=str(token_path),
        ),
    )
    token_payload = json.loads(token_path.read_text(encoding="utf-8"))

    calls = []
    monkeypatch.setattr(setup, "_resolve_command", lambda command: Path("/tmp/docker"))
    monkeypatch.setattr(
        setup,
        "_run_probe",
        lambda command, **kwargs: {"returncode": 0, "stdout": "27.0.0\n", "stderr": ""},
    )
    monkeypatch.setattr(
        setup,
        "_run_install_command",
        lambda command: calls.append(command) or {"returncode": 0, "summary": "completed"},
    )

    install_exit = setup.command_setup(
        tmp_path,
        _setup_args(
            setup_action="install",
            target="openwebui",
            yes=True,
            approval_token=str(token_path),
            receipt=str(receipt_path),
        ),
    )
    captured = capsys.readouterr()
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert token_exit == 0
    assert install_exit == 0
    assert calls == [[str(Path("/tmp/docker")), "pull", setup.OPENWEBUI_IMAGE]]
    assert payload["status"] == "installed"
    assert payload["receipt"] == "~/.local/state/uaa/openwebui-receipt.json"
    assert payload["receipt_scope_ref"].startswith("receipt-path-sha256:")
    assert payload["preview_hash"] == token_payload["preview_hash"]
    assert str(home) not in captured.out
    assert str(home) not in receipt_path.read_text(encoding="utf-8")
    assert stat.S_IMODE(receipt_path.stat().st_mode) == 0o600


def test_setup_install_custom_receipt_mismatch_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    setup = load_setup()
    home = tmp_path / "home"
    first_receipt = home / "state" / "first.json"
    second_receipt = home / "state" / "second.json"
    token_path = home / "state" / "approval.json"
    first_receipt.parent.mkdir(parents=True)
    monkeypatch.setattr(setup, "_bootstrap_user_home", lambda: home)
    monkeypatch.setattr(setup, "_utc_timestamp", lambda: "20260620T010203Z")
    monkeypatch.setattr(setup, "_resolve_command", lambda command: pytest.fail("Docker should not be resolved"))
    plan = setup._openwebui_install_plan(tmp_path)
    setup._attach_install_approval_paths(
        tmp_path,
        plan,
        _setup_args(receipt=str(first_receipt)),
    )
    setup.write_setup_install_approval_token(tmp_path, plan, token_path)

    exit_code = setup.command_setup(
        tmp_path,
        _setup_args(
            setup_action="install",
            target="openwebui",
            yes=True,
            approval_token=str(token_path),
            receipt=str(second_receipt),
        ),
    )
    captured = capsys.readouterr()
    payload = json.loads(second_receipt.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert "preview hash mismatch" in captured.out.lower()
    assert payload["receipt"] == "~/state/second.json"


def test_setup_install_custom_receipt_rejects_unsafe_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    setup = load_setup()
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(setup, "_bootstrap_user_home", lambda: home)

    existing = home / "existing.json"
    existing.write_text("keep", encoding="utf-8")
    symlink = home / "symlink.json"
    symlink.symlink_to(home / "missing-target.json")
    loop_parent = home / "loop"
    loop_parent.symlink_to(loop_parent)
    world_writable = home / "shared"
    world_writable.mkdir(mode=0o777)
    world_writable.chmod(0o777)
    unsafe = [
        (existing, "already exists"),
        (symlink, "must not be a symlink"),
        (loop_parent / "receipt.json", "could not be resolved safely"),
        (tmp_path / "outside.json", "current user's home"),
        (world_writable / "receipt.json", "world-writable"),
    ]

    for receipt_path, expected in unsafe:
        exit_code = setup.command_setup(
            tmp_path,
            _setup_args(
                setup_action="install",
                target="openwebui",
                receipt=str(receipt_path),
            ),
        )
        captured = capsys.readouterr()
        assert exit_code == 2
        assert expected in captured.out

    assert existing.read_text(encoding="utf-8") == "keep"
    assert not (world_writable / "receipt.json").exists()


def test_setup_install_custom_receipt_write_rejects_substituted_symlink(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    setup = load_setup()
    home = tmp_path / "home"
    home.mkdir()
    receipt_path = home / "receipt.json"
    outside = home / "outside.json"
    outside.write_text("keep", encoding="utf-8")
    monkeypatch.setattr(setup, "_bootstrap_user_home", lambda: home)
    plan = setup._openwebui_install_plan(tmp_path)
    setup._attach_install_approval_paths(
        tmp_path,
        plan,
        _setup_args(receipt=str(receipt_path)),
    )
    receipt_path.symlink_to(outside)

    with pytest.raises(ValueError, match="refusing to overwrite"):
        setup.write_setup_install_receipt(
            tmp_path,
            plan,
            status="failed",
            result_summary="No command was run.",
        )

    assert outside.read_text(encoding="utf-8") == "keep"


def test_setup_install_preview_token_stale_mismatch_and_replay_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    setup = load_setup()
    home = tmp_path / "home"
    home.mkdir()
    token_path = home / ".local" / "state" / "uaa" / "install-approval.json"
    token_path.parent.mkdir(parents=True)
    monkeypatch.setattr(setup, "_bootstrap_user_home", lambda: home)
    monkeypatch.setattr(setup, "_resolve_command", lambda command: pytest.fail("Docker should not be resolved"))

    plan = setup._openwebui_install_plan(tmp_path)
    setup.write_setup_install_approval_token(tmp_path, plan, token_path, ttl_seconds=-1)
    exit_code = setup.command_setup(
        tmp_path,
        _setup_args(setup_action="install", target="openwebui", yes=True, approval_token=str(token_path)),
    )
    stale = capsys.readouterr()
    assert exit_code == 1
    assert "expired" in stale.out.lower()

    token_path.unlink()
    setup.write_setup_install_approval_token(tmp_path, plan, token_path)
    payload = json.loads(token_path.read_text(encoding="utf-8"))
    payload["preview_hash"] = "f" * 64
    token_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    token_path.chmod(0o600)
    exit_code = setup.command_setup(
        tmp_path,
        _setup_args(setup_action="install", target="openwebui", yes=True, approval_token=str(token_path)),
    )
    mismatch = capsys.readouterr()
    assert exit_code == 1
    assert "preview hash mismatch" in mismatch.out.lower()

    token_path.unlink()
    setup.write_setup_install_approval_token(tmp_path, plan, token_path)
    payload = json.loads(token_path.read_text(encoding="utf-8"))
    payload["used_at"] = "20260620T010203Z"
    token_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    token_path.chmod(0o600)
    exit_code = setup.command_setup(
        tmp_path,
        _setup_args(setup_action="install", target="openwebui", yes=True, approval_token=str(token_path)),
    )
    replay = capsys.readouterr()
    assert exit_code == 1
    assert "already used" in replay.out.lower()


def test_setup_install_docker_not_ready_does_not_pull(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    setup = load_setup()
    calls = []
    home = tmp_path / "home"
    home.mkdir()
    token_path = home / ".local" / "state" / "uaa" / "install-approval.json"
    token_path.parent.mkdir(parents=True)
    monkeypatch.setattr(setup, "_bootstrap_user_home", lambda: home)
    monkeypatch.setattr(setup, "_utc_timestamp", lambda: "20260620T010203Z")
    monkeypatch.setattr(setup, "_resolve_command", lambda command: Path("/tmp/docker") if command == "docker" else None)
    monkeypatch.setattr(setup, "_run_probe", lambda command, **kwargs: {"returncode": 1, "stdout": "", "stderr": "daemon unavailable"})
    monkeypatch.setattr(setup, "_run_install_command", lambda command: calls.append(command) or {"returncode": 0, "summary": "completed"})
    setup.write_setup_install_approval_token(tmp_path, setup._openwebui_install_plan(tmp_path), token_path)

    exit_code = setup.command_setup(
        tmp_path,
        _setup_args(setup_action="install", target="openwebui", yes=True, approval_token=str(token_path)),
    )
    captured = capsys.readouterr()
    receipt_path = tmp_path / setup.SETUP_INSTALL_RECEIPT_DIR / "openwebui-20260620T010203Z.json"
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert calls == []
    assert payload["status"] == "failed"
    assert "Docker engine is not ready" in captured.out


def test_plain_setup_does_not_run_install_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    setup = load_setup()
    monkeypatch.setattr(setup, "build_setup_report", lambda root, **kwargs: _stable_report(setup))

    def fail_install(root: Any, args: Any) -> None:
        raise AssertionError("plain uaa setup must not run the install command")

    monkeypatch.setattr(setup, "command_setup_install", fail_install)

    exit_code = setup.command_setup(tmp_path, _setup_args(profile="minimal", json=True))

    assert exit_code == 0


def test_setup_report_groups_blocked_and_manual_next_steps() -> None:
    setup = load_setup()
    report = setup.SetupReport(
        mode="local-llama",
        system_summary={},
        findings=[
            setup.SetupFinding("python", "blocked", "missing", "Create .venv."),
            setup.SetupFinding("OpenWebUI port", "manual", "free", "Start OpenWebUI later."),
            setup.SetupFinding("frontier", "not-scoped", "not scoped", "Create a scoped milestone."),
            setup.SetupFinding("alias", "pass", "selected", "No action needed."),
        ],
        model_id="uaa-llama-cpp-local",
        next_steps=[],
    )

    assert report.overall_status == "blocked"
    assert report.blocked_next_steps == ["[python] Create .venv."]
    assert report.manual_next_steps == [
        "[OpenWebUI port] Start OpenWebUI later.",
        "[frontier] Create a scoped milestone.",
    ]

    serialized = setup.serialize_report(report)

    assert serialized["selected_model_alias"] == "uaa-llama-cpp-local"
    assert serialized["blocked_next_steps"] == ["[python] Create .venv."]
    assert serialized["manual_next_steps"] == [
        "[OpenWebUI port] Start OpenWebUI later.",
        "[frontier] Create a scoped milestone.",
    ]


def test_serialized_report_matches_safe_json_contract() -> None:
    setup = load_setup()
    report = setup.SetupReport(
        mode="local-llama",
        system_summary={"os": "Darwin", "architecture": "arm64", "python": "3.11.15"},
        findings=[
            setup.SetupFinding(
                "env: UAA_LLAMA_CPP_GATEWAY_KEY",
                "pass",
                "UAA_LLAMA_CPP_GATEWAY_KEY is present; value is intentionally redacted.",
                "No action needed.",
                why="Secret presence is enough for readiness.",
                authority_boundary="No secret values are printed.",
            )
        ],
        model_id="uaa-llama-cpp-local",
        next_steps=["Run: uaa start"],
        repair_plan=[],
        plan_commands=["source .uaa/dev/local-llama.env"],
        platform_hints=["Docker/OpenWebUI checks are readiness probes only."],
        profile="local-llama",
        selected_model_alias="uaa-llama-cpp-local",
        env_template=".uaa/dev/local-llama.env",
        report_path=".uaa/dev/setup-report.json",
    )

    payload = setup.serialize_report(report)

    assert set(payload) == {
        "profile",
        "mode",
        "overall_status",
        "system_summary",
        "findings",
        "model_id",
        "selected_model_alias",
        "blocked_next_steps",
        "manual_next_steps",
        "repair_plan",
        "plan_commands",
        "platform_hints",
        "next_steps",
        "env_template",
        "report_path",
    }
    assert payload["profile"] == "local-llama"
    assert payload["overall_status"] == "pass"
    assert isinstance(payload["system_summary"], dict)
    for key in ["findings", "repair_plan", "plan_commands", "platform_hints", "next_steps"]:
        assert isinstance(payload[key], list)
    assert set(payload["findings"][0]) == {"name", "status", "summary", "action", "why", "authority_boundary"}
    assert payload["findings"][0]["status"] in {"pass", "warn", "blocked", "manual", "not-scoped"}
    serialized = json.dumps(payload, sort_keys=True)
    assert "secret-gateway" not in serialized
    assert "secret-backend" not in serialized
    assert "sk-" not in serialized


def test_ordered_repair_plan_respects_dependencies() -> None:
    setup = load_setup()
    findings = [
        setup.SetupFinding("UAA local gateway", "manual", "disabled", "Restart backend."),
        setup.SetupFinding("llama-server", "blocked", "missing", "Install llama.cpp externally."),
        setup.SetupFinding("python environment", "blocked", "missing", "Create .venv."),
        setup.SetupFinding("local gateway env", "manual", "missing", "Source env."),
        setup.SetupFinding("OpenWebUI port", "manual", "free", "Start OpenWebUI later."),
    ]

    plan = setup._repair_plan(findings)

    assert plan == [
        "[blocked] python environment: Create .venv.",
        "[manual] local gateway env: Source env.",
        "[blocked] llama-server: Install llama.cpp externally.",
        "[manual] UAA local gateway: Restart backend.",
        "[manual] OpenWebUI port: Start OpenWebUI later.",
    ]


def test_explain_mode_renders_check_boundaries() -> None:
    setup = load_setup()
    report = setup.SetupReport(
        mode="local-llama",
        system_summary={},
        findings=setup._enrich_findings(
            [
                setup.SetupFinding(
                    "docker",
                    "manual",
                    "Docker is not ready.",
                    "Open Docker Desktop.",
                )
            ]
        ),
        model_id="uaa-llama-cpp-local",
        next_steps=[],
    )

    rendered = setup.render_report(report, hf_repo=setup.DEFAULT_HF_REPO, hf_file=setup.DEFAULT_HF_FILE, explain=True)

    assert "Why: The local OpenWebUI shell uses Docker" in rendered
    assert "Authority boundary: Docker/OpenWebUI checks do not pull images" in rendered


def test_local_llama_gateway_env_reports_missing_values_without_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    setup = load_setup()
    for key in [
        setup.UAA_LLAMA_CPP_GATEWAY_ENV,
        setup.UAA_LLAMA_CPP_GATEWAY_KEY_ENV,
        setup.UAA_LLAMA_CPP_BASE_URL_ENV,
        setup.UAA_LLAMA_CPP_MODEL_ID_ENV,
        setup.UAA_LLAMA_CPP_API_KEY_ENV,
    ]:
        monkeypatch.delenv(key, raising=False)

    finding = setup._probe_local_llama_gateway_env("uaa-llama-cpp-local")

    assert finding.status == "manual"
    assert "selected alias would be uaa-llama-cpp-local" in finding.summary
    assert setup.UAA_LLAMA_CPP_GATEWAY_KEY_ENV in finding.summary
    assert "uaa-local-llama-cpp-dev" not in finding.summary
    assert "uaa-llama-backend-dev" not in finding.summary


def test_local_llama_gateway_env_rejects_non_loopback_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    setup = load_setup()
    monkeypatch.setenv(setup.UAA_LLAMA_CPP_GATEWAY_ENV, "1")
    monkeypatch.setenv(setup.UAA_LLAMA_CPP_GATEWAY_KEY_ENV, "secret-value")
    monkeypatch.setenv(setup.UAA_LLAMA_CPP_BASE_URL_ENV, "https://example.com:8080")
    monkeypatch.setenv(setup.UAA_LLAMA_CPP_MODEL_ID_ENV, "uaa-llama-cpp-local")
    monkeypatch.setenv(setup.UAA_LLAMA_CPP_API_KEY_ENV, "backend-secret")

    finding = setup._probe_local_llama_gateway_env("uaa-llama-cpp-local")

    assert finding.status == "blocked"
    assert "not a loopback HTTP URL" in finding.summary
    assert "secret-value" not in finding.summary
    assert "backend-secret" not in finding.summary


def test_check_env_reports_safe_diff_without_secret_values(tmp_path: Path) -> None:
    setup = load_setup()
    env_file = tmp_path / "local-llama.env"
    env_file.write_text(
        "\n".join(
            [
                "export UAA_LLAMA_CPP_GATEWAY_ENABLED=1",
                "export UAA_LLAMA_CPP_GATEWAY_KEY=secret-gateway",
                "export UAA_LLAMA_CPP_API_KEY=secret-backend",
                "export UAA_LLAMA_CPP_BASE_URL=http://127.0.0.1:8081",
                "export UAA_LLAMA_CPP_MODEL_ID=other-model",
                "",
            ]
        ),
        encoding="utf-8",
    )

    findings = setup.check_local_llama_env_file(tmp_path, env_file, model_id="uaa-llama-cpp-local")
    summaries = "\n".join(finding.summary for finding in findings)

    assert any(finding.name == "env: UAA_LLAMA_CPP_GATEWAY_KEY" and finding.status == "pass" for finding in findings)
    assert "UAA_LLAMA_CPP_BASE_URL differs from expected safe value http://127.0.0.1:8080" in summaries
    assert "UAA_LLAMA_CPP_MODEL_ID differs from expected safe value uaa-llama-cpp-local" in summaries
    assert "secret-gateway" not in summaries
    assert "secret-backend" not in summaries


def test_existing_env_template_is_summarized_without_overwrite(tmp_path: Path) -> None:
    setup = load_setup()
    target = tmp_path / setup.LOCAL_ENV_PATH
    target.parent.mkdir(parents=True)
    target.write_text(
        "export UAA_LLAMA_CPP_GATEWAY_KEY=secret-gateway\n"
        "export UAA_LLAMA_CPP_API_KEY=secret-backend\n",
        encoding="utf-8",
    )

    path, finding = setup.prepare_local_llama_env(tmp_path, model_id="uaa-llama-cpp-local", overwrite=False)

    assert path == target
    assert finding.status == "manual"
    assert "Existing local env template kept" in finding.summary
    assert "secret-gateway" not in finding.summary
    assert "secret-backend" not in finding.summary
    assert target.read_text(encoding="utf-8") == (
        "export UAA_LLAMA_CPP_GATEWAY_KEY=secret-gateway\n"
        "export UAA_LLAMA_CPP_API_KEY=secret-backend\n"
    )


def test_write_report_creates_redacted_json_bundle(tmp_path: Path) -> None:
    setup = load_setup()
    report = setup.SetupReport(
        mode="local-llama",
        system_summary={"os": "test"},
        findings=[setup.SetupFinding("env: UAA_LLAMA_CPP_GATEWAY_KEY", "pass", "present; value redacted", "No action needed.")],
        model_id="uaa-llama-cpp-local",
        next_steps=[],
        repair_plan=[],
        plan_commands=["source .uaa/dev/local-llama.env"],
    )

    output = setup.write_setup_report(tmp_path, Path(".uaa/dev/setup-report.json"), report)
    payload = output.read_text(encoding="utf-8")

    assert output.relative_to(tmp_path) == Path(".uaa/dev/setup-report.json")
    assert "value redacted" in payload
    assert "secret" not in payload.lower()


def test_backend_port_distinguishes_uaa_health_from_generic_http(monkeypatch: pytest.MonkeyPatch) -> None:
    setup = load_setup()
    monkeypatch.setattr(setup, "_is_port_open", lambda host, port: True)
    monkeypatch.setattr(setup, "_url_status", lambda url, **kwargs: 200 if url.endswith("/health") else None)

    finding = setup._probe_backend_port()

    assert finding.status == "pass"
    assert "UAA likely running" in finding.summary

    monkeypatch.setattr(setup, "_url_status", lambda url, **kwargs: 404 if url.endswith("/health") else 200)

    finding = setup._probe_backend_port()

    assert finding.status == "warn"
    assert "HTTP server answered on backend port" in finding.summary


def test_setup_probes_honor_launcher_endpoint_overrides(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    setup = load_setup()
    monkeypatch.setenv(setup.UAA_LAUNCHER_BACKEND_HOST_ENV, "localhost")
    monkeypatch.setenv(setup.UAA_LAUNCHER_BACKEND_PORT_ENV, "8100")
    monkeypatch.setenv(setup.UAA_LAUNCHER_FRONTEND_PORT_ENV, "5273")
    monkeypatch.setenv(setup.UAA_LAUNCHER_OPENWEBUI_PORT_ENV, "3100")
    probes: list[tuple[str, int]] = []

    def free(host: str, port: int) -> bool:
        probes.append((host, port))
        return False

    monkeypatch.setattr(setup, "_is_port_open", free)

    backend = setup._probe_backend_port()
    frontend = setup._probe_frontend_port()
    openwebui = setup._probe_openwebui_port()

    assert "http://127.0.0.1:8100" in backend.summary
    assert "http://127.0.0.1:5273" in frontend.summary
    assert "http://127.0.0.1:3100" in openwebui.summary
    assert probes == [
        ("127.0.0.1", 8100),
        ("127.0.0.1", 5273),
        ("127.0.0.1", 3100),
    ]

    requested_urls: list[str] = []
    monkeypatch.setattr(setup, "_is_port_open", lambda host, port: (host, port) == ("127.0.0.1", 8100))
    monkeypatch.setattr(
        setup,
        "_url_status",
        lambda url, **_kwargs: requested_urls.append(url) or 200,
    )
    monkeypatch.setattr(setup, "_launcher_owns_backend", lambda _root, _url: True)

    gateway = setup._probe_uaa_gateway_status(tmp_path, mode="smoke")

    assert gateway.status == "pass"
    assert requested_urls == ["http://127.0.0.1:8100/v1/models"]

    frontend_steps = setup._next_steps(
        profile="frontend-only",
        mode="smoke",
        model_id="uaa-safe-local",
        hf_repo="unused",
        hf_file="unused",
    )
    smoke_steps = setup._next_steps(
        profile="openwebui-smoke",
        mode="smoke",
        model_id="uaa-safe-local",
        hf_repo="unused",
        hf_file="unused",
    )
    assert "Open http://127.0.0.1:5273." in frontend_steps
    assert "Open http://127.0.0.1:3100 and select uaa-safe-local." in smoke_steps


def test_setup_gateway_probe_never_sends_bearer_to_unowned_backend(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    setup = load_setup()
    requested: list[str] = []
    monkeypatch.setattr(setup, "_is_port_open", lambda _host, _port: True)
    monkeypatch.setattr(setup, "_launcher_owns_backend", lambda _root, _url: False)
    monkeypatch.setattr(
        setup,
        "_url_status",
        lambda url, **_kwargs: requested.append(url) or 200,
    )

    finding = setup._probe_uaa_gateway_status(tmp_path, mode="smoke")

    assert finding.status == "manual"
    assert "bearer was not sent" in finding.summary
    assert requested == []


def test_setup_backend_ownership_requires_exact_launcher_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    setup = load_setup()
    state = tmp_path / ".uaa" / "dev"
    (state / "pids").mkdir(parents=True)
    pid_file = state / "pids" / "backend.pid"
    pid_file.write_text("0\n", encoding="utf-8")
    assert setup._launcher_owns_backend(tmp_path, setup.BACKEND_URL) is False

    pid_file.write_text(f"{1 << 100}\n", encoding="utf-8")
    monkeypatch.setattr(
        setup.os,
        "kill",
        lambda _pid, _sig: (_ for _ in ()).throw(OverflowError()),
    )
    assert setup._launcher_owns_backend(tmp_path, setup.BACKEND_URL) is False

    pid_file.write_text("12345\n", encoding="utf-8")
    url = setup.BACKEND_URL
    metadata = {
        "name": "backend",
        "pid": 12345,
        "command": [
            str(tmp_path / ".venv" / "bin" / "python"),
            "-m",
            "uvicorn",
            "ultimate_ai_agent.api.app:app",
            "--host",
            setup.BACKEND_HOST,
            "--port",
            str(setup.BACKEND_PORT),
        ],
        "cwd": str(tmp_path),
        "url": url,
    }
    (state / "backend.json").write_text(json.dumps(metadata), encoding="utf-8")
    monkeypatch.setattr(setup.os, "kill", lambda _pid, _sig: None)

    assert setup._launcher_owns_backend(tmp_path, url)

    metadata["url"] = "http://127.0.0.1:8001"
    (state / "backend.json").write_text(json.dumps(metadata), encoding="utf-8")
    assert setup._launcher_owns_backend(tmp_path, url) is False


def test_setup_rejects_unsupported_launcher_ipv6_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    setup = load_setup()
    monkeypatch.setenv(setup.UAA_LAUNCHER_BACKEND_HOST_ENV, "::1")

    with pytest.raises(ValueError, match="127.0.0.1 or localhost"):
        setup._probe_backend_port()


def test_openwebui_data_dir_reports_prior_state_without_creating(tmp_path: Path) -> None:
    setup = load_setup()

    finding = setup._probe_openwebui_data_dir(tmp_path)

    assert finding.status == "pass"
    assert "will create it when requested" in finding.summary
    assert not (tmp_path / ".uaa" / "dev" / "openwebui-data").exists()


def test_plan_preview_is_honest_and_non_executing() -> None:
    setup = load_setup()
    report = setup.SetupReport(
        mode="local-llama",
        system_summary={},
        findings=[],
        model_id="uaa-llama-cpp-local",
        next_steps=[],
        repair_plan=["[manual] local gateway env: Source env."],
        plan_commands=["source .uaa/dev/local-llama.env"],
    )

    rendered = setup.render_plan(report)

    assert "Preview only" in rendered
    assert "source .uaa/dev/local-llama.env" in rendered
    assert "did not run commands" in rendered


def test_openwebui_image_probe_is_local_inspect_only(monkeypatch: pytest.MonkeyPatch) -> None:
    setup = load_setup()
    docker_path = Path("/tmp/docker")
    commands = []
    monkeypatch.setattr(setup, "_resolve_command", lambda command: docker_path if command == "docker" else None)

    def fake_run_probe(command: str, *, timeout_seconds: Any) -> dict[str, Any]:
        commands.append(command)
        assert timeout_seconds == 3.0
        return {"returncode": 1, "stdout": "", "stderr": "No such image"}

    monkeypatch.setattr(setup, "_run_probe", fake_run_probe)

    finding = setup._probe_openwebui_image(setup.SetupFinding("docker", "pass", "ready", "No action needed."))

    assert finding.status == "manual"
    assert "not present locally" in finding.summary
    assert commands == [
        [str(docker_path), "image", "inspect", "--format", "{{.Id}}", setup.OPENWEBUI_IMAGE],
    ]


def test_launcher_parser_exposes_setup_command() -> None:
    launcher = load_launcher()

    args = launcher.parse_args(["setup", "--profile", "openwebui-smoke", "--json", "--explain", "--plan"])

    assert args.command == "setup"
    assert args.profile == "openwebui-smoke"
    assert args.json is True
    assert args.explain is True
    assert args.plan is True


def test_launcher_parser_exposes_setup_install_command() -> None:
    launcher = load_launcher()

    args = launcher.parse_args(
        [
            "setup",
            "install",
            "--target",
            "openwebui",
            "--yes",
            "--approval-token",
            "~/.local/state/uaa/install-approval.json",
            "--receipt",
            "~/.local/state/uaa/openwebui-receipt.json",
        ]
    )

    assert args.command == "setup"
    assert args.setup_action == "install"
    assert args.target == "openwebui"
    assert args.yes is True
    assert args.approval_token == "~/.local/state/uaa/install-approval.json"
    assert args.receipt == "~/.local/state/uaa/openwebui-receipt.json"


def _stable_report(setup: Any) -> Any:
    return setup.SetupReport(
        mode="local-llama",
        system_summary={"os": "test", "architecture": "test", "python": "3.11.0"},
        findings=[
            setup.SetupFinding(
                "python environment",
                "pass",
                "Repo virtual environment is present.",
                "No action needed.",
            )
        ],
        model_id="uaa-llama-cpp-local",
        next_steps=["Run: uaa start"],
        repair_plan=[],
        plan_commands=["./scripts/dev/uaa start"],
        platform_hints=[],
        profile="minimal",
        selected_model_alias="uaa-llama-cpp-local",
    )


def _setup_args(**overrides: Any) -> Any:
    values = {
        "mode": "local-llama",
        "profile": None,
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
        "json": False,
        "setup_action": None,
        "target": None,
        "yes": False,
        "approval_token": None,
        "write_approval_token": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)
