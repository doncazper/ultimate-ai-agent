import json

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.code import workbench as code_workbench
from ultimate_ai_agent.core.code import (
    GOVERNED_CODE_PATCH_REVIEW_CONTRACT_REF,
    GOVERNED_CODE_WORKBENCH_CONTRACT_REF,
    GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS,
    GOVERNED_CODE_WORKBENCH_REQUIRED_REF_FIELDS,
    GovernedCodePatchReview,
    GovernedCodeWorkbenchProposal,
    build_governed_code_patch_review,
    build_governed_code_workbench_proposal,
    governed_code_workbench_authority_posture,
    governed_code_workbench_surface_bindings,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


DENIED_FLAGS = [
    "apply_execution_enabled",
    "approval_grant_capture_enabled",
    "direct_file_write_enabled",
    "unrestricted_shell_enabled",
    "shell_subprocess_execution_enabled",
    "remote_execution_enabled",
    "broad_coding_agent_autonomy_enabled",
    "provider_sdk_call_enabled",
    "web_fetch_enabled",
    "connector_write_enabled",
    "diff_body_storage_enabled",
    "production_authority_enabled",
]
IMMUTABLE_BASE_REVISION_REF = f"git-commit-ref:sha1:{'a' * 40}"


def test_governed_code_workbench_proposal_denies_runtime_authority() -> None:
    proposal = build_governed_code_workbench_proposal()
    payload = proposal.model_dump(mode="json")

    assert payload["contract_ref"] == GOVERNED_CODE_WORKBENCH_CONTRACT_REF
    assert payload["proposal_ref"] == "code-proposal:founder-loop-safe-diff"
    assert payload["repo_scope_ref"].startswith("repo-scope:governed-code:")
    assert payload["safe_diff_summary_ref"].startswith(
        "diff-summary-ref:governed-code:"
    )
    assert payload["validation_plan_ref"].startswith(
        "validation-plan-ref:governed-code:"
    )
    assert payload["expected_apply_receipt_ref"].startswith(
        "receipt-plan:governed-code-apply:"
    )
    assert payload["expected_rollback_receipt_ref"].startswith(
        "rollback-receipt-plan:governed-code:"
    )
    assert payload["repo_local_scope_required"] is True
    assert payload["safe_diff_summary_only"] is True
    assert payload["validation_required_before_apply"] is True
    assert payload["approval_required_before_apply"] is True
    assert payload["atomic_apply_required"] is True
    assert payload["rollback_receipt_required"] is True
    assert payload["audit_required"] is True
    assert payload["redaction_required"] is True
    assert set(GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS) <= set(
        payload["blocked_state_refs"]
    )

    for denied_flag in DENIED_FLAGS:
        assert payload[denied_flag] is False
        unsafe = dict(payload)
        unsafe[denied_flag] = True
        with pytest.raises(ValidationError):
            GovernedCodeWorkbenchProposal(**unsafe)


def test_governed_code_workbench_rejects_unsafe_diff_or_secret_text() -> None:
    payload = build_governed_code_workbench_proposal().model_dump(mode="json")

    unsafe = dict(payload)
    unsafe["safe_summary"] = "raw patch material"
    with pytest.raises(ValidationError):
        GovernedCodeWorkbenchProposal(**unsafe)

    unsafe = dict(payload)
    unsafe["validation_plan_summary"] = "contains api key placeholder"
    with pytest.raises(ValidationError):
        GovernedCodeWorkbenchProposal(**unsafe)


def test_governed_code_patch_review_binds_exact_hash_target_and_scope_without_apply() -> (
    None
):
    patch_body = "--- a/module.py\n+++ b/module.py\n@@\n-old = 1\n+new = 2\n"
    review = build_governed_code_patch_review(
        patch_body=patch_body,
        target_refs=["repo-target-ref:src-module"],
        base_revision_ref=IMMUTABLE_BASE_REVISION_REF,
    )
    payload = review.model_dump(mode="json")

    assert payload["contract_ref"] == GOVERNED_CODE_PATCH_REVIEW_CONTRACT_REF
    assert payload["patch_hash_ref"].startswith("patch-hash-ref:sha256:")
    assert payload["target_fingerprint_ref"].startswith(
        "target-fingerprint-ref:sha256:"
    )
    assert payload["approval_scope_fingerprint_ref"].startswith(
        "approval-scope-fingerprint-ref:sha256:"
    )
    assert payload["line_addition_count"] == 1
    assert payload["line_deletion_count"] == 1
    assert payload["patch_body_persisted"] is False
    assert payload["patch_apply_performed"] is False
    assert payload["approval_ref_grants_authority"] is False
    assert patch_body not in json.dumps(payload)


def test_governed_code_patch_review_rejects_empty_unsafe_or_authorizing_input() -> None:
    with pytest.raises(ValueError):
        build_governed_code_patch_review(
            patch_body="",
            target_refs=["repo-target-ref:src-module"],
        )
    with pytest.raises(ValueError):
        build_governed_code_patch_review(
            patch_body="+api key placeholder",
            target_refs=["repo-target-ref:src-module"],
        )

    payload = build_governed_code_patch_review(
        patch_body="--- a/module.py\n+++ b/module.py\n@@\n-old = 1\n+new = 2\n",
        target_refs=["repo-target-ref:src-module"],
        base_revision_ref=IMMUTABLE_BASE_REVISION_REF,
    ).model_dump(mode="python")
    payload["patch_apply_performed"] = True
    with pytest.raises(ValidationError):
        GovernedCodePatchReview(**payload)


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    [
        ("patch_hash_ref", f"patch-hash-ref:sha256:{'0' * 64}"),
        ("target_fingerprint_ref", f"target-fingerprint-ref:sha256:{'0' * 64}"),
        (
            "approval_scope_fingerprint_ref",
            f"approval-scope-fingerprint-ref:sha256:{'0' * 64}",
        ),
        ("review_ref", f"code-patch-review-ref:sha256:{'0' * 64}"),
        (
            "validation_plan_ref",
            f"validation-plan-ref:governed-code:sha256:{'0' * 64}",
        ),
        (
            "rollback_plan_ref",
            f"rollback-plan-ref:governed-code:sha256:{'0' * 64}",
        ),
        (
            "idempotency_key_ref",
            f"idempotency-ref:governed-code:sha256:{'0' * 64}",
        ),
        ("proposal_ref", "code-proposal:changed-review-scope"),
        ("base_revision_ref", "git-revision-ref:base:changed"),
        ("target_refs", ["repo-target-ref:changed-module"]),
        ("line_addition_count", 2),
        ("line_deletion_count", 2),
        ("schema_version", "governed_code_patch_review.v999"),
        ("safe_summary", "Alternate bounded safe patch review summary."),
    ],
)
def test_governed_code_patch_review_rejects_relational_fingerprint_drift(
    field_name: str,
    replacement: object,
) -> None:
    payload = build_governed_code_patch_review(
        patch_body="--- a/module.py\n+++ b/module.py\n@@\n-old = 1\n+new = 2\n",
        target_refs=["repo-target-ref:src-module"],
        base_revision_ref=IMMUTABLE_BASE_REVISION_REF,
    ).model_dump(mode="python")
    payload[field_name] = replacement

    with pytest.raises(ValidationError):
        GovernedCodePatchReview(**payload)


def test_governed_code_patch_review_requires_canonical_unique_targets() -> None:
    with pytest.raises(ValueError, match="unique target refs"):
        build_governed_code_patch_review(
            patch_body="+bounded change\n",
            target_refs=["repo-target-ref:a", "repo-target-ref:a"],
        )

    payload = build_governed_code_patch_review(
        patch_body="+bounded change\n",
        target_refs=["repo-target-ref:a", "repo-target-ref:b"],
        base_revision_ref=IMMUTABLE_BASE_REVISION_REF,
    ).model_dump(mode="python")
    payload["target_refs"] = list(reversed(payload["target_refs"]))
    with pytest.raises(ValidationError, match="targets must be canonical"):
        GovernedCodePatchReview(**payload)


@pytest.mark.parametrize(
    ("patch_body", "target_refs", "error"),
    [
        (
            "x" * (code_workbench.GOVERNED_CODE_PATCH_MAX_UTF8_BYTES + 1),
            ["repo-target-ref:bounded"],
            "byte limit",
        ),
        (
            "é" * (code_workbench.GOVERNED_CODE_PATCH_MAX_UTF8_BYTES // 2 + 1),
            ["repo-target-ref:bounded"],
            "byte limit",
        ),
        (
            "+x\n" * (code_workbench.GOVERNED_CODE_PATCH_MAX_LINES + 1),
            ["repo-target-ref:bounded"],
            "line limit",
        ),
        (
            "+" + "x" * code_workbench.GOVERNED_CODE_PATCH_MAX_LINE_BYTES,
            ["repo-target-ref:bounded"],
            "per-line byte limit",
        ),
        (
            "+bounded change\n",
            [
                f"repo-target-ref:bounded-{index}"
                for index in range(
                    code_workbench.GOVERNED_CODE_PATCH_MAX_TARGET_REFS + 1
                )
            ],
            "target limit",
        ),
    ],
)
def test_governed_code_patch_review_bounds_inputs_before_hashing(
    patch_body: str,
    target_refs: list[str],
    error: str,
) -> None:
    with pytest.raises(ValueError, match=error):
        build_governed_code_patch_review(
            patch_body=patch_body,
            target_refs=target_refs,
        )


def test_governed_code_patch_review_requires_immutable_base_revision() -> None:
    with pytest.raises(ValueError, match="immutable base revision"):
        build_governed_code_patch_review(
            patch_body="+bounded change\n",
            target_refs=["repo-target-ref:bounded"],
        )
    with pytest.raises(ValueError, match="immutable base revision"):
        build_governed_code_patch_review(
            patch_body="+bounded change\n",
            target_refs=["repo-target-ref:bounded"],
            base_revision_ref="git-revision-ref:governed-code:current-base",
        )


def test_governed_code_patch_review_replay_and_revision_binding() -> None:
    inputs = {
        "patch_body": "+bounded change\n",
        "target_refs": ["repo-target-ref:bounded"],
        "base_revision_ref": IMMUTABLE_BASE_REVISION_REF,
    }
    first = build_governed_code_patch_review(**inputs)
    replay = build_governed_code_patch_review(**inputs)
    changed = build_governed_code_patch_review(
        **{
            **inputs,
            "base_revision_ref": f"git-commit-ref:sha1:{'b' * 40}",
        }
    )

    assert first == replay
    assert first.review_ref != changed.review_ref
    assert first.approval_scope_fingerprint_ref != (
        changed.approval_scope_fingerprint_ref
    )
    assert first.idempotency_key_ref != changed.idempotency_key_ref


@pytest.mark.parametrize(
    "unsafe_ref",
    [
        "repo-target-ref:@private-user",
        "repo-target-ref:host.internal",
        "repo-target-ref:/" + "Users/example/private",
        "repo-target-ref:PRIVATE_VALUE" + "=placeholder",
    ],
)
def test_governed_code_patch_review_rejects_unsafe_refs(unsafe_ref: str) -> None:
    with pytest.raises(
        ValueError,
        match="(?:ref is unsafe|unsafe content|structured safe ref)",
    ):
        build_governed_code_patch_review(
            patch_body="+bounded change\n",
            target_refs=[unsafe_ref],
            base_revision_ref=IMMUTABLE_BASE_REVISION_REF,
        )


def test_governed_code_patch_review_is_immutable() -> None:
    review = build_governed_code_patch_review(
        patch_body="+bounded change\n",
        target_refs=["repo-target-ref:bounded"],
        base_revision_ref=IMMUTABLE_BASE_REVISION_REF,
    )

    with pytest.raises(ValidationError, match="frozen"):
        review.patch_apply_performed = True  # type: ignore[misc]
    assert isinstance(review.target_refs, tuple)


def test_governed_code_workbench_nested_authority_truth_is_immutable() -> None:
    proposal = build_governed_code_workbench_proposal()

    with pytest.raises(ValidationError, match="frozen"):
        proposal.work_classification.execution_authorized = True  # type: ignore[misc]
    with pytest.raises(ValidationError, match="frozen"):
        proposal.delegation_proposal.worker_execution_enabled = True  # type: ignore[misc]
    with pytest.raises(ValidationError, match="frozen"):
        proposal.cache_context_economics.runtime_model_switch_performed = True  # type: ignore[misc]
    assert isinstance(proposal.work_classification.reason_refs, tuple)
    assert isinstance(proposal.delegation_proposal.blocked_execution_refs, tuple)
    assert isinstance(proposal.cache_context_economics.evidence_refs, tuple)


def test_governed_code_workbench_posture_and_surface_bindings() -> None:
    posture = governed_code_workbench_authority_posture()
    bindings = governed_code_workbench_surface_bindings()

    assert posture["safe_refs_only"] is True
    assert posture["repo_local_scope_required"] is True
    assert posture["validation_required_before_apply"] is True
    assert posture["approval_required_before_apply"] is True
    assert posture["atomic_apply_required"] is True
    assert posture["rollback_receipt_required"] is True
    for denied_flag in DENIED_FLAGS:
        assert posture[denied_flag] is False

    surfaces = {binding["surface"]: binding for binding in bindings}
    assert set(surfaces) == {"Today", "Code", "Actions", "Evidence", "Memory"}
    assert surfaces["Memory"]["feed_status"] == (
        "cross_surface_memory_intake_proposal_refs_only"
    )
    assert surfaces["Memory"]["feed_ref"] == "memory-intake-proposal:local-coding"


def test_founder_loop_today_binds_governed_code_workbench(tmp_path) -> None:
    repo = FounderLoopRepository(tmp_path, seed_defaults=True)
    today = repo.today_summary()

    assert (
        today["governed_code_workbench_contract_ref"]
        == GOVERNED_CODE_WORKBENCH_CONTRACT_REF
    )
    assert today["governed_code_workbench_status"] == (
        "implemented_reviewable_repo_local_diff_contract_apply_blocked"
    )
    assert today["governed_code_workbench_required_ref_fields"] == (
        GOVERNED_CODE_WORKBENCH_REQUIRED_REF_FIELDS
    )
    assert set(GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS) <= set(
        today["governed_code_workbench_required_blocked_refs"]
    )
    assert set(GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS) <= set(
        today["governed_code_workbench_blocked_state_refs"]
    )
    for denied_flag in DENIED_FLAGS:
        assert today["governed_code_workbench_authority_posture"][denied_flag] is False

    module_feeds = {item["module"]: item for item in today["module_feed_contract"]}
    assert module_feeds["Code"]["status"] == (
        "implemented_governed_code_workbench_contract_apply_blocked"
    )
    assert (
        GOVERNED_CODE_WORKBENCH_CONTRACT_REF
        in module_feeds["Code"]["current_feed_refs"]
    )

    code_item = next(
        item
        for item in today["evidence_timeline"]
        if item["item_kind"] == "governed_code_workbench_proposal_ref"
    )
    assert GOVERNED_CODE_WORKBENCH_CONTRACT_REF in code_item["status_refs"]
    assert (
        today["governed_code_workbench_safe_diff_summary_ref"]
        in (code_item["status_refs"])
    )
    assert (
        today["governed_code_workbench_expected_apply_receipt_ref"]
        in (code_item["receipt_refs"])
    )
    assert code_item["history_answers"]["approved"]["status"] == "blocked"
    assert (
        "no files were changed" in (code_item["history_answers"]["happened"]["answer"])
    )
    assert code_item["approval_ref_authority"] is False
    assert code_item["rollback_execution_enabled"] is False
    assert code_item["raw_evidence_included"] is False
    assert set(GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS) <= set(
        code_item["blocked_states"]
    )

    serialized = json.dumps(today, sort_keys=True).lower()
    for forbidden in [
        "raw diff",
        "full diff",
        "unredacted diff",
        "raw patch",
        "provider payload",
        "api key",
        "/users/",
        "/home/",
        "/var/",
        "/etc/",
    ]:
        assert forbidden not in serialized
