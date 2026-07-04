from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.code import (
    CODING_COCKPIT_BACKEND_ROUTE_REF,
    CODING_COCKPIT_CONTEXT_BACKEND_ROUTE_REF,
    CODING_COCKPIT_CONTEXT_PACK_REF,
    CODING_COCKPIT_FRONTEND_ROUTE_REF,
    CODING_COCKPIT_PATCH_APPLY_BACKEND_ROUTE_REF,
    CODING_COCKPIT_PATCH_APPLY_READINESS_REF,
    CODING_COCKPIT_PATCH_BACKEND_ROUTE_REF,
    CODING_COCKPIT_PATCH_PROPOSAL_REF,
    CODING_COCKPIT_REQUIRED_BLOCKED_REFS,
    CODING_COCKPIT_SESSION_REF,
    CodingCockpitSessionReadModel,
    CodingPatchApplyReadinessReadModel,
    CodingPatchProposalReadModel,
    CodingWorkspaceContextReadModel,
    build_coding_cockpit_session_seed,
    build_coding_patch_apply_readiness,
    build_coding_patch_proposal_preview,
    build_coding_workspace_context_preview,
)


ROOT = Path(__file__).resolve().parents[1]


def test_coding_cockpit_session_seed_is_backend_owned_safe_refs_only() -> None:
    session = build_coding_cockpit_session_seed()
    payload = session.model_dump(mode="json")

    assert session.schema_version == "uaa-coding-cockpit-session.v1"
    assert session.session_ref == CODING_COCKPIT_SESSION_REF
    assert session.backend_route_refs == [CODING_COCKPIT_BACKEND_ROUTE_REF]
    assert session.frontend_route_refs == [CODING_COCKPIT_FRONTEND_ROUTE_REF]
    assert session.backend_owned is True
    assert session.mock_fallback is False
    assert session.local_read_model_only is True
    assert session.safe_refs_only is True
    assert session.raw_content_included is False
    assert session.control_center_grants_authority is False
    assert set(CODING_COCKPIT_REQUIRED_BLOCKED_REFS).issubset(
        session.blocked_authority_refs
    )
    assert session.same_ref_spine == [
        "coding-session:local-readonly-cockpit",
        "coding-task:cockpit-shell-seed",
        CODING_COCKPIT_CONTEXT_PACK_REF,
        CODING_COCKPIT_PATCH_PROPOSAL_REF,
        CODING_COCKPIT_PATCH_APPLY_READINESS_REF,
        "command-proposal:coding-blocked-seed",
        "git-status:coding-readonly-seed",
        "proof-ref:coding-cockpit-seed",
        "preview-ref:coding-blocked-seed",
    ]
    assert "Local coding cockpit" in session.full_strength_goal
    assert "Prompt 01 seed" in session.repo_safe_scope
    assert "scripts/dev/uaa_coding.py inspect-session" in session.cli_inspection_refs
    assert "scripts/dev/uaa_coding.py inspect-context" in session.cli_inspection_refs
    assert (
        "scripts/dev/uaa_coding.py inspect-patch-proposal"
        in session.cli_inspection_refs
    )
    assert (
        "scripts/dev/uaa_coding.py inspect-patch-apply-readiness"
        in session.cli_inspection_refs
    )
    assert all(not panel.mutation_enabled for panel in _coding_panels(session))
    assert all(not panel.runtime_authority_enabled for panel in _coding_panels(session))
    assert all(item.proof_refs for panel in _coding_panels(session) for item in panel.items)
    assert "/Users/" not in json.dumps(payload)


@pytest.mark.parametrize(
    "flag_name",
    [
        "file_write_enabled",
        "shell_subprocess_execution_enabled",
        "git_mutation_enabled",
        "provider_model_call_enabled",
        "browser_automation_enabled",
        "connector_write_enabled",
        "background_autonomy_enabled",
        "production_authority_enabled",
    ],
)
def test_coding_cockpit_session_rejects_runtime_authority_flags(
    flag_name: str,
) -> None:
    payload = build_coding_cockpit_session_seed().model_dump(mode="json")
    payload[flag_name] = True

    with pytest.raises(ValidationError, match=flag_name):
        CodingCockpitSessionReadModel(**payload)


def test_coding_cockpit_session_rejects_panel_mutation_authority() -> None:
    payload = build_coding_cockpit_session_seed().model_dump(mode="json")
    payload["terminal_preview"]["runtime_authority_enabled"] = True

    with pytest.raises(ValidationError, match="runtime authority"):
        CodingCockpitSessionReadModel(**payload)


def test_coding_context_pack_preview_is_backend_owned_safe_refs_only() -> None:
    context = build_coding_workspace_context_preview()
    payload = context.model_dump(mode="json")

    assert context.schema_version == "uaa-coding-workspace-context.v1"
    assert context.context_pack_ref == CODING_COCKPIT_CONTEXT_PACK_REF
    assert context.backend_route_refs == [CODING_COCKPIT_CONTEXT_BACKEND_ROUTE_REF]
    assert context.frontend_route_refs == [CODING_COCKPIT_FRONTEND_ROUTE_REF]
    assert context.backend_owned is True
    assert context.read_only is True
    assert context.preview_only is True
    assert context.safe_refs_only is True
    assert context.raw_paths_included is False
    assert context.raw_content_included is False
    assert context.repo_file_read_performed is False
    assert context.file_write_enabled is False
    assert context.shell_subprocess_execution_enabled is False
    assert context.git_mutation_enabled is False
    assert context.provider_model_call_enabled is False
    assert context.browser_automation_enabled is False
    assert context.connector_write_enabled is False
    assert context.production_authority_enabled is False
    assert context.token_estimate_total == sum(
        item.token_estimate for item in context.context_refs if item.included_in_preview
    )
    assert context.token_budget_remaining == (
        context.token_budget_limit - context.token_estimate_total
    )
    assert context.operator_selected_refs
    assert context.agent_selected_refs
    assert context.excluded_refs
    assert context.comparison
    assert "/Users/" not in json.dumps(payload)


def test_coding_context_rejects_raw_paths_and_runtime_authority() -> None:
    payload = build_coding_workspace_context_preview().model_dump(mode="json")
    payload["raw_paths_included"] = True
    with pytest.raises(ValidationError, match="raw_paths_included"):
        CodingWorkspaceContextReadModel(**payload)

    payload = build_coding_workspace_context_preview().model_dump(mode="json")
    payload["context_refs"][0]["raw_content_included"] = True
    with pytest.raises(ValidationError, match="raw content"):
        CodingWorkspaceContextReadModel(**payload)

    payload = build_coding_workspace_context_preview().model_dump(mode="json")
    payload["file_write_enabled"] = True
    with pytest.raises(ValidationError, match="file_write_enabled"):
        CodingWorkspaceContextReadModel(**payload)


def test_coding_patch_proposal_preview_is_backend_owned_safe_refs_only() -> None:
    proposal = build_coding_patch_proposal_preview()
    payload = proposal.model_dump(mode="json")

    assert proposal.schema_version == "uaa-coding-patch-proposal.v1"
    assert proposal.patch_proposal_ref == CODING_COCKPIT_PATCH_PROPOSAL_REF
    assert proposal.context_pack_ref == CODING_COCKPIT_CONTEXT_PACK_REF
    assert proposal.backend_route_refs == [CODING_COCKPIT_PATCH_BACKEND_ROUTE_REF]
    assert proposal.frontend_route_refs == [CODING_COCKPIT_FRONTEND_ROUTE_REF]
    assert proposal.backend_owned is True
    assert proposal.read_only is True
    assert proposal.proposal_only is True
    assert proposal.safe_refs_only is True
    assert proposal.raw_paths_included is False
    assert proposal.raw_content_included is False
    assert proposal.repo_file_read_performed is False
    assert proposal.patch_apply_enabled is False
    assert proposal.file_write_enabled is False
    assert proposal.shell_subprocess_execution_enabled is False
    assert proposal.git_mutation_enabled is False
    assert proposal.provider_model_call_enabled is False
    assert proposal.browser_automation_enabled is False
    assert proposal.connector_write_enabled is False
    assert proposal.production_authority_enabled is False
    assert proposal.file_changes
    assert proposal.diff_preview_refs
    assert proposal.diff_summary_lines
    assert "/Users/" not in json.dumps(payload)


def test_coding_patch_proposal_rejects_apply_and_raw_content() -> None:
    payload = build_coding_patch_proposal_preview().model_dump(mode="json")
    payload["patch_apply_enabled"] = True
    with pytest.raises(ValidationError, match="patch_apply_enabled"):
        CodingPatchProposalReadModel(**payload)

    payload = build_coding_patch_proposal_preview().model_dump(mode="json")
    payload["file_changes"][0]["raw_content_included"] = True
    with pytest.raises(ValidationError, match="raw content"):
        CodingPatchProposalReadModel(**payload)

    payload = build_coding_patch_proposal_preview().model_dump(mode="json")
    payload["file_write_enabled"] = True
    with pytest.raises(ValidationError, match="file_write_enabled"):
        CodingPatchProposalReadModel(**payload)


def test_coding_patch_apply_readiness_is_backend_owned_and_blocked() -> None:
    readiness = build_coding_patch_apply_readiness()
    payload = readiness.model_dump(mode="json")

    assert readiness.schema_version == "uaa-coding-patch-apply-readiness.v1"
    assert readiness.readiness_ref == CODING_COCKPIT_PATCH_APPLY_READINESS_REF
    assert readiness.patch_proposal_ref == CODING_COCKPIT_PATCH_PROPOSAL_REF
    assert readiness.backend_route_refs == [CODING_COCKPIT_PATCH_APPLY_BACKEND_ROUTE_REF]
    assert readiness.frontend_route_refs == [CODING_COCKPIT_FRONTEND_ROUTE_REF]
    assert readiness.backend_owned is True
    assert readiness.read_only is True
    assert readiness.readiness_only is True
    assert readiness.safe_refs_only is True
    assert readiness.raw_paths_included is False
    assert readiness.raw_content_included is False
    assert readiness.repo_file_read_performed is False
    assert readiness.exact_patch_body_available is False
    assert readiness.hunk_selection_contract_available is False
    assert readiness.checkpoint_contract_available is False
    assert readiness.approval_binding_available is False
    assert readiness.rollback_contract_available is False
    assert readiness.patch_apply_enabled is False
    assert readiness.file_write_enabled is False
    assert readiness.approval_grant_capture_enabled is False
    assert readiness.rollback_execution_enabled is False
    assert readiness.shell_subprocess_execution_enabled is False
    assert readiness.git_mutation_enabled is False
    assert readiness.provider_model_call_enabled is False
    assert readiness.browser_automation_enabled is False
    assert readiness.connector_write_enabled is False
    assert readiness.background_autonomy_enabled is False
    assert readiness.production_authority_enabled is False
    assert readiness.prerequisites
    assert any(item.status in {"missing", "blocked"} for item in readiness.prerequisites)
    assert readiness.unblock_prompt_refs == [
        "prompt-ref:unblock-coding-approved-patch-apply"
    ]
    assert "/Users/" not in json.dumps(payload)
    assert "credential" not in json.dumps(payload).lower()


def test_coding_patch_apply_readiness_rejects_apply_authority() -> None:
    payload = build_coding_patch_apply_readiness().model_dump(mode="json")
    payload["patch_apply_enabled"] = True
    with pytest.raises(ValidationError, match="patch_apply_enabled"):
        CodingPatchApplyReadinessReadModel(**payload)

    payload = build_coding_patch_apply_readiness().model_dump(mode="json")
    payload["file_write_enabled"] = True
    with pytest.raises(ValidationError, match="file_write_enabled"):
        CodingPatchApplyReadinessReadModel(**payload)

    payload = build_coding_patch_apply_readiness().model_dump(mode="json")
    payload["rollback_execution_enabled"] = True
    with pytest.raises(ValidationError, match="rollback_execution_enabled"):
        CodingPatchApplyReadinessReadModel(**payload)


def test_control_center_coding_session_route_returns_safe_read_model() -> None:
    client = TestClient(app)
    response = client.get("/control-center/coding/session")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_coding_session"
    assert body["service"] == "ControlCenterCodingAPI"
    assert body["trace_id"] == CODING_COCKPIT_SESSION_REF
    assert body["redactions_applied"] == [
        "redaction-ref:safe-refs-only",
        "redaction-ref:bounded-summaries-only",
        "redaction-ref:raw-content-omitted",
        "redaction-ref:raw-paths-omitted",
    ]

    data = body["data"]
    assert data["backend_owned"] is True
    assert data["mock_fallback"] is False
    assert data["file_write_enabled"] is False
    assert data["shell_subprocess_execution_enabled"] is False
    assert data["git_mutation_enabled"] is False
    assert data["provider_model_call_enabled"] is False
    assert data["browser_automation_enabled"] is False
    assert data["connector_write_enabled"] is False
    assert data["background_autonomy_enabled"] is False
    assert data["production_authority_enabled"] is False
    assert set(CODING_COCKPIT_REQUIRED_BLOCKED_REFS).issubset(
        data["blocked_authority_refs"]
    )


def test_control_center_coding_context_route_returns_safe_read_model() -> None:
    client = TestClient(app)
    response = client.get("/control-center/coding/context")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_coding_context"
    assert body["service"] == "ControlCenterCodingAPI"
    assert body["trace_id"] == CODING_COCKPIT_CONTEXT_PACK_REF
    assert body["redactions_applied"] == [
        "redaction-ref:safe-refs-only",
        "redaction-ref:raw-paths-omitted",
        "redaction-ref:raw-content-omitted",
        "redaction-ref:protected-context-blocked",
    ]

    data = body["data"]
    assert data["backend_owned"] is True
    assert data["read_only"] is True
    assert data["safe_refs_only"] is True
    assert data["raw_paths_included"] is False
    assert data["raw_content_included"] is False
    assert data["repo_file_read_performed"] is False
    assert data["file_write_enabled"] is False


def test_control_center_coding_patch_proposal_route_returns_safe_read_model() -> None:
    client = TestClient(app)
    response = client.get("/control-center/coding/patch-proposal")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_coding_patch_proposal"
    assert body["service"] == "ControlCenterCodingAPI"
    assert body["trace_id"] == CODING_COCKPIT_PATCH_PROPOSAL_REF
    assert body["redactions_applied"] == [
        "redaction-ref:safe-refs-only",
        "redaction-ref:raw-paths-omitted",
        "redaction-ref:raw-content-omitted",
        "redaction-ref:diff-body-omitted",
    ]

    data = body["data"]
    assert data["backend_owned"] is True
    assert data["proposal_only"] is True
    assert data["safe_refs_only"] is True
    assert data["raw_paths_included"] is False
    assert data["raw_content_included"] is False
    assert data["repo_file_read_performed"] is False
    assert data["patch_apply_enabled"] is False
    assert data["file_write_enabled"] is False


def test_control_center_coding_patch_apply_readiness_route_returns_safe_read_model() -> None:
    client = TestClient(app)
    response = client.get("/control-center/coding/patch-apply-readiness")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_coding_patch_apply_readiness"
    assert body["service"] == "ControlCenterCodingAPI"
    assert body["trace_id"] == CODING_COCKPIT_PATCH_APPLY_READINESS_REF
    assert body["redactions_applied"] == [
        "redaction-ref:safe-refs-only",
        "redaction-ref:raw-paths-omitted",
        "redaction-ref:raw-content-omitted",
        "redaction-ref:diff-body-omitted",
    ]

    data = body["data"]
    assert data["backend_owned"] is True
    assert data["readiness_only"] is True
    assert data["safe_refs_only"] is True
    assert data["patch_apply_enabled"] is False
    assert data["file_write_enabled"] is False
    assert data["approval_grant_capture_enabled"] is False
    assert data["rollback_execution_enabled"] is False


def test_coding_cockpit_route_and_capabilities_are_manifested_as_local_read_model() -> None:
    manifest = build_api_manifest(app)
    routes = {(route.method, route.path): route for route in manifest.routes}
    route = routes[("GET", "/control-center/coding/session")]
    context_route = routes[("GET", "/control-center/coding/context")]
    patch_route = routes[("GET", "/control-center/coding/patch-proposal")]
    apply_route = routes[("GET", "/control-center/coding/patch-apply-readiness")]

    assert route.operation_id == "get_control_center_coding_session"
    assert route.tags == ["control-center"]
    assert route.side_effect_class == "local_dev_workspace_only"
    assert route.route_classification == "local_sensitive"
    assert route.approval_posture == "not_required_for_route_classification"
    assert route.idempotency_required is False
    assert context_route.operation_id == "get_control_center_coding_context"
    assert context_route.tags == ["control-center"]
    assert context_route.side_effect_class == "local_dev_workspace_only"
    assert context_route.route_classification == "local_sensitive"
    assert context_route.approval_posture == "not_required_for_route_classification"
    assert context_route.idempotency_required is False
    assert patch_route.operation_id == "get_control_center_coding_patch_proposal"
    assert patch_route.tags == ["control-center"]
    assert patch_route.side_effect_class == "local_dev_workspace_only"
    assert patch_route.route_classification == "local_sensitive"
    assert patch_route.approval_posture == "not_required_for_route_classification"
    assert patch_route.idempotency_required is False
    assert apply_route.operation_id == "get_control_center_coding_patch_apply_readiness"
    assert apply_route.tags == ["control-center"]
    assert apply_route.side_effect_class == "local_dev_workspace_only"
    assert apply_route.route_classification == "local_sensitive"
    assert apply_route.approval_posture == "not_required_for_route_classification"
    assert apply_route.idempotency_required is False
    assert "control_center_coding_cockpit_session_read_model" in (
        manifest.capabilities_declared
    )
    assert "control_center_coding_context_pack_preview_read_model" in (
        manifest.capabilities_declared
    )
    assert "control_center_coding_patch_proposal_read_model" in (
        manifest.capabilities_declared
    )
    assert "control_center_coding_patch_apply_readiness_read_model" in (
        manifest.capabilities_declared
    )
    for capability in [
        "control_center_coding_cockpit_file_writes",
        "control_center_coding_cockpit_shell_subprocess_execution",
        "control_center_coding_cockpit_git_mutation",
        "control_center_coding_cockpit_provider_model_calls",
        "control_center_coding_cockpit_browser_automation",
        "control_center_coding_cockpit_connector_writes",
        "control_center_coding_cockpit_background_autonomy",
        "control_center_coding_cockpit_production_authority",
    ]:
        assert capability in manifest.capabilities_blocked


def test_coding_cockpit_cli_inspection_prints_same_safe_session() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/dev/uaa_coding.py"), "inspect-session"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)

    assert data["session_ref"] == CODING_COCKPIT_SESSION_REF
    assert data["backend_owned"] is True
    assert data["mock_fallback"] is False
    assert data["frontend_route_refs"] == [CODING_COCKPIT_FRONTEND_ROUTE_REF]
    assert "/Users/" not in result.stdout
    assert "credential" not in result.stdout.lower()


def test_coding_context_cli_inspection_prints_same_safe_context() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/dev/uaa_coding.py"), "inspect-context"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)

    assert data["context_pack_ref"] == CODING_COCKPIT_CONTEXT_PACK_REF
    assert data["backend_owned"] is True
    assert data["read_only"] is True
    assert data["safe_refs_only"] is True
    assert data["repo_file_read_performed"] is False
    assert "/Users/" not in result.stdout
    assert "credential" not in result.stdout.lower()


def test_coding_patch_proposal_cli_inspection_prints_same_safe_proposal() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_coding.py"),
            "inspect-patch-proposal",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)

    assert data["patch_proposal_ref"] == CODING_COCKPIT_PATCH_PROPOSAL_REF
    assert data["backend_owned"] is True
    assert data["proposal_only"] is True
    assert data["safe_refs_only"] is True
    assert data["patch_apply_enabled"] is False
    assert "/Users/" not in result.stdout
    assert "credential" not in result.stdout.lower()


def test_coding_patch_apply_readiness_cli_inspection_prints_same_safe_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_coding.py"),
            "inspect-patch-apply-readiness",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)

    assert data["readiness_ref"] == CODING_COCKPIT_PATCH_APPLY_READINESS_REF
    assert data["backend_owned"] is True
    assert data["readiness_only"] is True
    assert data["safe_refs_only"] is True
    assert data["patch_apply_enabled"] is False
    assert data["file_write_enabled"] is False
    assert "/Users/" not in result.stdout
    assert "credential" not in result.stdout.lower()


def _coding_panels(session: CodingCockpitSessionReadModel):
    return [
        session.workspace_context,
        session.task_thread,
        session.task_timeline,
        session.diff_preview,
        session.proof_preview,
        session.terminal_preview,
        session.git_preview,
        session.test_output_preview,
        session.live_preview,
        session.chat_thread,
    ]
