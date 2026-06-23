from __future__ import annotations

from copy import deepcopy

from scripts.verification.repo import load_json
from scripts.verify_founder_loop_v1 import (
    PROOF_SCRIPT,
    RELEASE_SURFACE_PATH,
    ROUTE_STATUS_PATH,
    verify,
)


def test_founder_loop_v1_proof_verifier_passes_current_repo() -> None:
    assert verify() == []


def test_founder_loop_v1_proof_verifier_flags_ship_without_proof() -> None:
    release_surface = deepcopy(load_json(RELEASE_SURFACE_PATH))
    actions = next(route for route in release_surface["routes"] if route["path"] == "/actions")
    actions["proof_lanes"] = [
        proof for proof in actions["proof_lanes"] if proof != PROOF_SCRIPT
    ]

    failures = verify(
        release_surface=release_surface,
        route_status=load_json(ROUTE_STATUS_PATH),
        check_behavior=False,
        check_files=False,
    )

    assert any("/actions missing FCC-V1-007 proof lane" in failure for failure in failures)


def test_founder_loop_v1_proof_verifier_flags_blocked_ship_route() -> None:
    release_surface = deepcopy(load_json(RELEASE_SURFACE_PATH))
    memory = next(route for route in release_surface["routes"] if route["path"] == "/memory")
    memory["blocked_capabilities"] = ["memory_context_injection"]

    failures = verify(
        release_surface=release_surface,
        route_status=load_json(ROUTE_STATUS_PATH),
        check_behavior=False,
        check_files=False,
    )

    assert any("/memory ship route cannot list blocked capabilities" in failure for failure in failures)


def test_founder_loop_v1_proof_verifier_flags_route_status_overclaim() -> None:
    route_status = deepcopy(load_json(ROUTE_STATUS_PATH))
    settings = next(
        surface
        for surface in route_status["surfaces"]
        if surface["surface"] == "Settings"
    )
    settings["release_status"] = "founder_loop_v1_proofed"

    failures = verify(
        release_surface=load_json(RELEASE_SURFACE_PATH),
        route_status=route_status,
        check_behavior=False,
        check_files=False,
    )

    assert "Settings must remain status-only" in failures
