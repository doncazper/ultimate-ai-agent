from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.build_identity import BuildIdentity, build_identity
from ultimate_ai_agent.core.control_center.dogfood_live_loop import (
    DOGFOOD_LIVE_LOOP_SCHEMA_VERSION,
    build_dogfood_live_loop_acceptance_read_model,
    validate_dogfood_live_loop_acceptance,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository, FounderLoopStorageError
from ultimate_ai_agent.core.time import utc_now


BACKEND_TRUTH_SCHEMA_VERSION = "uaa-control-center-backend-truth.v1"
BACKEND_TRUTH_SOURCE_REF = "source-ref:python-core:control-center-backend-truth"
BACKEND_TRUTH_CLI_REF = (
    "python scripts/dev/uaa_founder_loop.py inspect-backend-truth"
)
BACKEND_TRUTH_TTL_SECONDS = 45
_BACKEND_INSTANCE_REF = f"backend-instance-ref:control-center:{uuid.uuid4().hex}"
_EXPECTED_INCOMPLETE_STORAGE_ERRORS = {
    "DOGFOOD_LIVE_LOOP_ACTION_NOT_FOUND",
    "DOGFOOD_LIVE_LOOP_LOCAL_TASK_PROOF_NOT_FOUND",
}


def backend_instance_ref() -> str:
    return _BACKEND_INSTANCE_REF


class CriticalSurfaceBinding(BaseModel):
    surface_ref: str
    label: str
    frontend_paths: list[str] = Field(min_length=1)
    backend_route_refs: list[str] = Field(min_length=1)
    contract_status: Literal["backend_contract_declared"] = (
        "backend_contract_declared"
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_binding(self) -> "CriticalSurfaceBinding":
        validate_execution_ref(self.surface_ref, "surface_ref")
        validate_safe_execution_text(self.label, "label")
        for path in self.frontend_paths:
            if not path.startswith("/") or " " in path:
                raise ValueError("Critical frontend paths must be local route paths")
        for route_ref in self.backend_route_refs:
            if not route_ref.startswith(("GET /", "POST /")):
                raise ValueError("Critical backend route refs must name API routes")
        return self


class BackendTruthEvidenceBinding(BaseModel):
    status: Literal[
        "verified_complete",
        "unverified_incomplete",
        "invalid_evidence",
        "storage_unavailable",
    ]
    acceptance_schema_version: str
    acceptance_integrity_ref: str
    action_refs: list[str] = Field(default_factory=list)
    run_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    memory_candidate_refs: list[str] = Field(default_factory=list)
    issue_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_evidence(self) -> "BackendTruthEvidenceBinding":
        validate_execution_ref(
            self.acceptance_integrity_ref, "acceptance_integrity_ref"
        )
        for field_name in (
            "action_refs",
            "run_refs",
            "proof_refs",
            "receipt_refs",
            "evidence_refs",
            "memory_candidate_refs",
            "issue_refs",
        ):
            for value in getattr(self, field_name):
                validate_execution_ref(value, field_name)
        if self.status == "verified_complete" and self.issue_refs:
            raise ValueError("Verified evidence cannot retain validation issues")
        if self.status != "verified_complete" and not self.issue_refs:
            raise ValueError("Unverified evidence must expose validation issues")
        if self.status == "invalid_evidence" and not self.receipt_refs:
            raise ValueError("Invalid durable evidence must identify a receipt ref")
        if self.status == "storage_unavailable" and self.receipt_refs:
            raise ValueError("Unavailable storage cannot claim durable receipt proof")
        return self


class BackendTruthAuthorityPosture(BaseModel):
    mode_ref: Literal["authority-mode-ref:read-only-local"] = (
        "authority-mode-ref:read-only-local"
    )
    approval_refs_are_identifiers_only: Literal[True] = True
    control_center_grants_authority: Literal[False] = False
    runtime_model_call_enabled: Literal[False] = False
    browser_or_web_execution_enabled: Literal[False] = False
    connector_write_enabled: Literal[False] = False
    shell_subprocess_execution_enabled: Literal[False] = False
    background_autonomy_enabled: Literal[False] = False
    production_authority_enabled: Literal[False] = False

    model_config = ConfigDict(extra="forbid")


class ControlCenterBackendTruth(BaseModel):
    schema_version: Literal["uaa-control-center-backend-truth.v1"] = (
        BACKEND_TRUTH_SCHEMA_VERSION
    )
    source_ref: Literal["source-ref:python-core:control-center-backend-truth"] = (
        BACKEND_TRUTH_SOURCE_REF
    )
    generated_at: datetime
    valid_until: datetime
    backend_revision_ref: str
    backend_instance_ref: str
    source_revision_bound: bool
    critical_surfaces: list[CriticalSurfaceBinding] = Field(min_length=12)
    evidence_binding: BackendTruthEvidenceBinding
    authority_posture: BackendTruthAuthorityPosture = Field(
        default_factory=BackendTruthAuthorityPosture
    )
    cli_ref: str = BACKEND_TRUTH_CLI_REF
    safe_refs_only: Literal[True] = True
    redacted_summaries_only: Literal[True] = True
    raw_content_included: Literal[False] = False
    raw_paths_included: Literal[False] = False
    envelope_integrity_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_truth(self) -> "ControlCenterBackendTruth":
        if self.generated_at.tzinfo is None or self.valid_until.tzinfo is None:
            raise ValueError("Backend truth timestamps must be timezone aware")
        lifetime = self.valid_until - self.generated_at
        if lifetime <= timedelta(0) or lifetime > timedelta(seconds=120):
            raise ValueError("Backend truth freshness window is invalid")
        validate_execution_ref(self.backend_revision_ref, "backend_revision_ref")
        validate_execution_ref(self.backend_instance_ref, "backend_instance_ref")
        validate_execution_ref(self.envelope_integrity_ref, "envelope_integrity_ref")
        validate_safe_execution_text(self.cli_ref, "cli_ref")
        expected_surfaces = [
            binding.model_dump(mode="json") for binding in CRITICAL_SURFACES
        ]
        actual_surfaces = [
            binding.model_dump(mode="json") for binding in self.critical_surfaces
        ]
        if actual_surfaces != expected_surfaces:
            raise ValueError("Critical backend truth surface binding drift")
        expected_integrity = backend_truth_integrity_ref(
            self.model_dump(mode="json", exclude={"envelope_integrity_ref"})
        )
        if self.envelope_integrity_ref != expected_integrity:
            raise ValueError("Backend truth envelope integrity mismatch")
        return self


CRITICAL_SURFACES: tuple[CriticalSurfaceBinding, ...] = (
    CriticalSurfaceBinding(
        surface_ref="critical-surface:start-here",
        label="Start Here",
        frontend_paths=["/start"],
        backend_route_refs=["GET /control-center/start-here/summary"],
    ),
    CriticalSurfaceBinding(
        surface_ref="critical-surface:today",
        label="Today",
        frontend_paths=["/", "/today", "/workspace", "/workspace/today"],
        backend_route_refs=["GET /control-center/today/summary"],
    ),
    CriticalSurfaceBinding(
        surface_ref="critical-surface:plans",
        label="Plans",
        frontend_paths=["/plans"],
        backend_route_refs=["GET /control-center/today/summary"],
    ),
    CriticalSurfaceBinding(
        surface_ref="critical-surface:action-inbox",
        label="Action Inbox",
        frontend_paths=["/actions", "/workspace/decisions"],
        backend_route_refs=["GET /control-center/actions/inbox"],
    ),
    CriticalSurfaceBinding(
        surface_ref="critical-surface:approvals",
        label="Approvals",
        frontend_paths=["/approvals", "/workspace/decisions"],
        backend_route_refs=["GET /control-center/approvals/queue"],
    ),
    CriticalSurfaceBinding(
        surface_ref="critical-surface:work-board",
        label="Work Board",
        frontend_paths=["/work-board", "/workspace/work-board"],
        backend_route_refs=["GET /control-center/work-board"],
    ),
    CriticalSurfaceBinding(
        surface_ref="critical-surface:morning-briefing",
        label="Morning Briefing",
        frontend_paths=[
            "/briefing",
            "/morning-briefing",
            "/workspace",
            "/workspace/today",
        ],
        backend_route_refs=["GET /control-center/morning-briefing/summary"],
    ),
    CriticalSurfaceBinding(
        surface_ref="critical-surface:memory",
        label="Memory",
        frontend_paths=["/memory", "/workspace/knowledge"],
        backend_route_refs=["GET /control-center/memory/review"],
    ),
    CriticalSurfaceBinding(
        surface_ref="critical-surface:evidence-proof",
        label="Evidence and Proof",
        frontend_paths=["/proof", "/evidence", "/workspace/activity-trust"],
        backend_route_refs=[
            "GET /control-center/proof/index",
            "GET /control-center/evidence/timeline",
            "GET /control-center/runs/observability",
        ],
    ),
    CriticalSurfaceBinding(
        surface_ref="critical-surface:setup",
        label="Setup",
        frontend_paths=["/setup", "/workspace/onboarding"],
        backend_route_refs=["GET /control-center/setup-assistant/summary"],
    ),
    CriticalSurfaceBinding(
        surface_ref="critical-surface:chat-handoff",
        label="Chat handoff",
        frontend_paths=["/chat"],
        backend_route_refs=["GET /control-center/agent-loop/thread"],
    ),
    CriticalSurfaceBinding(
        surface_ref="critical-surface:active-run",
        label="Active run",
        frontend_paths=["/runs", "/workspace/activity-trust"],
        backend_route_refs=["GET /control-center/runs/observability"],
    ),
)


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def backend_truth_integrity_ref(payload: dict[str, Any]) -> str:
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"proof-ref:backend-truth-envelope:sha256:{digest}"


def _acceptance_integrity_ref(acceptance: dict[str, Any]) -> str:
    digest = hashlib.sha256(_canonical_json(acceptance).encode("utf-8")).hexdigest()
    return f"proof-ref:dogfood-live-loop:sha256:{digest}"


def build_control_center_backend_truth(
    *,
    repo: FounderLoopRepository,
    now: datetime | None = None,
    identity: BuildIdentity | None = None,
) -> dict[str, Any]:
    generated_at = (now or utc_now()).astimezone(UTC).replace(microsecond=0)
    current_identity = identity or build_identity()
    storage_unavailable = False
    try:
        acceptance = build_dogfood_live_loop_acceptance_read_model(
            repo=repo,
            seed_fixture=False,
            limit=50,
        )
        issues = validate_dogfood_live_loop_acceptance(
            acceptance,
            require_seeded=False,
        )
    except FounderLoopStorageError as exc:
        acceptance = {
            "schema_version": DOGFOOD_LIVE_LOOP_SCHEMA_VERSION,
            "action_refs": [],
            "run_refs": [],
            "proof_refs": [],
            "receipt_refs": [],
            "evidence_refs": [],
            "memory_candidate_refs": [],
        }
        storage_error_ref = str(exc)
        storage_unavailable = (
            storage_error_ref not in _EXPECTED_INCOMPLETE_STORAGE_ERRORS
        )
        issues = [
            (
                "backend-truth-storage-unavailable"
                if storage_unavailable
                else "dogfood-live-loop-durable-proof-unavailable"
            )
        ]
    if not current_identity.source_revision_bound:
        issues.append("backend-source-revision-unbound")
    complete = not issues
    durable_receipt_present = bool(
        acceptance.get("local_task_commit_receipt_ref")
    )
    if storage_unavailable:
        evidence_status = "storage_unavailable"
    elif complete:
        evidence_status = "verified_complete"
    elif durable_receipt_present:
        evidence_status = "invalid_evidence"
    else:
        evidence_status = "unverified_incomplete"
    evidence = BackendTruthEvidenceBinding(
        status=evidence_status,
        acceptance_schema_version=str(acceptance.get("schema_version")),
        acceptance_integrity_ref=_acceptance_integrity_ref(acceptance),
        action_refs=list(acceptance.get("action_refs") or [])[:12],
        run_refs=list(acceptance.get("run_refs") or [])[:12],
        proof_refs=list(acceptance.get("proof_refs") or [])[:12],
        receipt_refs=list(acceptance.get("receipt_refs") or [])[:12],
        evidence_refs=list(acceptance.get("evidence_refs") or [])[:20],
        memory_candidate_refs=list(
            acceptance.get("memory_candidate_refs") or []
        )[:12],
        issue_refs=[f"issue-ref:{issue}" for issue in issues],
    )
    payload: dict[str, Any] = {
        "schema_version": BACKEND_TRUTH_SCHEMA_VERSION,
        "source_ref": BACKEND_TRUTH_SOURCE_REF,
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
        "valid_until": (
            generated_at + timedelta(seconds=BACKEND_TRUTH_TTL_SECONDS)
        ).isoformat().replace("+00:00", "Z"),
        "backend_revision_ref": current_identity.commit_ref,
        "backend_instance_ref": backend_instance_ref(),
        "source_revision_bound": current_identity.source_revision_bound,
        "critical_surfaces": [
            binding.model_dump(mode="json") for binding in CRITICAL_SURFACES
        ],
        "evidence_binding": evidence.model_dump(mode="json"),
        "authority_posture": BackendTruthAuthorityPosture().model_dump(mode="json"),
        "cli_ref": BACKEND_TRUTH_CLI_REF,
        "safe_refs_only": True,
        "redacted_summaries_only": True,
        "raw_content_included": False,
        "raw_paths_included": False,
    }
    payload["envelope_integrity_ref"] = backend_truth_integrity_ref(payload)
    return ControlCenterBackendTruth(**payload).model_dump(mode="json")
