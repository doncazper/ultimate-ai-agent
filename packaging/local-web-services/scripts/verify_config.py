#!/usr/bin/env python3
"""Verify the pinned local-web-service package without exposing local state."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys


DIGEST = re.compile(r"^[a-z0-9./-]+(?:@[a-z0-9./:-]+)?@sha256:[0-9a-f]{64}$")
EXPECTED_PUBLISHED = {"firecrawl-api", "searxng"}
DISALLOWED = (
    "0.0.0.0:${UAA_",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OLLAMA_BASE_URL",
    "PROXY_PASSWORD",
    "SELF_HOSTED_WEBHOOK_URL",
    "FIRECRAWL_API_KEY",
)
SEARXNG_SECRET_PLACEHOLDER = "__UAA_SEARXNG_SECRET__"


def _root() -> Path:
    return Path(__file__).resolve().parents[3]


def verify_static(package: Path) -> list[str]:
    failures: list[str] = []
    lock = json.loads((package / "provider_lock.json").read_text(encoding="utf-8"))
    providers = lock.get("providers")
    if not isinstance(providers, dict) or not providers:
        failures.append("provider lock must contain providers")
    else:
        for provider_ref, record in providers.items():
            image = record.get("image") if isinstance(record, dict) else None
            if not isinstance(image, str) or not DIGEST.fullmatch(image):
                failures.append(f"provider image is not digest-pinned: {provider_ref}")

    compose = (package / "compose.yaml").read_text(encoding="utf-8")
    for fragment in DISALLOWED:
        if fragment in compose:
            failures.append(f"compose contains disabled configuration ref: {fragment}")
    if compose.count('"127.0.0.1:${UAA_') != 2:
        failures.append("compose must publish exactly two loopback adapter ports")
    if "POSTGRES_PASSWORD_FILE" not in compose or "/run/secrets/" not in compose:
        failures.append("compose must inject generated secrets by file")
    if "SEARXNG_ENDPOINT: http://searxng:8080" not in compose:
        failures.append("Firecrawl must use the internal SearXNG endpoint")
    return failures


def verify_local_state(root: Path) -> list[str]:
    failures: list[str] = []
    state = root / ".uaa" / "local-web-services"
    for filename in ("firecrawl_postgres_password", "firecrawl_bull_auth_key"):
        path = state / filename
        if not path.is_file() or path.is_symlink():
            failures.append(f"generated secret is missing or unsafe: {filename}")
            continue
        if len(path.read_bytes().strip()) < 32:
            failures.append(f"generated secret is unexpectedly short: {filename}")
        if os.stat(path).st_mode & 0o077:
            failures.append(f"generated secret permissions are too broad: {filename}")

    settings_path = state / "searxng" / "settings.yml"
    if not settings_path.is_file() or settings_path.is_symlink():
        failures.append("generated SearXNG settings are missing or unsafe")
        return failures
    settings = settings_path.read_text(encoding="utf-8")
    for fragment in (
        "- json",
        "max_page: 1",
        "public_instance: false",
        "limiter: true",
    ):
        if fragment not in settings:
            failures.append(f"generated SearXNG settings are missing: {fragment}")
    if SEARXNG_SECRET_PLACEHOLDER in settings:
        failures.append("generated SearXNG secret placeholder was not replaced")
    if os.stat(settings_path).st_mode & 0o077:
        failures.append("generated SearXNG settings permissions are too broad")
    return failures


def verify_rendered(package: Path) -> list[str]:
    command = [
        "docker",
        "compose",
        "-f",
        str(package / "compose.yaml"),
        "config",
        "--format",
        "json",
    ]
    try:
        result = subprocess.run(
            command, check=False, capture_output=True, text=True, timeout=30
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ["Docker Compose config validation unavailable"]
    if result.returncode != 0:
        return ["Docker Compose config validation failed"]
    try:
        rendered = json.loads(result.stdout)
    except json.JSONDecodeError:
        return ["Docker Compose did not return valid rendered JSON"]
    services = rendered.get("services", {})
    published = {name for name, service in services.items() if service.get("ports")}
    if published != EXPECTED_PUBLISHED:
        return ["rendered Compose publishes an unexpected service"]
    for service_name in published:
        for port in services[service_name]["ports"]:
            if port.get("host_ip") != "127.0.0.1":
                return ["rendered Compose contains a non-loopback published port"]
    return []


def main() -> int:
    root = _root()
    package = root / "packaging" / "local-web-services"
    failures = (
        verify_static(package) + verify_local_state(root) + verify_rendered(package)
    )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("local web service configuration verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
