"""Authoritative Queue-of-Record V2 for bounded UAA developer work."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)

from uaa_developer_orchestrator.coordinator import DeveloperWorkTask
from uaa_developer_orchestrator.coordinator import DeveloperWorkTaskDraft
from uaa_developer_orchestrator.coordinator import DeveloperWorkQueueTaskView


QUEUE_RECORD_MANIFEST_PATH = "docs/roadmap/UAA_DEVELOPER_QUEUE_V2_MANIFEST.json"
QUEUE_RECORD_STARVATION_RISK_REF = "developer-risk-ref:queue-v2-starvation"
QUEUE_RECORD_SUPERSEDED_TASK_RISK_REF = (
    "developer-risk-ref:queue-v2-superseded-task-present"
)
QUEUE_RECORD_ITEM_COUNT = 37
QUEUE_RECORD_LEGACY_SOURCE_ACCEPTANCE_PREFIX = (
    "legacy-source-acceptance-ref:sha256:"
)


class DeveloperQueueRecordPolicy(BaseModel):
    automatic_agent_dispatch: Literal[False] = False
    automatic_git_or_github_mutation: Literal[False] = False
    explicit_ledger_confirmation_required: Literal[True] = True
    max_parallel_claims: Literal[3] = 3
    max_claims_per_wip_lane: Literal[1] = 1
    queue_starvation_is_failure: Literal[True] = True
    legacy_recovery_admission_enabled: Literal[False] = False

    model_config = ConfigDict(extra="forbid")


class DeveloperQueueRecordAuthorityBoundary(BaseModel):
    runtime_authority_granted: Literal[False] = False
    provider_authority_granted: Literal[False] = False
    connector_write_authority_granted: Literal[False] = False
    browser_authority_granted: Literal[False] = False
    shell_authority_granted: Literal[False] = False
    remote_dispatch_authority_granted: Literal[False] = False
    public_distribution_authority_granted: Literal[False] = False

    model_config = ConfigDict(extra="forbid")


class DeveloperQueueRecordWave(BaseModel):
    wave_id: str
    title: str
    objective: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_wave(self) -> "DeveloperQueueRecordWave":
        for value in [self.wave_id, self.title, self.objective]:
            validate_safe_task_text(value, "developer_queue_record_wave_text")
        return self


class DeveloperQueueRecordItem(BaseModel):
    queue_order: int = Field(..., ge=0)
    wave_id: str
    item_id: str
    slug: str
    title: str
    result_summary: str
    queue_status: Literal["owned_active", "reconciliation_active", "queued"]
    priority: Literal["p0", "p1", "p2", "p3"]
    concurrency: Literal["parallel_safe", "exclusive"]
    wip_lane: Literal["shared_core", "product_surface", "verification_read_only"]
    source_refs: list[str] = Field(default_factory=list)
    scope_refs: list[str] = Field(default_factory=list)
    guardrail_refs: list[str] = Field(default_factory=list)
    depends_on_item_ids: list[str] = Field(default_factory=list)
    merge_after_item_ids: list[str] = Field(default_factory=list)
    branch_ref: str
    worktree_ref: str
    workstream_ref: str
    existing_owner_ref: str | None = None
    next_safe_action: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_item(self) -> "DeveloperQueueRecordItem":
        for value in [
            *self.source_refs,
            *self.scope_refs,
            *self.guardrail_refs,
            self.branch_ref,
            self.worktree_ref,
            self.workstream_ref,
            *([self.existing_owner_ref] if self.existing_owner_ref else []),
        ]:
            validate_task_ref(value, "developer_queue_record_ref")
        for value in [
            self.wave_id,
            self.item_id,
            self.slug,
            self.title,
            self.result_summary,
            self.queue_status,
            self.priority,
            self.concurrency,
            self.wip_lane,
            self.next_safe_action,
        ]:
            validate_safe_task_text(value, "developer_queue_record_text")
        if not self.source_refs or not self.scope_refs or not self.guardrail_refs:
            raise ValueError("queue record item requires sources and exact scope")
        if self.item_id in {*self.depends_on_item_ids, *self.merge_after_item_ids}:
            raise ValueError("queue record item cannot depend on itself")
        for values in [self.depends_on_item_ids, self.merge_after_item_ids]:
            if len(values) != len(set(values)):
                raise ValueError("queue record item ordering refs must be unique")
        active = self.queue_status in {"owned_active", "reconciliation_active"}
        if active != (self.existing_owner_ref is not None):
            raise ValueError("queue record active owner binding is invalid")
        return self


class DeveloperQueueRecordGatedItem(BaseModel):
    gated_order: int = Field(..., ge=1)
    item_ref: str
    title: str
    gate_refs: list[str] = Field(default_factory=list)
    safe_summary: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_item(self) -> "DeveloperQueueRecordGatedItem":
        validate_task_ref(self.item_ref, "developer_queue_record_gated_ref")
        for value in self.gate_refs:
            validate_task_ref(value, "developer_queue_record_gate_ref")
        for value in [self.title, self.safe_summary]:
            validate_safe_task_text(value, "developer_queue_record_gated_text")
        if not self.gate_refs:
            raise ValueError("gated queue item requires explicit gates")
        return self


class DeveloperQueueRecordNonTopLevelItem(BaseModel):
    item_ref: str
    disposition: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_item(self) -> "DeveloperQueueRecordNonTopLevelItem":
        validate_task_ref(self.item_ref, "developer_queue_record_non_top_level_ref")
        validate_safe_task_text(
            self.disposition, "developer_queue_record_non_top_level_text"
        )
        return self


class DeveloperQueueRecordStalePullRequest(BaseModel):
    pull_request_number: int = Field(..., ge=1)
    title: str
    state: Literal["open_draft_conflict_dirty"]
    head_sha: str
    base_sha: str
    disposition: Literal["compare_then_supersede_or_close"]
    automatic_close_authorized: Literal[False] = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_pull_request(self) -> "DeveloperQueueRecordStalePullRequest":
        for value in [self.title, self.state, self.disposition]:
            validate_safe_task_text(value, "developer_queue_record_pr_text")
        for value in [self.head_sha, self.base_sha]:
            if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
                raise ValueError("queue record pull request SHA is invalid")
        return self


class DeveloperQueueRecordManifest(BaseModel):
    schema_version: Literal["uaa.developer_queue_manifest.v2"]
    artifact_status: Literal["authoritative_queue_of_record"]
    queue_ref: str
    supersedes_refs: list[str] = Field(default_factory=list)
    policy: DeveloperQueueRecordPolicy
    authority_boundary: DeveloperQueueRecordAuthorityBoundary
    waves: list[DeveloperQueueRecordWave] = Field(default_factory=list)
    items: list[DeveloperQueueRecordItem] = Field(default_factory=list)
    gated_items: list[DeveloperQueueRecordGatedItem] = Field(default_factory=list)
    non_top_level_items: list[DeveloperQueueRecordNonTopLevelItem] = Field(
        default_factory=list
    )
    stale_pull_requests: list[DeveloperQueueRecordStalePullRequest] = Field(
        default_factory=list
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_manifest(self) -> "DeveloperQueueRecordManifest":
        validate_task_ref(self.queue_ref, "developer_queue_record_queue_ref")
        for value in self.supersedes_refs:
            validate_task_ref(value, "developer_queue_record_supersedes_ref")
        if [item.queue_order for item in self.items] != list(
            range(QUEUE_RECORD_ITEM_COUNT)
        ):
            raise ValueError("queue record must contain contiguous Q00 through Q36")
        if [item.item_id for item in self.items] != [
            f"Q{index:02d}" for index in range(QUEUE_RECORD_ITEM_COUNT)
        ]:
            raise ValueError("queue record item ids must be exact Q00 through Q36")
        wave_ids = [wave.wave_id for wave in self.waves]
        if wave_ids != [f"wave-{index}" for index in range(7)]:
            raise ValueError("queue record waves must be exact wave-0 through wave-6")
        if any(item.wave_id not in set(wave_ids) for item in self.items):
            raise ValueError("queue record item references an unknown wave")
        slugs = [item.slug for item in self.items]
        if len(slugs) != len(set(slugs)):
            raise ValueError("queue record item slugs must be unique")
        seen: set[str] = set()
        for item in self.items:
            if not set(item.depends_on_item_ids).issubset(seen):
                raise ValueError("queue dependencies must reference earlier items")
            if not set(item.merge_after_item_ids).issubset(seen):
                raise ValueError("queue merge ordering must reference earlier items")
            for source_ref in item.source_refs:
                if not source_ref.startswith(
                    QUEUE_RECORD_LEGACY_SOURCE_ACCEPTANCE_PREFIX
                ):
                    continue
                parts = source_ref.split(":")
                if len(parts) != 5 or parts[3] != "sha256":
                    raise ValueError("queue legacy source acceptance ref is invalid")
                legacy_fingerprint_ref = (
                    f"planning-fingerprint-ref:sha256:{parts[2]}"
                )
                if source_ref != queue_record_legacy_source_acceptance_ref(
                    item, legacy_fingerprint_ref
                ):
                    raise ValueError("queue legacy source acceptance binding is stale")
            seen.add(item.item_id)
        goat_item = self.items[31]
        if goat_item.slug != "final-goatcitadel-comparison":
            raise ValueError("Q31 must remain the final GoatCitadel comparison")
        if self.items[32].depends_on_item_ids != ["Q15", "Q31"]:
            raise ValueError(
                "Wave 6 must begin after the CRM foundation and Q31 comparison gate"
            )
        if any(item.wave_id != "wave-6" for item in self.items[32:]):
            raise ValueError("Q32 through Q36 must remain in wave-6")
        if self.items[-1].slug != "cross-module-adoption-closure":
            raise ValueError("Q36 must remain the functional adoption closure")
        if [item.gated_order for item in self.gated_items] != list(range(1, 12)):
            raise ValueError("queue record requires the eleven ordered gated items")
        if len(self.stale_pull_requests) != 2 or {
            item.pull_request_number for item in self.stale_pull_requests
        } != {362, 365}:
            raise ValueError("queue record requires exact stale PR triage records")
        return self


class DeveloperQueueRecordHealth(BaseModel):
    schema_version: Literal["uaa.developer_queue_health.v2"] = (
        "uaa.developer_queue_health.v2"
    )
    queue_ref: str
    queue_item_count: Literal[37] = 37
    admitted_item_count: int = Field(..., ge=0)
    nonterminal_item_count: int = Field(..., ge=0)
    claimed_item_count: int = Field(..., ge=0)
    gated_item_count: Literal[11] = 11
    unadmitted_task_refs: list[str] = Field(default_factory=list)
    stale_contract_task_refs: list[str] = Field(default_factory=list)
    superseded_task_refs_present: list[str] = Field(default_factory=list)
    admission_gap_detected: bool
    record_drift_detected: bool
    queue_starvation_detected: bool
    stale_pull_request_triage_pending_count: Literal[2] = 2
    risk_refs: list[str] = Field(default_factory=list)
    safe_summary: str
    next_safe_action: str
    automatic_agent_dispatch_performed: Literal[False] = False
    git_or_github_mutation_performed: Literal[False] = False
    product_runtime_authority_granted: Literal[False] = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_health(self) -> "DeveloperQueueRecordHealth":
        validate_task_ref(self.queue_ref, "developer_queue_record_health_queue_ref")
        for value in [
            *self.unadmitted_task_refs,
            *self.stale_contract_task_refs,
            *self.superseded_task_refs_present,
            *self.risk_refs,
        ]:
            validate_task_ref(value, "developer_queue_record_health_ref")
        for value in [self.safe_summary, self.next_safe_action]:
            validate_safe_task_text(value, "developer_queue_record_health_text")
        if self.queue_starvation_detected and QUEUE_RECORD_STARVATION_RISK_REF not in self.risk_refs:
            raise ValueError("queue starvation risk binding is missing")
        if self.superseded_task_refs_present and QUEUE_RECORD_SUPERSEDED_TASK_RISK_REF not in self.risk_refs:
            raise ValueError("superseded task risk binding is missing")
        return self


def _read_json_without_duplicate_keys(path: Path) -> object:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        payload: dict[str, object] = {}
        for key, value in pairs:
            if key in payload:
                raise ValueError("duplicate queue record manifest key")
            payload[key] = value
        return payload

    try:
        return json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        raise ValueError("DEVELOPER_QUEUE_V2_MANIFEST_INVALID") from None


def load_developer_queue_record_manifest(
    root: Path | None = None,
) -> DeveloperQueueRecordManifest:
    repository_root = root or Path(__file__).resolve().parents[3]
    try:
        return DeveloperQueueRecordManifest.model_validate(
            _read_json_without_duplicate_keys(
                repository_root / QUEUE_RECORD_MANIFEST_PATH
            )
        )
    except (ValueError, TypeError):
        raise ValueError("DEVELOPER_QUEUE_V2_MANIFEST_INVALID") from None


def queue_record_task_ref(item: DeveloperQueueRecordItem) -> str:
    return f"dev-task:queue-v2-{item.item_id.lower()}-{item.slug}"


def queue_record_legacy_source_acceptance_ref(
    item: DeveloperQueueRecordItem,
    legacy_fingerprint_ref: str,
) -> str:
    """Bind one explicit legacy fingerprint to this item's current source set."""

    validate_task_ref(
        legacy_fingerprint_ref, "developer_queue_legacy_source_fingerprint_ref"
    )
    legacy_digest = legacy_fingerprint_ref.rsplit(":", maxsplit=1)[-1]
    source_refs = [
        ref
        for ref in item.source_refs
        if not ref.startswith(QUEUE_RECORD_LEGACY_SOURCE_ACCEPTANCE_PREFIX)
    ]
    digest = hashlib.sha256(
        json.dumps(
            {
                "item_id": item.item_id,
                "task_ref": queue_record_task_ref(item),
                "legacy_fingerprint_ref": legacy_fingerprint_ref,
                "source_refs": source_refs,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:24]
    return (
        f"{QUEUE_RECORD_LEGACY_SOURCE_ACCEPTANCE_PREFIX}{legacy_digest}:"
        f"sha256:{digest}"
    )


def _task_contract_ref(payload: dict[str, object]) -> str:
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"planning-contract-ref:sha256:{digest[:24]}"


def _task_contract_payload(
    *,
    task_ref: str,
    queue_order: int,
    title: str,
    safe_summary: str,
    priority: str,
    concurrency: str,
    wip_lane: str,
    in_scope_refs: list[str],
    out_of_scope_refs: list[str],
    sol_thinking_level: str,
    branch_ref: str,
    worktree_ref: str,
    workstream_ref: str,
    depends_on_task_refs: list[str],
    next_safe_action: str,
) -> dict[str, object]:
    return {
        "task_ref": task_ref,
        "queue_order": queue_order,
        "title": title,
        "safe_summary": safe_summary,
        "priority": priority,
        "concurrency": concurrency,
        "wip_lane": wip_lane,
        "in_scope_refs": in_scope_refs,
        "out_of_scope_refs": out_of_scope_refs,
        "sol_thinking_level": sol_thinking_level,
        "branch_ref": branch_ref,
        "worktree_ref": worktree_ref,
        "workstream_ref": workstream_ref,
        "depends_on_task_refs": depends_on_task_refs,
        "next_safe_action": next_safe_action,
    }


def queue_record_task_contract_ref(
    task: DeveloperWorkTask | DeveloperWorkTaskDraft | DeveloperWorkQueueTaskView,
) -> str:
    """Fingerprint the queue-owned task contract, excluding whole-manifest digest."""

    return _task_contract_ref(
        _task_contract_payload(
            task_ref=task.task_ref,
            queue_order=task.queue_order,
            title=task.title,
            safe_summary=task.safe_summary,
            priority=task.priority,
            concurrency=task.concurrency,
            wip_lane=task.wip_lane,
            in_scope_refs=task.in_scope_refs,
            out_of_scope_refs=task.out_of_scope_refs,
            sol_thinking_level=task.sol_thinking_level,
            branch_ref=task.branch_ref,
            worktree_ref=task.worktree_ref,
            workstream_ref=task.workstream_ref,
            depends_on_task_refs=task.depends_on_task_refs,
            next_safe_action=task.next_safe_action,
        )
    )


def queue_record_canonical_item_contract_ref(
    task: DeveloperWorkTask | DeveloperWorkTaskDraft | DeveloperWorkQueueTaskView,
) -> str:
    """Fingerprint one Queue V2 item, including its exact source refs.

    The digest intentionally excludes the whole-manifest fingerprint so an
    unrelated item edit cannot invalidate this admitted item.
    """

    return _task_contract_ref(
        {
            **_task_contract_payload(
                task_ref=task.task_ref,
                queue_order=task.queue_order,
                title=task.title,
                safe_summary=task.safe_summary,
                priority=task.priority,
                concurrency=task.concurrency,
                wip_lane=task.wip_lane,
                in_scope_refs=task.in_scope_refs,
                out_of_scope_refs=task.out_of_scope_refs,
                sol_thinking_level=task.sol_thinking_level,
                branch_ref=task.branch_ref,
                worktree_ref=task.worktree_ref,
                workstream_ref=task.workstream_ref,
                depends_on_task_refs=task.depends_on_task_refs,
                next_safe_action=task.next_safe_action,
            ),
            "canonical_task_ref": task.canonical_task_ref,
            "canonical_source_ref": task.canonical_source_ref,
            "canonical_source_refs": task.canonical_source_refs,
            "scope_contract_ref": task.scope_contract_ref,
            "worktree_posture": task.worktree_posture,
            "acceptance_refs": task.acceptance_refs,
            "verifier_refs": task.verifier_refs,
            "merge_gate_refs": task.merge_gate_refs,
        }
    ).replace("planning-contract-ref:", "planning-item-contract-ref:", 1)


def _manifest_item_contract_ref(
    item: DeveloperQueueRecordItem,
    *,
    task_ref_by_item_id: Mapping[str, str],
) -> str:
    return _task_contract_ref(
        _task_contract_payload(
            task_ref=task_ref_by_item_id[item.item_id],
            queue_order=item.queue_order,
            title=f"{item.item_id} {item.title}",
            safe_summary=item.result_summary,
            priority=item.priority,
            concurrency=item.concurrency,
            wip_lane=item.wip_lane,
            in_scope_refs=item.scope_refs,
            out_of_scope_refs=item.guardrail_refs,
            sol_thinking_level=(
                "xhigh" if item.concurrency == "exclusive" else "high"
            ),
            branch_ref=item.branch_ref,
            worktree_ref=item.worktree_ref,
            workstream_ref=item.workstream_ref,
            depends_on_task_refs=[
                task_ref_by_item_id[dependency]
                for dependency in item.depends_on_item_ids
            ],
            next_safe_action=item.next_safe_action,
        )
    )


def build_developer_queue_record_drafts(
    root: Path | None = None,
) -> list[DeveloperWorkTaskDraft]:
    repository_root = root or Path(__file__).resolve().parents[3]
    manifest_path = repository_root / QUEUE_RECORD_MANIFEST_PATH
    manifest = load_developer_queue_record_manifest(repository_root)
    manifest_digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    task_ref_by_item_id = {
        item.item_id: queue_record_task_ref(item) for item in manifest.items
    }
    drafts: list[DeveloperWorkTaskDraft] = []
    for item in manifest.items:
        draft = DeveloperWorkTaskDraft(
            task_ref=task_ref_by_item_id[item.item_id],
            queue_order=item.queue_order,
            title=f"{item.item_id} {item.title}",
            safe_summary=item.result_summary,
            priority=item.priority,
            concurrency=item.concurrency,
            wip_lane=item.wip_lane,
            canonical_task_ref=f"canonical-task-ref:queue-v2/{item.item_id}",
            canonical_source_ref=f"repo-ref:developer-queue-v2/{item.item_id}",
            canonical_source_fingerprint_ref=(
                f"planning-fingerprint-ref:sha256:{manifest_digest[:24]}"
            ),
            canonical_source_refs=item.source_refs,
            scope_contract_ref=f"scope-contract-ref:queue-v2/{item.item_id}",
            in_scope_refs=item.scope_refs,
            out_of_scope_refs=item.guardrail_refs,
            sol_thinking_level=(
                "xhigh" if item.concurrency == "exclusive" else "high"
            ),
            branch_ref=item.branch_ref,
            worktree_ref=item.worktree_ref,
            workstream_ref=item.workstream_ref,
            acceptance_refs=[
                f"acceptance-ref:queue-v2/{item.item_id}/result",
                f"acceptance-ref:queue-v2/{item.item_id}/scope",
            ],
            verifier_refs=[
                f"verifier-ref:queue-v2/{item.item_id}/focused",
                f"verifier-ref:queue-v2/{item.item_id}/redaction",
            ],
            merge_gate_refs=[
                f"merge-gate-ref:queue-v2/{item.item_id}/independent-review",
                f"merge-gate-ref:queue-v2/{item.item_id}/exact-head-ci",
            ],
            depends_on_task_refs=[
                task_ref_by_item_id[dependency]
                for dependency in item.depends_on_item_ids
            ],
            next_safe_action=item.next_safe_action,
        )
        drafts.append(
            draft.model_copy(
                update={
                    "canonical_item_contract_ref": (
                        queue_record_canonical_item_contract_ref(draft)
                    )
                }
            )
        )
    return drafts


def assess_developer_queue_record_health(
    *,
    manifest: DeveloperQueueRecordManifest,
    task_states: Mapping[str, str],
    task_contract_refs: Mapping[str, str] | None = None,
) -> DeveloperQueueRecordHealth:
    expected_refs = [queue_record_task_ref(item) for item in manifest.items]
    unadmitted_refs = [ref for ref in expected_refs if ref not in task_states]
    task_ref_by_item_id = {
        item.item_id: queue_record_task_ref(item) for item in manifest.items
    }
    expected_contract_refs = {
        task_ref_by_item_id[item.item_id]: _manifest_item_contract_ref(
            item,
            task_ref_by_item_id=task_ref_by_item_id,
        )
        for item in manifest.items
    }
    observed_contract_refs = task_contract_refs or {}
    stale_contract_refs = [
        ref
        for ref in expected_refs
        if ref in observed_contract_refs
        and observed_contract_refs[ref] != expected_contract_refs[ref]
    ]
    admitted_count = len(expected_refs) - len(unadmitted_refs)
    nonterminal_count = sum(
        task_states.get(ref) in {"queued", "claimed", "blocked", "review"}
        for ref in expected_refs
    )
    claimed_count = sum(task_states.get(ref) == "claimed" for ref in expected_refs)
    superseded_refs = sorted(
        ref for ref in task_states if ref.startswith("dev-task:recovery-")
    )
    admission_gap = bool(unadmitted_refs or stale_contract_refs)
    starvation = admission_gap and nonterminal_count == 0
    risk_refs = [
        *([QUEUE_RECORD_STARVATION_RISK_REF] if starvation else []),
        *(
            [QUEUE_RECORD_SUPERSEDED_TASK_RISK_REF]
            if superseded_refs
            else []
        ),
    ]
    if starvation:
        summary = (
            "The authoritative queue has no admitted nonterminal item. This is a "
            "control-plane starvation failure."
        )
        next_action = (
            "Explicitly admit Queue-of-Record V2 and claim only named owner-held work "
            "within the three distinct WIP lanes."
        )
    elif admission_gap:
        summary = "Queue-of-Record V2 has missing or stale durable records."
        next_action = (
            "Idempotently amend exact stale queued contracts and admit remaining V2 "
            "records without duplicating owners or activating gated work."
        )
    elif superseded_refs:
        summary = "Queue-of-Record V2 is admitted but superseded recovery tasks remain."
        next_action = (
            "Reconcile superseded recovery records explicitly before any claim; do not "
            "silently execute duplicate work."
        )
    else:
        summary = "All thirty-seven authoritative queue items have durable records."
        next_action = (
            "Advance dependency-ready work with one named owner per lane and keep the "
            "eleven authority-heavy items visible but gated."
        )
    return DeveloperQueueRecordHealth(
        queue_ref=manifest.queue_ref,
        admitted_item_count=admitted_count,
        nonterminal_item_count=nonterminal_count,
        claimed_item_count=claimed_count,
        unadmitted_task_refs=unadmitted_refs,
        stale_contract_task_refs=stale_contract_refs,
        superseded_task_refs_present=superseded_refs,
        admission_gap_detected=admission_gap,
        record_drift_detected=bool(stale_contract_refs),
        queue_starvation_detected=starvation,
        risk_refs=risk_refs,
        safe_summary=summary,
        next_safe_action=next_action,
    )
