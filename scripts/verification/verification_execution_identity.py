from __future__ import annotations

import fcntl
import hashlib
import hmac
import json
import os
import re
import secrets
import stat
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable, Iterator

from ultimate_ai_agent.core._compat import UTC

from scripts.verification.verification_contracts import (
    DIGEST_PATTERN,
    MAX_DURATION_MS,
    SAFE_REF_PATTERN,
    SHA_PATTERN,
    TYPESCRIPT_EXECUTION_COMMAND_REFS,
    VerificationPlan,
    VerificationTerminalStatus,
    VerificationUnit,
    dependency_state_fingerprint,
    verification_unit_definition_fingerprint,
)


IDENTITY_SCHEMA_VERSION = "uaa_verification_execution_identity.v2"
TERMINAL_PROOF_SCHEMA_VERSION = "uaa_verification_execution_terminal_proof.v1"
FENCE_STATE_SCHEMA_VERSION = "uaa_verification_execution_fence_state.v2"
REDACTION_STATUS = "content_free_refs_hashes_counts_and_timestamps_only"
MAX_STATE_BYTES = 32 * 1024
MAX_FENCE_ENTRIES = 1024
MAX_RESULT_REFS = 256
_OWNER_TOKEN_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)
_STATE_NAME_PATTERN = re.compile(r"^execution-[0-9a-f]{64}\.json$")
_STAGE_NAME_PATTERN = re.compile(
    r"^\.(execution-[0-9a-f]{64}\.json)\.[0-9]{1,20}\.[0-9a-f]{16}\.tmp$"
)
_LOCK_NAME = ".verification-execution-fence.lock"


class VerificationExecutionIdentityError(ValueError):
    """An execution identity or terminal proof is not exact and content-bound."""


class VerificationExecutionFenceError(RuntimeError):
    """The durable execution fence could not be used safely."""


class VerificationExecutionFenceStateError(VerificationExecutionFenceError):
    """Existing fence state is malformed, unsafe, or contradictory."""


class VerificationExecutionFenceCapacityError(VerificationExecutionFenceError):
    """The bounded execution fence cannot accept another exact identity."""


class VerificationExecutionFenceDisposition(StrEnum):
    START_GRANTED = "start_granted"
    TERMINAL_PROOF_REUSED = "terminal_proof_reused"
    DETERMINISTIC_FAILURE_REJECTED = "deterministic_failure_rejected"
    RECOVERY_REQUIRED = "recovery_required"
    EXCLUSIVE_RESOURCE_ATTEMPT_REJECTED = "exclusive_resource_attempt_rejected"


class VerificationExecutionFailureCategory(StrEnum):
    NOT_APPLICABLE = "not_applicable"
    DETERMINISTIC_CODE_FAILURE = "deterministic_code_failure"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"
    UNKNOWN_EXECUTION = "unknown_execution"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


_FAILURE_REASON_CATEGORIES = {
    "reason-ref:verification:not-applicable": (
        VerificationExecutionFailureCategory.NOT_APPLICABLE
    ),
    "reason-ref:verification:deterministic-code-failure": (
        VerificationExecutionFailureCategory.DETERMINISTIC_CODE_FAILURE
    ),
    "reason-ref:verification:infrastructure-failure": (
        VerificationExecutionFailureCategory.INFRASTRUCTURE_FAILURE
    ),
    "reason-ref:verification:execution-result-unknown": (
        VerificationExecutionFailureCategory.UNKNOWN_EXECUTION
    ),
    "reason-ref:verification:execution-blocked": (
        VerificationExecutionFailureCategory.BLOCKED
    ),
    "reason-ref:verification:execution-cancelled": (
        VerificationExecutionFailureCategory.CANCELLED
    ),
}


def _canonical_digest(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _validate_ref(value: object, *, label: str) -> str:
    if not isinstance(value, str) or SAFE_REF_PATTERN.fullmatch(value) is None:
        raise VerificationExecutionIdentityError(f"{label} must be a bounded safe ref")
    return value


def _validate_digest(value: object, *, label: str) -> str:
    if not isinstance(value, str) or DIGEST_PATTERN.fullmatch(value) is None:
        raise VerificationExecutionIdentityError(
            f"{label} must be a lowercase SHA-256 digest"
        )
    return value


def _validate_timestamp(value: object, *, label: str) -> datetime:
    if not isinstance(value, str) or _TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise VerificationExecutionIdentityError(f"{label} must be canonical UTC")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise VerificationExecutionIdentityError(
            f"{label} must be canonical UTC"
        ) from exc
    if parsed.tzinfo != UTC:
        raise VerificationExecutionIdentityError(f"{label} must be canonical UTC")
    return parsed


def _validate_digest_ref(value: object, *, prefix: str, label: str) -> str:
    ref = _validate_ref(value, label=label)
    if not ref.startswith(prefix):
        raise VerificationExecutionIdentityError(
            f"{label} must be a content-bound verification ref"
        )
    _validate_digest(ref.removeprefix(prefix), label=label)
    return ref


def _validate_terminal_result_ref(value: object) -> str:
    for prefix in (
        "result-ref:ci:",
        "result-ref:verification:",
        "receipt:verification:",
    ):
        if isinstance(value, str) and value.startswith(prefix):
            return _validate_digest_ref(
                value,
                prefix=prefix,
                label="terminal result ref",
            )
    raise VerificationExecutionIdentityError(
        "terminal result ref must be a content-bound verification ref"
    )


def _classify_terminal_failure(
    *,
    status: VerificationTerminalStatus,
    failure_reason_ref: object,
    failure_evidence_ref: object,
) -> VerificationExecutionFailureCategory:
    if not isinstance(status, VerificationTerminalStatus):
        raise VerificationExecutionIdentityError(
            "terminal proof status must be typed"
        )
    reason_ref = _validate_ref(failure_reason_ref, label="terminal failure reason ref")
    category = _FAILURE_REASON_CATEGORIES.get(reason_ref)
    if category is None:
        raise VerificationExecutionIdentityError(
            "terminal failure reason is not canonically classified"
        )
    expected_category_by_status = {
        VerificationTerminalStatus.PASSED: {
            VerificationExecutionFailureCategory.NOT_APPLICABLE
        },
        VerificationTerminalStatus.FAILED: {
            VerificationExecutionFailureCategory.DETERMINISTIC_CODE_FAILURE,
            VerificationExecutionFailureCategory.INFRASTRUCTURE_FAILURE,
            VerificationExecutionFailureCategory.UNKNOWN_EXECUTION,
        },
        VerificationTerminalStatus.BLOCKED: {
            VerificationExecutionFailureCategory.BLOCKED
        },
        VerificationTerminalStatus.CANCELLED: {
            VerificationExecutionFailureCategory.CANCELLED
        },
    }
    if status not in expected_category_by_status:
        raise VerificationExecutionIdentityError(
            "terminal proof status is not terminal"
        )
    if category not in expected_category_by_status.get(status, set()):
        raise VerificationExecutionIdentityError(
            "terminal failure category contradicts terminal status"
        )
    if category is VerificationExecutionFailureCategory.NOT_APPLICABLE:
        if failure_evidence_ref is not None:
            raise VerificationExecutionIdentityError(
                "passed execution cannot claim failure evidence"
            )
    else:
        if failure_evidence_ref is None:
            raise VerificationExecutionIdentityError(
                "non-passing execution requires content-bound failure evidence"
            )
        _validate_terminal_result_ref(failure_evidence_ref)
    return category


@dataclass(frozen=True)
class VerificationExecutionIdentity:
    schema_version: str
    identity_ref: str
    repository_sha: str
    plan_fingerprint: str
    unit_ref: str
    execution_surface_ref: str
    verification_definition_fingerprint: str
    verification_dag_fingerprint: str
    unit_definition_fingerprint: str
    command_selection_fingerprint: str
    dependency_state_fingerprint: str
    dependency_lock_fingerprint: str
    platform_fingerprint: str
    command_manifest_fingerprint: str
    verifier_definition_fingerprint: str
    test_collection_fingerprint: str
    test_inventory_fingerprint: str
    pytest_shard_plan_fingerprint: str
    typescript_project_fingerprint: str
    typescript_runtime_fingerprint: str | None
    typescript_version_ref: str | None
    exclusive_resource_ref: str | None
    exclusive_resource_attempt_fingerprint: str | None
    identity_fingerprint: str
    redaction_status: str = REDACTION_STATUS

    def validate(self) -> None:
        if self.schema_version != IDENTITY_SCHEMA_VERSION:
            raise VerificationExecutionIdentityError(
                "unsupported verification execution identity schema"
            )
        for value, label in (
            (self.schema_version, "execution identity schema"),
            (self.identity_ref, "execution identity ref"),
            (self.unit_ref, "execution unit ref"),
            (self.execution_surface_ref, "execution surface ref"),
        ):
            _validate_ref(value, label=label)
        if SHA_PATTERN.fullmatch(self.repository_sha) is None:
            raise VerificationExecutionIdentityError(
                "execution identity requires an exact lowercase SHA"
            )
        for value, label in (
            (self.plan_fingerprint, "execution plan fingerprint"),
            (
                self.verification_definition_fingerprint,
                "verification definition fingerprint",
            ),
            (self.verification_dag_fingerprint, "verification DAG fingerprint"),
            (self.unit_definition_fingerprint, "unit definition fingerprint"),
            (self.command_selection_fingerprint, "command selection fingerprint"),
            (self.dependency_state_fingerprint, "dependency state fingerprint"),
            (self.dependency_lock_fingerprint, "dependency lock fingerprint"),
            (self.platform_fingerprint, "platform fingerprint"),
            (self.command_manifest_fingerprint, "command manifest fingerprint"),
            (self.verifier_definition_fingerprint, "verifier definition fingerprint"),
            (self.test_collection_fingerprint, "test collection fingerprint"),
            (self.test_inventory_fingerprint, "test inventory fingerprint"),
            (self.pytest_shard_plan_fingerprint, "pytest shard plan fingerprint"),
            (self.typescript_project_fingerprint, "TypeScript project fingerprint"),
            (self.identity_fingerprint, "execution identity fingerprint"),
        ):
            _validate_digest(value, label=label)
        if (self.typescript_runtime_fingerprint is None) != (
            self.typescript_version_ref is None
        ):
            raise VerificationExecutionIdentityError(
                "TypeScript execution identity runtime bindings must be paired"
            )
        if self.typescript_runtime_fingerprint is not None:
            _validate_digest(
                self.typescript_runtime_fingerprint,
                label="TypeScript runtime fingerprint",
            )
            _validate_ref(self.typescript_version_ref, label="TypeScript version ref")
        if (self.exclusive_resource_ref is None) != (
            self.exclusive_resource_attempt_fingerprint is None
        ):
            raise VerificationExecutionIdentityError(
                "exclusive resource execution bindings must be paired"
            )
        if self.exclusive_resource_ref is not None:
            _validate_ref(
                self.exclusive_resource_ref,
                label="exclusive verification resource ref",
            )
            if self.exclusive_resource_ref not in {
                "resource-ref:complete-pytest",
                "resource-ref:typescript-typecheck",
            }:
                raise VerificationExecutionIdentityError(
                    "exclusive verification resource is not canonical"
                )
            _validate_digest(
                self.exclusive_resource_attempt_fingerprint,
                label="exclusive resource attempt fingerprint",
            )
            if (
                self.exclusive_resource_ref == "resource-ref:typescript-typecheck"
                and self.typescript_runtime_fingerprint is None
            ):
                raise VerificationExecutionIdentityError(
                    "TypeScript resource attempt requires an exact runtime binding"
                )
            expected_resource_fingerprint = (
                verification_exclusive_resource_attempt_fingerprint(
                    repository_sha=self.repository_sha,
                    dependency_state_ref=self.dependency_state_fingerprint,
                    exclusive_resource_ref=self.exclusive_resource_ref,
                    typescript_runtime_fingerprint=(
                        self.typescript_runtime_fingerprint
                    ),
                    typescript_version_ref=self.typescript_version_ref,
                )
            )
            if not hmac.compare_digest(
                self.exclusive_resource_attempt_fingerprint,
                expected_resource_fingerprint,
            ):
                raise VerificationExecutionIdentityError(
                    "exclusive resource attempt fingerprint is not content bound"
                )
        if self.redaction_status != REDACTION_STATUS:
            raise VerificationExecutionIdentityError(
                "execution identity redaction posture is invalid"
            )
        expected = verification_execution_identity_fingerprint(self)
        if self.identity_fingerprint != expected:
            raise VerificationExecutionIdentityError(
                "execution identity fingerprint does not match its payload"
            )
        if self.identity_ref != f"execution-identity:{expected}":
            raise VerificationExecutionIdentityError(
                "execution identity ref is not content-bound"
            )


def verification_execution_identity_fingerprint(
    identity: VerificationExecutionIdentity,
) -> str:
    payload = {
        field_name: getattr(identity, field_name)
        for field_name in VerificationExecutionIdentity.__dataclass_fields__
        if field_name not in {"identity_ref", "identity_fingerprint"}
    }
    return _canonical_digest(payload)


def verification_exclusive_resource_attempt_fingerprint(
    *,
    repository_sha: str,
    dependency_state_ref: str,
    exclusive_resource_ref: str,
    typescript_runtime_fingerprint: str | None,
    typescript_version_ref: str | None,
) -> str:
    if SHA_PATTERN.fullmatch(repository_sha) is None:
        raise VerificationExecutionIdentityError(
            "exclusive resource attempt requires an exact repository SHA"
        )
    _validate_digest(
        dependency_state_ref,
        label="exclusive resource dependency state fingerprint",
    )
    _validate_ref(exclusive_resource_ref, label="exclusive verification resource ref")
    if (typescript_runtime_fingerprint is None) != (typescript_version_ref is None):
        raise VerificationExecutionIdentityError(
            "exclusive TypeScript resource bindings must be paired"
        )
    if typescript_runtime_fingerprint is not None:
        _validate_digest(
            typescript_runtime_fingerprint,
            label="exclusive TypeScript runtime fingerprint",
        )
        _validate_ref(typescript_version_ref, label="exclusive TypeScript version ref")
    return _canonical_digest(
        {
            "repository_sha": repository_sha,
            "dependency_state_fingerprint": dependency_state_ref,
            "exclusive_resource_ref": exclusive_resource_ref,
            "typescript_runtime_fingerprint": typescript_runtime_fingerprint,
            "typescript_version_ref": typescript_version_ref,
        }
    )


def build_verification_execution_identity(
    plan: VerificationPlan,
    unit: VerificationUnit,
    *,
    execution_surface_ref: str,
    typescript_runtime_fingerprint: str | None = None,
    typescript_version_ref: str | None = None,
) -> VerificationExecutionIdentity:
    """Bind one canonical unit start to all plan and dependency dimensions."""

    plan.validate()
    unit.validate()
    if plan.schema_version not in {
        "uaa_ci_command_manifest.v4",
        "uaa_ci_command_manifest.v3",
        "uaa_verification_plan.v3",
    }:
        raise VerificationExecutionIdentityError(
            "execution identity requires a v3 plan with exact DAG bindings"
        )
    if plan.verification_dag_fingerprint is None:
        raise VerificationExecutionIdentityError(
            "execution identity requires an exact verification DAG binding"
        )
    if unit.unit_ref not in plan.selected_unit_refs:
        raise VerificationExecutionIdentityError(
            "verification unit is not a member of the exact plan"
        )
    selected_unit_definitions = dict(plan.selected_unit_definition_fingerprints)
    supplied_unit_fingerprint = verification_unit_definition_fingerprint(unit)
    expected_unit_fingerprint = selected_unit_definitions.get(unit.unit_ref)
    if expected_unit_fingerprint is None or not hmac.compare_digest(
        expected_unit_fingerprint,
        supplied_unit_fingerprint,
    ):
        raise VerificationExecutionIdentityError(
            "verification unit definition does not match its exact plan binding"
        )
    _validate_ref(execution_surface_ref, label="execution surface ref")
    surface_prefix = "surface-ref:"
    if not execution_surface_ref.startswith(surface_prefix):
        raise VerificationExecutionIdentityError(
            "execution surface must use the canonical surface-ref namespace"
        )
    surface = execution_surface_ref.removeprefix(surface_prefix)
    if not surface or surface not in unit.execution_surfaces:
        raise VerificationExecutionIdentityError(
            "verification unit is unavailable on the requested execution surface"
        )
    if unit.lane_ref is not None and unit.lane_ref not in plan.selected_lane_refs:
        raise VerificationExecutionIdentityError(
            "verification unit lane is not a member of the exact plan"
        )
    if not set(unit.command_refs).issubset(plan.selected_command_refs):
        raise VerificationExecutionIdentityError(
            "verification unit commands are not a subset of the exact plan"
        )
    typescript_execution = any(
        command_ref in TYPESCRIPT_EXECUTION_COMMAND_REFS
        for command_ref in unit.command_refs
    )
    if typescript_execution and typescript_runtime_fingerprint is None:
        raise VerificationExecutionIdentityError(
            "TypeScript execution identity requires an exact runtime binding"
        )
    if not typescript_execution and (
        typescript_runtime_fingerprint is not None
        or typescript_version_ref is not None
    ):
        raise VerificationExecutionIdentityError(
            "non-TypeScript execution identity cannot vary by TypeScript runtime"
        )
    fenced_resource_refs = tuple(
        resource_ref
        for resource_ref in unit.exclusive_resource_refs
        if resource_ref
        in {
            "resource-ref:complete-pytest",
            "resource-ref:typescript-typecheck",
        }
    )
    if len(fenced_resource_refs) > 1:
        raise VerificationExecutionIdentityError(
            "one verification unit cannot consume multiple exact execution resources"
        )
    exclusive_resource_ref = (
        fenced_resource_refs[0] if fenced_resource_refs else None
    )
    dependency_state_ref = dependency_state_fingerprint(plan)
    exclusive_resource_attempt_ref = (
        verification_exclusive_resource_attempt_fingerprint(
            repository_sha=plan.repository_sha,
            dependency_state_ref=dependency_state_ref,
            exclusive_resource_ref=exclusive_resource_ref,
            typescript_runtime_fingerprint=typescript_runtime_fingerprint,
            typescript_version_ref=typescript_version_ref,
        )
        if exclusive_resource_ref is not None
        else None
    )
    fields: dict[str, object] = {
        "schema_version": IDENTITY_SCHEMA_VERSION,
        "repository_sha": plan.repository_sha,
        "plan_fingerprint": plan.plan_fingerprint,
        "unit_ref": unit.unit_ref,
        "execution_surface_ref": execution_surface_ref,
        "verification_definition_fingerprint": plan.definition_fingerprint,
        "verification_dag_fingerprint": plan.verification_dag_fingerprint,
        "unit_definition_fingerprint": supplied_unit_fingerprint,
        "command_selection_fingerprint": _canonical_digest(
            {
                "plan_selected_command_refs": plan.selected_command_refs,
                "unit_command_refs": unit.command_refs,
            }
        ),
        "dependency_state_fingerprint": dependency_state_ref,
        "dependency_lock_fingerprint": _canonical_digest(
            plan.dependency_lock_fingerprints
        ),
        "platform_fingerprint": plan.platform_fingerprint,
        "command_manifest_fingerprint": plan.command_manifest_fingerprint,
        "verifier_definition_fingerprint": plan.verifier_definition_fingerprint,
        "test_collection_fingerprint": plan.test_collection_fingerprint,
        "test_inventory_fingerprint": _canonical_digest(
            {
                "collection_posture": plan.test_collection_posture,
                "selected_test_refs": plan.selected_test_refs,
            }
        ),
        "pytest_shard_plan_fingerprint": plan.pytest_shard_plan_fingerprint,
        "typescript_project_fingerprint": plan.typescript_project_fingerprint,
        "typescript_runtime_fingerprint": typescript_runtime_fingerprint,
        "typescript_version_ref": typescript_version_ref,
        "exclusive_resource_ref": exclusive_resource_ref,
        "exclusive_resource_attempt_fingerprint": exclusive_resource_attempt_ref,
        "redaction_status": REDACTION_STATUS,
    }
    provisional = VerificationExecutionIdentity(
        identity_ref="execution-identity:" + "0" * 64,
        identity_fingerprint="0" * 64,
        **fields,
    )
    fingerprint = verification_execution_identity_fingerprint(provisional)
    identity = VerificationExecutionIdentity(
        identity_ref=f"execution-identity:{fingerprint}",
        identity_fingerprint=fingerprint,
        **fields,
    )
    identity.validate()
    return identity


@dataclass(frozen=True)
class VerificationExecutionTerminalProof:
    schema_version: str
    proof_ref: str
    identity_ref: str
    identity_fingerprint: str
    status: VerificationTerminalStatus
    receipt_ref: str
    result_refs: tuple[str, ...]
    output_digest: str
    completed_at: str
    failure_category: VerificationExecutionFailureCategory
    failure_reason_ref: str
    failure_evidence_ref: str | None
    proof_fingerprint: str
    redaction_status: str = REDACTION_STATUS

    def validate(self) -> None:
        if self.schema_version != TERMINAL_PROOF_SCHEMA_VERSION:
            raise VerificationExecutionIdentityError(
                "unsupported verification terminal proof schema"
            )
        for value, label in (
            (self.schema_version, "terminal proof schema"),
            (self.proof_ref, "terminal proof ref"),
            (self.identity_ref, "terminal identity ref"),
        ):
            _validate_ref(value, label=label)
        _validate_digest_ref(
            self.receipt_ref,
            prefix="receipt:verification:",
            label="terminal receipt ref",
        )
        _validate_digest(self.identity_fingerprint, label="terminal identity fingerprint")
        _validate_digest(self.output_digest, label="terminal output digest")
        _validate_digest(self.proof_fingerprint, label="terminal proof fingerprint")
        if (
            not isinstance(self.result_refs, tuple)
            or not self.result_refs
            or len(self.result_refs) > MAX_RESULT_REFS
            or len(self.result_refs) != len(set(self.result_refs))
        ):
            raise VerificationExecutionIdentityError(
                "terminal proof result refs are invalid"
            )
        for result_ref in self.result_refs:
            _validate_terminal_result_ref(result_ref)
        if self.status not in {
            VerificationTerminalStatus.PASSED,
            VerificationTerminalStatus.FAILED,
            VerificationTerminalStatus.BLOCKED,
            VerificationTerminalStatus.CANCELLED,
        }:
            raise VerificationExecutionIdentityError(
                "terminal proof status is not terminal"
            )
        if not isinstance(self.failure_category, VerificationExecutionFailureCategory):
            raise VerificationExecutionIdentityError(
                "terminal failure category is invalid"
            )
        classified = _classify_terminal_failure(
            status=self.status,
            failure_reason_ref=self.failure_reason_ref,
            failure_evidence_ref=self.failure_evidence_ref,
        )
        if self.failure_evidence_ref is not None and self.failure_evidence_ref not in {
            self.receipt_ref,
            *self.result_refs,
        }:
            raise VerificationExecutionIdentityError(
                "terminal failure evidence is not a member of terminal proof results"
            )
        if classified is not self.failure_category:
            raise VerificationExecutionIdentityError(
                "terminal failure category does not match canonical classification"
            )
        _validate_timestamp(self.completed_at, label="terminal completion timestamp")
        if self.redaction_status != REDACTION_STATUS:
            raise VerificationExecutionIdentityError(
                "terminal proof redaction posture is invalid"
            )
        expected = verification_execution_terminal_proof_fingerprint(self)
        if self.proof_fingerprint != expected:
            raise VerificationExecutionIdentityError(
                "terminal proof fingerprint does not match its payload"
            )
        if self.proof_ref != f"execution-proof:{expected}":
            raise VerificationExecutionIdentityError(
                "terminal proof ref is not content-bound"
            )

    @property
    def deterministic_failure(self) -> bool:
        return (
            self.status is VerificationTerminalStatus.FAILED
            and self.failure_category
            is VerificationExecutionFailureCategory.DETERMINISTIC_CODE_FAILURE
        )


def verification_execution_terminal_proof_fingerprint(
    proof: VerificationExecutionTerminalProof,
) -> str:
    payload = {
        field_name: getattr(proof, field_name)
        for field_name in VerificationExecutionTerminalProof.__dataclass_fields__
        if field_name not in {"proof_ref", "proof_fingerprint"}
    }
    return _canonical_digest(payload)


def build_verification_execution_terminal_proof(
    identity: VerificationExecutionIdentity,
    *,
    status: VerificationTerminalStatus,
    receipt_ref: str,
    result_refs: tuple[str, ...],
    output_digest: str,
    completed_at: str,
    failure_reason_ref: str = "reason-ref:verification:not-applicable",
    failure_evidence_ref: str | None = None,
) -> VerificationExecutionTerminalProof:
    identity.validate()
    failure_category = _classify_terminal_failure(
        status=status,
        failure_reason_ref=failure_reason_ref,
        failure_evidence_ref=failure_evidence_ref,
    )
    fields: dict[str, object] = {
        "schema_version": TERMINAL_PROOF_SCHEMA_VERSION,
        "identity_ref": identity.identity_ref,
        "identity_fingerprint": identity.identity_fingerprint,
        "status": status,
        "receipt_ref": receipt_ref,
        "result_refs": result_refs,
        "output_digest": output_digest,
        "completed_at": completed_at,
        "failure_category": failure_category,
        "failure_reason_ref": failure_reason_ref,
        "failure_evidence_ref": failure_evidence_ref,
        "redaction_status": REDACTION_STATUS,
    }
    provisional = VerificationExecutionTerminalProof(
        proof_ref="execution-proof:" + "0" * 64,
        proof_fingerprint="0" * 64,
        **fields,
    )
    fingerprint = verification_execution_terminal_proof_fingerprint(provisional)
    proof = VerificationExecutionTerminalProof(
        proof_ref=f"execution-proof:{fingerprint}",
        proof_fingerprint=fingerprint,
        **fields,
    )
    proof.validate()
    return proof


@dataclass(frozen=True)
class VerificationExecutionFenceDecision:
    disposition: VerificationExecutionFenceDisposition
    identity_ref: str
    reason_ref: str
    owner_token: str | None = field(default=None, repr=False, compare=False)
    terminal_proof: VerificationExecutionTerminalProof | None = None

    def validate(self) -> None:
        if not isinstance(self.disposition, VerificationExecutionFenceDisposition):
            raise VerificationExecutionFenceStateError(
                "execution fence disposition is invalid"
            )
        _validate_ref(self.identity_ref, label="fence identity ref")
        _validate_ref(self.reason_ref, label="fence reason ref")
        if self.disposition is VerificationExecutionFenceDisposition.START_GRANTED:
            if (
                not isinstance(self.owner_token, str)
                or _OWNER_TOKEN_PATTERN.fullmatch(self.owner_token) is None
                or self.terminal_proof is not None
            ):
                raise VerificationExecutionFenceStateError(
                    "start grant requires one private owner token"
                )
        elif self.owner_token is not None:
            raise VerificationExecutionFenceStateError(
                "non-start fence decisions cannot expose an owner token"
            )
        if self.disposition in {
            VerificationExecutionFenceDisposition.TERMINAL_PROOF_REUSED,
            VerificationExecutionFenceDisposition.DETERMINISTIC_FAILURE_REJECTED,
        }:
            if self.terminal_proof is None:
                raise VerificationExecutionFenceStateError(
                    "terminal fence decision requires exact proof"
                )
            self.terminal_proof.validate()
        elif self.terminal_proof is not None:
            raise VerificationExecutionFenceStateError(
                "non-terminal fence decision cannot claim terminal proof"
            )


def _canonical_now(clock: Callable[[], datetime]) -> str:
    observed = clock()
    if not isinstance(observed, datetime) or observed.tzinfo is None:
        raise VerificationExecutionFenceError("verification fence clock is invalid")
    return observed.astimezone(UTC).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _strict_json(raw: bytes) -> dict[str, Any]:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise VerificationExecutionFenceStateError(
                    "verification fence state has duplicate fields"
                )
            result[key] = value
        return result

    def reject_constant(_value: str) -> None:
        raise VerificationExecutionFenceStateError(
            "verification fence state contains a non-finite value"
        )

    try:
        decoded = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, RecursionError, ValueError) as exc:
        raise VerificationExecutionFenceStateError(
            "verification fence state is malformed"
        ) from exc
    if not isinstance(decoded, dict):
        raise VerificationExecutionFenceStateError(
            "verification fence state must be an object"
        )
    return decoded


def _safe_root_components(path: Path) -> tuple[str, ...]:
    if not path.is_absolute() or len(os.fspath(path)) > 4096:
        raise VerificationExecutionFenceError(
            "verification fence root is unsafe or unavailable"
        )
    components = path.parts[1:]
    if not components or len(components) > 64:
        raise VerificationExecutionFenceError(
            "verification fence root is unsafe or unavailable"
        )
    if any(
        not component
        or component in {".", ".."}
        or len(os.fsencode(component)) > 255
        or "\x00" in component
        for component in components
    ):
        raise VerificationExecutionFenceError(
            "verification fence root is unsafe or unavailable"
        )
    return components


def _open_root_directory(path: Path, *, create: bool) -> int:
    components = _safe_root_components(path)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(os.path.sep, flags)
        for index, component in enumerate(components):
            is_leaf = index == len(components) - 1
            try:
                child = os.open(component, flags, dir_fd=descriptor)
            except FileNotFoundError:
                if not create or not is_leaf:
                    raise
                try:
                    os.mkdir(component, mode=0o700, dir_fd=descriptor)
                    os.fsync(descriptor)
                except FileExistsError:
                    pass
                child = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) != 0o700
        ):
            raise OSError("unsafe root metadata")
        return descriptor
    except OSError:
        if descriptor is not None:
            os.close(descriptor)
        raise VerificationExecutionFenceError(
            "verification fence root is unsafe or unavailable"
        ) from None


def _open_fence_lock(root_descriptor: int, *, initialize: bool) -> int:
    common_flags = os.O_RDWR
    common_flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        if initialize:
            try:
                descriptor = os.open(
                    _LOCK_NAME,
                    common_flags | os.O_CREAT | os.O_EXCL,
                    0o600,
                    dir_fd=root_descriptor,
                )
            except FileExistsError:
                descriptor = os.open(
                    _LOCK_NAME,
                    common_flags,
                    dir_fd=root_descriptor,
                )
        else:
            descriptor = os.open(
                _LOCK_NAME,
                common_flags,
                dir_fd=root_descriptor,
            )
    except OSError:
        raise VerificationExecutionFenceStateError(
            "verification fence lock is unsafe or unavailable"
        ) from None
    try:
        metadata = os.fstat(descriptor)
    except OSError:
        os.close(descriptor)
        raise VerificationExecutionFenceStateError(
            "verification fence lock is unsafe or unavailable"
        ) from None
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o600
        or metadata.st_size != 0
    ):
        os.close(descriptor)
        raise VerificationExecutionFenceStateError(
            "verification fence lock is unsafe"
        )
    return descriptor


class VerificationExecutionFence:
    """Owner-only, bounded, fd-relative start/terminal execution fence."""

    def __init__(
        self,
        root: Path,
        *,
        max_entries: int = MAX_FENCE_ENTRIES,
        lock_timeout_seconds: float = 2.0,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        token_factory: Callable[[], str] = lambda: secrets.token_hex(32),
    ) -> None:
        if (
            not isinstance(max_entries, int)
            or isinstance(max_entries, bool)
            or not 1 <= max_entries <= MAX_FENCE_ENTRIES
        ):
            raise ValueError("verification fence entry bound is invalid")
        if not isinstance(lock_timeout_seconds, (int, float)) or not (
            0 <= lock_timeout_seconds <= 30
        ):
            raise ValueError("verification fence lock timeout is invalid")
        self._root = Path(root)
        self._max_entries = max_entries
        self._lock_timeout_seconds = float(lock_timeout_seconds)
        self._clock = clock
        self._token_factory = token_factory
        descriptor = _open_root_directory(self._root, create=True)
        try:
            metadata = os.fstat(descriptor)
            self._root_identity = (metadata.st_dev, metadata.st_ino)
            lock_descriptor = _open_fence_lock(descriptor, initialize=True)
            lock_metadata = os.fstat(lock_descriptor)
            self._lock_identity = (lock_metadata.st_dev, lock_metadata.st_ino)
            os.close(lock_descriptor)
        finally:
            os.close(descriptor)

    def state_path_for(self, identity: VerificationExecutionIdentity) -> Path:
        """Return the deterministic test/inspection path; I/O remains fd-relative."""

        identity.validate()
        return self._root / self._state_name(identity)

    @staticmethod
    def _state_name(identity: VerificationExecutionIdentity) -> str:
        state_fingerprint = (
            identity.exclusive_resource_attempt_fingerprint
            or identity.identity_fingerprint
        )
        return f"execution-{state_fingerprint}.json"

    @contextmanager
    def _locked_root(self) -> Iterator[int]:
        root_descriptor = _open_root_directory(self._root, create=False)
        lock_descriptor: int | None = None
        try:
            metadata = os.fstat(root_descriptor)
            if (metadata.st_dev, metadata.st_ino) != self._root_identity:
                raise VerificationExecutionFenceStateError(
                    "verification fence root identity changed"
                )
            lock_descriptor = _open_fence_lock(root_descriptor, initialize=False)
            lock_metadata = os.fstat(lock_descriptor)
            if (lock_metadata.st_dev, lock_metadata.st_ino) != self._lock_identity:
                raise VerificationExecutionFenceStateError(
                    "verification fence lock identity changed"
                )
            deadline = time.monotonic() + self._lock_timeout_seconds
            while True:
                try:
                    fcntl.flock(lock_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise VerificationExecutionFenceError(
                            "verification fence lock acquisition is bounded"
                        ) from None
                    time.sleep(min(0.01, max(0.001, deadline - time.monotonic())))
            self._recover_publication_stages(root_descriptor)
            yield root_descriptor
        except OSError:
            raise VerificationExecutionFenceStateError(
                "verification fence lock is unavailable"
            ) from None
        finally:
            if lock_descriptor is not None:
                try:
                    fcntl.flock(lock_descriptor, fcntl.LOCK_UN)
                except OSError:
                    pass
                os.close(lock_descriptor)
            os.close(root_descriptor)

    def _bounded_root_entries(self, root_descriptor: int) -> tuple[str, ...]:
        try:
            entries = tuple(sorted(os.listdir(root_descriptor)))
        except OSError:
            raise VerificationExecutionFenceStateError(
                "verification fence directory cannot be enumerated"
            ) from None
        if len(entries) > self._max_entries + 2:
            raise VerificationExecutionFenceCapacityError(
                "verification fence directory entry bound is exhausted"
            )
        return entries

    def _recover_publication_stages(self, root_descriptor: int) -> None:
        """Recover only internal stages while the owner-bound root lock is held."""

        removed = False
        entries = self._bounded_root_entries(root_descriptor)
        for entry in entries:
            if entry == _LOCK_NAME:
                continue
            stage_match = _STAGE_NAME_PATTERN.fullmatch(entry)
            if stage_match is None:
                if _STATE_NAME_PATTERN.fullmatch(entry) is None:
                    raise VerificationExecutionFenceStateError(
                        "verification fence directory contains an unsafe entry"
                    )
                if self._read_state(root_descriptor, entry) is None:
                    raise VerificationExecutionFenceStateError(
                        "verification fence state disappeared during recovery"
                    )
                continue
            flags = os.O_RDONLY
            flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
            try:
                stage_descriptor = os.open(entry, flags, dir_fd=root_descriptor)
            except OSError:
                raise VerificationExecutionFenceStateError(
                    "verification fence publication stage is unsafe"
                ) from None
            try:
                stage_metadata = os.fstat(stage_descriptor)
                if (
                    not stat.S_ISREG(stage_metadata.st_mode)
                    or stage_metadata.st_uid != os.getuid()
                    or stat.S_IMODE(stage_metadata.st_mode) != 0o600
                    or stage_metadata.st_nlink not in {1, 2}
                ):
                    raise VerificationExecutionFenceStateError(
                        "verification fence publication stage is unsafe"
                    )
                if stage_metadata.st_nlink == 2:
                    final_name = stage_match.group(1)
                    try:
                        final_descriptor = os.open(
                            final_name,
                            flags,
                            dir_fd=root_descriptor,
                        )
                    except OSError:
                        raise VerificationExecutionFenceStateError(
                            "verification fence interrupted publication is unsafe"
                        ) from None
                    try:
                        final_metadata = os.fstat(final_descriptor)
                        if (
                            not stat.S_ISREG(final_metadata.st_mode)
                            or final_metadata.st_uid != os.getuid()
                            or stat.S_IMODE(final_metadata.st_mode) != 0o600
                            or final_metadata.st_nlink != 2
                            or (final_metadata.st_dev, final_metadata.st_ino)
                            != (stage_metadata.st_dev, stage_metadata.st_ino)
                            or not 0 < final_metadata.st_size <= MAX_STATE_BYTES
                        ):
                            raise VerificationExecutionFenceStateError(
                                "verification fence interrupted publication is unsafe"
                            )
                        chunks: list[bytes] = []
                        remaining = MAX_STATE_BYTES + 1
                        while remaining:
                            chunk = os.read(
                                final_descriptor,
                                min(remaining, 65_536),
                            )
                            if not chunk:
                                break
                            chunks.append(chunk)
                            remaining -= len(chunk)
                        raw = b"".join(chunks)
                        after = os.fstat(final_descriptor)
                        if (
                            len(raw) != final_metadata.st_size
                            or (
                                final_metadata.st_dev,
                                final_metadata.st_ino,
                                final_metadata.st_size,
                                final_metadata.st_mtime_ns,
                                final_metadata.st_ctime_ns,
                            )
                            != (
                                after.st_dev,
                                after.st_ino,
                                after.st_size,
                                after.st_mtime_ns,
                                after.st_ctime_ns,
                            )
                        ):
                            raise VerificationExecutionFenceStateError(
                                "verification fence interrupted publication changed"
                            )
                        payload = _strict_json(raw)
                        if self._encode_state(payload) != raw:
                            raise VerificationExecutionFenceStateError(
                                "verification fence interrupted publication is noncanonical"
                            )
                    finally:
                        os.close(final_descriptor)
            finally:
                os.close(stage_descriptor)
            try:
                os.unlink(entry, dir_fd=root_descriptor)
                os.fsync(root_descriptor)
            except OSError:
                raise VerificationExecutionFenceStateError(
                    "verification fence publication recovery failed"
                ) from None
            removed = True
            if stage_metadata.st_nlink == 2:
                try:
                    recovered = os.stat(
                        stage_match.group(1),
                        dir_fd=root_descriptor,
                        follow_symlinks=False,
                    )
                except OSError:
                    raise VerificationExecutionFenceStateError(
                        "verification fence publication recovery failed"
                    ) from None
                if recovered.st_nlink != 1:
                    raise VerificationExecutionFenceStateError(
                        "verification fence publication recovery failed"
                    )
        if removed:
            self._bounded_root_entries(root_descriptor)

    @staticmethod
    def _read_state(root_descriptor: int, state_name: str) -> dict[str, Any] | None:
        flags = os.O_RDONLY
        flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        descriptor: int | None = None
        try:
            descriptor = os.open(state_name, flags, dir_fd=root_descriptor)
        except FileNotFoundError:
            return None
        except OSError:
            raise VerificationExecutionFenceStateError(
                "verification fence state is unsafe or unavailable"
            ) from None
        try:
            metadata = os.fstat(descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o600
                or not 0 < metadata.st_size <= MAX_STATE_BYTES
            ):
                raise VerificationExecutionFenceStateError(
                    "verification fence state is unsafe"
                )
            chunks: list[bytes] = []
            remaining = MAX_STATE_BYTES + 1
            while remaining:
                chunk = os.read(descriptor, min(remaining, 65_536))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            raw = b"".join(chunks)
            after = os.fstat(descriptor)
            before_identity = (
                metadata.st_dev,
                metadata.st_ino,
                metadata.st_size,
                metadata.st_mtime_ns,
                metadata.st_ctime_ns,
            )
            after_identity = (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            )
            if len(raw) != metadata.st_size or before_identity != after_identity:
                raise VerificationExecutionFenceStateError(
                    "verification fence state changed while read"
                )
            return _strict_json(raw)
        finally:
            os.close(descriptor)

    @staticmethod
    def _encode_state(payload: dict[str, Any]) -> bytes:
        try:
            encoded = (
                json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise VerificationExecutionFenceStateError(
                "verification fence state cannot be encoded"
            ) from exc
        if not 0 < len(encoded) <= MAX_STATE_BYTES:
            raise VerificationExecutionFenceStateError(
                "verification fence state exceeds its byte bound"
            )
        return encoded

    @staticmethod
    def _write_state(
        root_descriptor: int,
        state_name: str,
        payload: dict[str, Any],
        *,
        replace_existing: bool,
    ) -> None:
        encoded = VerificationExecutionFence._encode_state(payload)
        temporary_name = f".{state_name}.{os.getpid()}.{secrets.token_hex(8)}.tmp"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        descriptor: int | None = None
        temporary_created = False
        try:
            descriptor = os.open(
                temporary_name,
                flags,
                0o600,
                dir_fd=root_descriptor,
            )
            temporary_created = True
            metadata = os.fstat(descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o600
            ):
                raise VerificationExecutionFenceStateError(
                    "verification fence temporary state is unsafe"
                )
            view = memoryview(encoded)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise VerificationExecutionFenceStateError(
                        "verification fence state write made no progress"
                    )
                view = view[written:]
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = None
            if replace_existing:
                os.replace(
                    temporary_name,
                    state_name,
                    src_dir_fd=root_descriptor,
                    dst_dir_fd=root_descriptor,
                )
            else:
                os.link(
                    temporary_name,
                    state_name,
                    src_dir_fd=root_descriptor,
                    dst_dir_fd=root_descriptor,
                    follow_symlinks=False,
                )
                os.unlink(temporary_name, dir_fd=root_descriptor)
            temporary_created = False
            os.fsync(root_descriptor)
            published = VerificationExecutionFence._read_state(
                root_descriptor, state_name
            )
            if published != _strict_json(encoded):
                raise VerificationExecutionFenceStateError(
                    "verification fence state publication could not be verified"
                )
        except FileExistsError:
            raise VerificationExecutionFenceStateError(
                "verification fence state already exists"
            ) from None
        except OSError:
            raise VerificationExecutionFenceStateError(
                "verification fence state could not be published"
            ) from None
        finally:
            if descriptor is not None:
                os.close(descriptor)
            if temporary_created:
                try:
                    os.unlink(temporary_name, dir_fd=root_descriptor)
                except OSError:
                    pass

    @staticmethod
    def _proof_from_payload(payload: object) -> VerificationExecutionTerminalProof:
        if not isinstance(payload, dict) or set(payload) != set(
            VerificationExecutionTerminalProof.__dataclass_fields__
        ):
            raise VerificationExecutionFenceStateError(
                "verification fence terminal proof shape is invalid"
            )
        try:
            proof = VerificationExecutionTerminalProof(
                schema_version=payload["schema_version"],
                proof_ref=payload["proof_ref"],
                identity_ref=payload["identity_ref"],
                identity_fingerprint=payload["identity_fingerprint"],
                status=VerificationTerminalStatus(payload["status"]),
                receipt_ref=payload["receipt_ref"],
                result_refs=tuple(payload["result_refs"]),
                output_digest=payload["output_digest"],
                completed_at=payload["completed_at"],
                failure_category=VerificationExecutionFailureCategory(
                    payload["failure_category"]
                ),
                failure_reason_ref=payload["failure_reason_ref"],
                failure_evidence_ref=payload["failure_evidence_ref"],
                proof_fingerprint=payload["proof_fingerprint"],
                redaction_status=payload["redaction_status"],
            )
            proof.validate()
        except (KeyError, TypeError, ValueError) as exc:
            raise VerificationExecutionFenceStateError(
                "verification fence terminal proof is invalid"
            ) from exc
        return proof

    @staticmethod
    def _validate_state_identity(
        payload: dict[str, Any], identity: VerificationExecutionIdentity
    ) -> bool:
        if (
            payload.get("schema_version") != FENCE_STATE_SCHEMA_VERSION
            or payload.get("redaction_status") != REDACTION_STATUS
        ):
            raise VerificationExecutionFenceStateError(
                "verification fence state identity is invalid"
            )
        try:
            stored_identity_ref = payload.get("identity_ref")
            stored_identity_fingerprint = payload.get("identity_fingerprint")
            _validate_ref(stored_identity_ref, label="stored execution identity ref")
            _validate_digest(
                stored_identity_fingerprint,
                label="stored execution identity fingerprint",
            )
            stored_resource_ref = payload.get("exclusive_resource_ref")
            stored_resource_fingerprint = payload.get(
                "exclusive_resource_attempt_fingerprint"
            )
            if (stored_resource_ref is None) != (
                stored_resource_fingerprint is None
            ):
                raise VerificationExecutionIdentityError(
                    "verification fence resource binding is invalid"
                )
            if stored_resource_ref is not None:
                _validate_ref(
                    stored_resource_ref,
                    label="stored exclusive verification resource ref",
                )
                _validate_digest(
                    stored_resource_fingerprint,
                    label="stored exclusive resource attempt fingerprint",
                )
        except VerificationExecutionIdentityError as exc:
            raise VerificationExecutionFenceStateError(
                "verification fence state binding is invalid"
            ) from exc
        if stored_identity_ref != f"execution-identity:{stored_identity_fingerprint}":
            raise VerificationExecutionFenceStateError(
                "verification fence stored identity is not content bound"
            )
        if (
            stored_resource_ref != identity.exclusive_resource_ref
            or stored_resource_fingerprint
            != identity.exclusive_resource_attempt_fingerprint
        ):
            raise VerificationExecutionFenceStateError(
                "verification fence resource binding changed"
            )
        exact_identity = (
            stored_identity_ref == identity.identity_ref
            and stored_identity_fingerprint == identity.identity_fingerprint
        )
        if not exact_identity and identity.exclusive_resource_ref is None:
            raise VerificationExecutionFenceStateError(
                "verification fence state identity is invalid"
            )
        return exact_identity

    def _decision_for_state(
        self,
        payload: dict[str, Any],
        identity: VerificationExecutionIdentity,
    ) -> VerificationExecutionFenceDecision:
        exact_identity = self._validate_state_identity(payload, identity)
        posture = payload.get("posture")
        common_fields = {
            "schema_version",
            "posture",
            "identity_ref",
            "identity_fingerprint",
            "exclusive_resource_ref",
            "exclusive_resource_attempt_fingerprint",
            "owner_token_fingerprint",
            "started_at",
            "redaction_status",
        }
        if posture == "started":
            if set(payload) != common_fields:
                raise VerificationExecutionFenceStateError(
                    "verification fence start state shape is invalid"
                )
            _validate_digest(
                payload.get("owner_token_fingerprint"),
                label="owner token fingerprint",
            )
            _validate_timestamp(payload.get("started_at"), label="start timestamp")
            if exact_identity:
                decision = VerificationExecutionFenceDecision(
                    disposition=VerificationExecutionFenceDisposition.RECOVERY_REQUIRED,
                    identity_ref=identity.identity_ref,
                    reason_ref="reason-ref:verification:durable-start-unsettled",
                )
        elif posture == "terminal":
            terminal_fields = common_fields | {"terminal_proof"}
            if set(payload) != terminal_fields:
                raise VerificationExecutionFenceStateError(
                    "verification fence terminal state shape is invalid"
                )
            _validate_digest(
                payload.get("owner_token_fingerprint"),
                label="owner token fingerprint",
            )
            _validate_timestamp(payload.get("started_at"), label="start timestamp")
            proof = self._proof_from_payload(payload.get("terminal_proof"))
            if (
                proof.identity_ref != payload.get("identity_ref")
                or proof.identity_fingerprint != payload.get("identity_fingerprint")
            ):
                raise VerificationExecutionFenceStateError(
                    "verification fence terminal proof identity is invalid"
                )
            if exact_identity:
                deterministic_failure = (
                    proof.status is VerificationTerminalStatus.FAILED
                    and proof.deterministic_failure
                )
                decision = VerificationExecutionFenceDecision(
                    disposition=(
                        VerificationExecutionFenceDisposition.DETERMINISTIC_FAILURE_REJECTED
                        if deterministic_failure
                        else VerificationExecutionFenceDisposition.TERMINAL_PROOF_REUSED
                    ),
                    identity_ref=identity.identity_ref,
                    reason_ref=(
                        "reason-ref:verification:deterministic-failure-no-rerun"
                        if deterministic_failure
                        else "reason-ref:verification:exact-terminal-proof-reused"
                    ),
                    terminal_proof=proof,
                )
        else:
            raise VerificationExecutionFenceStateError(
                "verification fence posture is invalid"
            )
        if not exact_identity:
            decision = VerificationExecutionFenceDecision(
                disposition=(
                    VerificationExecutionFenceDisposition.EXCLUSIVE_RESOURCE_ATTEMPT_REJECTED
                ),
                identity_ref=identity.identity_ref,
                reason_ref=(
                    "reason-ref:verification:exclusive-resource-attempt-already-recorded"
                ),
            )
        decision.validate()
        return decision

    def begin(
        self, identity: VerificationExecutionIdentity
    ) -> VerificationExecutionFenceDecision:
        identity.validate()
        state_name = self._state_name(identity)
        with self._locked_root() as root_descriptor:
            payload = self._read_state(root_descriptor, state_name)
            if payload is not None:
                return self._decision_for_state(payload, identity)
            entry_count = sum(
                1
                for name in os.listdir(root_descriptor)
                if _STATE_NAME_PATTERN.fullmatch(name) is not None
            )
            if entry_count >= self._max_entries:
                raise VerificationExecutionFenceCapacityError(
                    "verification fence entry bound is exhausted"
                )
            owner_token = self._token_factory()
            if (
                not isinstance(owner_token, str)
                or _OWNER_TOKEN_PATTERN.fullmatch(owner_token) is None
            ):
                raise VerificationExecutionFenceError(
                    "verification fence token source is invalid"
                )
            started_at = _canonical_now(self._clock)
            state = {
                "schema_version": FENCE_STATE_SCHEMA_VERSION,
                "posture": "started",
                "identity_ref": identity.identity_ref,
                "identity_fingerprint": identity.identity_fingerprint,
                "exclusive_resource_ref": identity.exclusive_resource_ref,
                "exclusive_resource_attempt_fingerprint": (
                    identity.exclusive_resource_attempt_fingerprint
                ),
                "owner_token_fingerprint": hashlib.sha256(
                    owner_token.encode("ascii")
                ).hexdigest(),
                "started_at": started_at,
                "redaction_status": REDACTION_STATUS,
            }
            self._write_state(
                root_descriptor,
                state_name,
                state,
                replace_existing=False,
            )
            decision = VerificationExecutionFenceDecision(
                disposition=VerificationExecutionFenceDisposition.START_GRANTED,
                identity_ref=identity.identity_ref,
                reason_ref="reason-ref:verification:execution-start-granted",
                owner_token=owner_token,
            )
            decision.validate()
            return decision

    def complete(
        self,
        identity: VerificationExecutionIdentity,
        *,
        owner_token: str,
        terminal_proof: VerificationExecutionTerminalProof,
    ) -> VerificationExecutionTerminalProof:
        identity.validate()
        terminal_proof.validate()
        if (
            terminal_proof.identity_ref != identity.identity_ref
            or terminal_proof.identity_fingerprint != identity.identity_fingerprint
        ):
            raise VerificationExecutionFenceStateError(
                "terminal proof does not match the exact execution identity"
            )
        if (
            not isinstance(owner_token, str)
            or _OWNER_TOKEN_PATTERN.fullmatch(owner_token) is None
        ):
            raise VerificationExecutionFenceStateError(
                "verification fence owner token is invalid"
            )
        state_name = self._state_name(identity)
        with self._locked_root() as root_descriptor:
            payload = self._read_state(root_descriptor, state_name)
            if payload is None:
                raise VerificationExecutionFenceStateError(
                    "verification execution has no durable start"
                )
            existing_decision = self._decision_for_state(payload, identity)
            if (
                existing_decision.disposition
                is VerificationExecutionFenceDisposition.EXCLUSIVE_RESOURCE_ATTEMPT_REJECTED
            ):
                raise VerificationExecutionFenceStateError(
                    "verification fence belongs to another exact execution identity"
                )
            expected_owner_digest = payload.get("owner_token_fingerprint")
            if not isinstance(expected_owner_digest, str) or not hmac.compare_digest(
                expected_owner_digest,
                hashlib.sha256(owner_token.encode("ascii")).hexdigest(),
            ):
                raise VerificationExecutionFenceStateError(
                    "verification fence owner does not match durable start"
                )
            if payload.get("posture") == "terminal":
                existing = existing_decision.terminal_proof
                if existing is None:
                    raise VerificationExecutionFenceStateError(
                        "verification fence terminal proof is missing"
                    )
                if existing != terminal_proof:
                    raise VerificationExecutionFenceStateError(
                        "verification execution already has different terminal proof"
                    )
                return existing
            if payload.get("posture") != "started":
                raise VerificationExecutionFenceStateError(
                    "verification fence posture is invalid"
                )
            started_at = _validate_timestamp(
                payload.get("started_at"), label="start timestamp"
            )
            completed_at = _validate_timestamp(
                terminal_proof.completed_at, label="terminal completion timestamp"
            )
            if completed_at < started_at:
                raise VerificationExecutionFenceStateError(
                    "verification terminal proof precedes durable start"
                )
            if int((completed_at - started_at).total_seconds() * 1_000) > (
                MAX_DURATION_MS
            ):
                raise VerificationExecutionFenceStateError(
                    "verification execution exceeds its bounded duration"
                )
            terminal_state = {
                **payload,
                "posture": "terminal",
                "terminal_proof": asdict(terminal_proof),
            }
            self._write_state(
                root_descriptor,
                state_name,
                terminal_state,
                replace_existing=True,
            )
            return terminal_proof

    def abort_prestart(
        self,
        identity: VerificationExecutionIdentity,
        *,
        owner_token: str,
    ) -> None:
        """Remove a durable fence only when command spawn was never attempted."""

        identity.validate()
        if (
            not isinstance(owner_token, str)
            or _OWNER_TOKEN_PATTERN.fullmatch(owner_token) is None
        ):
            raise VerificationExecutionFenceStateError(
                "verification fence owner token is invalid"
            )
        state_name = self._state_name(identity)
        with self._locked_root() as root_descriptor:
            payload = self._read_state(root_descriptor, state_name)
            if payload is None:
                raise VerificationExecutionFenceStateError(
                    "verification execution has no durable pre-start"
                )
            if not self._validate_state_identity(payload, identity):
                raise VerificationExecutionFenceStateError(
                    "verification fence belongs to another exact execution identity"
                )
            expected_owner_digest = payload.get("owner_token_fingerprint")
            if not isinstance(expected_owner_digest, str) or not hmac.compare_digest(
                expected_owner_digest,
                hashlib.sha256(owner_token.encode("ascii")).hexdigest(),
            ):
                raise VerificationExecutionFenceStateError(
                    "verification fence owner does not match durable pre-start"
                )
            if payload.get("posture") != "started":
                raise VerificationExecutionFenceStateError(
                    "terminal verification execution cannot be aborted"
                )
            try:
                os.unlink(state_name, dir_fd=root_descriptor)
                os.fsync(root_descriptor)
            except OSError:
                raise VerificationExecutionFenceStateError(
                    "verification fence pre-start could not be aborted"
                ) from None
            if self._read_state(root_descriptor, state_name) is not None:
                raise VerificationExecutionFenceStateError(
                    "verification fence pre-start abort could not be verified"
                )


VerificationExecutionFenceStore = VerificationExecutionFence
