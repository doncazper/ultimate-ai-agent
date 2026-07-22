#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verification.ci_command_manifest import (  # noqa: E402
    CI_ARCHITECTURE_PROFILE_REF,
    CI_JOB_GRAPH,
    VERIFICATION_DAG,
    build_plan,
    ci_architecture_inventory,
    lane_registry,
)
from scripts.verification.verification_contracts import (  # noqa: E402
    TYPESCRIPT_EXECUTION_COMMAND_REFS,
    VerificationReceipt,
    VerificationTerminalStatus,
    VerificationUnitKind,
    dependency_closed_unit_refs,
    dependency_lock_set_fingerprint,
    verification_run_manifest_payload,
)
from scripts.verification.verification_github_transport import (  # noqa: E402
    VerificationGithubTransportError,
    decode_github_job_output,
    validate_github_job_output_against_plan,
)
from scripts.verification.verification_run_aggregator import (  # noqa: E402
    aggregate_verification_run,
    validate_receipt_for_plan_unit,
)
from scripts.verification.typescript_binding import (  # noqa: E402
    TypeScriptBindingError,
    build_declared_typescript_binding,
    resolve_typescript_runtime_binding,
)

SCHEMA_VERSION = "uaa_ci_evidence_dag_gate.v1"
SAFE_REF = re.compile(r"^[a-z0-9][a-z0-9:._-]{0,191}$")
SHA = re.compile(r"^[0-9a-f]{40}$")
MAX_ENVELOPE_CHARS = 400_000
MAX_OUTPUT_BYTES = 128 * 1024


class CiEvidenceDagError(ValueError):
    def __init__(self, reason_ref: str) -> None:
        self.reason_ref = reason_ref
        super().__init__(f"CI evidence DAG rejected ({reason_ref})")


def _fail(reason_ref: str) -> None:
    raise CiEvidenceDagError(reason_ref)


def _timestamp(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        _fail("reason-ref:ci-evidence:receipt-timestamp-invalid")


def _parse_binding(value: str, *, label: str) -> tuple[str, str]:
    if not isinstance(value, str) or "=" not in value:
        _fail(f"reason-ref:ci-evidence:{label}-binding-invalid")
    unit_ref, bound_value = value.split("=", 1)
    if SAFE_REF.fullmatch(unit_ref) is None or not bound_value:
        _fail(f"reason-ref:ci-evidence:{label}-binding-invalid")
    return unit_ref, bound_value


def _exact_map(values: tuple[str, ...], *, label: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        unit_ref, bound_value = _parse_binding(value, label=label)
        if unit_ref in result:
            _fail(f"reason-ref:ci-evidence:{label}-duplicate")
        result[unit_ref] = bound_value
    return result


def _optional_map(
    values: tuple[str, ...],
    expected_refs: tuple[str, ...],
) -> dict[str, str]:
    if not values:
        _fail("reason-ref:ci-evidence:optional-envelope-missing")
    result: dict[str, str] = {}
    for value in values:
        if not isinstance(value, str) or "=" not in value:
            _fail("reason-ref:ci-evidence:optional-envelope-binding-invalid")
        unit_ref, bound_value = value.split("=", 1)
        if SAFE_REF.fullmatch(unit_ref) is None or unit_ref in result:
            _fail("reason-ref:ci-evidence:optional-envelope-binding-invalid")
        result[unit_ref] = bound_value
    if tuple(result) != expected_refs:
        _fail("reason-ref:ci-evidence:optional-envelope-membership-invalid")
    if any(not result[unit_ref] for unit_ref in expected_refs):
        _fail("reason-ref:ci-evidence:optional-envelope-missing")
    return result


def _resolve_canonical_typescript_runtime(
    repo: Path,
    expected_project_fingerprint: str,
) -> tuple[str, str]:
    try:
        declared = build_declared_typescript_binding(repo / "apps/control-center")
        if declared.declared_project_fingerprint != expected_project_fingerprint:
            raise TypeScriptBindingError(
                "typescript-runtime:terminal-plan-binding-mismatch"
            )
        runtime = resolve_typescript_runtime_binding(
            repo / "apps/control-center",
            declared,
        )
    except (OSError, subprocess.SubprocessError, TypeScriptBindingError, ValueError):
        _fail("reason-ref:ci-evidence:typescript-runtime-invalid")
    return (
        runtime.resolved_runtime_fingerprint,
        f"typescript-version:{runtime.typescript_version}",
    )


def validate_final_gate(
    repo: Path,
    repository_sha: str,
    base_sha: str,
    visual_scope: str,
    result_bindings: tuple[str, ...],
    envelope_bindings: tuple[str, ...],
    optional_envelope_bindings: tuple[str, ...] = (),
) -> dict[str, Any]:
    if SHA.fullmatch(repository_sha) is None or SHA.fullmatch(base_sha) is None:
        _fail("reason-ref:ci-evidence:sha-invalid")
    if visual_scope not in {"affected", "not_affected"}:
        _fail("reason-ref:ci-evidence:visual-scope-invalid")
    upstream_units = tuple(unit for unit in CI_JOB_GRAPH if unit.unit_ref != "foundation-gate-report")
    expected_refs = tuple(unit.unit_ref for unit in upstream_units)
    expected_envelope_refs = tuple(
        unit.unit_ref
        for unit in upstream_units
        if unit.evidence_posture != "typed_optional"
    )
    expected_optional_refs = tuple(
        unit.unit_ref
        for unit in upstream_units
        if unit.evidence_posture == "typed_optional"
    )
    results = _exact_map(result_bindings, label="result")
    envelopes = _exact_map(envelope_bindings, label="envelope")
    optional_envelopes = _optional_map(
        optional_envelope_bindings,
        expected_optional_refs,
    )
    if tuple(results) != expected_refs:
        _fail("reason-ref:ci-evidence:result-membership-invalid")
    if tuple(envelopes) != expected_envelope_refs:
        _fail("reason-ref:ci-evidence:envelope-membership-invalid")
    if any(results[unit_ref] != "success" for unit_ref in expected_refs):
        _fail("reason-ref:ci-evidence:upstream-not-successful")
    try:
        plan = build_plan(
            repo,
            repository_sha,
            base_sha=base_sha,
            frontend_visual_scope=visual_scope,
            verify_repository_state=True,
        )
    except (OSError, subprocess.SubprocessError, TypeScriptBindingError, ValueError):
        _fail("reason-ref:ci-evidence:canonical-plan-invalid")
    canonical_typescript_runtime = _resolve_canonical_typescript_runtime(
        repo,
        plan.typescript_project_fingerprint,
    )
    units_by_ref = {unit.unit_ref: unit for unit in upstream_units}
    decoded_receipts: dict[str, VerificationReceipt] = {}
    receipt_refs: list[tuple[str, str]] = []
    envelope_refs: list[tuple[str, str]] = []
    for unit in upstream_units:
        unit_ref = unit.unit_ref
        encoded = (
            optional_envelopes[unit_ref]
            if unit_ref in optional_envelopes
            else envelopes[unit_ref]
        )
        if not encoded:
            continue
        if len(encoded) > MAX_ENVELOPE_CHARS:
            _fail("reason-ref:ci-evidence:envelope-size-invalid")
        try:
            envelope = decode_github_job_output(encoded)
            validate_github_job_output_against_plan(envelope, plan)
        except VerificationGithubTransportError:
            _fail("reason-ref:ci-evidence:envelope-invalid")
        receipt = envelope.receipt
        unit = units_by_ref[unit_ref]
        if receipt.unit_ref != unit_ref:
            _fail("reason-ref:ci-evidence:cross-unit-substitution")
        try:
            validate_receipt_for_plan_unit(
                receipt,
                plan=plan,
                unit=unit,
                execution_surface_ref="surface-ref:github",
            )
        except ValueError:
            _fail("reason-ref:ci-evidence:receipt-unit-invalid")
        receipt_typescript_commands = {
            command_ref
            for command_ref, _result_ref in (
                *receipt.executed_command_result_bindings,
                *receipt.reused_command_receipt_bindings,
            )
        }.intersection(TYPESCRIPT_EXECUTION_COMMAND_REFS)
        if receipt_typescript_commands and (
            receipt.typescript_runtime_fingerprint,
            receipt.typescript_version_ref,
        ) != canonical_typescript_runtime:
            _fail("reason-ref:ci-evidence:typescript-runtime-invalid")
        optional_nonexecution_commands = tuple(
            command_ref
            for command_ref, _result_ref, _reason_ref in (
                receipt.nonexecuted_command_result_bindings
            )
        )
        expected_optional_commands = (
            lane_registry()[unit.lane_ref].optional_command_refs
            if unit.lane_ref is not None
            else ()
        )
        if unit.evidence_posture == "typed_optional":
            if (
                receipt.status not in {
                    VerificationTerminalStatus.PASSED,
                    VerificationTerminalStatus.BLOCKED,
                }
                or (
                    receipt.status is VerificationTerminalStatus.BLOCKED
                    and optional_nonexecution_commands != expected_optional_commands
                )
                or (
                    receipt.status is VerificationTerminalStatus.PASSED
                    and optional_nonexecution_commands
                )
            ):
                _fail("reason-ref:ci-evidence:optional-command-proof-invalid")
            if unit_ref == "release-lane-visual-regression" and (
                (visual_scope == "affected")
                != (receipt.status is VerificationTerminalStatus.PASSED)
            ):
                _fail("reason-ref:ci-evidence:visual-envelope-posture-invalid")
        elif (
            receipt.status is not VerificationTerminalStatus.PASSED
            or optional_nonexecution_commands
        ):
            _fail("reason-ref:ci-evidence:receipt-not-accepted")
        for dependency_ref in unit.needs:
            dependency_unit = units_by_ref[dependency_ref]
            dependency_receipt = decoded_receipts.get(dependency_ref)
            if dependency_receipt is None:
                _fail("reason-ref:ci-evidence:dependency-proof-invalid")
            if not (
                dependency_receipt.status is VerificationTerminalStatus.PASSED
                or (
                    dependency_unit.evidence_posture == "typed_optional"
                    and dependency_receipt.status
                    is VerificationTerminalStatus.BLOCKED
                )
            ):
                _fail("reason-ref:ci-evidence:dependency-proof-invalid")
            # A derived aggregate's interval is the span of its dependencies,
            # so its completion is the causal boundary. Executed units must
            # instead start only after every dependency completes.
            comparison_time = (
                receipt.completed_at
                if unit.unit_kind is VerificationUnitKind.AGGREGATE
                else receipt.started_at
            )
            if _timestamp(dependency_receipt.completed_at) > _timestamp(comparison_time):
                _fail("reason-ref:ci-evidence:dependency-proof-invalid")
        if unit.unit_kind is VerificationUnitKind.AGGREGATE:
            run = envelope.final_run_manifest
            aggregate_dependency_refs = dependency_closed_unit_refs(
                CI_JOB_GRAPH,
                unit.needs,
            )
            expected_dependency_refs = tuple(
                decoded_receipts[dependency_ref].receipt_ref
                for dependency_ref in aggregate_dependency_refs
            )
            expected_dependency_digest = hashlib.sha256(
                json.dumps(expected_dependency_refs, separators=(",", ":")).encode()
            ).hexdigest()
            dependency_receipts = tuple(
                decoded_receipts[dependency_ref]
                for dependency_ref in aggregate_dependency_refs
            )
            expected_started_at = min(
                dependency_receipts,
                key=lambda dependency: _timestamp(dependency.started_at),
            ).started_at
            expected_completed_at = max(
                dependency_receipts,
                key=lambda dependency: _timestamp(dependency.completed_at),
            ).completed_at
            expected_duration_ms = max(
                0,
                int(
                    (
                        _timestamp(expected_completed_at)
                        - _timestamp(expected_started_at)
                    ).total_seconds()
                    * 1000
                ),
            )
            expected_aggregate_bindings = tuple(
                (*receipt_refs, (unit_ref, receipt.receipt_ref))
            )
            expected_missing = tuple(
                candidate.unit_ref
                for candidate in CI_JOB_GRAPH
                if candidate.unit_ref not in {
                    *tuple(item.unit_ref for item in upstream_units[: upstream_units.index(unit) + 1])
                }
            )
            if (
                run is None
                or run.status is not VerificationTerminalStatus.BLOCKED
                or receipt.result_refs != expected_dependency_refs
                or receipt.output_digest != expected_dependency_digest
                or receipt.started_at != expected_started_at
                or receipt.completed_at != expected_completed_at
                or receipt.duration_ms != expected_duration_ms
                or run.unit_receipt_bindings != expected_aggregate_bindings
                or run.started_at != expected_started_at
                or run.completed_at != expected_completed_at
                or run.missing_unit_refs != expected_missing
                or run.failed_unit_refs
                or run.reason_refs != ("reason-ref:verification:whole-run-incomplete",)
            ):
                _fail("reason-ref:ci-evidence:aggregate-proof-invalid")
        elif envelope.final_run_manifest is not None:
            _fail("reason-ref:ci-evidence:unexpected-run-manifest")
        if unit_ref == "release-lane-frontend":
            frontend_source = decoded_receipts.get("control-center-frontend")
            if (
                frontend_source is None
                or "command:frontend.check"
                not in dict(frontend_source.executed_command_result_bindings)
                or receipt.reused_command_receipt_bindings
                != (("command:frontend.check", frontend_source.receipt_ref),)
            ):
                _fail("reason-ref:ci-evidence:reused-proof-invalid")
        decoded_receipts[unit_ref] = receipt
        receipt_refs.append((unit_ref, receipt.receipt_ref))
        envelope_refs.append((unit_ref, envelope.content_ref))
    aggregate_result = aggregate_verification_run(
        plan,
        VERIFICATION_DAG,
        tuple(
            receipt
            for unit_ref, receipt in decoded_receipts.items()
            if units_by_ref[unit_ref].unit_kind is not VerificationUnitKind.AGGREGATE
        ),
        execution_surface_ref="surface-ref:github",
    )
    derived_pytest = next(
        (
            receipt
            for receipt in aggregate_result.derived_receipts
            if receipt.unit_ref == "pytest"
        ),
        None,
    )
    terminal_run = aggregate_result.run_manifest
    if (
        derived_pytest != decoded_receipts.get("pytest")
        or terminal_run.status is not VerificationTerminalStatus.BLOCKED
        or terminal_run.missing_unit_refs != ("foundation-gate-report",)
        or terminal_run.failed_unit_refs
        or terminal_run.reason_refs
        != ("reason-ref:verification:whole-run-incomplete",)
    ):
        _fail("reason-ref:ci-evidence:terminal-run-proof-invalid")
    inventory = ci_architecture_inventory()
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "architecture_profile_ref": CI_ARCHITECTURE_PROFILE_REF,
        "repository_sha": repository_sha,
        "base_sha": base_sha,
        "frontend_visual_scope": visual_scope,
        "plan_fingerprint": plan.plan_fingerprint,
        "command_manifest_fingerprint": plan.command_manifest_fingerprint,
        "dependency_lock_set_fingerprint": dependency_lock_set_fingerprint(plan),
        "verifier_definition_fingerprint": plan.verifier_definition_fingerprint,
        "required_check_contexts": inventory["required_check_contexts"],
        "receipt_bindings": tuple(receipt_refs),
        "envelope_bindings": tuple(envelope_refs),
        "terminal_run_manifest": verification_run_manifest_payload(terminal_run),
        "redaction_status": "content_free_refs_hashes_and_statuses_only",
    }
    payload["content_fingerprint"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    return payload


def _write_output(path: Path, payload: dict[str, Any]) -> None:
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    if len(encoded) > MAX_OUTPUT_BYTES:
        _fail("reason-ref:ci-evidence:output-size-invalid")
    absolute = Path(os.path.abspath(os.fspath(path)))
    if absolute == Path(absolute.anchor) or absolute.name in {"", ".", ".."}:
        _fail("reason-ref:ci-evidence:output-invalid")
    parent_components = absolute.parent.parts[1:]
    if any(component in {"", ".", ".."} for component in parent_components):
        _fail("reason-ref:ci-evidence:output-invalid")
    directory_flags = (
        os.O_RDONLY
        | os.O_DIRECTORY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    parent_descriptor: int | None = None
    descriptor: int | None = None
    try:
        parent_descriptor = os.open(absolute.anchor, directory_flags)
        root_info = os.fstat(parent_descriptor)
        root_mode = stat.S_IMODE(root_info.st_mode)
        if (
            not stat.S_ISDIR(root_info.st_mode)
            or root_info.st_uid not in {0, os.geteuid()}
            or (root_mode & 0o022 and not root_mode & stat.S_ISVTX)
        ):
            _fail("reason-ref:ci-evidence:output-invalid")
        for component in parent_components:
            child_descriptor = os.open(
                component,
                directory_flags,
                dir_fd=parent_descriptor,
            )
            child_info = os.fstat(child_descriptor)
            child_mode = stat.S_IMODE(child_info.st_mode)
            if (
                not stat.S_ISDIR(child_info.st_mode)
                or child_info.st_uid not in {0, os.geteuid()}
                or (child_mode & 0o022 and not child_mode & stat.S_ISVTX)
            ):
                os.close(child_descriptor)
                _fail("reason-ref:ci-evidence:output-invalid")
            os.close(parent_descriptor)
            parent_descriptor = child_descriptor
        descriptor = os.open(
            absolute.name,
            flags,
            0o600,
            dir_fd=parent_descriptor,
        )
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) & 0o077
        ):
            _fail("reason-ref:ci-evidence:output-invalid")
        offset = 0
        while offset < len(encoded):
            written = os.write(descriptor, encoded[offset:])
            if written <= 0:
                _fail("reason-ref:ci-evidence:output-invalid")
            offset += written
        os.fsync(descriptor)
        final_info = os.fstat(descriptor)
        if (
            final_info.st_dev != info.st_dev
            or final_info.st_ino != info.st_ino
            or final_info.st_uid != info.st_uid
            or final_info.st_size != len(encoded)
        ):
            _fail("reason-ref:ci-evidence:output-invalid")
    except OSError:
        _fail("reason-ref:ci-evidence:output-invalid")
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if parent_descriptor is not None:
            try:
                os.close(parent_descriptor)
            except OSError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the exact-head CI evidence DAG")
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument(
        "--visual-scope",
        required=True,
        choices=("affected", "not_affected"),
    )
    parser.add_argument("--result", action="append", default=[])
    parser.add_argument("--envelope", action="append", default=[])
    parser.add_argument("--optional-envelope", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        payload = validate_final_gate(
            args.repo.resolve(),
            args.sha,
            args.base_sha,
            args.visual_scope,
            tuple(args.result),
            tuple(args.envelope),
            tuple(args.optional_envelope),
        )
        _write_output(args.output, payload)
    except CiEvidenceDagError as exc:
        print(exc, file=sys.stderr)
        return 1
    print("PASS: exact-head CI evidence DAG is complete and content-bound")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
