#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from ultimate_ai_agent.core.build_identity import (  # noqa: E402
    verified_clean_source_commit,
)

ROOT = Path(__file__).resolve().parent.parent
COMPOSE_FILE = ROOT / "packaging" / "local-runtime" / "compose.yaml"
CONTROL_CENTER_ROOT = ROOT / "apps" / "control-center"
STATE_DIR = ROOT / ".uaa" / "local-runtime"
PROOF_DIR = STATE_DIR / "packaging-proof"
LOCAL_SECRET_FILE = STATE_DIR / "uaa_local_runtime_secret"
SUMMARY_PATH = PROOF_DIR / "latest.json"
SCREENSHOT_PATH = PROOF_DIR / "control-center-today.png"
DEFAULT_API_PORT = 8000
DEFAULT_CONTROL_CENTER_PORT = 5173
DEFAULT_TIMEOUT_SECONDS = 180


@dataclass(frozen=True)
class ProofStep:
    step_id: str
    status: str
    safe_evidence_ref: str
    reason_codes: tuple[str, ...] = ()

    def to_summary(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "status": self.status,
            "safe_evidence_ref": self.safe_evidence_ref,
            "raw_log_included": False,
            "reason_codes": list(self.reason_codes),
        }


def run_packaging_proof(*, timeout_seconds: int) -> int:
    steps: list[ProofStep] = []
    route_count: int | None = None
    screenshot_hash: str | None = None
    status = "failed"
    _prepare_local_state()
    api_port = _select_available_port(DEFAULT_API_PORT)
    control_center_port = _select_available_port(
        DEFAULT_CONTROL_CENTER_PORT,
        reserved_ports={api_port},
    )
    compose_env = {
        "UAA_LOCAL_RUNTIME_API_PORT": str(api_port),
        "UAA_LOCAL_RUNTIME_CONTROL_CENTER_PORT": str(control_center_port),
        "UAA_BUILD_COMMIT": verified_clean_source_commit(ROOT),
    }
    api_health_url = f"http://127.0.0.1:{api_port}/health"
    api_manifest_url = f"http://127.0.0.1:{api_port}/api/manifest"
    control_center_url = f"http://127.0.0.1:{control_center_port}/today"

    try:
        _run_checked(
            [
                "docker",
                "compose",
                "-f",
                str(COMPOSE_FILE),
                "up",
                "--build",
                "--detach",
            ],
            timeout=timeout_seconds,
            env_overrides=compose_env,
        )
        steps.append(_passed("compose-build"))

        _wait_for_url(api_health_url, timeout_seconds=timeout_seconds)
        steps.append(_passed("api-health"))

        manifest = _wait_for_json(api_manifest_url, timeout_seconds=timeout_seconds)
        route_count = _extract_route_count(manifest)
        if route_count <= 0:
            raise RuntimeError("route manifest returned no route entries")
        steps.append(_passed("route-manifest-check"))

        control_center_html = _wait_for_text(control_center_url, timeout_seconds=timeout_seconds)
        if "Ultimate AI Agent Control Center" not in control_center_html and 'id="root"' not in control_center_html:
            raise RuntimeError("control center did not return the expected shell")
        steps.append(_passed("control-center-load"))

        _capture_screenshot(control_center_url)
        screenshot_hash = "sha256:" + hashlib.sha256(SCREENSHOT_PATH.read_bytes()).hexdigest()
        steps.append(_passed("screenshot-capture"))
        status = "passed"
    except Exception as exc:  # noqa: BLE001 - keep evidence safe and concise.
        steps.append(
            ProofStep(
                step_id="packaging-proof",
                status="failed",
                safe_evidence_ref="packaging-proof:failure",
                reason_codes=(_safe_reason(exc),),
            )
        )
    finally:
        shutdown_status = _compose_down(timeout_seconds=timeout_seconds, env_overrides=compose_env)
        steps.append(shutdown_status)
        _write_summary(
            status=status if shutdown_status.status == "passed" else "failed",
            steps=steps,
            route_count=route_count,
            screenshot_hash=screenshot_hash,
        )

    print(
        json.dumps(
            {
                "status": status if steps[-1].status == "passed" else "failed",
                "proof_ref": "packaging-proof:latest",
                "summary_ref": "packaging-proof-summary:latest",
                "step_count": len(steps),
            },
            sort_keys=True,
        )
    )
    return 0 if status == "passed" and steps[-1].status == "passed" else 1


def _prepare_local_state() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    PROOF_DIR.mkdir(parents=True, exist_ok=True)
    if not LOCAL_SECRET_FILE.exists():
        LOCAL_SECRET_FILE.write_text(secrets.token_urlsafe(48) + "\n", encoding="utf-8")
    LOCAL_SECRET_FILE.chmod(0o600)


def _run_checked(
    args: list[str],
    *,
    timeout: int,
    cwd: Path = ROOT,
    env_overrides: dict[str, str] | None = None,
) -> None:
    env = {
        **os.environ,
        "COMPOSE_PROJECT_NAME": "uaa_packaging_proof",
        **(env_overrides or {}),
    }
    result = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"command failed: {args[0]}")


def _compose_down(*, timeout_seconds: int, env_overrides: dict[str, str]) -> ProofStep:
    try:
        _run_checked(
            [
                "docker",
                "compose",
                "-f",
                str(COMPOSE_FILE),
                "down",
                "--remove-orphans",
            ],
            timeout=timeout_seconds,
            env_overrides=env_overrides,
        )
    except Exception as exc:  # noqa: BLE001 - safe reason only.
        return ProofStep(
            step_id="clean-shutdown",
            status="failed",
            safe_evidence_ref="packaging-proof:clean-shutdown",
            reason_codes=(_safe_reason(exc),),
        )
    return _passed("clean-shutdown")


def _wait_for_json(url: str, *, timeout_seconds: int) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last_error: str | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                return json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            last_error = _safe_reason(exc)
            time.sleep(2)
    raise TimeoutError(last_error or "json endpoint was not ready")


def _wait_for_text(url: str, *, timeout_seconds: int) -> str:
    deadline = time.monotonic() + timeout_seconds
    last_error: str | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                return response.read().decode("utf-8", errors="replace")
        except (OSError, urllib.error.URLError) as exc:
            last_error = _safe_reason(exc)
            time.sleep(2)
    raise TimeoutError(last_error or "text endpoint was not ready")


def _wait_for_url(url: str, *, timeout_seconds: int) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: str | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if 200 <= response.status < 500:
                    return
        except (OSError, urllib.error.URLError) as exc:
            last_error = _safe_reason(exc)
            time.sleep(2)
    raise TimeoutError(last_error or "endpoint was not ready")


def _capture_screenshot(control_center_url: str) -> None:
    if SCREENSHOT_PATH.exists():
        SCREENSHOT_PATH.unlink()
    _run_checked(
        [
            "npx",
            "playwright",
            "screenshot",
            "--full-page",
            "--timeout=15000",
            control_center_url,
            str(SCREENSHOT_PATH),
        ],
        timeout=60,
        cwd=CONTROL_CENTER_ROOT,
    )
    if not SCREENSHOT_PATH.exists() or SCREENSHOT_PATH.stat().st_size == 0:
        raise RuntimeError("screenshot proof was not created")


def _extract_route_count(manifest: dict[str, Any]) -> int:
    routes = manifest.get("routes")
    if isinstance(routes, list):
        return len(routes)
    route_count = manifest.get("route_count")
    if isinstance(route_count, int):
        return route_count
    paths = manifest.get("paths")
    if isinstance(paths, dict):
        return len(paths)
    return 0


def _select_available_port(preferred_port: int, *, reserved_ports: set[int] | None = None) -> int:
    reserved = reserved_ports or set()
    if preferred_port not in reserved and _is_port_available(preferred_port):
        return preferred_port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def _write_summary(
    *,
    status: str,
    steps: list[ProofStep],
    route_count: int | None,
    screenshot_hash: str | None,
) -> None:
    summary = {
        "schema_version": "uaa-local-runtime-packaging-proof-summary.v1",
        "status": status,
        "proof_ref": "packaging-proof:latest",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "scope": "local-loopback-docker-compose-only",
        "distribution_claims_allowed": False,
        "route_manifest": {
            "endpoint_ref": "local-loopback-api-manifest",
            "route_count": route_count,
        },
        "screenshot_proof": {
            "safe_evidence_ref": "packaging-proof:screenshot-capture",
            "artifact_ref": "packaging-proof-artifact:control-center-today",
            "sha256": screenshot_hash,
            "raw_private_screenshot_included": False,
        },
        "steps": [step.to_summary() for step in steps],
        "redactions_applied": [
            "raw_logs_omitted",
            "raw_paths_omitted",
            "credentials_omitted",
            "host_details_omitted",
            "safe_refs_only",
        ],
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _passed(step_id: str) -> ProofStep:
    return ProofStep(
        step_id=step_id,
        status="passed",
        safe_evidence_ref=f"packaging-proof:{step_id}",
    )


def _safe_reason(exc: BaseException) -> str:
    if isinstance(exc, (FileNotFoundError, PermissionError)):
        return exc.__class__.__name__.upper()
    if isinstance(exc, subprocess.TimeoutExpired):
        return "COMMAND_TIMEOUT"
    if isinstance(exc, TimeoutError):
        return "ENDPOINT_TIMEOUT"
    return exc.__class__.__name__.upper()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Maximum seconds to wait for compose launch and endpoint readiness.",
    )
    args = parser.parse_args(argv)
    return run_packaging_proof(timeout_seconds=args.timeout_seconds)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
