#!/usr/bin/env python
"""Inspect the exact-approved filesystem mutation lane in a temp workspace."""

from __future__ import annotations

import argparse
import json
import tempfile
from datetime import timedelta
from pathlib import Path
from typing import Any

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.files import (
    FileKind,
    FilePatchProposal,
    FileSensitivity,
    LocalFileManager,
)
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.time import utc_now


SCHEMA_VERSION = "filesystem_mutation_lane_inspection.v1"
CLI_REF = "scripts/inspect_filesystem_mutation_lane.py"


def _actor_context() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="operator_ref:filesystem-mutation-dogfood",
        authority_source=AuthoritySource.explicit_user_request,
    )


def _grant_patch_approval(
    manager: LocalFileManager,
    proposal: FilePatchProposal,
    *,
    approval_ref: str,
) -> tuple[LocalApprovalAuthority, FilePatchProposal]:
    authority = LocalApprovalAuthority()
    request = manager.approval_request_for_patch(proposal)
    authority.create_request(request)
    grant = authority.grant(
        request.approval_request_id,
        approved_by_actor_id="operator_ref:filesystem-mutation-reviewer",
        approved_actions=[request.requested_action],
        approved_resource_refs=request.resource_refs,
        approval_ref=approval_ref,
        expires_at=utc_now() + timedelta(minutes=5),
    )
    return authority, proposal.model_copy(update={"approval_ref": grant.approval_ref})


def _grant_rollback_approval(
    manager: LocalFileManager,
    rollback_plan: Any,
    *,
    approval_ref: str,
) -> tuple[LocalApprovalAuthority, str]:
    authority = LocalApprovalAuthority()
    request = manager.approval_request_for_rollback(
        rollback_plan,
        run_id="run-ref:filesystem-mutation-dogfood",
        actor_context=_actor_context(),
    )
    authority.create_request(request)
    grant = authority.grant(
        request.approval_request_id,
        approved_by_actor_id="operator_ref:filesystem-mutation-reviewer",
        approved_actions=[request.requested_action],
        approved_resource_refs=request.resource_refs,
        approval_ref=approval_ref,
        expires_at=utc_now() + timedelta(minutes=5),
    )
    return authority, grant.approval_ref


def build_filesystem_mutation_lane_report() -> dict[str, Any]:
    """Run one exact-approved patch and rollback in a temporary workspace."""

    with tempfile.TemporaryDirectory(prefix="uaa-filesystem-lane-") as temp_dir:
        workspace = Path(temp_dir) / "workspace"
        workspace.mkdir()
        target = workspace / "artifact.txt"
        target.write_text("previous-private-text", encoding="utf-8")

        manager = LocalFileManager(workspace_root=workspace)
        target_ref = manager.build_file_ref("artifact.txt")
        proposal = FilePatchProposal(
            proposal_id="file-patch-proposal:filesystem-mutation-dogfood",
            run_id="run-ref:filesystem-mutation-dogfood",
            actor_context=_actor_context(),
            file_ref=target_ref.file_ref,
            target_path="artifact.txt",
            purpose="Inspect exact-approved filesystem mutation lane in a temp workspace.",
            new_content="updated-private-text",
            expected_existing_hash=target_ref.content_hash,
            file_kind=FileKind.artifact,
            sensitivity=FileSensitivity.project_private,
            idempotency_key="idempotency-ref:filesystem-mutation-dogfood:apply",
            audit_ref="audit-ref:filesystem-mutation-dogfood:apply",
            event_ref="evidence-ref:filesystem-mutation-dogfood:temp-workspace",
        )

        proposal_decision = manager.propose_patch(proposal)
        approval_authority, approved_proposal = _grant_patch_approval(
            manager,
            proposal,
            approval_ref="approval-ref:filesystem-mutation-dogfood:apply",
        )
        apply_result = manager.apply_patch_proposal(
            approved_proposal,
            approval_authority=approval_authority,
        )
        rollback_plan = manager.get_rollback_plan(apply_result.rollback_ref)
        rollback_authority, rollback_approval_ref = _grant_rollback_approval(
            manager,
            rollback_plan,
            approval_ref="approval-ref:filesystem-mutation-dogfood:rollback",
        )
        rollback_receipt = manager.rollback_with_receipt(
            rollback_plan,
            audit_ref="audit-ref:filesystem-mutation-dogfood:rollback",
            idempotency_key="idempotency-ref:filesystem-mutation-dogfood:rollback",
            approval_ref=rollback_approval_ref,
            approval_authority=rollback_authority,
            run_id="run-ref:filesystem-mutation-dogfood",
            actor_context=_actor_context(),
        )
        duplicate_apply = manager.apply_patch_proposal(
            approved_proposal,
            approval_authority=approval_authority,
        )

        return {
            "schema_version": SCHEMA_VERSION,
            "lane": "filesystem_mutation",
            "status": "core_exact_temp_workspace_verified",
            "cli_ref": CLI_REF,
            "workspace_scope": "temporary_workspace_only",
            "safe_path_class": "single_artifact_file_ref",
            "control_center_apply_route_enabled": False,
            "backend_apply_route_enabled": False,
            "broad_filesystem_authority_enabled": False,
            "home_directory_write_enabled": False,
            "delete_export_enabled": False,
            "shell_subprocess_execution_enabled": False,
            "unreviewed_generated_changes_enabled": False,
            "raw_content_persisted": False,
            "raw_path_persisted": False,
            "proposal": {
                "allowed": proposal_decision.allowed,
                "status": proposal_decision.status,
                "reason_codes": proposal_decision.reason_codes,
                "file_ref": proposal_decision.file_ref,
                "target_ref": proposal_decision.target_ref,
                "preview_ref": proposal_decision.preview_ref,
                "rollback_plan_ref": proposal_decision.rollback_plan_ref,
                "idempotency_key": proposal_decision.idempotency_key,
                "audit_ref": proposal_decision.audit_ref,
                "redactions_applied": proposal_decision.redactions_applied,
            },
            "apply": {
                "allowed": apply_result.allowed,
                "status": apply_result.status,
                "reason_codes": apply_result.reason_codes,
                "receipt_ref": apply_result.receipt_ref,
                "rollback_ref": apply_result.rollback_ref,
                "preimage_ref": apply_result.preimage_ref,
                "postimage_ref": apply_result.postimage_ref,
                "idempotency_key": apply_result.idempotency_key,
                "audit_ref": apply_result.audit_ref,
                "approval_ref": apply_result.approval_ref,
                "mutation_performed": bool(apply_result.receipt and apply_result.receipt.mutation_performed),
                "raw_content_stored": bool(apply_result.receipt and apply_result.receipt.raw_content_stored),
                "raw_path_stored": bool(apply_result.receipt and apply_result.receipt.raw_path_stored),
                "redactions_applied": apply_result.redactions_applied,
            },
            "rollback": {
                "status": rollback_receipt.status,
                "reason_codes": rollback_receipt.reason_codes,
                "receipt_ref": rollback_receipt.receipt_ref,
                "rollback_ref": rollback_receipt.rollback_ref,
                "preimage_ref": rollback_receipt.preimage_ref,
                "restored_image_ref": rollback_receipt.restored_image_ref,
                "idempotency_key": rollback_receipt.idempotency_key,
                "audit_ref": rollback_receipt.audit_ref,
                "approval_ref": rollback_receipt.approval_ref,
                "rollback_performed": rollback_receipt.rollback_performed,
                "raw_content_stored": rollback_receipt.raw_content_stored,
                "raw_path_stored": rollback_receipt.raw_path_stored,
                "redactions_applied": rollback_receipt.redactions_applied,
            },
            "replay_guard": {
                "duplicate_apply_status": duplicate_apply.status,
                "duplicate_apply_allowed": duplicate_apply.allowed,
                "duplicate_apply_reason_codes": duplicate_apply.reason_codes,
            },
            "restored_to_preimage": target.read_text(encoding="utf-8") == "previous-private-text",
            "next_safe_action": "keep_control_center_files_apply_route_blocked_until_api_cli_ui_receipts_are_scoped",
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect exact-approved filesystem mutation lane posture."
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    report = build_filesystem_mutation_lane_report()
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
