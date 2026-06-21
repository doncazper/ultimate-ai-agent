#!/usr/bin/env python3
"""Verify the local backup minimum set and offline restore behavior.

This verifier uses a deterministic synthetic fixture in a temporary workspace.
It does not inspect real local state, print filesystem paths, perform live
restore, or execute external commands.
"""
from __future__ import annotations


import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "uaa_backup_restore_verification.v1"
TASK_REF = "UAA-P1-045"
MINIMUM_STATE_CATEGORIES = (
    "runs",
    "receipts",
    "approvals",
    "settings",
    "registry",
    "audit_summaries",
    "local_model_cache_refs",
)
REPORT_SAFETY = {
    "raw_prompt_included": False,
    "raw_response_included": False,
    "raw_provider_payload_included": False,
    "raw_path_included": False,
    "raw_log_included": False,
    "username_included": False,
    "hostname_included": False,
    "serial_included": False,
    "environment_dump_included": False,
    "credential_material_included": False,
}
FORBIDDEN_OUTPUT_FRAGMENTS = (
    "/users/",
    "\\users\\",
    "raw prompt:",
    "raw response:",
    "raw provider payload:",
    "raw path:",
    "raw log:",
    "username:",
    "hostname:",
    "environment dump:",
    "credential:",
    "api_key",
    "secret_key",
    "password=",
    "token=",
)


def _fixture_records() -> dict[str, dict[str, Any]]:
    return {
        "runs": {
            "state_ref": "state:runs:fixture",
            "records": [
                {
                    "run_ref": "run:local-fixture",
                    "state": "paused",
                    "idempotency_ref": "idempotency:local-fixture",
                    "audit_refs": ["audit:local-fixture"],
                    "receipt_refs": ["receipt:local-fixture"],
                    "replay_refs": ["replay:local-fixture"],
                    "safe_summary": "Synthetic paused run record for offline restore verification.",
                }
            ],
        },
        "receipts": {
            "state_ref": "state:receipts:fixture",
            "records": [
                {
                    "receipt_ref": "receipt:local-fixture",
                    "run_ref": "run:local-fixture",
                    "receipt_hash": (
                        "sha256:1111111111111111111111111111111111111111111111111111111111111111"
                    ),
                    "safe_summary": "Synthetic redacted receipt record.",
                }
            ],
        },
        "approvals": {
            "state_ref": "state:approvals:fixture",
            "records": [
                {
                    "approval_ref": "approval:local-fixture",
                    "scope_ref": "scope:local-fixture",
                    "status": "revocable",
                    "safe_summary": "Synthetic exact-scope approval record.",
                }
            ],
        },
        "settings": {
            "state_ref": "state:settings:fixture",
            "records": [
                {
                    "settings_ref": "settings:local-loopback",
                    "mode": "local_loopback",
                    "safe_summary": "Synthetic loopback settings record without raw host or path.",
                }
            ],
        },
        "registry": {
            "state_ref": "state:registry:fixture",
            "records": [
                {
                    "registry_ref": "registry:capability-fixture",
                    "capability_ref": "capability:preview-only-fixture",
                    "status": "inspectable",
                    "safe_summary": "Synthetic registry entry for restore verification.",
                }
            ],
        },
        "audit_summaries": {
            "state_ref": "state:audit-summaries:fixture",
            "records": [
                {
                    "audit_ref": "audit:local-fixture",
                    "event_count": 1,
                    "safe_summary": "Synthetic audit summary with safe refs only.",
                }
            ],
        },
        "local_model_cache_refs": {
            "state_ref": "state:local-model-cache-refs:fixture",
            "records": [
                {
                    "model_cache_ref": "model-cache:approved-fixture",
                    "model_ref": "model:approved-gguf-fixture",
                    "cache_status": "referenced_only",
                    "safe_summary": "Synthetic model cache reference without raw cache location.",
                }
            ],
        },
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_fixture_state(state_dir: Path) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    for category, payload in _fixture_records().items():
        _write_json(
            state_dir / f"{category}.json",
            {
                "category": category,
                "safe_ref": payload["state_ref"],
                "records": payload["records"],
            },
        )


def _hash_bytes(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _hash_file(path: Path) -> str:
    return _hash_bytes(path.read_bytes())


def _copy_state_files(source_dir: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for category in MINIMUM_STATE_CATEGORIES:
        target = target_dir / f"{category}.json"
        target.write_bytes((source_dir / f"{category}.json").read_bytes())


def _manifest_for_directory(state_dir: Path) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for category in MINIMUM_STATE_CATEGORIES:
        source = state_dir / f"{category}.json"
        payload = json.loads(source.read_text(encoding="utf-8"))
        items.append(
            {
                "category": category,
                "state_ref": payload["safe_ref"],
                "backup_item_ref": f"backup-item:{category}",
                "hash_algorithm": "sha256",
                "hash_value": _hash_file(source),
                "record_count": len(payload["records"]),
                "safe_summary": f"{category} included in the synthetic minimum backup set.",
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "task_ref": TASK_REF,
        "backup_ref": "backup:offline-restore-fixture",
        "restore_ref": "restore:offline-restore-fixture",
        "minimum_state_categories": list(MINIMUM_STATE_CATEGORIES),
        "items": items,
        "backup_integrity_status": "pass",
        "offline_restore_status": "not_run",
        "corruption_detection_status": "not_run",
        "live_restore_supported": False,
        "live_restore_status": "not_scoped",
        "report_safety": REPORT_SAFETY,
        "rollback_ref": "rollback:backup-restore-verifier",
        "safe_summary": (
            "Synthetic backup minimum set is hash-verified before offline restore."
        ),
        "failure_guidance": [],
    }


def _validate_directory_against_manifest(
    state_dir: Path,
    manifest: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    item_by_category = {
        item["category"]: item
        for item in manifest.get("items", [])
        if isinstance(item, dict) and isinstance(item.get("category"), str)
    }
    for category in MINIMUM_STATE_CATEGORIES:
        expected = item_by_category.get(category)
        if expected is None:
            failures.append(f"missing manifest item for category:{category}")
            continue
        state_file = state_dir / f"{category}.json"
        if not state_file.exists():
            failures.append(f"missing restored category:{category}")
            continue
        if _hash_file(state_file) != expected.get("hash_value"):
            failures.append(f"integrity mismatch for category:{category}")
            continue
        payload = json.loads(state_file.read_text(encoding="utf-8"))
        if payload.get("category") != category:
            failures.append(f"category label mismatch for category:{category}")
        if not str(payload.get("safe_ref", "")).startswith("state:"):
            failures.append(f"unsafe state ref for category:{category}")
        records = payload.get("records")
        if not isinstance(records, list) or not records:
            failures.append(f"empty restored records for category:{category}")
    return failures


def _scan_output_safety(payload: dict[str, Any]) -> list[str]:
    text = json.dumps(payload, sort_keys=True).lower()
    return [
        f"forbidden output fragment detected: {fragment}"
        for fragment in FORBIDDEN_OUTPUT_FRAGMENTS
        if fragment in text
    ]


def _verify_corruption_detection(backup_dir: Path, manifest: dict[str, Any]) -> bool:
    corrupted_dir = backup_dir.parent / "corrupted_restore"
    _copy_state_files(backup_dir, corrupted_dir)
    corrupted_file = corrupted_dir / "runs.json"
    payload = json.loads(corrupted_file.read_text(encoding="utf-8"))
    payload["records"][0]["safe_summary"] = "Synthetic corruption probe."
    _write_json(corrupted_file, payload)
    return bool(_validate_directory_against_manifest(corrupted_dir, manifest))


def build_backup_restore_report() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="uaa-backup-restore-") as tmp:
        workspace = Path(tmp)
        source_dir = workspace / "source_state"
        backup_dir = workspace / "backup_state"
        restore_dir = workspace / "restored_state"
        _write_fixture_state(source_dir)
        manifest = _manifest_for_directory(source_dir)
        _copy_state_files(source_dir, backup_dir)
        backup_failures = _validate_directory_against_manifest(backup_dir, manifest)
        _copy_state_files(backup_dir, restore_dir)
        restore_failures = _validate_directory_against_manifest(restore_dir, manifest)
        corruption_detected = _verify_corruption_detection(backup_dir, manifest)

    failures = [*backup_failures, *restore_failures]
    if not corruption_detected:
        failures.append("corruption probe was not detected")

    report = {
        **manifest,
        "overall_status": "pass" if not failures else "fail",
        "backup_integrity_status": "pass" if not backup_failures else "fail",
        "offline_restore_status": "pass" if not restore_failures else "fail",
        "corruption_detection_status": "pass" if corruption_detected else "fail",
        "failure_guidance": [
            "Re-run the backup verifier and inspect category safe refs; do not perform live restore."
        ]
        if failures
        else [],
        "validation_failures": failures,
    }
    safety_failures = _scan_output_safety(report)
    if safety_failures:
        report["overall_status"] = "fail"
        report["validation_failures"] = [*report["validation_failures"], *safety_failures]
    return report


def validate_backup_restore_verification() -> list[str]:
    report = build_backup_restore_report()
    failures = list(report.get("validation_failures", []))
    categories = set(report.get("minimum_state_categories", []))
    if categories != set(MINIMUM_STATE_CATEGORIES):
        failures.append("backup minimum set categories are incomplete")
    if report.get("live_restore_supported") is not False:
        failures.append("live restore must remain unclaimed")
    if report.get("live_restore_status") != "not_scoped":
        failures.append("live restore status must be not_scoped")
    safety = report.get("report_safety")
    if safety != REPORT_SAFETY:
        failures.append("report safety flags drifted")
    if _scan_output_safety(report):
        failures.append("backup restore report contains forbidden raw/private output")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable summary")
    args = parser.parse_args(argv)
    report = build_backup_restore_report()
    failures = validate_backup_restore_verification()
    if args.json:
        print(json.dumps({**report, "validation_failures": failures}, indent=2, sort_keys=True))
    elif failures:
        for failure in failures:
            print(f"FAIL: {failure}")
    else:
        print("OK: Backup integrity and offline restore verification passed with safe refs only")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
