#!/usr/bin/env python3
from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol

if __package__ in {None, ""}:
    ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ROOT))
    from scripts.verification.api_routes import route_index
else:
    from .api_routes import route_index


@dataclass(frozen=True)
class ApiVerifierSpec:
    milestone_id: str
    module_name: str


@dataclass(frozen=True)
class ApiVerifierContext:
    app: Any
    manifest: dict[str, Any]
    routes_by_key: dict[tuple[str, str], dict[str, Any]]
    client: Any
    https_client: Any


class ApiVerifierModule(Protocol):
    SUCCESS_MESSAGE: str

    def verify(self, context: ApiVerifierContext | None = None) -> list[str]:
        ...


API_VERIFIER_SPECS = (
    ApiVerifierSpec("UAA-P1-080", "scripts.verify_uaa_p1_080_api_route_classification"),
    ApiVerifierSpec("UAA-P1-081", "scripts.verify_uaa_p1_081_fastapi_security_headers"),
    ApiVerifierSpec("UAA-P1-082", "scripts.verify_uaa_p1_082_loopback_cors"),
    ApiVerifierSpec("UAA-P1-083", "scripts.verify_uaa_p1_083_local_auth_gate"),
    ApiVerifierSpec("UAA-P1-084", "scripts.verify_uaa_p1_084_mutating_route_idempotency"),
    ApiVerifierSpec("UAA-P1-085", "scripts.verify_uaa_p1_085_targeted_rate_limits"),
    ApiVerifierSpec("UAA-P1-086", "scripts.verify_uaa_p1_086_api_boundary_enforcement_tests"),
)


@lru_cache(maxsize=1)
def default_api_verifier_context() -> ApiVerifierContext:
    from fastapi.testclient import TestClient

    from ultimate_ai_agent.api.app import app
    from ultimate_ai_agent.api.manifest import build_api_manifest

    manifest = build_api_manifest(app).model_dump(mode="json")
    return ApiVerifierContext(
        app=app,
        manifest=manifest,
        routes_by_key=route_index(manifest),
        client=TestClient(app),
        https_client=TestClient(app, base_url="https://testserver"),
    )


def _iter_verifiers() -> list[tuple[ApiVerifierSpec, ApiVerifierModule]]:
    return [
        (spec, importlib.import_module(spec.module_name))
        for spec in API_VERIFIER_SPECS
    ]


def run_api_verifier_lane(context: ApiVerifierContext | None = None) -> int:
    context = context or default_api_verifier_context()
    for spec, module in _iter_verifiers():
        verify = getattr(module, "verify", None)
        if not callable(verify):
            print(f"ERROR: {spec.milestone_id} verifier module missing verify(context)")
            return 1
        failures = verify(context)
        if failures:
            for failure in failures:
                print(f"ERROR: {failure}")
            return 1
        print(module.SUCCESS_MESSAGE)
    return 0


def main() -> int:
    return run_api_verifier_lane()


if __name__ == "__main__":
    raise SystemExit(main())
