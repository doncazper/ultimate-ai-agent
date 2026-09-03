from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ultimate_ai_agent.core.authority import (
    AUTHORITY_LEASE_LOCAL_OPERATOR_REF,
    AuthorityCapability,
    AuthorityConstraint,
    AuthorityConstraintKind,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseRevokeRequest,
    AuthorityLeaseScope,
    AuthorityLeaseStatus,
    AuthorityLeaseStore,
    TrustMode,
    build_authority_lease_approval_requirement_for_request,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    AuthorityLeaseApprovalConflictError,
    AuthorityLeaseApprovalStateError,
    build_authority_lease_backend_approval_ref,
    issue_authority_lease_with_backend_approval,
)
from ultimate_ai_agent.core.authority.authority_constants import (
    AUTHORITY_STATE_LOCK_KEY,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    runtime_local_model_endpoint_ref,
    runtime_local_model_model_ref,
)
from ultimate_ai_agent.core.private_path_security import require_private_tree


LEASE_DURATION_MINUTES = 120
EXPECTED_DOMAINS = {"provider_model_calls": ["execute"]}
ISSUE_REASON_REF = "reason-ref:taw08:founder-private-live-acceptance"
REVOKE_REASON_REF = "reason-ref:taw08:founder-private-live-acceptance-complete"
ISSUE_ROLLBACK_REASON_REF = (
    "reason-ref:taw08:founder-private-live-acceptance-issue-failed"
)
LEASE_HELPER_PATH_REF = (
    "repo-path-ref:scripts/manage_tool_aware_cognition_taw08_live_lease.py"
)
LEASE_POSTURE_REF = "authority-posture-ref:taw08:provider-model-execute:v1"
LEASE_RUN_CONSTRAINT_REF = "authority-constraint-ref:taw08:founder-private-run"
LOCAL_MODEL_BASE_URL = "http://127.0.0.1:1234"
LOCAL_MODEL_REF = "qwen3.8-27b"


def _helper_digest_ref() -> str:
    path = Path(__file__)
    before = path.lstat()
    if (
        path.is_symlink()
        or not stat.S_ISREG(before.st_mode)
        or before.st_size <= 0
        or before.st_size > 1024 * 1024
    ):
        raise ValueError("TAW-08 lease helper source is invalid")
    content = path.read_bytes()
    after = path.lstat()
    if not os.path.samestat(before, after) or before.st_mtime_ns != after.st_mtime_ns:
        raise ValueError("TAW-08 lease helper changed during inspection")
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def lease_constraints(
    *,
    candidate_revision_ref: str,
    candidate_manifest_digest_ref: str,
    run_ref: str,
) -> dict[str, object]:
    if not re.fullmatch(r"git-sha:[0-9a-f]{40}", candidate_revision_ref):
        raise ValueError("candidate revision ref is invalid")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", candidate_manifest_digest_ref):
        raise ValueError("candidate manifest digest ref is invalid")
    if not re.fullmatch(r"run-ref:taw08:[a-z0-9][a-z0-9._:-]{0,160}", run_ref):
        raise ValueError("founder acceptance run ref is invalid")
    return {
        "candidate_revision_ref": candidate_revision_ref,
        "candidate_manifest_digest_ref": candidate_manifest_digest_ref,
        "run_ref": run_ref,
        "local_model_endpoint_ref": runtime_local_model_endpoint_ref(
            LOCAL_MODEL_BASE_URL
        ),
        "local_model_model_ref": runtime_local_model_model_ref(LOCAL_MODEL_REF),
        "exact_resource_refs_required": True,
        "lease_helper_path_ref": LEASE_HELPER_PATH_REF,
        "lease_helper_digest_ref": _helper_digest_ref(),
        "lease_posture_ref": LEASE_POSTURE_REF,
    }


def _exact_resource_refs(constraints: dict[str, object]) -> list[str]:
    refs = [
        constraints.get("run_ref"),
        constraints.get("local_model_endpoint_ref"),
        constraints.get("local_model_model_ref"),
    ]
    if not all(isinstance(ref, str) for ref in refs):
        raise ValueError("TAW-08 exact local model resource binding is invalid")
    return sorted(str(ref) for ref in refs)


def _issue_request(constraints: dict[str, object]) -> AuthorityLeaseIssueRequest:
    return AuthorityLeaseIssueRequest(
        mode=TrustMode.full_machine_access_session,
        scope=AuthorityLeaseScope.mission,
        mission_ref=str(constraints["run_ref"]),
        operator_ref=AUTHORITY_LEASE_LOCAL_OPERATOR_REF,
        requested_domains={
            AuthorityDomain.provider_model_calls: [AuthorityCapability.execute]
        },
        authority_constraints=[
            AuthorityConstraint(
                constraint_ref=LEASE_RUN_CONSTRAINT_REF,
                kind=AuthorityConstraintKind.resource_refs,
                allowed_refs=_exact_resource_refs(constraints),
                safe_summary=(
                    "Limit local model execution to the exact TAW-08 run, "
                    "loopback endpoint, and model."
                ),
            )
        ],
        constraints=constraints,
        decision_reason_ref=ISSUE_REASON_REF,
        duration_minutes=LEASE_DURATION_MINUTES,
        safe_summary=(
            "Authorize the exact founder-private TAW-08 local live-model "
            "measurement window for two hours."
        ),
    )


def _expected_stored_constraints(
    binding_constraints: dict[str, object], *, idempotency_ref: str
) -> tuple[dict[str, object], Any]:
    request = _issue_request(binding_constraints)
    requirement = build_authority_lease_approval_requirement_for_request(
        request,
        idempotency_ref=idempotency_ref,
    )
    approval_ref = build_authority_lease_backend_approval_ref(
        requirement,
        idempotency_ref=idempotency_ref,
    )
    return (
        {
            **binding_constraints,
            "decision_reason_ref": ISSUE_REASON_REF,
            "idempotency_ref": idempotency_ref,
            "approval_required": True,
            "approval_validated": True,
            "approval_ref": approval_ref,
            "approval_scope_ref": requirement.approval_scope_ref,
            "approval_request_ref": requirement.approval_request_ref,
            "approval_status": "approved",
            "unsupported_adapters_execute": False,
        },
        requirement,
    )


def _stored_constraints_match(
    constraints: object,
    *,
    expected_binding: dict[str, object] | None = None,
    idempotency_ref: str | None = None,
    receipt: Any | None = None,
) -> bool:
    if not isinstance(constraints, dict):
        return False
    binding_keys = {
        "candidate_revision_ref",
        "candidate_manifest_digest_ref",
        "run_ref",
        "lease_helper_path_ref",
        "lease_helper_digest_ref",
        "lease_posture_ref",
        "local_model_endpoint_ref",
        "local_model_model_ref",
        "exact_resource_refs_required",
    }
    observed_binding = {key: constraints.get(key) for key in binding_keys}
    if not all(
        isinstance(value, str)
        for key, value in observed_binding.items()
        if key != "exact_resource_refs_required"
    ) or observed_binding["exact_resource_refs_required"] is not True:
        return False
    if expected_binding is not None and observed_binding != expected_binding:
        return False
    if expected_binding is None:
        if (
            not re.fullmatch(
                r"git-sha:[0-9a-f]{40}",
                str(observed_binding["candidate_revision_ref"]),
            )
            or not re.fullmatch(
                r"sha256:[0-9a-f]{64}",
                str(observed_binding["candidate_manifest_digest_ref"]),
            )
            or not re.fullmatch(
                r"run-ref:taw08:[a-z0-9][a-z0-9._:-]{0,160}",
                str(observed_binding["run_ref"]),
            )
            or observed_binding["lease_helper_path_ref"] != LEASE_HELPER_PATH_REF
            or not re.fullmatch(
                r"sha256:[0-9a-f]{64}",
                str(observed_binding["lease_helper_digest_ref"]),
            )
            or observed_binding["lease_posture_ref"] != LEASE_POSTURE_REF
            or observed_binding["local_model_endpoint_ref"]
            != runtime_local_model_endpoint_ref(LOCAL_MODEL_BASE_URL)
            or observed_binding["local_model_model_ref"]
            != runtime_local_model_model_ref(LOCAL_MODEL_REF)
        ):
            return False
        validated_binding = dict(observed_binding)
    else:
        try:
            validated_binding = lease_constraints(
                candidate_revision_ref=str(observed_binding["candidate_revision_ref"]),
                candidate_manifest_digest_ref=str(
                    observed_binding["candidate_manifest_digest_ref"]
                ),
                run_ref=str(observed_binding["run_ref"]),
            )
        except ValueError:
            return False
    if observed_binding != validated_binding:
        return False
    observed_idempotency_ref = constraints.get("idempotency_ref")
    if not isinstance(observed_idempotency_ref, str):
        return False
    if idempotency_ref is not None and observed_idempotency_ref != idempotency_ref:
        return False
    expected, requirement = _expected_stored_constraints(
        validated_binding,
        idempotency_ref=observed_idempotency_ref,
    )
    if constraints != expected:
        return False
    if receipt is not None and (
        receipt.idempotency_ref != observed_idempotency_ref
        or receipt.approval_ref != expected["approval_ref"]
        or receipt.approval_scope_ref != requirement.approval_scope_ref
        or receipt.approval_request_ref != requirement.approval_request_ref
        or receipt.approval_status != "approved"
    ):
        return False
    return True


def _captured_stored_constraints_match(
    constraints: object,
    *,
    expected_binding: dict[str, object],
    idempotency_ref: str,
) -> bool:
    if not isinstance(constraints, dict):
        return False
    observed_binding = {
        key: constraints.get(key)
        for key in {
            "candidate_revision_ref",
            "candidate_manifest_digest_ref",
            "run_ref",
            "lease_helper_path_ref",
            "lease_helper_digest_ref",
            "lease_posture_ref",
            "local_model_endpoint_ref",
            "local_model_model_ref",
            "exact_resource_refs_required",
        }
    }
    if observed_binding != expected_binding:
        return False
    expected, _requirement = _expected_stored_constraints(
        expected_binding,
        idempotency_ref=idempotency_ref,
    )
    return constraints == expected


def _owner_only_state_dir(path: Path) -> Path:
    return require_private_tree(
        path,
        purpose="authority state directory",
    )


def _validate_owner_only_tree(root: Path) -> None:
    require_private_tree(root, purpose="authority state directory")


def _domain_payload(value: dict[Any, list[Any]]) -> dict[str, list[str]]:
    return {
        getattr(domain, "value", str(domain)): sorted(
            getattr(capability, "value", str(capability)) for capability in capabilities
        )
        for domain, capabilities in sorted(
            value.items(), key=lambda item: getattr(item[0], "value", str(item[0]))
        )
    }


def _safe_receipt(*, lease: Any, receipt: Any) -> dict[str, object]:
    granted_domains = _domain_payload(receipt.granted_domains)
    expires_at = receipt.lease_expires_at
    if expires_at is None and lease is not None:
        expires_at = lease.expires_at
    if expires_at is None:
        raise RuntimeError("TAW-08 lease receipt has no expiry")
    payload = {
        "lease_ref": receipt.lease_ref,
        "status": receipt.status,
        "expires_at": expires_at.isoformat(),
        "granted_domains": granted_domains,
        "receipt_ref": receipt.receipt_ref,
        "candidate_revision_ref": lease.constraints["candidate_revision_ref"],
        "candidate_manifest_digest_ref": lease.constraints[
            "candidate_manifest_digest_ref"
        ],
        "run_ref": lease.constraints["run_ref"],
        "lease_helper_digest_ref": lease.constraints["lease_helper_digest_ref"],
        "lease_posture_ref": lease.constraints["lease_posture_ref"],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    if len(encoded) > 4_096:
        raise RuntimeError("TAW-08 lease receipt exceeds the output bound")
    return payload


def _compensating_revoke_new_issue(
    store: AuthorityLeaseStore,
    *,
    lease: Any,
    issue_idempotency_ref: str,
) -> None:
    rollback_token = hashlib.sha256(
        f"{issue_idempotency_ref}:{lease.lease_ref}".encode("utf-8")
    ).hexdigest()[:24]
    rollback_idempotency_ref = (
        f"idempotency-ref:taw08-live-issue-rollback-{rollback_token}"
    )
    revoked, receipt = store.revoke_lease(
        AuthorityLeaseRevokeRequest(
            lease_ref=lease.lease_ref,
            decision_reason_ref=ISSUE_ROLLBACK_REASON_REF,
            safe_summary=(
                "Revoke a newly issued TAW-08 lease after issue validation failed."
            ),
        ),
        idempotency_ref=rollback_idempotency_ref,
    )
    if (
        revoked is None
        or revoked.lease_ref != lease.lease_ref
        or revoked.status != AuthorityLeaseStatus.revoked
        or receipt.status != "revoked"
        or receipt.lease_ref != lease.lease_ref
        or receipt.granted_domains
        or receipt.execution_performed
        or receipt.raw_paths_included
        or receipt.raw_prompt_included
        or receipt.raw_response_included
        or receipt.raw_provider_payload_included
    ):
        raise RuntimeError("TAW-08 live lease compensating revoke failed")


def _interrupted_exact_active_lease(
    store: AuthorityLeaseStore,
    *,
    request: AuthorityLeaseIssueRequest,
    expected_binding: dict[str, object],
    idempotency_ref: str,
) -> Any | None:
    matches = [
        lease
        for lease in store.list_leases(active_only=True)
        if lease.status == AuthorityLeaseStatus.active
        and lease.mode == TrustMode.full_machine_access_session
        and lease.scope == AuthorityLeaseScope.mission
        and lease.mission_ref == expected_binding["run_ref"]
        and lease.authority_constraints == request.authority_constraints
        and lease.operator_ref == AUTHORITY_LEASE_LOCAL_OPERATOR_REF
        and _domain_payload(lease.domains) == EXPECTED_DOMAINS
        and _captured_stored_constraints_match(
            lease.constraints,
            expected_binding=expected_binding,
            idempotency_ref=idempotency_ref,
        )
    ]
    if len(matches) > 1:
        raise RuntimeError("TAW-08 interrupted lease issue state is ambiguous")
    return matches[0] if matches else None


def _active_lease_matches_exact_issue(
    lease: Any,
    *,
    request: AuthorityLeaseIssueRequest,
    expected_binding: dict[str, object],
    idempotency_ref: str,
) -> bool:
    return (
        lease.status == AuthorityLeaseStatus.active
        and lease.mode == TrustMode.full_machine_access_session
        and lease.scope == AuthorityLeaseScope.mission
        and lease.mission_ref == expected_binding["run_ref"]
        and lease.authority_constraints == request.authority_constraints
        and lease.operator_ref == AUTHORITY_LEASE_LOCAL_OPERATOR_REF
        and _domain_payload(lease.domains) == EXPECTED_DOMAINS
        and _captured_stored_constraints_match(
            lease.constraints,
            expected_binding=expected_binding,
            idempotency_ref=idempotency_ref,
        )
    )


def issue_live_lease(
    *,
    state_dir: Path,
    idempotency_ref: str,
    candidate_revision_ref: str,
    candidate_manifest_digest_ref: str,
    run_ref: str,
) -> dict[str, object]:
    prior_umask = os.umask(0o077)
    try:
        return _issue_live_lease(
            state_dir=state_dir,
            idempotency_ref=idempotency_ref,
            candidate_revision_ref=candidate_revision_ref,
            candidate_manifest_digest_ref=candidate_manifest_digest_ref,
            run_ref=run_ref,
        )
    finally:
        os.umask(prior_umask)


def _issue_live_lease(
    *,
    state_dir: Path,
    idempotency_ref: str,
    candidate_revision_ref: str,
    candidate_manifest_digest_ref: str,
    run_ref: str,
) -> dict[str, object]:
    resolved_state = _owner_only_state_dir(state_dir)
    expected_constraints = lease_constraints(
        candidate_revision_ref=candidate_revision_ref,
        candidate_manifest_digest_ref=candidate_manifest_digest_ref,
        run_ref=run_ref,
    )
    request = _issue_request(expected_constraints)
    store = AuthorityLeaseStore(resolved_state)
    with store.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
        return _issue_live_lease_locked(
            store=store,
            request=request,
            expected_constraints=expected_constraints,
            idempotency_ref=idempotency_ref,
        )


def _issue_live_lease_locked(
    *,
    store: AuthorityLeaseStore,
    request: AuthorityLeaseIssueRequest,
    expected_constraints: dict[str, object],
    idempotency_ref: str,
) -> dict[str, object]:
    active_before = store.list_leases(active_only=True)
    if active_before and (
        len(active_before) != 1
        or not _active_lease_matches_exact_issue(
            active_before[0],
            request=request,
            expected_binding=expected_constraints,
            idempotency_ref=idempotency_ref,
        )
    ):
        raise RuntimeError("TAW-08 authority state has another active lease")
    try:
        requirement, grant, lease, receipt = (
            issue_authority_lease_with_backend_approval(
                store,
                request,
                idempotency_ref=idempotency_ref,
                approved_by_actor_id=AUTHORITY_LEASE_LOCAL_OPERATOR_REF,
            )
        )
    except BaseException:
        interrupted_lease = _interrupted_exact_active_lease(
            store,
            request=request,
            expected_binding=expected_constraints,
            idempotency_ref=idempotency_ref,
        )
        if interrupted_lease is not None:
            _compensating_revoke_new_issue(
                store,
                lease=interrupted_lease,
                issue_idempotency_ref=idempotency_ref,
            )
        raise
    try:
        if (
            receipt.status not in {"issued", "replayed"}
            or lease is None
            or lease.status != AuthorityLeaseStatus.active
            or not lease.is_active()
            or lease.mode != TrustMode.full_machine_access_session
            or lease.scope != AuthorityLeaseScope.mission
            or lease.mission_ref != expected_constraints["run_ref"]
            or lease.authority_constraints != request.authority_constraints
            or lease.operator_ref != AUTHORITY_LEASE_LOCAL_OPERATOR_REF
            or _domain_payload(lease.domains) != EXPECTED_DOMAINS
            or _domain_payload(receipt.requested_domains) != EXPECTED_DOMAINS
            or _domain_payload(receipt.granted_domains) != EXPECTED_DOMAINS
            or not _stored_constraints_match(
                lease.constraints,
                expected_binding=expected_constraints,
                idempotency_ref=idempotency_ref,
                receipt=receipt,
            )
            or lease.expires_at - lease.issued_at
            != timedelta(minutes=LEASE_DURATION_MINUTES)
            or receipt.lease_issued_at != lease.issued_at
            or receipt.lease_expires_at != lease.expires_at
            or receipt.denied_domain_refs
            or receipt.unsupported_adapter_refs
            or not requirement.approval_required
            or not receipt.approval_required
            or not receipt.approval_validated
            or receipt.approval_status != "approved"
            or (receipt.status == "issued" and grant is None)
            or receipt.execution_performed
            or receipt.raw_paths_included
            or receipt.raw_prompt_included
            or receipt.raw_response_included
            or receipt.raw_provider_payload_included
        ):
            raise RuntimeError("TAW-08 live lease issue binding drift")
        active_after = store.list_leases(active_only=True)
        if (
            len(active_after) != 1
            or active_after[0].lease_ref != lease.lease_ref
            or not _active_lease_matches_exact_issue(
                active_after[0],
                request=request,
                expected_binding=expected_constraints,
                idempotency_ref=idempotency_ref,
            )
        ):
            raise RuntimeError("TAW-08 authority state is not dedicated")
        _validate_owner_only_tree(store.state_dir)
        return _safe_receipt(lease=lease, receipt=receipt)
    except BaseException:
        issued_exact_lease = _interrupted_exact_active_lease(
            store,
            request=request,
            expected_binding=expected_constraints,
            idempotency_ref=idempotency_ref,
        )
        if issued_exact_lease is not None:
            _compensating_revoke_new_issue(
                store,
                lease=issued_exact_lease,
                issue_idempotency_ref=idempotency_ref,
            )
        raise


def revoke_live_lease(
    *, state_dir: Path, lease_ref: str, idempotency_ref: str
) -> dict[str, object]:
    prior_umask = os.umask(0o077)
    try:
        return _revoke_live_lease(
            state_dir=state_dir,
            lease_ref=lease_ref,
            idempotency_ref=idempotency_ref,
        )
    finally:
        os.umask(prior_umask)


def _revoke_live_lease(
    *, state_dir: Path, lease_ref: str, idempotency_ref: str
) -> dict[str, object]:
    resolved_state = _owner_only_state_dir(state_dir)
    store = AuthorityLeaseStore(resolved_state)
    existing = store.get_lease(lease_ref)
    issuance_constraints: dict[str, object] | None = None
    revocation_binding_valid = False
    if existing is not None and isinstance(existing.constraints, dict):
        issuance_constraints = dict(existing.constraints)
        observed_revocation_reason_ref = issuance_constraints.pop(
            "revocation_reason_ref",
            None,
        )
        observed_revocation_idempotency_ref = issuance_constraints.pop(
            "revocation_idempotency_ref",
            None,
        )
        if existing.status == AuthorityLeaseStatus.active:
            revocation_binding_valid = (
                observed_revocation_reason_ref is None
                and observed_revocation_idempotency_ref is None
            )
        elif existing.status == AuthorityLeaseStatus.revoked:
            revocation_binding_valid = (
                observed_revocation_reason_ref == REVOKE_REASON_REF
                and observed_revocation_idempotency_ref == idempotency_ref
            )
    stored_binding_valid = bool(
        revocation_binding_valid
        and issuance_constraints is not None
        and _stored_constraints_match(issuance_constraints)
    )
    expected_authority_constraints: list[AuthorityConstraint] | None = None
    if (
        stored_binding_valid
        and existing is not None
        and issuance_constraints is not None
    ):
        binding = {
            key: issuance_constraints.get(key)
            for key in (
                "candidate_revision_ref",
                "candidate_manifest_digest_ref",
                "run_ref",
                "local_model_endpoint_ref",
                "local_model_model_ref",
                "exact_resource_refs_required",
                "lease_helper_path_ref",
                "lease_helper_digest_ref",
                "lease_posture_ref",
            )
        }
        try:
            expected_authority_constraints = _issue_request(
                binding
            ).authority_constraints
        except (TypeError, ValueError):
            stored_binding_valid = False
    if (
        existing is None
        or existing.lease_ref != lease_ref
        or existing.mode != TrustMode.full_machine_access_session
        or existing.scope != AuthorityLeaseScope.mission
        or existing.mission_ref != existing.constraints.get("run_ref")
        or not stored_binding_valid
        or existing.authority_constraints != expected_authority_constraints
        or existing.operator_ref != AUTHORITY_LEASE_LOCAL_OPERATOR_REF
        or _domain_payload(existing.domains) != EXPECTED_DOMAINS
        or existing.expires_at - existing.issued_at
        != timedelta(minutes=LEASE_DURATION_MINUTES)
    ):
        raise ValueError("TAW-08 revoke target is not the exact live lease")
    request = AuthorityLeaseRevokeRequest(
        lease_ref=lease_ref,
        decision_reason_ref=REVOKE_REASON_REF,
        safe_summary="Revoke the exact founder-private TAW-08 live-model lease.",
    )
    lease, receipt = store.revoke_lease(
        request,
        idempotency_ref=idempotency_ref,
    )
    if (
        receipt.status not in {"revoked", "replayed"}
        or lease is None
        or lease.lease_ref != lease_ref
        or lease.status != AuthorityLeaseStatus.revoked
        or receipt.lease_ref != lease_ref
        or receipt.mode != TrustMode.full_machine_access_session
        or receipt.scope != AuthorityLeaseScope.mission
        or receipt.lease_issued_at != existing.issued_at
        or receipt.lease_expires_at != existing.expires_at
        or receipt.granted_domains
        or receipt.execution_performed
        or receipt.raw_paths_included
        or receipt.raw_prompt_included
        or receipt.raw_response_included
        or receipt.raw_provider_payload_included
    ):
        raise RuntimeError("TAW-08 live lease revoke binding drift")
    _validate_owner_only_tree(resolved_state)
    return _safe_receipt(lease=lease, receipt=receipt)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Issue or revoke only the exact two-hour TAW-08 provider-model "
            "execution lease. This command never calls a model."
        )
    )
    subparsers = parser.add_subparsers(dest="operation", required=True)
    issue = subparsers.add_parser("issue")
    issue.add_argument("--state-dir", type=Path, required=True)
    issue.add_argument("--idempotency-ref", required=True)
    issue.add_argument("--candidate-revision-ref", required=True)
    issue.add_argument("--candidate-manifest-digest-ref", required=True)
    issue.add_argument("--run-ref", required=True)
    revoke = subparsers.add_parser("revoke")
    revoke.add_argument("--state-dir", type=Path, required=True)
    revoke.add_argument("--lease-ref", required=True)
    revoke.add_argument("--idempotency-ref", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    prior_umask = os.umask(0o077)
    try:
        if arguments.operation == "issue":
            payload = issue_live_lease(
                state_dir=arguments.state_dir,
                idempotency_ref=arguments.idempotency_ref,
                candidate_revision_ref=arguments.candidate_revision_ref,
                candidate_manifest_digest_ref=(arguments.candidate_manifest_digest_ref),
                run_ref=arguments.run_ref,
            )
        else:
            payload = revoke_live_lease(
                state_dir=arguments.state_dir,
                lease_ref=arguments.lease_ref,
                idempotency_ref=arguments.idempotency_ref,
            )
    except (
        OSError,
        ValueError,
        RuntimeError,
        ValidationError,
        AuthorityLeaseApprovalConflictError,
        AuthorityLeaseApprovalStateError,
    ):
        print("TAW-08 live lease operation blocked.", file=sys.stderr)
        return 1
    finally:
        os.umask(prior_umask)
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
