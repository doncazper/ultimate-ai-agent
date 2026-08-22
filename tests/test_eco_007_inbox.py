from __future__ import annotations

import itertools
from datetime import timedelta
from pathlib import Path

import pytest

from ultimate_ai_agent.core.approvals.authority import LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import (
    ApprovalRiskLevel,
    ApprovalSubjectType,
)
from ultimate_ai_agent.core.approvals.requests import ApprovalRequest
from ultimate_ai_agent.core.ecosystem.contracts import CanonicalOwnerId
from ultimate_ai_agent.core.ecosystem.inbox import (
    ECO_INBOX_ARTIFACT_RECORD_KIND_REF,
    ECO_INBOX_MODULE_REF,
    ECO_INBOX_MUTATION_ACTION,
    InboxArtifactKind,
    InboxConflict,
    InboxConversationThread,
    InboxEntityLink,
    InboxProposalKind,
    InboxProposalReviewState,
    InboxRepository,
    InboxSourceArtifact,
    InboxSourceBinding,
    InboxSourceMode,
    InboxSourceProposal,
    InboxTriageState,
)
from ultimate_ai_agent.core.ecosystem.local_data import (
    EcosystemLocalDataError,
    EcosystemLocalDataPlatform,
    InMemoryLocalDataCryptoBackend,
    InMemoryLocalDataPathResolver,
    PutRecord,
)
from ultimate_ai_agent.core.ecosystem.today import TodayItemKind
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.time import utc_now


WORKSPACE = "workspace-ref:eco-007"
OTHER_WORKSPACE = "workspace-ref:eco-007-other"
_COUNTER = itertools.count(1)


def _approval(
    authority: LocalApprovalAuthority, *, action: str, resources: tuple[str, ...]
):
    suffix = next(_COUNTER)
    request = ApprovalRequest(
        approval_request_id=f"approval_request_eco007_{suffix}",
        run_id="run_eco_007_tests",
        subject_type=ApprovalSubjectType.kernel_task,
        subject_id=f"subject_eco007_{suffix}",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="actor_eco007_test",
            authority_source=AuthoritySource.foundation_test,
        ),
        requested_action=action,
        purpose="Verify one exact ECO-007 Inbox mutation.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.user_private,
            source="source-ref:eco-007-test",
            requires_redaction=True,
        ),
        resource_refs=list(resources),
        expires_at=utc_now() + timedelta(minutes=10),
    )
    authority.create_request(request)
    grant = authority.create_test_grant(
        request.approval_request_id, approval_ref=f"approval_eco007_{suffix}"
    )
    return request.to_validation_request(grant.approval_ref)


@pytest.fixture
def workbench(
    tmp_path: Path,
) -> tuple[InboxRepository, LocalApprovalAuthority, Path]:
    authority = LocalApprovalAuthority()
    database_path = (tmp_path / "ecosystem.sqlite3").resolve()
    platform = EcosystemLocalDataPlatform(
        database_path=database_path,
        crypto_backend=InMemoryLocalDataCryptoBackend(),
        approval_authority=authority,
        path_resolver=InMemoryLocalDataPathResolver(),
    )
    for workspace_ref, key_ref in (
        (WORKSPACE, "key-version-ref:eco-007"),
        (OTHER_WORKSPACE, "key-version-ref:eco-007-other"),
    ):
        platform.create_workspace(
            workspace_ref=workspace_ref,
            key_version_ref=key_ref,
            approval=_approval(
                authority,
                action="ecosystem.local_data.create_workspace",
                resources=(workspace_ref, key_ref),
            ),
        )
    return InboxRepository(platform), authority, database_path


def _resources(
    *,
    workspace_ref: str = WORKSPACE,
    record_ref: str,
    operation_ref: str,
    idempotency_ref: str,
    related_refs: tuple[str, ...] = (),
) -> tuple[str, ...]:
    return InboxRepository.mutation_resource_refs(
        workspace_ref=workspace_ref,
        record_ref=record_ref,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        related_refs=related_refs,
    )


def _create_binding(
    repository: InboxRepository,
    authority: LocalApprovalAuthority,
    *,
    binding_ref: str = "inbox-binding-ref:manual",
    source_mode: InboxSourceMode = InboxSourceMode.manual,
    workspace_ref: str = WORKSPACE,
    state: str = "ready",
) -> InboxSourceBinding:
    binding = InboxSourceBinding(
        workspace_ref=workspace_ref,
        binding_ref=binding_ref,
        source_mode=source_mode,
        source_type_ref=f"source-type-ref:{source_mode.value}",
        display_name=f"Private {source_mode.value} source",
        state=state,
    )
    operation_ref = f"operation-ref:create-binding-{next(_COUNTER)}"
    idempotency_ref = f"idempotency-ref:create-binding-{next(_COUNTER)}"
    repository.create_binding(
        binding=binding,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_approval(
            authority,
            action=ECO_INBOX_MUTATION_ACTION,
            resources=_resources(
                workspace_ref=workspace_ref,
                record_ref=binding_ref,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
            ),
        ),
    )
    return binding


def _prepare(
    repository: InboxRepository,
    *,
    artifact_ref: str = "inbox-artifact-ref:one",
    binding_ref: str = "inbox-binding-ref:manual",
    content: str = "Discuss the launch checklist with the design team.",
    expires_at: str | None = None,
):
    return repository.prepare_manual_import(
        workspace_ref=WORKSPACE,
        binding_ref=binding_ref,
        artifact_ref=artifact_ref,
        artifact_kind=InboxArtifactKind.email,
        title="Private launch discussion",
        content=content,
        source_locator_ref=f"source-locator-ref:{artifact_ref.rsplit(':', 1)[-1]}",
        received_at="2026-08-21T10:00:00-07:00",
        operation_ref=f"operation-ref:import-{artifact_ref.rsplit(':', 1)[-1]}",
        idempotency_ref=f"idempotency-ref:import-{artifact_ref.rsplit(':', 1)[-1]}",
        evidence_refs=("evidence-ref:manual-review",),
        expires_at=expires_at,
    )


def _commit(
    repository: InboxRepository,
    authority: LocalApprovalAuthority,
    prepared,
):
    return repository.commit_import(
        prepared,
        approval=_approval(
            authority,
            action=ECO_INBOX_MUTATION_ACTION,
            resources=prepared.plan.approval_resource_refs,
        ),
    )


def test_manual_import_plan_is_content_free_and_payload_is_encrypted_at_rest(
    workbench,
) -> None:
    repository, authority, database_path = workbench
    _create_binding(repository, authority)
    raw_content = "Discuss the launch checklist with the design team."
    prepared = _prepare(repository, content=raw_content)

    plan_json = prepared.plan.model_dump_json()
    assert raw_content not in plan_json
    assert prepared.plan.raw_content_included is False
    assert prepared.plan.source_path_included is False
    assert prepared.plan.external_read_performed is False

    receipt = _commit(repository, authority, prepared)
    assert receipt.replayed is False
    assert (
        repository.read_artifact(
            workspace_ref=WORKSPACE, artifact_ref=prepared.artifact.artifact_ref
        ).artifact.content
        == raw_content
    )
    database_bytes = database_path.read_bytes()
    assert raw_content.encode() not in database_bytes
    assert prepared.artifact.title.encode() not in database_bytes


def test_exact_import_replay_is_idempotent(workbench) -> None:
    repository, authority, _database_path = workbench
    _create_binding(repository, authority)
    prepared = _prepare(repository)
    approval = _approval(
        authority,
        action=ECO_INBOX_MUTATION_ACTION,
        resources=prepared.plan.approval_resource_refs,
    )

    first = repository.commit_import(prepared, approval=approval)
    second = repository.commit_import(prepared, approval=approval)

    assert first.replayed is False
    assert second.replayed is True
    assert second.receipt_ref == first.receipt_ref


def test_source_mode_and_disabled_binding_fail_closed(workbench) -> None:
    repository, authority, _database_path = workbench
    _create_binding(
        repository,
        authority,
        binding_ref="inbox-binding-ref:synthetic",
        source_mode=InboxSourceMode.synthetic,
    )
    _create_binding(
        repository,
        authority,
        binding_ref="inbox-binding-ref:disabled",
        state="disabled",
    )

    with pytest.raises(InboxConflict, match="ECO_INBOX_SOURCE_MODE_MISMATCH"):
        _prepare(repository, binding_ref="inbox-binding-ref:synthetic")
    with pytest.raises(InboxConflict, match="ECO_INBOX_BINDING_NOT_READY"):
        _prepare(repository, binding_ref="inbox-binding-ref:disabled")


def test_synthetic_import_uses_only_synthetic_binding(workbench) -> None:
    repository, authority, _database_path = workbench
    binding_ref = "inbox-binding-ref:synthetic"
    _create_binding(
        repository,
        authority,
        binding_ref=binding_ref,
        source_mode=InboxSourceMode.synthetic,
    )

    prepared = repository.prepare_synthetic_import(
        workspace_ref=WORKSPACE,
        binding_ref=binding_ref,
        artifact_ref="inbox-artifact-ref:synthetic",
        artifact_kind=InboxArtifactKind.note,
        title="Synthetic fixture",
        content="Synthetic artifact for governed proposal testing.",
        source_locator_ref="source-locator-ref:synthetic-fixture",
        received_at="2026-08-21T17:00:00Z",
        operation_ref="operation-ref:import-synthetic",
        idempotency_ref="idempotency-ref:import-synthetic",
    )
    _commit(repository, authority, prepared)

    assert prepared.plan.source_mode == InboxSourceMode.synthetic
    assert (
        repository.read_artifact(
            workspace_ref=WORKSPACE, artifact_ref="inbox-artifact-ref:synthetic"
        ).artifact.external_read_performed
        is False
    )


def test_triage_links_are_workspace_scoped_and_search_is_content_free(
    workbench,
) -> None:
    repository, authority, _database_path = workbench
    _create_binding(repository, authority)
    prepared = _prepare(repository)
    _commit(repository, authority, prepared)
    link = InboxEntityLink(
        workspace_ref=WORKSPACE,
        entity_ref="task-ref:launch-review",
        owner_app=CanonicalOwnerId.tasks,
    )
    operation_ref = "operation-ref:triage-one"
    idempotency_ref = "idempotency-ref:triage-one"
    repository.triage_artifact(
        workspace_ref=WORKSPACE,
        artifact_ref=prepared.artifact.artifact_ref,
        triage_state=InboxTriageState.linked,
        classification_ref="classification-ref:reviewed",
        links=(link,),
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_approval(
            authority,
            action=ECO_INBOX_MUTATION_ACTION,
            resources=_resources(
                record_ref=prepared.artifact.artifact_ref,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
            ),
        ),
    )

    result = repository.search_artifacts(
        workspace_ref=WORKSPACE, query="launch checklist"
    )
    assert [item.artifact.artifact_ref for item in result.artifacts] == [
        prepared.artifact.artifact_ref
    ]
    assert result.raw_query_included is False
    assert result.query_ref.startswith("inbox-search-query-ref:sha256:")
    assert "query" not in type(result).model_fields
    assert (
        repository.search_artifacts(
            workspace_ref=OTHER_WORKSPACE, query="launch checklist"
        ).artifacts
        == ()
    )

    with pytest.raises(ValueError, match="CROSS_WORKSPACE_LINK_DENIED"):
        InboxSourceArtifact.model_validate(
            {
                **prepared.artifact.model_dump(mode="json"),
                "triage_state": InboxTriageState.linked,
                "links": (
                    InboxEntityLink(
                        workspace_ref=OTHER_WORKSPACE,
                        entity_ref="task-ref:foreign",
                        owner_app=CanonicalOwnerId.tasks,
                    ),
                ),
            }
        )


def test_thread_requires_existing_same_binding_artifacts(workbench) -> None:
    repository, authority, _database_path = workbench
    _create_binding(repository, authority)
    _create_binding(
        repository,
        authority,
        binding_ref="inbox-binding-ref:other",
    )
    prepared = _prepare(repository)
    _commit(repository, authority, prepared)
    thread = InboxConversationThread(
        workspace_ref=WORKSPACE,
        thread_ref="inbox-thread-ref:launch",
        binding_ref="inbox-binding-ref:manual",
        artifact_refs=(prepared.artifact.artifact_ref,),
    )
    operation_ref = "operation-ref:create-thread"
    idempotency_ref = "idempotency-ref:create-thread"
    repository.create_thread(
        thread=thread,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_approval(
            authority,
            action=ECO_INBOX_MUTATION_ACTION,
            resources=_resources(
                record_ref=thread.thread_ref,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
                related_refs=(thread.binding_ref, *thread.artifact_refs),
            ),
        ),
    )
    assert (
        repository.read_thread(workspace_ref=WORKSPACE, thread_ref=thread.thread_ref)
        == thread
    )

    with pytest.raises(InboxConflict, match="THREAD_ARTIFACT_BINDING_INVALID"):
        repository.create_thread(
            thread=thread.model_copy(
                update={
                    "thread_ref": "inbox-thread-ref:wrong-binding",
                    "binding_ref": "inbox-binding-ref:other",
                }
            ),
            operation_ref="operation-ref:wrong-binding-thread",
            idempotency_ref="idempotency-ref:wrong-binding-thread",
            approval=_approval(
                authority,
                action=ECO_INBOX_MUTATION_ACTION,
                resources=_resources(
                    record_ref="inbox-thread-ref:wrong-binding",
                    operation_ref="operation-ref:wrong-binding-thread",
                    idempotency_ref="idempotency-ref:wrong-binding-thread",
                    related_refs=(
                        "inbox-binding-ref:other",
                        prepared.artifact.artifact_ref,
                    ),
                ),
            ),
        )


def test_reviewed_proposal_is_still_non_mutating_and_can_feed_today(workbench) -> None:
    repository, authority, _database_path = workbench
    _create_binding(repository, authority)
    prepared = _prepare(repository)
    _commit(repository, authority, prepared)
    proposal = InboxSourceProposal(
        workspace_ref=WORKSPACE,
        proposal_ref="inbox-proposal-ref:launch-task",
        binding_ref=prepared.artifact.binding_ref,
        artifact_ref=prepared.artifact.artifact_ref,
        proposal_kind=InboxProposalKind.task,
        target_owner=CanonicalOwnerId.tasks,
        proposed_target_ref="task-ref:launch-follow-up",
        proposal_summary_ref="proposal-summary-ref:launch-follow-up",
        evidence_refs=("evidence-ref:manual-review",),
        due_at="2026-08-22T18:00:00Z",
    )
    create_operation = "operation-ref:create-proposal"
    create_idempotency = "idempotency-ref:create-proposal"
    repository.create_proposal(
        proposal=proposal,
        operation_ref=create_operation,
        idempotency_ref=create_idempotency,
        approval=_approval(
            authority,
            action=ECO_INBOX_MUTATION_ACTION,
            resources=_resources(
                record_ref=proposal.proposal_ref,
                operation_ref=create_operation,
                idempotency_ref=create_idempotency,
                related_refs=(proposal.binding_ref, proposal.artifact_ref),
            ),
        ),
    )
    with pytest.raises(InboxConflict, match="NOT_REVIEWED_FOR_TODAY"):
        repository.to_today_candidate(
            proposal, source_result_ref="source-result-ref:inbox-review"
        )

    review_operation = "operation-ref:review-proposal"
    review_idempotency = "idempotency-ref:review-proposal"
    repository.review_proposal(
        workspace_ref=WORKSPACE,
        proposal_ref=proposal.proposal_ref,
        review_state=InboxProposalReviewState.accepted_for_changeset,
        reviewer_ref="reviewer-ref:human",
        decision_reason_ref="decision-reason-ref:accepted",
        reviewed_at="2026-08-21T18:00:00Z",
        operation_ref=review_operation,
        idempotency_ref=review_idempotency,
        approval=_approval(
            authority,
            action=ECO_INBOX_MUTATION_ACTION,
            resources=_resources(
                record_ref=proposal.proposal_ref,
                operation_ref=review_operation,
                idempotency_ref=review_idempotency,
            ),
        ),
    )
    reviewed = repository.read_proposal(
        workspace_ref=WORKSPACE, proposal_ref=proposal.proposal_ref
    )
    candidate = repository.to_today_candidate(
        reviewed, source_result_ref="source-result-ref:inbox-review"
    )

    assert reviewed.mutation_authorized is False
    assert reviewed.target_write_performed is False
    assert reviewed.raw_content_included is False
    assert candidate.owner_app == CanonicalOwnerId.inbox
    assert candidate.item_kind == TodayItemKind.source_proposal
    assert candidate.canonical_ref == proposal.proposal_ref


def test_archive_removes_search_result_and_preserves_retention_candidate(
    workbench,
) -> None:
    repository, authority, _database_path = workbench
    _create_binding(repository, authority)
    prepared = _prepare(repository, expires_at="2026-08-20T00:00:00Z")
    _commit(repository, authority, prepared)
    operation_ref = "operation-ref:archive-artifact"
    idempotency_ref = "idempotency-ref:archive-artifact"
    repository.archive_artifact(
        workspace_ref=WORKSPACE,
        artifact_ref=prepared.artifact.artifact_ref,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_approval(
            authority,
            action=ECO_INBOX_MUTATION_ACTION,
            resources=_resources(
                record_ref=prepared.artifact.artifact_ref,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
            ),
        ),
    )

    assert (
        repository.search_artifacts(
            workspace_ref=WORKSPACE, query="launch checklist"
        ).artifacts
        == ()
    )
    assert (
        repository.read_artifact(
            workspace_ref=WORKSPACE, artifact_ref=prepared.artifact.artifact_ref
        ).archived
        is True
    )
    assert repository.retention_candidates(
        workspace_ref=WORKSPACE, as_of="2026-08-21T00:00:00Z"
    ) == (prepared.artifact.artifact_ref,)


def test_private_path_and_secret_shaped_inputs_are_rejected(workbench) -> None:
    repository, authority, _database_path = workbench
    _create_binding(repository, authority)

    with pytest.raises(ValueError, match="SOURCE_LOCATOR_REF_SAFE_REF_REQUIRED"):
        repository.prepare_manual_import(
            workspace_ref=WORKSPACE,
            binding_ref="inbox-binding-ref:manual",
            artifact_ref="inbox-artifact-ref:path",
            artifact_kind=InboxArtifactKind.file,
            title="Private file",
            content="Reviewed local artifact content.",
            source_locator_ref="/Users/private/source.txt",
            received_at="2026-08-21T17:00:00Z",
            operation_ref="operation-ref:import-path",
            idempotency_ref="idempotency-ref:import-path",
        )
    with pytest.raises(ValueError, match="SECRET_LIKE_CONTENT_DENIED"):
        _prepare(repository, content="Authorization: Bearer abcdefghijklmnop")


def test_generic_platform_apply_cannot_spoof_inbox_domain(workbench) -> None:
    repository, authority, _database_path = workbench
    operation_ref = "operation-ref:spoof-inbox"
    idempotency_ref = "idempotency-ref:spoof-inbox"
    record_ref = "inbox-artifact-ref:spoof"
    resources = _resources(
        record_ref=record_ref,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
    )
    operation = PutRecord(
        operation_ref=operation_ref,
        module_ref=ECO_INBOX_MODULE_REF,
        record_ref=record_ref,
        record_kind_ref=ECO_INBOX_ARTIFACT_RECORD_KIND_REF,
        safe_summary_ref="inbox-artifact-summary-ref:spoof",
        private_payload={"raw": "not-domain-validated"},
        search_terms=("spoof",),
        expected_version=0,
        retention_ref="retention-ref:test",
    )

    with pytest.raises(
        EcosystemLocalDataError, match="ECO_MUTATION_REQUIRES_REPOSITORY_VALIDATION"
    ):
        repository.platform.apply(
            workspace_ref=WORKSPACE,
            idempotency_ref=idempotency_ref,
            operations=(operation,),
            approval=_approval(
                authority,
                action=ECO_INBOX_MUTATION_ACTION,
                resources=resources,
            ),
            requested_action=ECO_INBOX_MUTATION_ACTION,
        )
