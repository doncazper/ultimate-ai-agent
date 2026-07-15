from __future__ import annotations

import errno
import json
import threading
import time
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.communications.matrix_session import (
    MATRIX_DISCOVERY_PENDING_FRESHNESS_REF,
    MATRIX_DISCOVERY_PENDING_OBSERVATION_REF,
    MatrixSessionCommand,
    MatrixSessionOperation,
    MatrixSessionTransientInput,
    execute_matrix_session_command,
    issue_exact_matrix_session_lease,
    matrix_discovery_freshness_ref,
    matrix_homeserver_observation_ref,
    matrix_homeserver_ref,
    matrix_session_request_fingerprint_ref,
)
from ultimate_ai_agent.core.time import utc_now


ROOT = Path(__file__).resolve().parents[1]
HARNESS_URL = "http://127.0.0.1:18008"
_HARNESS_PORT_WAIT_SECONDS = 60


def _bind_harness_server() -> ThreadingHTTPServer:
    """Own the exact harness port without a cross-account lock artifact."""

    deadline = time.monotonic() + _HARNESS_PORT_WAIT_SECONDS
    while True:
        try:
            return ThreadingHTTPServer(("127.0.0.1", 18008), _MatrixFixtureHandler)
        except OSError as exc:
            if exc.errno != errno.EADDRINUSE:
                raise
            if time.monotonic() >= deadline:
                raise TimeoutError("MATRIX_TEST_HARNESS_PORT_BUSY") from exc
            time.sleep(0.05)


class _MatrixFixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        payloads = {
            "/.well-known/matrix/client": {"m.homeserver": {"base_url": HARNESS_URL}},
            "/_matrix/client/versions": {"versions": ["v1.11"]},
            "/_matrix/client/v3/login": {
                "flows": [
                    {"type": "m.login.password"},
                    {"type": "m.login.sso"},
                ]
            },
        }
        payload = payloads.get(self.path)
        if payload is None:
            self.send_response(404)
            self.send_header("content-length", "0")
            self.end_headers()
            return
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, _format: str, *_args: object) -> None:
        return


def _command(operation: MatrixSessionOperation) -> MatrixSessionCommand:
    suffix = operation.value.replace("_", "-")
    observation_ref = matrix_homeserver_observation_ref(HARNESS_URL)
    request_created_at = utc_now()
    values: dict[str, object] = {
        "operation": operation,
        "request_ref": f"request-ref:matrix-node-integration:{suffix}",
        "task_ref": f"task-ref:matrix-node-integration:{suffix}",
        "mission_ref": "mission-ref:matrix-node-integration",
        "run_ref": f"run-ref:matrix-node-integration:{suffix}",
        "dispatch_ref": f"dispatch-ref:matrix-node-integration:{suffix}",
        "idempotency_ref": f"idempotency-ref:matrix-node-integration:{suffix}",
        "lease_ref": f"authority-lease-ref:matrix-node-integration:{suffix}",
        "homeserver_ref": matrix_homeserver_ref(HARNESS_URL),
        "endpoint_class_ref": "endpoint-class-ref:matrix:local-harness",
        "discovery_observation_ref": (
            MATRIX_DISCOVERY_PENDING_OBSERVATION_REF
            if operation == MatrixSessionOperation.discovery_read
            else observation_ref
        ),
        "discovery_freshness_ref": (
            MATRIX_DISCOVERY_PENDING_FRESHNESS_REF
            if operation == MatrixSessionOperation.discovery_read
            else matrix_discovery_freshness_ref(observation_ref)
        ),
        "readiness_ref": "readiness-ref:matrix-session:node-integration",
        "request_created_at": request_created_at,
        "start_deadline": request_created_at + timedelta(minutes=2),
    }
    values["request_fingerprint_ref"] = matrix_session_request_fingerprint_ref(**values)
    return MatrixSessionCommand(**values)


def test_dispatcher_executes_real_node_discovery_and_auth_method_reads(
    tmp_path: Path,
) -> None:
    server = _bind_harness_server()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        state = tmp_path / "authority"
        store = AuthorityLeaseStore(state)
        discovery = _command(MatrixSessionOperation.discovery_read)
        issue_exact_matrix_session_lease(discovery, store=store, confirmed=False)
        discovery_result = execute_matrix_session_command(
            discovery,
            repo_root=ROOT,
            authority_state_dir=state,
            transient_input=MatrixSessionTransientInput(discovery_origin=HARNESS_URL),
            lease_store=store,
        )
        assert discovery_result.receipt.status == "succeeded"
        assert discovery_result.adapter_result is not None
        assert discovery_result.adapter_result.safe_output[
            "homeserver_observation_ref"
        ] == matrix_homeserver_observation_ref(HARNESS_URL)

        auth_methods = _command(MatrixSessionOperation.auth_methods_read)
        issue_exact_matrix_session_lease(auth_methods, store=store, confirmed=False)
        auth_result = execute_matrix_session_command(
            auth_methods,
            repo_root=ROOT,
            authority_state_dir=state,
            transient_input=MatrixSessionTransientInput(endpoint_url=HARNESS_URL),
            lease_store=store,
        )
        assert auth_result.receipt.status == "succeeded", (
            auth_result.receipt.model_dump()
        )
        assert auth_result.adapter_result is not None
        assert auth_result.adapter_result.safe_output["capabilities"] == {
            "credential_auth": True,
            "browser_sso": True,
            "oauth": False,
        }
        assert auth_result.receipt.raw_provider_payload_included is False
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
