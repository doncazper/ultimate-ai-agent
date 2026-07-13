from __future__ import annotations

from typing import Any


FOUNDER_LOOP_EXACT_ATTENTION_ACTION_REF = (
    "founder-action:canonical-readme-metadata-inspection"
)
FOUNDER_LOOP_EXACT_ATTENTION_SOURCE_EVIDENCE_REF = (
    "evidence-ref:founder-loop:canonical-readme-metadata"
)


def ensure_exact_attention_action(repository: Any, record_model: Any) -> None:
    """Seed one exact metadata action without coupling its contract to storage."""

    with repository._connect() as conn:  # noqa: SLF001 - internal storage helper
        existing = conn.execute(
            "SELECT item_ref FROM action_inbox WHERE item_ref = ?",
            (FOUNDER_LOOP_EXACT_ATTENTION_ACTION_REF,),
        ).fetchone()
        if existing is not None:
            return
        repository._upsert_action_record(  # noqa: SLF001 - internal storage helper
            conn,
            record_model(
                item_ref=FOUNDER_LOOP_EXACT_ATTENTION_ACTION_REF,
                title="Inspect canonical repository overview metadata",
                safe_summary=(
                    "Inspect metadata for the predeclared canonical repository "
                    "overview without reading file content."
                ),
                surface="Today",
                priority="medium",
                risk_class="low",
                action_kind="exact_filesystem_metadata_inspection",
                status="review_ready",
                side_effect_class="local_dev_workspace_only",
                authority_boundary=(
                    "Python Agent Core requires inspected source refs, exact local "
                    "approval, and a mission-scoped files/read lease."
                ),
                approval_required=True,
                approval_envelope_ref=(
                    "approval-envelope:founder-loop:canonical-readme-metadata"
                ),
                approval_envelope_status="review_ready_exact_scope_required",
                state_change_contract_ref=(
                    "contract-ref:founder-loop-attention-workflow:v1"
                ),
                state_change_readiness="exact_metadata_action_review_ready",
                blocked_state="Exact approval and mission lease are required.",
                evidence_refs=[
                    FOUNDER_LOOP_EXACT_ATTENTION_SOURCE_EVIDENCE_REF
                ],
                idempotency_key_ref=(
                    "idempotency-ref:founder-loop:canonical-readme-metadata"
                ),
                expires_at="recheck_before_exact_execution",
                stale_state="recheck_sources_approval_and_lease_before_start",
                rollback_ref=(
                    "rollback-ref:founder-loop-attention-workflow:read-only-no-mutation"
                ),
                safe_disable_ref=(
                    "safe-disable-ref:founder-loop-filesystem-metadata-v1"
                ),
                next_safe_action=(
                    "Inspect the safe source refs before preparing exact execution."
                ),
            ),
        )


__all__ = [
    "FOUNDER_LOOP_EXACT_ATTENTION_ACTION_REF",
    "FOUNDER_LOOP_EXACT_ATTENTION_SOURCE_EVIDENCE_REF",
    "ensure_exact_attention_action",
]
