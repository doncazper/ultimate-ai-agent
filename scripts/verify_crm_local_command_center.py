#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority  # noqa: E402
from ultimate_ai_agent.core.authority import (  # noqa: E402
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
)
from ultimate_ai_agent.core.crm import (  # noqa: E402
    CRM_LOCAL_BLOCKED_AUTHORITY_REFS,
    CRM_LOCAL_COMMAND_CENTER_CONTRACT_REF,
    CRM_LOCAL_COMMAND_CENTER_CLI_REFS,
    CRM_LOCAL_COMMAND_CENTER_ROUTE_REFS,
    CRM_LOCAL_MUTATION_CONTRACT_REF,
    CrmLocalMutationRequest,
    CrmLocalStore,
    build_crm_local_command_center_read_model,
    crm_local_mutation_approval_request,
    expected_crm_local_mutation_approval_ref,
)


DOC_REFS = [
    "docs/control_center/UAA_CRM_LOCAL_COMMAND_CENTER_PLAN.md",
    "docs/control_center/UAA_CRM_FEATURE_MINE_FOLLOWUPBOSS_WISEAGENT.md",
    "docs/control_center/CRM_LOCAL_COMMAND_CENTER_M2.md",
    "docs/control_center/authority_graduation_blockers/crm_connector_read_lanes_2026_07_05.md",
    "docs/control_center/authority_graduation_blockers/crm_sends_writes_2026_07_05.md",
    "docs/prompts/crm_local_command_center/unblock_crm_connector_read_lanes.prompt.md",
    "docs/prompts/crm_local_command_center/unblock_crm_sends_writes.prompt.md",
]
CRM_BLOCKER_REQUIRED_FRAGMENTS = {
    "docs/control_center/authority_graduation_blockers/crm_connector_read_lanes_2026_07_05.md": [
        "blocked pending exact authoritylease domain/capability support",
        "exact connector/source scope and named test account scope",
        "the authority model is mode/domain/capability inside an active authoritylease",
    ],
    "docs/control_center/authority_graduation_blockers/crm_sends_writes_2026_07_05.md": [
        "blocked pending exact authoritylease domain/capability support",
        "exact domain/capability definition for one write or send action",
        "validation for the exact capability",
    ],
}
CRM_BLOCKER_FORBIDDEN_FRAGMENTS = {
    "blocked pending exact authority graduation",
    "named test account lane",
    "exact lane definition",
    "validation for the exact lane",
}
READ_PATHS = [
    "/control-center/crm/summary",
    "/control-center/crm/relationships",
    "/control-center/crm/timeline",
    "/control-center/crm/follow-ups",
    "/control-center/crm/pipelines",
    "/control-center/crm/smart-lists",
]
MUTATION_PATH = "/control-center/crm/local-mutations"
DENIED_AUTHORITY_FIELDS = [
    "connector_runtime_enabled",
    "connector_write_enabled",
    "account_sync_enabled",
    "send_enabled",
    "calendar_write_enabled",
    "provider_model_call_enabled",
    "live_web_enabled",
    "browser_runtime_enabled",
    "background_autonomy_enabled",
    "external_crm_write_enabled",
    "production_authority_enabled",
]
DENIED_CONNECTOR_READ_FIELDS = [
    "connector_runtime_enabled",
    "connector_writes_enabled",
    "raw_body_ingestion_enabled",
    "live_connector_read_performed",
    "external_account_auth_enabled",
    "background_polling_enabled",
    "provider_model_call_enabled",
]
FORBIDDEN_OUTPUT_FRAGMENTS = [
    "person@example",
    "private note",
    "api_key",
    "password=",
    "authorization: bearer",
]


def _fail(message: str) -> None:
    raise SystemExit(f"CRM local command center verifier failed: {message}")


def _read(rel_path: str) -> str:
    path = ROOT / rel_path
    if not path.exists():
        _fail(f"missing required file: {rel_path}")
    return path.read_text(encoding="utf-8")


def _load_json(rel_path: str) -> dict:
    return json.loads(_read(rel_path))


def _route_index() -> dict[tuple[str, str], object]:
    return {(route.method, route.path): route for route in build_api_manifest(app).routes}


def _assert_read_model() -> None:
    crm = build_crm_local_command_center_read_model()
    payload = crm.model_dump(mode="json")
    serialized = crm.model_dump_json()

    if crm.contract_ref != CRM_LOCAL_COMMAND_CENTER_CONTRACT_REF:
        _fail("contract ref drifted")
    if crm.backend_owned is not True or crm.safe_refs_only is not True:
        _fail("CRM read model must be backend-owned and safe-ref-only")
    if payload["raw_contact_details_included"] is not False:
        _fail("CRM read model exposed raw contact posture")
    if payload["raw_message_bodies_included"] is not False:
        _fail("CRM read model exposed raw body posture")
    if payload["raw_paths_included"] is not False:
        _fail("CRM read model exposed raw path posture")
    if payload["provider_payloads_included"] is not False:
        _fail("CRM read model exposed provider payload posture")
    if set(CRM_LOCAL_COMMAND_CENTER_ROUTE_REFS) - set(crm.route_refs):
        _fail("CRM route refs drifted")
    if set(CRM_LOCAL_COMMAND_CENTER_CLI_REFS) - set(crm.cli_refs):
        _fail("CRM CLI refs drifted")
    if len(crm.smart_lists) < 10 or len(crm.reports) < 9:
        _fail("CRM read model is missing smart-list or report coverage")
    for field in DENIED_AUTHORITY_FIELDS:
        if getattr(crm.authority_posture, field) is not False:
            _fail(f"authority field unexpectedly enabled: {field}")
    for ref in CRM_LOCAL_BLOCKED_AUTHORITY_REFS:
        if ref not in crm.authority_posture.blocked_authority_refs:
            _fail(f"blocked authority ref missing: {ref}")
    connector = crm.connector_read_lanes
    if connector.readiness_status != "blocked_missing_exact_authority":
        _fail(
            "CRM connector read readiness must stay blocked without implemented AuthorityLease scope"
        )
    if connector.disabled_by_default is not True:
        _fail("CRM connector read lane must be disabled by default")
    if connector.cli_inspection_ref not in crm.cli_refs:
        _fail("CRM connector read CLI parity ref missing")
    if len(connector.missing_prerequisite_refs) < 5:
        _fail("CRM connector read lane is missing prerequisite refs")
    if len(connector.promotion_path_refs) < 5:
        _fail("CRM connector read lane is missing promotion path refs")
    for field in DENIED_CONNECTOR_READ_FIELDS:
        if getattr(connector, field) is not False:
            _fail(f"connector read field unexpectedly enabled: {field}")
    lowered = serialized.lower()
    for fragment in FORBIDDEN_OUTPUT_FRAGMENTS:
        if fragment in lowered:
            _fail(f"forbidden raw output fragment leaked: {fragment}")


def _assert_cli() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/dev/uaa_crm.py"),
                "inspect-connector-read-lanes",
                "--state-dir",
                str(Path(tmp) / "crm"),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    payload = json.loads(result.stdout)
    connector = payload["connector_read_lanes"]
    if connector["readiness_status"] != "blocked_missing_exact_authority":
        _fail("CRM connector read CLI readiness status drifted")
    for field in DENIED_CONNECTOR_READ_FIELDS:
        if connector[field] is not False:
            _fail(f"CRM connector read CLI enabled denied field: {field}")


def _assert_local_mutation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = CrmLocalStore(
            Path(tmp),
            active_authority_leases=[
                AuthorityLease(
                    lease_ref="authority-lease-ref:crm-verifier-contacts-write",
                    mode=TrustMode.ask_before_changes,
                    domains={
                        AuthorityDomain.contacts: [AuthorityCapability.write],
                    },
                    safe_summary=(
                        "Verifier lease grants Contacts write for local CRM mutation."
                    ),
                )
            ],
        )
        target_ref = "follow-up-ref:crm-local:alpha:due"
        idempotency_ref = "idempotency-ref:crm-verifier-local-001"
        approval_ref = expected_crm_local_mutation_approval_ref(
            target_ref=target_ref,
            idempotency_ref=idempotency_ref,
        )
        request = CrmLocalMutationRequest(
            mutation_kind="mark_follow_up_complete",
            target_ref=target_ref,
            approval_ref=approval_ref,
        )
        approval_request = crm_local_mutation_approval_request(
            request=request,
            idempotency_ref=idempotency_ref,
        )
        authority = LocalApprovalAuthority()
        authority.create_request(approval_request)
        authority.grant(
            approval_request.approval_request_id,
            approved_by_actor_id=request.actor_context.actor_id,
            approval_ref=approval_ref,
        )
        receipt = store.record_local_mutation(
            request=request,
            idempotency_ref=idempotency_ref,
            approval_authority=authority,
        )
        if receipt.contract_ref != CRM_LOCAL_MUTATION_CONTRACT_REF:
            _fail("local mutation contract ref drifted")
        if receipt.approval_status != "approved":
            _fail("local mutation receipt was not exact-approved")
        if receipt.authority_decision_outcome != "ask":
            _fail("local mutation receipt did not prove Contacts write authority")
        if receipt.authority_domain_ref != "authority-domain-ref:contacts":
            _fail("local mutation authority domain drifted")
        if receipt.authority_capability_ref != "authority-capability-ref:write":
            _fail("local mutation authority capability drifted")
        if receipt.local_mutation_performed is not True:
            _fail("local mutation receipt did not record local mutation")
        denied = [
            receipt.connector_write_performed,
            receipt.send_performed,
            receipt.calendar_write_performed,
            receipt.account_sync_performed,
            receipt.external_crm_write_performed,
            receipt.provider_model_call_performed,
            receipt.browser_automation_performed,
            receipt.raw_content_stored,
        ]
        if any(denied):
            _fail("local mutation receipt performed denied external authority")
        replay = store.record_local_mutation(
            request=request,
            idempotency_ref=idempotency_ref,
            approval_authority=authority,
        )
        if replay.receipt_ref != receipt.receipt_ref or replay.replayed is not True:
            _fail("local mutation idempotent replay failed")


def _assert_routes() -> None:
    routes = _route_index()
    openapi_paths = app.openapi()["paths"]
    for path in READ_PATHS:
        key = ("GET", path)
        route = routes.get(key)
        if route is None:
            _fail(f"missing CRM read route: {path}")
        if route.side_effect_class != "local_dev_workspace_only":
            _fail(f"CRM read route side-effect class drifted: {path}")
        if route.route_classification != "local_readonly":
            _fail(f"CRM read route classification drifted: {path}")
        if path not in openapi_paths or "get" not in openapi_paths[path]:
            _fail(f"CRM read route missing from OpenAPI: {path}")
    mutation = routes.get(("POST", MUTATION_PATH))
    if mutation is None:
        _fail("missing CRM local mutation route")
    if mutation.side_effect_class != "local_dev_workspace_only":
        _fail("CRM mutation side-effect class drifted")
    if mutation.route_classification != "mutating_requires_authority":
        _fail("CRM mutation classification drifted")
    if getattr(mutation, "idempotency_required", False) is not True:
        _fail("CRM mutation must require idempotency")
    if MUTATION_PATH not in openapi_paths or "post" not in openapi_paths[MUTATION_PATH]:
        _fail("CRM mutation route missing from OpenAPI")


def _assert_docs() -> None:
    for rel_path in DOC_REFS:
        text = " ".join(_read(rel_path).lower().split())
        if "production authority" not in text:
            _fail(f"{rel_path} missing production authority boundary")
        if rel_path.startswith("docs/control_center/CRM_") or rel_path.startswith(
            "docs/control_center/UAA_CRM_"
        ):
            for fragment in [
                CRM_LOCAL_COMMAND_CENTER_CONTRACT_REF,
                "no live web fetching",
                "connector runtime",
            ]:
                if fragment.lower() not in text:
                    _fail(f"{rel_path} missing fragment: {fragment}")
        if "unblock_crm" in rel_path or "authority_graduation_blockers" in rel_path:
            if "blocked" not in text and "do not add" not in text:
                _fail(f"{rel_path} missing blocked/unblock authority language")
        for fragment in CRM_BLOCKER_REQUIRED_FRAGMENTS.get(rel_path, []):
            if fragment not in text:
                _fail(f"{rel_path} missing AuthorityLease blocker fragment: {fragment}")
        if rel_path in CRM_BLOCKER_REQUIRED_FRAGMENTS:
            for fragment in CRM_BLOCKER_FORBIDDEN_FRAGMENTS:
                if fragment in text:
                    _fail(f"{rel_path} contains stale authority wording: {fragment}")


def _assert_manifests() -> None:
    route_status = _load_json("docs/control_center/route_status_manifest.json")
    release_surface = _load_json("docs/control_center/release_surface_manifest.json")
    crm_surface = next(
        item for item in route_status["surfaces"] if item["surface"] == "CRM"
    )
    if crm_surface["release_status"] != "partial_backend_not_product_ready":
        _fail("route status CRM release status drifted")
    route_paths = {route["path"] for route in crm_surface["current_backend_routes"]}
    if set(READ_PATHS + [MUTATION_PATH]) - route_paths:
        _fail("route status CRM backend routes missing")
    release_route = next(
        item for item in release_surface["routes"] if item["path"] == "/crm"
    )
    if release_route["status"] != "partial":
        _fail("release surface CRM status drifted")
    if release_route["route_classification"] != "local_sensitive":
        _fail("release surface CRM route classification drifted")
    if "connector_runtime" not in release_route["blocked_capabilities"]:
        _fail("release surface CRM missing connector blocker")


def main() -> int:
    original_state_dir = os.environ.get("UAA_CRM_STATE_DIR")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["UAA_CRM_STATE_DIR"] = str(Path(tmp) / "crm")
            _assert_read_model()
            _assert_cli()
            _assert_local_mutation()
            _assert_routes()
            _assert_docs()
            _assert_manifests()
    finally:
        if original_state_dir is None:
            os.environ.pop("UAA_CRM_STATE_DIR", None)
        else:
            os.environ["UAA_CRM_STATE_DIR"] = original_state_dir
    print("CRM local command center verifier passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
