#!/usr/bin/env python3
"""Measure verifier value with fixed, safe, in-process synthetic mutations.

The synthetic inputs in this module are transient. They are never written into
the repository, emitted in output, or included in a receipt. Results contain
only bounded refs, hashes, counts, and durations so they can be projected into
``VerificationValueRecord`` contracts by the canonical verification layer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Callable, Iterator


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import verify_product_truth  # noqa: E402
from scripts import verify_security_redaction_artifacts  # noqa: E402
from scripts.verification import api_contract_snapshot  # noqa: E402
from scripts.verification import run_frontend_check  # noqa: E402
from scripts.verification.ci_command_manifest import build_plan  # noqa: E402
from scripts.verification.verification_contracts import (  # noqa: E402
    VerificationValueRecord,
    dependency_state_fingerprint,
    verification_value_record_fingerprint,
)


SCHEMA_VERSION = "uaa_verifier_value_measurement_run.v2"
RECORD_SCHEMA_VERSION = "uaa_verification_value.v2"
REDACTION_STATUS = "content_free_refs_hashes_counts_and_durations_only"
UNIT_REF = "unit:verification-value-measurement"
MAX_PROBE_DURATION_MS = 60_000
_FRONTEND_PROBE_LOCK = threading.Lock()


class VerifierValueMeasurementError(RuntimeError):
    """The fixed verifier-value measurement could not settle safely."""


@dataclass(frozen=True)
class SyntheticProbe:
    probe_ref: str
    verifier_ref: str
    synthetic_mutation_ref: str
    defect_ref: str
    overlap_ref: str
    disposition: str
    execute: Callable[[], bool]


@dataclass(frozen=True)
class MeasurementBindings:
    repository_sha: str
    dependency_state_fingerprint: str
    platform_fingerprint: str
    command_manifest_fingerprint: str
    verifier_definition_fingerprint: str
    test_collection_fingerprint: str

    def payload(self) -> dict[str, str]:
        return asdict(self)


def _canonical(payload: object) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _digest(payload: object) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


def bindings_from_repository(repo: Path = ROOT) -> MeasurementBindings:
    try:
        repository_sha = subprocess.run(
            ("git", "rev-parse", "HEAD"),
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        dirty = subprocess.run(
            ("git", "status", "--porcelain", "--untracked-files=all"),
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        ).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        raise VerifierValueMeasurementError(
            "verification measurement repository state is unavailable"
        ) from exc
    if dirty:
        raise VerifierValueMeasurementError(
            "verification measurement requires a clean exact repository state"
        )
    plan = build_plan(repo, repository_sha)
    return MeasurementBindings(
        repository_sha=plan.repository_sha,
        dependency_state_fingerprint=dependency_state_fingerprint(plan),
        platform_fingerprint=plan.platform_fingerprint,
        command_manifest_fingerprint=plan.command_manifest_fingerprint,
        verifier_definition_fingerprint=plan.verifier_definition_fingerprint,
        test_collection_fingerprint=plan.test_collection_fingerprint,
    )


def _validate_owner_only_directory(path: Path) -> None:
    metadata = path.lstat()
    if (
        path.is_symlink()
        or not stat.S_ISDIR(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o700
        or metadata.st_uid != os.getuid()
    ):
        raise VerifierValueMeasurementError(
            "synthetic measurement boundary is not owner-only"
        )


@contextmanager
def _owner_only_temporary_directory() -> Iterator[Path]:
    parent = Path(tempfile.gettempdir()).resolve(strict=True)
    parent_metadata = parent.lstat()
    if parent.is_symlink() or not stat.S_ISDIR(parent_metadata.st_mode):
        raise VerifierValueMeasurementError(
            "synthetic measurement parent is unsafe"
        )
    with tempfile.TemporaryDirectory(
        prefix="uaa-verifier-value-",
        dir=parent,
    ) as directory:
        path = Path(directory)
        path.chmod(0o700)
        _validate_owner_only_directory(path)
        yield path


def _write_private_json(path: Path, payload: object) -> None:
    parent = path.parent
    _validate_owner_only_directory(parent)
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            json.dump(payload, handle, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    metadata = path.lstat()
    if (
        path.is_symlink()
        or not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o600
        or metadata.st_uid != os.getuid()
    ):
        raise VerifierValueMeasurementError(
            "synthetic measurement file is not owner-only"
        )


def _product_truth_probe() -> bool:
    # Split the input so the repository source itself is not an unsafe claim.
    synthetic_input = "blocked" + " capability is complete"
    findings = verify_product_truth.scan_text(
        "synthetic/value-probe.md",
        synthetic_input,
    )
    return any(
        finding.category == "blocked_work_claimed_complete" for finding in findings
    )


def _security_redaction_probe() -> bool:
    # Split the input so the repository source itself contains no credential.
    synthetic_input = "api_" + "key=" + ("x" * 16)
    findings = verify_security_redaction_artifacts.scan_text(
        "synthetic/value-probe.txt",
        synthetic_input,
    )
    return any(finding.category == "secret_like_material" for finding in findings)


def _api_contract_probe() -> bool:
    stored = api_contract_snapshot.load_snapshot()
    manifest_keys = (
        "route_classification_vocabulary",
        "route_classification_summary",
        "route_auth_posture_summary",
        "route_approval_posture_summary",
        "route_idempotency_posture_summary",
        "idempotency_audit_policy_ref",
        "route_rate_limit_posture_summary",
        "rate_limit_policy_ref",
        "routes",
    )
    manifest = json.loads(
        json.dumps({key: stored[key] for key in manifest_keys}, sort_keys=True)
    )
    paths: dict[str, dict[str, dict[str, str]]] = {}
    for route in stored["routes"]:
        paths.setdefault(route["path"], {})[route["method"].lower()] = {
            "operationId": route["operation_id"]
        }
    original_path = sorted(paths)[0]
    operation = paths.pop(original_path)
    paths[f"{original_path}-synthetic-drift"] = operation
    try:
        api_contract_snapshot.build_snapshot_from_sources(
            manifest,
            {"paths": paths},
        )
    except ValueError as exc:
        return "API_CONTRACT_OPENAPI_ROUTE_IDENTITY_DRIFT" in str(exc)
    return False


def _frontend_declaration_probe() -> bool:
    # Verify the real declaration first so a pre-existing defect cannot be
    # mislabeled as a successfully killed synthetic mutation.
    scripts = run_frontend_check._load_scripts()
    synthetic_scripts = dict(scripts)
    synthetic_scripts["lint"] = "synthetic-declaration-drift"
    with _FRONTEND_PROBE_LOCK, _owner_only_temporary_directory() as temporary:
        application = temporary / "control-center"
        application.mkdir(mode=0o700)
        _write_private_json(
            application / "package.json",
            {"scripts": synthetic_scripts},
        )
        original_application = run_frontend_check.APP
        try:
            run_frontend_check.APP = application
            run_frontend_check._load_scripts()
        except run_frontend_check.FrontendCheckError as exc:
            return "duplicate-proof declaration changed" in str(exc)
        finally:
            run_frontend_check.APP = original_application
    return False


PROBES = (
    SyntheticProbe(
        probe_ref="probe:verifier-value:product-truth",
        verifier_ref="verifier:product-truth",
        synthetic_mutation_ref="mutation:product-truth-overclaim",
        defect_ref="defect:unsupported-product-claim",
        overlap_ref="overlap:documentation-text-scan-partial",
        disposition="retain",
        execute=_product_truth_probe,
    ),
    SyntheticProbe(
        probe_ref="probe:verifier-value:security-redaction",
        verifier_ref="verifier:security-redaction",
        synthetic_mutation_ref="mutation:durable-secret-like-content",
        defect_ref="defect:unsafe-durable-artifact-content",
        overlap_ref="overlap:product-truth-claim-scan-partial",
        disposition="retain",
        execute=_security_redaction_probe,
    ),
    SyntheticProbe(
        probe_ref="probe:verifier-value:api-contract",
        verifier_ref="verifier:api-contract",
        synthetic_mutation_ref="mutation:api-route-identity-drift",
        defect_ref="defect:api-schema-route-and-security-policy-drift",
        overlap_ref="overlap:shared-api-context",
        disposition="retain",
        execute=_api_contract_probe,
    ),
    SyntheticProbe(
        probe_ref="probe:verifier-value:frontend-declaration",
        verifier_ref="verifier:control-center-frontend",
        synthetic_mutation_ref="mutation:frontend-package-script-drift",
        defect_ref="defect:frontend-type-test-build-contract",
        overlap_ref="overlap:frontend-safety-static-partial",
        disposition="retain",
        execute=_frontend_declaration_probe,
    ),
)


def _probe_definition_fingerprint(probe: SyntheticProbe) -> str:
    return _digest(
        {
            "probe_ref": probe.probe_ref,
            "verifier_ref": probe.verifier_ref,
            "synthetic_mutation_ref": probe.synthetic_mutation_ref,
            "defect_ref": probe.defect_ref,
            "overlap_ref": probe.overlap_ref,
            "disposition": probe.disposition,
        }
    )


def _run_probe(
    probe: SyntheticProbe,
    bindings: MeasurementBindings,
) -> VerificationValueRecord:
    started = time.monotonic_ns()
    try:
        killed = probe.execute()
    except (
        json.JSONDecodeError,
        OSError,
        TypeError,
        ValueError,
        VerifierValueMeasurementError,
    ):
        outcome = "blocked"
    else:
        outcome = "killed" if killed else "survived"
    duration_ms = min(
        MAX_PROBE_DURATION_MS,
        max(0, (time.monotonic_ns() - started + 999_999) // 1_000_000),
    )
    provisional = VerificationValueRecord(
        schema_version=RECORD_SCHEMA_VERSION,
        value_ref="value:verification:" + "0" * 64,
        unit_ref=UNIT_REF,
        verifier_ref=probe.verifier_ref,
        synthetic_mutation_ref=probe.synthetic_mutation_ref,
        defect_ref=probe.defect_ref,
        outcome=outcome,
        receipt_ref="receipt:verification-value:" + "0" * 64,
        overlap_ref=probe.overlap_ref,
        disposition=probe.disposition,
        duration_ms=duration_ms,
        repository_sha=bindings.repository_sha,
        dependency_state_fingerprint=(
            bindings.dependency_state_fingerprint
        ),
        platform_fingerprint=bindings.platform_fingerprint,
        command_manifest_fingerprint=bindings.command_manifest_fingerprint,
        verifier_definition_fingerprint=(
            bindings.verifier_definition_fingerprint
        ),
        test_collection_fingerprint=bindings.test_collection_fingerprint,
        probe_definition_fingerprint=_probe_definition_fingerprint(probe),
        detection_ref=f"detection:verification:{outcome}",
        value_fingerprint="0" * 64,
    )
    fingerprint = verification_value_record_fingerprint(provisional)
    result = replace(
        provisional,
        value_ref=f"value:verification:{fingerprint}",
        receipt_ref=f"receipt:verification-value:{fingerprint}",
        value_fingerprint=fingerprint,
    )
    result.validate()
    return result


def run_measurements(
    bindings: MeasurementBindings | None = None,
) -> dict[str, object]:
    exact_bindings = bindings or bindings_from_repository()
    results = tuple(_run_probe(probe, exact_bindings) for probe in PROBES)
    records = [asdict(result) for result in results]
    killed_count = sum(record["outcome"] == "killed" for record in records)
    status = "passed" if killed_count == len(records) else "failed"
    unsigned: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "unit_ref": UNIT_REF,
        "bindings": exact_bindings.payload(),
        "probe_count": len(records),
        "killed_count": killed_count,
        "blocked_count": sum(record["outcome"] == "blocked" for record in records),
        "survived_count": sum(
            record["outcome"] == "survived" for record in records
        ),
        "value_records": records,
        "redaction_status": REDACTION_STATUS,
    }
    fingerprint = _digest(unsigned)
    return {
        **unsigned,
        "measurement_run_ref": (
            f"measurement-run:verification-value:sha256:{fingerprint}"
        ),
        "fingerprint": fingerprint,
    }


def validate_measurement_run(payload: dict[str, object]) -> None:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise VerifierValueMeasurementError(
            "verification value measurement schema is invalid"
        )
    unsigned = {
        key: value
        for key, value in payload.items()
        if key not in {"measurement_run_ref", "fingerprint"}
    }
    fingerprint = _digest(unsigned)
    if (
        payload.get("fingerprint") != fingerprint
        or payload.get("measurement_run_ref")
        != f"measurement-run:verification-value:sha256:{fingerprint}"
    ):
        raise VerifierValueMeasurementError(
            "verification value measurement fingerprint is invalid"
        )
    records = payload.get("value_records")
    if (
        not isinstance(records, list)
        or payload.get("probe_count") != len(records)
        or payload.get("killed_count")
        != sum(
            isinstance(record, dict) and record.get("outcome") == "killed"
            for record in records
        )
        or payload.get("blocked_count")
        != sum(
            isinstance(record, dict) and record.get("outcome") == "blocked"
            for record in records
        )
        or payload.get("survived_count")
        != sum(
            isinstance(record, dict) and record.get("outcome") == "survived"
            for record in records
        )
        or payload.get("status")
        != (
            "passed"
            if sum(
                isinstance(record, dict) and record.get("outcome") == "killed"
                for record in records
            )
            == len(records)
            else "failed"
        )
    ):
        raise VerifierValueMeasurementError(
            "verification value measurement counts are invalid"
        )
    if payload.get("redaction_status") != REDACTION_STATUS:
        raise VerifierValueMeasurementError(
            "verification value measurement redaction posture is invalid"
        )
    raw_bindings = payload.get("bindings")
    if not isinstance(raw_bindings, dict) or set(raw_bindings) != set(
        MeasurementBindings.__dataclass_fields__
    ):
        raise VerifierValueMeasurementError(
            "verification value measurement bindings are invalid"
        )
    try:
        bindings = MeasurementBindings(**raw_bindings)
    except TypeError as exc:
        raise VerifierValueMeasurementError(
            "verification value measurement bindings are invalid"
        ) from exc
    expected_probes = {
        (probe.verifier_ref, probe.synthetic_mutation_ref): probe
        for probe in PROBES
    }
    observed_probes: set[tuple[str, str]] = set()
    for record in records:
        if not isinstance(record, dict):
            raise VerifierValueMeasurementError(
                "verification value measurement record is invalid"
            )
        if set(record) != set(VerificationValueRecord.__dataclass_fields__):
            raise VerifierValueMeasurementError(
                "verification value measurement record shape is invalid"
            )
        try:
            value_record = VerificationValueRecord(**record)
            value_record.validate()
        except (TypeError, ValueError) as exc:
            raise VerifierValueMeasurementError(
                "verification value record binding is invalid"
            ) from exc
        key = (
            value_record.verifier_ref,
            value_record.synthetic_mutation_ref,
        )
        probe = expected_probes.get(key)
        if (
            probe is None
            or key in observed_probes
            or value_record.probe_definition_fingerprint
            != _probe_definition_fingerprint(probe)
            or value_record.detection_ref
            != f"detection:verification:{value_record.outcome}"
            or any(
                getattr(value_record, field_name)
                != getattr(bindings, field_name)
                for field_name in MeasurementBindings.__dataclass_fields__
            )
        ):
            raise VerifierValueMeasurementError(
                "verification value record measurement binding is invalid"
            )
        observed_probes.add(key)
    if observed_probes != set(expected_probes):
        raise VerifierValueMeasurementError(
            "verification value measurement probe set is incomplete"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Measure fixed verifier value with safe synthetic mutations."
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = run_measurements()
    validate_measurement_run(result)
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(
            "Verifier value measurement: "
            f"{result['status']}; "
            f"killed={result['killed_count']}/{result['probe_count']}"
        )
        for record in result["value_records"]:
            print(f"  {record['verifier_ref']}: {record['outcome']}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
