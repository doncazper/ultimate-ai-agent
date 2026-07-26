from __future__ import annotations

import hashlib
import json
import re
import threading
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.build_identity import BuildIdentity, build_identity
from ultimate_ai_agent.core.control_center.local_tasks import (
    FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND,
    local_task_ref_for_action,
)
from ultimate_ai_agent.core.control_center.proof import (
    build_local_task_commit_proof_record,
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
FOUNDER_LOOP_DURABLE_EVIDENCE_SCHEMA_VERSION = (
    "founder-loop-durable-evidence.v1"
)
FOUNDER_LOOP_DURABLE_EVIDENCE_INTEGRITY_PREFIX = (
    "proof-ref:founder-loop-durable-evidence:sha256:"
)
_BACKEND_INSTANCE_REF = f"backend-instance-ref:control-center:{uuid.uuid4().hex}"
_INVALID_CLAIMED_RECEIPT_REF = (
    "receipt-ref:founder-loop-durable-proof-invalid-claim"
)
_ISSUED_ENVELOPE_LOCK = threading.Lock()
_LATEST_ISSUED_ENVELOPE: dict[str, Any] | None = None


def backend_instance_ref() -> str:
    return _BACKEND_INSTANCE_REF


def _register_issued_backend_truth(payload: dict[str, Any]) -> None:
    global _LATEST_ISSUED_ENVELOPE
    issued = {
        "envelope_integrity_ref": payload["envelope_integrity_ref"],
        "backend_revision_ref": payload["backend_revision_ref"],
        "backend_instance_ref": payload["backend_instance_ref"],
        "generated_at": payload["generated_at"],
        "valid_until": payload["valid_until"],
    }
    with _ISSUED_ENVELOPE_LOCK:
        _LATEST_ISSUED_ENVELOPE = issued


def backend_truth_envelope_is_current(
    *,
    envelope_integrity_ref: str,
    backend_revision_ref: str,
    expected_backend_instance_ref: str,
    now: datetime | None = None,
) -> bool:
    """Verify an exact, latest-issued, unexpired backend truth envelope."""
    with _ISSUED_ENVELOPE_LOCK:
        issued = (
            dict(_LATEST_ISSUED_ENVELOPE)
            if _LATEST_ISSUED_ENVELOPE is not None
            else None
        )
    if issued is None:
        return False
    current = (now or utc_now()).astimezone(UTC)
    try:
        generated_at = datetime.fromisoformat(
            str(issued["generated_at"]).replace("Z", "+00:00")
        )
        valid_until = datetime.fromisoformat(
            str(issued["valid_until"]).replace("Z", "+00:00")
        )
    except (KeyError, TypeError, ValueError):
        return False
    return bool(
        issued["envelope_integrity_ref"] == envelope_integrity_ref
        and issued["backend_revision_ref"] == backend_revision_ref
        and issued["backend_instance_ref"] == expected_backend_instance_ref
        and generated_at <= current <= valid_until
    )


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
    acceptance_schema_version: Literal["founder-loop-durable-evidence.v1"]
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
        if re.fullmatch(
            rf"{re.escape(FOUNDER_LOOP_DURABLE_EVIDENCE_INTEGRITY_PREFIX)}"
            r"[0-9a-f]{64}",
            self.acceptance_integrity_ref,
        ) is None:
            raise ValueError("Durable evidence integrity ref is invalid")
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
    critical_surfaces: list[CriticalSurfaceBinding] = Field(min_length=13)
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
        surface_ref="critical-surface:overview",
        label="Overview",
        frontend_paths=["/"],
        backend_route_refs=[
            "GET /control-center/dashboard",
            "GET /control-center/settings/status",
        ],
    ),
    CriticalSurfaceBinding(
        surface_ref="critical-surface:start-here",
        label="Start Here",
        frontend_paths=["/start"],
        backend_route_refs=["GET /control-center/start-here/summary"],
    ),
    CriticalSurfaceBinding(
        surface_ref="critical-surface:today",
        label="Today",
        frontend_paths=["/today", "/workspace", "/workspace/today"],
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
    CriticalSurfaceBinding(
        surface_ref="critical-surface:settings",
        label="Settings",
        frontend_paths=["/settings", "/workspace/settings"],
        backend_route_refs=["GET /control-center/settings/status"],
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
    return f"{FOUNDER_LOOP_DURABLE_EVIDENCE_INTEGRITY_PREFIX}{digest}"


def _safe_refs(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    refs: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            continue
        try:
            validate_execution_ref(item, "durable_evidence_ref")
        except ValueError:
            continue
        if item not in refs:
            refs.append(item)
    return refs


def _safe_claimed_receipt_ref(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return (
        value
        if value in _safe_refs([value])
        else _INVALID_CLAIMED_RECEIPT_REF
    )


def _durable_local_task_candidate(
    *,
    action: dict[str, Any],
    repo: FounderLoopRepository,
) -> dict[str, Any] | None:
    if action.get("action_kind") != FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND:
        return None
    item_ref = action.get("item_ref")
    receipt_ref = action.get("local_task_commit_receipt_ref")
    local_task_ref = action.get("local_task_ref")
    if not all(isinstance(value, str) and value for value in (
        item_ref,
        receipt_ref,
        local_task_ref,
    )):
        return None
    expected_local_task_ref = local_task_ref_for_action(item_ref)
    item_suffix = expected_local_task_ref.removeprefix("local-task:founder-loop:")
    if (
        local_task_ref != expected_local_task_ref
        or not receipt_ref.startswith(
            f"receipt:founder-loop-local-task:{item_suffix}:"
        )
        or receipt_ref not in _safe_refs(action.get("receipt_refs"))
    ):
        return None
    expected_proof_ref = f"proof-ref:local-task-commit:{item_suffix}"
    proof = build_local_task_commit_proof_record(action=action)
    if (
        proof.get("proof_kind") != "local_task_commit"
        or proof.get("proof_ref") != expected_proof_ref
        or receipt_ref not in _safe_refs(proof.get("receipt_refs"))
    ):
        return None
    receipt = repo.validated_local_task_commit_receipt(receipt_ref)
    if (
        receipt.get("item_ref") != item_ref
        or receipt.get("local_task_ref") != local_task_ref
        or receipt.get("receipt_ref") != receipt_ref
        or receipt.get("approval_ref")
        != action.get("local_task_commit_approval_ref")
        or receipt.get("idempotency_key_ref")
        != action.get("idempotency_key_ref")
        or receipt.get("audit_ref") not in _safe_refs(action.get("audit_refs"))
    ):
        return None
    evidence_refs = _safe_refs(action.get("evidence_refs"))
    proof_evidence_refs = _safe_refs(proof.get("evidence_refs"))
    receipt_evidence_refs = _safe_refs(receipt.get("evidence_refs"))
    if (
        not evidence_refs
        or not proof_evidence_refs
        or not receipt_evidence_refs
        or not set(receipt_evidence_refs).issubset(set(evidence_refs))
    ):
        return None
    return {
        "action_ref": item_ref,
        "run_refs": _safe_refs(proof.get("run_refs")),
        "proof_ref": expected_proof_ref,
        "receipt_ref": receipt_ref,
        "evidence_refs": list(
            dict.fromkeys(
                [*evidence_refs, *receipt_evidence_refs, *proof_evidence_refs]
            )
        ),
    }


def _build_founder_loop_durable_evidence(
    *,
    repo: FounderLoopRepository,
    limit: int = 50,
) -> tuple[dict[str, Any], list[str]]:
    bounded_limit = min(max(int(limit), 12), 50)
    today = repo.today_summary(limit=bounded_limit)
    today_actions = [
        item for item in today.get("actions", []) if isinstance(item, dict)
    ]
    durable_actions = repo.list_durable_local_task_actions()
    actions_by_ref: dict[str, dict[str, Any]] = {}
    for action in [*today_actions, *durable_actions]:
        item_ref = action.get("item_ref")
        if isinstance(item_ref, str) and item_ref:
            actions_by_ref[item_ref] = action
    actions = list(actions_by_ref.values())
    candidates: list[dict[str, Any]] = []
    invalid_claimed_receipt_refs: list[str] = []
    for action in actions:
        claimed_receipt_ref = action.get("local_task_commit_receipt_ref")
        has_claimed_receipt = (
            action.get("action_kind")
            == FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND
            and isinstance(claimed_receipt_ref, str)
            and bool(claimed_receipt_ref)
        )
        try:
            candidate = _durable_local_task_candidate(
                action=action,
                repo=repo,
            )
        except FounderLoopStorageError:
            candidate = None
        if has_claimed_receipt and candidate is None:
            invalid_claimed_receipt_refs.append(
                _safe_claimed_receipt_ref(claimed_receipt_ref)
                or _INVALID_CLAIMED_RECEIPT_REF
            )
        if candidate is not None:
            candidates.append(candidate)
    claimed_receipt_refs = list(
        dict.fromkeys(
            safe_receipt_ref
            for action in actions
            if action.get("action_kind")
            == FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND
            and (
                safe_receipt_ref := _safe_claimed_receipt_ref(
                    action.get("local_task_commit_receipt_ref")
                )
            )
        )
    )
    evidence_memory = today.get("evidence_memory_loop_binding_read_model")
    evidence_memory = evidence_memory if isinstance(evidence_memory, dict) else {}
    memory_candidate_refs = _safe_refs(
        evidence_memory.get("memory_candidate_refs")
    )
    candidate = candidates[0] if candidates else None
    envelope = {
        "schema_version": FOUNDER_LOOP_DURABLE_EVIDENCE_SCHEMA_VERSION,
        "action_refs": [candidate["action_ref"]] if candidate else [],
        "run_refs": candidate["run_refs"] if candidate else [],
        "proof_refs": [candidate["proof_ref"]] if candidate else [],
        "receipt_refs": (
            list(
                dict.fromkeys(
                    [
                        candidate["receipt_ref"],
                        *invalid_claimed_receipt_refs,
                    ]
                )
            )[:12]
            if candidate
            else claimed_receipt_refs[:12]
        ),
        "evidence_refs": candidate["evidence_refs"] if candidate else [],
        "memory_candidate_refs": memory_candidate_refs[:12],
        "safe_refs_only": True,
        "raw_content_included": False,
        "raw_paths_included": False,
    }
    issues: list[str] = []
    if invalid_claimed_receipt_refs:
        issues.append("founder-loop-durable-proof-invalid")
    elif candidate is None:
        issues.append(
            "founder-loop-durable-proof-invalid"
            if claimed_receipt_refs
            else "founder-loop-durable-local-task-proof-unavailable"
        )
    elif not candidate["run_refs"]:
        issues.append("founder-loop-durable-run-proof-unavailable")
    return envelope, issues


def build_control_center_backend_truth(
    *,
    repo: FounderLoopRepository | None,
    now: datetime | None = None,
    identity: BuildIdentity | None = None,
) -> dict[str, Any]:
    generated_at = (now or utc_now()).astimezone(UTC).replace(microsecond=0)
    current_identity = identity or build_identity()
    storage_unavailable = repo is None
    if repo is None:
        acceptance = {
            "schema_version": FOUNDER_LOOP_DURABLE_EVIDENCE_SCHEMA_VERSION,
            "action_refs": [],
            "run_refs": [],
            "proof_refs": [],
            "receipt_refs": [],
            "evidence_refs": [],
            "memory_candidate_refs": [],
        }
        issues = ["backend-truth-storage-unavailable"]
    else:
        try:
            acceptance, issues = _build_founder_loop_durable_evidence(
                repo=repo,
                limit=50,
            )
        except FounderLoopStorageError:
            acceptance = {
                "schema_version": FOUNDER_LOOP_DURABLE_EVIDENCE_SCHEMA_VERSION,
                "action_refs": [],
                "run_refs": [],
                "proof_refs": [],
                "receipt_refs": [],
                "evidence_refs": [],
                "memory_candidate_refs": [],
            }
            storage_unavailable = True
            issues = ["backend-truth-storage-unavailable"]
    if not current_identity.source_revision_bound:
        issues.append("backend-source-revision-unbound")
    complete = not issues
    durable_receipt_present = bool(acceptance.get("receipt_refs"))
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
    validated = ControlCenterBackendTruth(**payload).model_dump(mode="json")
    _register_issued_backend_truth(validated)
    return validated
