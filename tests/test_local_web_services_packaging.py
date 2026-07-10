from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import stat
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packaging" / "local-web-services"


def _load_setup_module():
    path = PACKAGE / "scripts" / "setup_local_state.py"
    spec = importlib.util.spec_from_file_location("setup_local_web_services", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_provider_lock_pins_all_images_and_records_capability_limits() -> None:
    lock = json.loads((PACKAGE / "provider_lock.json").read_text(encoding="utf-8"))

    assert lock["schema_version"] == "uaa-local-web-services-provider-lock.v1"
    assert lock["providers"]
    for provider in lock["providers"].values():
        image = provider["image"]
        assert "@sha256:" in image
        assert not image.endswith(":latest")
    assert lock["capability_limits"]["searxng"] == ["bounded-json-search"]
    assert lock["capability_limits"]["firecrawl_self_hosted"] == [
        "one-page-markdown-extraction"
    ]
    assert "firecrawl-browser" in lock["explicitly_disabled"]


def test_compose_publishes_only_adapter_apis_on_loopback() -> None:
    if shutil.which("docker") is None:
        pytest.skip("Docker is unavailable")
    result = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(PACKAGE / "compose.yaml"),
            "config",
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    rendered = json.loads(result.stdout)

    published = {
        name: service["ports"]
        for name, service in rendered["services"].items()
        if service.get("ports")
    }
    assert set(published) == {"firecrawl-api", "searxng"}
    assert all(
        port["host_ip"] == "127.0.0.1" for ports in published.values() for port in ports
    )
    assert rendered["networks"]["firecrawl-backend"]["internal"] is True
    assert rendered["networks"]["search-backend"]["internal"] is True
    assert "firecrawl-postgres-data" in rendered["volumes"]


def test_compose_uses_file_secrets_and_omits_cloud_model_and_proxy_secrets() -> None:
    compose = (PACKAGE / "compose.yaml").read_text(encoding="utf-8")

    assert "POSTGRES_PASSWORD_FILE" in compose
    assert "firecrawl_postgres_password" in compose
    assert "firecrawl_bull_auth_key" in compose
    assert "SEARXNG_ENDPOINT: http://searxng:8080" in compose
    for forbidden in (
        "FIRECRAWL_API_KEY",
        "OPENAI_API_KEY",
        "OLLAMA_BASE_URL",
        "PROXY_PASSWORD",
        "SELF_HOSTED_WEBHOOK_URL",
    ):
        assert forbidden not in compose


def test_searxng_configuration_enables_bounded_json_and_private_limiter() -> None:
    settings = (PACKAGE / "searxng" / "settings.yml.template").read_text(
        encoding="utf-8"
    )
    limiter = (PACKAGE / "searxng" / "limiter.toml").read_text(encoding="utf-8")

    assert "- json" in settings
    assert "max_page: 1" in settings
    assert "public_instance: false" in settings
    assert "limiter: true" in settings
    assert settings.count("__UAA_SEARXNG_SECRET__") == 1
    assert "pass_searxng_org = false" in limiter


def test_setup_generates_mode_600_secrets_without_overwriting(tmp_path: Path) -> None:
    module = _load_setup_module()
    state_dir = tmp_path / "state"
    template = PACKAGE / "searxng" / "settings.yml.template"

    first = module.setup_local_state(state_dir=state_dir, template=template)
    postgres_before = (state_dir / "firecrawl_postgres_password").read_text(
        encoding="utf-8"
    )
    second = module.setup_local_state(state_dir=state_dir, template=template)

    assert first == (3, 0)
    assert second == (0, 3)
    assert (state_dir / "firecrawl_postgres_password").read_text(
        encoding="utf-8"
    ) == postgres_before
    for path in (
        state_dir / "firecrawl_postgres_password",
        state_dir / "firecrawl_bull_auth_key",
        state_dir / "searxng" / "settings.yml",
    ):
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert path.read_text(encoding="utf-8").strip()
    generated_settings = (state_dir / "searxng" / "settings.yml").read_text(
        encoding="utf-8"
    )
    assert "__UAA_SEARXNG_SECRET__" not in generated_settings


def test_setup_cli_output_is_safe(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(PACKAGE / "scripts" / "setup_local_state.py"),
            "--state-dir",
            str(tmp_path / "state"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "credential_values_displayed=false" in result.stdout
    assert str(tmp_path) not in result.stdout
    assert result.stderr == ""
