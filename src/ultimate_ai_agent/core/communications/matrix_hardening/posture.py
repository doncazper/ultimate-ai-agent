from __future__ import annotations

from ultimate_ai_agent.core.communications.matrix_messaging.constants import (
    MATRIX_MESSAGING_MAX_OUTBOX_RECORDS,
)
from ultimate_ai_agent.core.communications.matrix_sync.constants import (
    MATRIX_SYNC_MAX_BYTES,
    MATRIX_SYNC_MAX_CACHE_BYTES,
    MATRIX_SYNC_MAX_CACHE_EVENTS,
    MATRIX_SYNC_MAX_EVENTS,
    MATRIX_SYNC_MAX_RELATION_DEPTH,
    MATRIX_SYNC_MAX_ROOM_EVENT_REFS,
    MATRIX_SYNC_MAX_ROOMS,
)

from .contracts import (
    MatrixHardeningBudget,
    MatrixHardeningCheck,
    MatrixHardeningCheckCategory,
    MatrixHardeningCheckStatus,
    MatrixHardeningPosture,
    stable_matrix_hardening_ref,
)


def _check(
    category: MatrixHardeningCheckCategory,
    status: MatrixHardeningCheckStatus,
    summary: str,
    *,
    evidence_refs: tuple[str, ...] = (),
    blocker_refs: tuple[str, ...] = (),
) -> MatrixHardeningCheck:
    return MatrixHardeningCheck(
        check_ref=f"check-ref:matrix-hardening:{category.value.replace('_', '-')}",
        category=category,
        status=status,
        evidence_refs=evidence_refs,
        blocker_refs=blocker_refs,
        safe_summary=summary,
    )


def _budget(name: str, unit: str, limit: int) -> MatrixHardeningBudget:
    return MatrixHardeningBudget(
        budget_ref=f"budget-ref:matrix-hardening:{name}",
        unit=unit,  # type: ignore[arg-type]
        limit=limit,
        evidence_ref=f"evidence-ref:msg-mx-011:{name}-bound",
    )


def build_default_matrix_hardening_posture() -> MatrixHardeningPosture:
    checks = (
        _check(
            MatrixHardeningCheckCategory.large_room_backpressure,
            MatrixHardeningCheckStatus.passed,
            "Sync payload, room, event, relation, and retained-history bounds fail closed before resource escape.",
            evidence_refs=("evidence-ref:msg-mx-011:large-room-backpressure",),
        ),
        _check(
            MatrixHardeningCheckCategory.cache_queue_bounds,
            MatrixHardeningCheckStatus.passed,
            "Protected cache history and encrypted outbox record counts are cumulatively bounded.",
            evidence_refs=("evidence-ref:msg-mx-011:cache-outbox-bounds",),
        ),
        _check(
            MatrixHardeningCheckCategory.migration_multi_device,
            MatrixHardeningCheckStatus.blocked,
            "Cache migration and persistent multi-device ownership remain uncomposed and cannot be exercised by hardening.",
            blocker_refs=(
                "blocker-ref:msg-mx-011:cache-migration-executor-uncomposed",
                "blocker-ref:msg-mx-011:persistent-session-owner-unavailable",
            ),
        ),
        _check(
            MatrixHardeningCheckCategory.rate_limit_malicious_events,
            MatrixHardeningCheckStatus.passed,
            "Targeted API limits and hostile event shape, depth, replay, relation, and scope denials are verified locally.",
            evidence_refs=("evidence-ref:msg-mx-011:abuse-malicious-event-suite",),
        ),
        _check(
            MatrixHardeningCheckCategory.retention_deletion_low_disk,
            MatrixHardeningCheckStatus.passed,
            "Retention pruning, exact purge, stage cleanup, and content-free low-disk failure posture are verified.",
            evidence_refs=("evidence-ref:msg-mx-011:retention-low-disk-drill",),
        ),
        _check(
            MatrixHardeningCheckCategory.restart_offline_recovery,
            MatrixHardeningCheckStatus.passed,
            "Encrypted cache and outbox restart, stale state, uncertain outcome, and offline fail-closed paths are covered.",
            evidence_refs=("evidence-ref:msg-mx-011:restart-offline-recovery",),
        ),
        _check(
            MatrixHardeningCheckCategory.accessibility_keyboard_focus,
            MatrixHardeningCheckStatus.passed,
            "Desktop landmarks, status semantics, labeled controls, keyboard activation, and inspector focus behavior are verified.",
            evidence_refs=("evidence-ref:msg-mx-011:desktop-accessibility",),
        ),
        _check(
            MatrixHardeningCheckCategory.localization_readiness,
            MatrixHardeningCheckStatus.partial,
            "Operator statuses use bounded typed labels, but a production localization catalog is a later product lane.",
            blocker_refs=("blocker-ref:msg-mx-011:localization-catalog-not-selected",),
        ),
        _check(
            MatrixHardeningCheckCategory.telemetry_redaction,
            MatrixHardeningCheckStatus.passed,
            "Receipts, posture, errors, diagnostics, and test evidence remain safe-ref and content-free.",
            evidence_refs=("evidence-ref:msg-mx-011:telemetry-redaction-suite",),
        ),
        _check(
            MatrixHardeningCheckCategory.dependency_sbom,
            MatrixHardeningCheckStatus.passed,
            "Pinned Matrix dependencies remain subject to repository supply-chain, license, audit, and SBOM gates.",
            evidence_refs=("evidence-ref:msg-mx-011:dependency-sbom-gates",),
        ),
        _check(
            MatrixHardeningCheckCategory.rollback_safe_disable,
            MatrixHardeningCheckStatus.passed,
            "Accepted lanes retain exact rollback or compensation truth and block new starts under safe-disable.",
            evidence_refs=("evidence-ref:msg-mx-011:rollback-safe-disable-drills",),
        ),
        _check(
            MatrixHardeningCheckCategory.element_interoperability,
            MatrixHardeningCheckStatus.external_facility_required,
            "Independent Element Desktop and external test accounts were unavailable; no acceptance evidence is simulated.",
            blocker_refs=("blocker-ref:msg-mx-011:element-external-facility-required",),
        ),
    )
    budgets = (
        _budget("sync-response-bytes", "bytes", MATRIX_SYNC_MAX_BYTES),
        _budget("sync-batch-events", "events", MATRIX_SYNC_MAX_EVENTS),
        _budget("sync-rooms", "rooms", MATRIX_SYNC_MAX_ROOMS),
        _budget("cache-ciphertext-bytes", "bytes", MATRIX_SYNC_MAX_CACHE_BYTES),
        _budget("cache-retained-events", "events", MATRIX_SYNC_MAX_CACHE_EVENTS),
        _budget("room-event-refs", "events", MATRIX_SYNC_MAX_ROOM_EVENT_REFS),
        _budget("relation-depth", "relations", MATRIX_SYNC_MAX_RELATION_DEPTH),
        _budget("outbox-records", "records", MATRIX_MESSAGING_MAX_OUTBOX_RECORDS),
    )
    values: dict[str, object] = {
        "checks": checks,
        "budgets": budgets,
        "blocked_later_lane_refs": (
            "blocked-lane-ref:matrix:calls",
            "blocked-lane-ref:matrix:agent-room-participants",
            "blocked-lane-ref:matrix:hosted-infrastructure",
            "blocked-lane-ref:matrix:public-federation",
            "blocked-lane-ref:matrix:production-deployment",
        ),
        "safe_summary": (
            "MSG-MX-011 adds no runtime lane. Existing local Messenger primitives have "
            "bounded performance, cache, queue, failure, redaction, accessibility, and "
            "safe-disable evidence; migration, persistent multi-device ownership, a "
            "localization catalog, and Element interoperability remain explicit gaps."
        ),
    }
    payload = MatrixHardeningPosture.model_validate(
        {
            **values,
            "posture_ref": stable_matrix_hardening_ref(
                "posture-ref:matrix-hardening",
                MatrixHardeningPosture.model_construct(
                    posture_ref="posture-ref:matrix-hardening:pending",
                    **values,
                ).model_dump(mode="json", exclude={"posture_ref"}),
            ),
        }
    )
    return payload


__all__ = ["build_default_matrix_hardening_posture"]
