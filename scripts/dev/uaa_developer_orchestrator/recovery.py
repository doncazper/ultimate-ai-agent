"""Recover the stranded UAA backlog without rewriting historical queue evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)

from uaa_developer_orchestrator.coordinator import DeveloperWorkTaskDraft


RECOVERY_MANIFEST_PATH = "docs/roadmap/UAA_DEVELOPER_QUEUE_RECOVERY_MANIFEST.json"
HISTORICAL_MANIFEST_PATH = "docs/roadmap/UAA_REMAINING_QUEUE_MANIFEST.json"
RECOVERY_PROMPT_PREFIX = PurePosixPath("docs/prompts/remaining_queue_recovery")
QUEUE_STARVATION_RISK_REF = "developer-risk-ref:recovery-queue-starvation"


class DeveloperQueueRecoveryPolicy(BaseModel):
    automatic_agent_dispatch: Literal[False] = False
    automatic_git_or_github_mutation: Literal[False] = False
    explicit_ledger_confirmation_required: Literal[True] = True
    max_parallel_claims: Literal[3] = 3
    queue_starvation_is_failure: Literal[True] = True

    model_config = ConfigDict(extra="forbid")


class DeveloperQueueRecoveryItem(BaseModel):
    recovery_order: int = Field(..., ge=1)
    item_id: str
    title: str
    origin_kind: Literal["historical_remaining_queue", "canonical_product_backlog"]
    origin_ref: str
    prompt_path: str
    prompt_sha256: str
    task_ref: str
    canonical_task_ref: str
    priority: Literal["p0", "p1", "p2", "p3"]
    concurrency: Literal["parallel_safe", "exclusive"]
    scope_contract_ref: str
    in_scope_refs: list[str] = Field(default_factory=list)
    out_of_scope_refs: list[str] = Field(default_factory=list)
    sol_thinking_level: Literal["medium", "high", "xhigh"]
    branch_ref: str
    worktree_ref: str
    workstream_ref: str
    acceptance_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    merge_gate_refs: list[str] = Field(default_factory=list)
    depends_on_item_ids: list[str] = Field(default_factory=list)
    next_safe_action: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_item(self) -> "DeveloperQueueRecoveryItem":
        for value in [
            self.origin_ref,
            self.task_ref,
            self.canonical_task_ref,
            self.scope_contract_ref,
            self.branch_ref,
            self.worktree_ref,
            self.workstream_ref,
            *self.in_scope_refs,
            *self.out_of_scope_refs,
            *self.acceptance_refs,
            *self.verifier_refs,
            *self.merge_gate_refs,
        ]:
            validate_task_ref(value, "developer_queue_recovery_ref")
        for value in [
            self.item_id,
            self.title,
            self.origin_kind,
            self.priority,
            self.concurrency,
            self.sol_thinking_level,
            self.next_safe_action,
        ]:
            validate_safe_task_text(value, "developer_queue_recovery_text")
        if not self.task_ref.startswith("dev-task:recovery-"):
            raise ValueError("recovery task ref must use the recovery namespace")
        if not self.in_scope_refs or not self.out_of_scope_refs:
            raise ValueError("recovery item requires exact scope boundaries")
        if (
            not self.acceptance_refs
            or not self.verifier_refs
            or not self.merge_gate_refs
        ):
            raise ValueError(
                "recovery item requires acceptance, verifier, and merge gates"
            )
        if len(self.depends_on_item_ids) != len(set(self.depends_on_item_ids)):
            raise ValueError("recovery item dependencies must be unique")
        if self.item_id in self.depends_on_item_ids:
            raise ValueError("recovery item cannot depend on itself")
        if len(self.prompt_sha256) != 64 or any(
            character not in "0123456789abcdef" for character in self.prompt_sha256
        ):
            raise ValueError("recovery prompt digest is invalid")
        prompt_path = PurePosixPath(self.prompt_path)
        if (
            prompt_path.is_absolute()
            or ".." in prompt_path.parts
            or prompt_path.suffix != ".md"
            or prompt_path.parent != RECOVERY_PROMPT_PREFIX
        ):
            raise ValueError("recovery prompt path is outside the recovery source set")
        return self


class DeveloperQueueRecoveryManifest(BaseModel):
    schema_version: Literal["uaa.developer_queue_recovery_manifest.v1"]
    artifact_status: Literal["triage_ready_recovery"]
    historical_manifest_ref: str
    historical_manifest_sha256: str
    recovery_policy: DeveloperQueueRecoveryPolicy
    items: list[DeveloperQueueRecoveryItem] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_manifest(self) -> "DeveloperQueueRecoveryManifest":
        validate_task_ref(
            self.historical_manifest_ref,
            "developer_queue_recovery_historical_ref",
        )
        if len(self.historical_manifest_sha256) != 64 or any(
            character not in "0123456789abcdef"
            for character in self.historical_manifest_sha256
        ):
            raise ValueError("historical manifest digest is invalid")
        if not self.items:
            raise ValueError("recovery manifest requires tasks")
        if [item.recovery_order for item in self.items] != list(
            range(1, len(self.items) + 1)
        ):
            raise ValueError("recovery order must be contiguous")
        item_ids = [item.item_id for item in self.items]
        task_refs = [item.task_ref for item in self.items]
        branch_refs = [item.branch_ref for item in self.items]
        worktree_refs = [item.worktree_ref for item in self.items]
        for values, label in [
            (item_ids, "item"),
            (task_refs, "task"),
            (branch_refs, "branch"),
            (worktree_refs, "worktree"),
        ]:
            if len(values) != len(set(values)):
                raise ValueError(f"recovery {label} refs must be unique")
        seen: set[str] = set()
        for item in self.items:
            if not set(item.depends_on_item_ids).issubset(seen):
                raise ValueError("recovery dependencies must reference earlier items")
            seen.add(item.item_id)
        if self.items[-1].item_id != "queue-09-final-goat-comparison":
            raise ValueError("final GoatCitadel comparison must remain the last gate")
        return self


class DeveloperQueueRecoveryHealth(BaseModel):
    schema_version: Literal["uaa.developer_queue_recovery_health.v1"] = (
        "uaa.developer_queue_recovery_health.v1"
    )
    recovery_item_count: int = Field(..., ge=0)
    admitted_recovery_item_count: int = Field(..., ge=0)
    nonterminal_recovery_item_count: int = Field(..., ge=0)
    unadmitted_task_refs: list[str] = Field(default_factory=list)
    admission_gap_detected: bool
    queue_starvation_detected: bool
    risk_ref: str | None = None
    max_parallel_claims: Literal[3] = 3
    safe_summary: str
    next_safe_action: str
    automatic_agent_dispatch_performed: Literal[False] = False
    git_or_github_mutation_performed: Literal[False] = False
    product_runtime_authority_granted: Literal[False] = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_health(self) -> "DeveloperQueueRecoveryHealth":
        for value in [
            *self.unadmitted_task_refs,
            *([self.risk_ref] if self.risk_ref else []),
        ]:
            validate_task_ref(value, "developer_queue_recovery_health_ref")
        for value in [self.safe_summary, self.next_safe_action]:
            validate_safe_task_text(value, "developer_queue_recovery_health_text")
        if self.queue_starvation_detected != (self.risk_ref is not None):
            raise ValueError("queue starvation risk binding is invalid")
        return self


def _read_json_without_duplicate_keys(path: Path) -> object:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        payload: dict[str, object] = {}
        for key, value in pairs:
            if key in payload:
                raise ValueError("duplicate recovery manifest key")
            payload[key] = value
        return payload

    try:
        return json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        raise ValueError("DEVELOPER_QUEUE_RECOVERY_MANIFEST_INVALID") from None


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        raise ValueError("DEVELOPER_QUEUE_RECOVERY_SOURCE_UNAVAILABLE") from None


def load_developer_queue_recovery_manifest(
    root: Path | None = None,
) -> DeveloperQueueRecoveryManifest:
    repository_root = root or Path(__file__).resolve().parents[3]
    manifest_path = repository_root / RECOVERY_MANIFEST_PATH
    try:
        manifest = DeveloperQueueRecoveryManifest.model_validate(
            _read_json_without_duplicate_keys(manifest_path)
        )
    except (ValueError, TypeError):
        raise ValueError("DEVELOPER_QUEUE_RECOVERY_MANIFEST_INVALID") from None
    if (
        _sha256(repository_root / HISTORICAL_MANIFEST_PATH)
        != manifest.historical_manifest_sha256
    ):
        raise ValueError("DEVELOPER_QUEUE_RECOVERY_HISTORICAL_BINDING_MISMATCH")
    for item in manifest.items:
        if _sha256(repository_root / item.prompt_path) != item.prompt_sha256:
            raise ValueError("DEVELOPER_QUEUE_RECOVERY_SOURCE_DIGEST_MISMATCH")
    return manifest


def build_developer_queue_recovery_drafts(
    root: Path | None = None,
) -> list[DeveloperWorkTaskDraft]:
    manifest = load_developer_queue_recovery_manifest(root)
    task_ref_by_item_id = {item.item_id: item.task_ref for item in manifest.items}
    return [
        DeveloperWorkTaskDraft(
            task_ref=item.task_ref,
            title=item.title,
            safe_summary=(
                "Recovered from an explicit repository source contract. The task "
                "remains unclaimed and grants no execution or product authority."
            ),
            priority=item.priority,
            concurrency=item.concurrency,
            canonical_task_ref=item.canonical_task_ref,
            canonical_source_ref=f"repo-ref:remaining-queue-recovery/{item.item_id}",
            canonical_source_fingerprint_ref=(
                f"planning-fingerprint-ref:sha256:{item.prompt_sha256[:24]}"
            ),
            scope_contract_ref=item.scope_contract_ref,
            in_scope_refs=item.in_scope_refs,
            out_of_scope_refs=item.out_of_scope_refs,
            sol_thinking_level=item.sol_thinking_level,
            branch_ref=item.branch_ref,
            worktree_ref=item.worktree_ref,
            workstream_ref=item.workstream_ref,
            acceptance_refs=item.acceptance_refs,
            verifier_refs=item.verifier_refs,
            merge_gate_refs=item.merge_gate_refs,
            depends_on_task_refs=[
                task_ref_by_item_id[dependency]
                for dependency in item.depends_on_item_ids
            ],
            next_safe_action=item.next_safe_action,
        )
        for item in manifest.items
    ]


def assess_developer_queue_recovery_health(
    *,
    manifest: DeveloperQueueRecoveryManifest,
    task_states: Mapping[str, str],
) -> DeveloperQueueRecoveryHealth:
    expected_refs = [item.task_ref for item in manifest.items]
    unadmitted_refs = [
        task_ref for task_ref in expected_refs if task_ref not in task_states
    ]
    admitted_count = len(expected_refs) - len(unadmitted_refs)
    nonterminal_count = sum(
        1
        for task_ref in expected_refs
        if task_states.get(task_ref) in {"queued", "claimed", "blocked", "review"}
    )
    admission_gap = bool(unadmitted_refs)
    starvation = admission_gap and nonterminal_count == 0
    if starvation:
        summary = (
            "A nonempty recovered roadmap has no admitted nonterminal task. Queue "
            "starvation is a control-plane failure, not an idle success state."
        )
        next_action = (
            "Explicitly admit the recovery manifest, then claim at most three "
            "nonconflicting dependency-ready tasks across named owners."
        )
    elif admission_gap:
        summary = (
            "Recovered work remains partially unadmitted while at least one recovery "
            "task is active or queued."
        )
        next_action = (
            "Admit the remaining recovery items idempotently without duplicating active "
            "owners, then preserve the three-claim global WIP limit."
        )
    else:
        summary = "Every recovered roadmap item has a durable queue record."
        next_action = (
            "Keep at most three independent claims active and advance dependency-ready "
            "work rather than concentrating the entire program on one PR."
        )
    return DeveloperQueueRecoveryHealth(
        recovery_item_count=len(expected_refs),
        admitted_recovery_item_count=admitted_count,
        nonterminal_recovery_item_count=nonterminal_count,
        unadmitted_task_refs=unadmitted_refs,
        admission_gap_detected=admission_gap,
        queue_starvation_detected=starvation,
        risk_ref=QUEUE_STARVATION_RISK_REF if starvation else None,
        safe_summary=summary,
        next_safe_action=next_action,
    )
