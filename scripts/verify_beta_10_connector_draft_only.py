#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.connectors import (
    CONNECTOR_DRAFT_PROPOSAL_BLOCKED_AUTHORITY_REFS,
    CONNECTOR_DRAFT_PROPOSAL_CLI_REF,
    CONNECTOR_DRAFT_PROPOSAL_PROOF_REF,
    ConnectorDraftProposalItem,
    ConnectorDraftProposalReadModel,
    build_connector_draft_proposal_read_model,
)
from ultimate_ai_agent.core.control_center.founder_loop import (
    FounderLoopControlCenterService,
)
from ultimate_ai_agent.core.control_center.trust_authority import (
    build_trust_authority_matrix_read_model,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parent.parent
LANE_DOC = ROOT / "docs/control_center/CONNECTOR_DRAFT_ONLY_PROPOSALS.md"
AUTHORITY_BOARD = ROOT / "docs/control_center/AUTHORITY_GRADUATION_BOARD.md"
RELEASE_SURFACE = ROOT / "docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md"
FRONTEND_ROUTES = ROOT / "docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
CURRENT_BOARD = ROOT / "docs/kanban/current_board.md"
FRONTEND_TEST = ROOT / "apps/control-center/src/App.test.tsx"
LANE_SOURCE = ROOT / "src/ultimate_ai_agent/core/connectors/connector_draft_proposals.py"
PROOF_SOURCE = ROOT / "src/ultimate_ai_agent/core/control_center/proof.py"
SOURCE_READINESS_SOURCE = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"

REQUIRED_DOC_FRAGMENTS = (
    "Full-strength version",
    "Repo-safe beta-10 version",
    "Blocked / needs authority",
    "Exact promotion path",
    "connector send/write/runtime remains blocked",
    "No connector send, write, account sync, OAuth, auth-material collection",
)


def _append_core_failures(failures: list[str]) -> None:
    read_model = build_connector_draft_proposal_read_model()
    if read_model.source != "python_core_connector_draft_proposal_read_model":
        failures.append("connector draft proposal read model source drift")
    if not read_model.backend_owned:
        failures.append("connector draft proposal read model is not backend-owned")
    if read_model.proposal_count != 2:
        failures.append("connector draft proposal count drift")
    for field in (
        "raw_payloads_persisted",
        "connector_runtime_enabled",
        "account_auth_enabled",
        "oauth_enabled",
        "credential_collection_enabled",
        "connector_writes_enabled",
        "connector_sends_enabled",
        "background_sync_enabled",
        "scheduler_enabled",
        "provider_model_calls_enabled",
        "memory_write_enabled",
        "context_injection_enabled",
        "production_authority_enabled",
    ):
        if getattr(read_model, field):
            failures.append(f"read model enables {field}")
    if CONNECTOR_DRAFT_PROPOSAL_PROOF_REF not in read_model.proof_refs:
        failures.append("read model missing connector draft proof ref")
    for ref in CONNECTOR_DRAFT_PROPOSAL_BLOCKED_AUTHORITY_REFS:
        if ref not in read_model.blocked_authority_refs:
            failures.append(f"read model missing blocked authority ref: {ref}")

    storage_record = read_model.storage_record()
    if "credential_collection_enabled" in storage_record:
        failures.append("storage record includes credential collection posture")
    for proposal in storage_record.get("proposals", []):
        if "credential_material_persisted" in proposal:
            failures.append("proposal storage record includes credential material posture")
        if "credential_collection_enabled" in proposal:
            failures.append("proposal storage record includes credential collection posture")

    for proposal in read_model.proposals:
        for field in (
            "approval_required_to_draft",
            "outbound_approval_ref_grants_authority",
            "target_session_ref_grants_authority",
            "raw_payloads_persisted",
            "raw_body_persisted",
            "raw_content_persisted",
            "raw_draft_body_persisted",
            "contact_data_persisted",
            "credential_material_persisted",
            "connector_runtime_enabled",
            "account_auth_enabled",
            "oauth_enabled",
            "credential_collection_enabled",
            "connector_write_enabled",
            "connector_send_enabled",
            "connector_delete_enabled",
            "connector_delivery_worker_enabled",
            "background_sync_enabled",
            "scheduler_enabled",
            "provider_model_calls_enabled",
            "memory_write_enabled",
            "context_injection_enabled",
            "delivery_execution_performed",
            "connector_write_performed",
            "connector_send_performed",
            "account_sync_performed",
            "production_authority_enabled",
        ):
            if getattr(proposal, field):
                failures.append(f"{proposal.proposal_ref} enables {field}")
        if not proposal.approval_required_to_send:
            failures.append(f"{proposal.proposal_ref} does not require send approval")
        if CONNECTOR_DRAFT_PROPOSAL_PROOF_REF not in proposal.proof_refs:
            failures.append(f"{proposal.proposal_ref} missing proof ref")

    for flag_name, flag_value in {
        "connector_send_enabled": True,
        "connector_write_performed": True,
        "oauth_enabled": True,
        "credential_collection_enabled": True,
    }.items():
        try:
            ConnectorDraftProposalItem.model_validate(
                {
                    **read_model.proposals[0].model_dump(mode="json"),
                    flag_name: flag_value,
                }
            )
        except Exception:
            pass
        else:
            failures.append(f"proposal validator accepts authority flag {flag_name}")

    try:
        ConnectorDraftProposalReadModel(
            proposal_count=read_model.proposal_count,
            proposals=read_model.proposals,
            connector_sends_enabled=True,
        )
    except Exception:
        pass
    else:
        failures.append("read model validator accepts connector sends")


def _append_cli_failures(failures: list[str]) -> None:
    result = subprocess.run(
        [sys.executable, "scripts/inspect_connector_draft_proposals.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    if payload.get("status") != "draft_proposals_ready_no_send_write":
        failures.append("CLI connector draft status drift")
    if payload.get("real_connector_runtime_performed") is not False:
        failures.append("CLI claims real connector runtime")
    if payload.get("connector_send_or_write_performed") is not False:
        failures.append("CLI claims connector send/write")
    for field in (
        "connector_runtime_enabled",
        "connector_writes_enabled",
        "connector_sends_enabled",
        "provider_model_calls_enabled",
        "memory_write_enabled",
        "context_injection_enabled",
        "production_authority_enabled",
    ):
        if payload.get(field) is not False:
            failures.append(f"CLI enables {field}")
    output_text = result.stdout.lower()
    for forbidden in ("founder@example", "api" + "_key", "access-token", "cookie"):
        if forbidden in output_text:
            failures.append(f"CLI output includes forbidden material: {forbidden}")


def _append_control_center_failures(failures: list[str]) -> None:
    with TemporaryDirectory() as directory:
        service = FounderLoopControlCenterService(
            FounderLoopRepository(Path(directory) / "founder-loop.sqlite3")
        )
        source_readiness = service.source_readiness()
        proposals = source_readiness.get("connector_draft_proposals", {})
        if proposals.get("schema_version") != "connector_draft_proposal_read_model.v1":
            failures.append("Source Readiness connector draft proposal schema missing")
        if proposals.get("source") != "python_core_connector_draft_proposal_read_model":
            failures.append("Source Readiness connector draft proposal source drift")
        if proposals.get("backend_owned") is not True:
            failures.append("Source Readiness connector draft proposals not backend-owned")
        if proposals.get("connector_writes_enabled") is not False:
            failures.append("Source Readiness connector writes enabled")
        if proposals.get("connector_sends_enabled") is not False:
            failures.append("Source Readiness connector sends enabled")
        if proposals.get("credential_collection_enabled") is not None:
            failures.append("Source Readiness stores credential collection posture")
        if source_readiness.get("connector_draft_proposals_enabled") is not True:
            failures.append("Source Readiness does not expose draft proposal refs")

        proof_detail = service.proof_detail(CONNECTOR_DRAFT_PROPOSAL_PROOF_REF)
        record = proof_detail.get("record", {})
        if record.get("proof_kind") != "connector_draft_proposal":
            failures.append("Proof Detail missing connector draft proposal kind")
        if record.get("status") != "draft_proposals_ready_no_send_write":
            failures.append("Proof Detail connector draft proposal status drift")
        if "GET /control-center/sources/readiness" not in record.get(
            "backend_route_refs", []
        ):
            failures.append("Proof Detail missing Source Readiness backend route ref")
        for ref in (
            "blocked-state:connector-draft-only:no-connector-send",
            "blocked-state:connector-draft-only:no-connector-write",
            "blocked-state:connector-draft-only:no-oauth",
        ):
            if ref not in record.get("blocked_authority_refs", []):
                failures.append(f"Proof Detail missing blocked ref: {ref}")
        for field in (
            "connector_send_enabled",
            "connector_write_enabled",
            "provider_model_call_enabled",
            "background_autonomy_enabled",
            "production_authority_enabled",
            "raw_content_included",
        ):
            if record.get(field) is not False:
                failures.append(f"Proof Detail enables {field}")

    trust = build_trust_authority_matrix_read_model(today_summary={})
    lanes = trust.get("lanes", [])
    lane = next(
        (item for item in lanes if item.get("lane_ref") == "trust-lane:connector-draft-only"),
        None,
    )
    if lane is None:
        failures.append("Trust matrix missing connector draft-only lane")
    else:
        if CONNECTOR_DRAFT_PROPOSAL_CLI_REF not in lane.get("cli_inspection_refs", []):
            failures.append("Trust matrix missing connector draft CLI ref")
        if CONNECTOR_DRAFT_PROPOSAL_PROOF_REF not in lane.get("proof_refs", []):
            failures.append("Trust matrix missing connector draft proof ref")
        if "blocked-state:trust:no-connector-send" not in lane.get(
            "blocked_authority_refs", []
        ):
            failures.append("Trust matrix missing connector send block")

    route_paths = {route.path for route in build_api_manifest(app).routes}
    for forbidden_route in (
        "/control-center/connectors/draft",
        "/control-center/connectors/draft/send",
        "/control-center/connector-drafts/send",
    ):
        if forbidden_route in route_paths:
            failures.append(f"unexpected connector draft execution route: {forbidden_route}")


def _append_static_failures(failures: list[str]) -> None:
    required_fragments = {
        LANE_DOC: list(REQUIRED_DOC_FRAGMENTS),
        AUTHORITY_BOARD: [
            "Connector Write / Send Capability",
            "Connector Draft-Only Proposal",
            "live connector runtime",
        ],
        RELEASE_SURFACE: [
            "Connector Draft-Only",
            "no connector send/write",
        ],
        FRONTEND_ROUTES: [
            "Connector Draft-Only",
            "/inbox",
            "/proof",
        ],
        TRUTH_PACKET: [
            "Connector draft-only proposals",
            "Source Readiness, Inbox, Trust, Proof, and CLI inspection",
        ],
        CURRENT_BOARD: [
            "Beta 10 Connector Draft-Only",
            "docs/control_center/CONNECTOR_DRAFT_ONLY_PROPOSALS.md",
        ],
        FRONTEND_TEST: [
            "renders connector draft proposal proof as inspection-only",
            "Connector draft proposals",
            "send and write remain blocked",
            "queryByRole(\"button\"",
        ],
    }
    for path, fragments in required_fragments.items():
        if not path.exists():
            failures.append(f"missing required file: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        compact = " ".join(text.split())
        for fragment in fragments:
            if fragment not in text and fragment not in compact:
                failures.append(
                    f"{path.relative_to(ROOT)} missing beta-10 fragment: {fragment}"
                )
    for path in (LANE_SOURCE, PROOF_SOURCE, SOURCE_READINESS_SOURCE):
        text = path.read_text(encoding="utf-8")
        lane_section = text
        if path == SOURCE_READINESS_SOURCE:
            start = text.find("connector_draft_proposals")
            end = text.find("return source_readiness", start)
            lane_section = text[start:end] if start != -1 and end != -1 else text
        if "perform_low_risk_connector_write" in lane_section:
            failures.append(
                f"{path.relative_to(ROOT)} wires beta-10 draft lane to connector write execution"
            )
        if "connector_write_execution_low_risk" in lane_section:
            failures.append(
                f"{path.relative_to(ROOT)} imports connector write execution into beta-10 draft lane"
            )


def validate_beta_10_connector_draft_only() -> list[str]:
    failures: list[str] = []
    _append_core_failures(failures)
    _append_cli_failures(failures)
    _append_control_center_failures(failures)
    _append_static_failures(failures)
    return failures


def main() -> int:
    failures = validate_beta_10_connector_draft_only()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Beta 10 connector draft-only verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
