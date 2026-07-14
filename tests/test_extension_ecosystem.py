import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.capability_availability.read_model import (
    build_capability_availability_read_model,
)
from ultimate_ai_agent.core.extension_catalog import (
    ExtensionHashStatus,
    ExtensionInstallDisabledRecordIssueRequest,
    build_default_inspectable_extension_catalog,
    validate_inspectable_extension_catalog,
)
from ultimate_ai_agent.core.extension_catalog.ecosystem import (
    ExtensionDeveloperValidationResult,
    ExtensionEcosystemReadModel,
    build_default_extension_ecosystem_read_model,
    validate_extension_catalog_entry_for_development,
)
from ultimate_ai_agent.core.extension_catalog import runtime as extension_runtime


def test_extension_ecosystem_projects_every_declared_capability_fail_closed() -> None:
    ecosystem = build_default_extension_ecosystem_read_model()
    expected_count = sum(
        len(entry.declared_capabilities) for entry in ecosystem.entries
    )

    assert ecosystem.availability_snapshot_count == expected_count == 4
    assert ecosystem.schema_version == "uaa_extension_ecosystem_read_model.v1"
    assert ecosystem.developer_validation_count == len(ecosystem.entries) == 3
    assert ecosystem.catalog_visibility_grants_authority is False
    assert ecosystem.activation_metadata_grants_authority is False
    assert ecosystem.request_scoped_invocation_decision_required is True
    assert [item.status for item in ecosystem.developer_validation_results] == [
        "validated_metadata_only",
        "validated_metadata_only",
        "blocked",
    ]
    for item in ecosystem.developer_validation_results:
        assert item.configuration_status == "not_configured"
        assert item.health_status == "unknown"
        assert item.authority_posture == "blocked"
        assert item.resource_status == "unknown"
        assert item.safe_disable_status == "unknown"
        assert item.signature_verified is False
        assert item.runtime_import_enabled is False
        assert item.execution_enabled is False


def test_capability_availability_contains_all_extension_snapshots() -> None:
    ecosystem = build_default_extension_ecosystem_read_model()
    availability = build_capability_availability_read_model()
    by_ref = {item.snapshot_ref: item for item in availability.snapshots}

    assert set(ecosystem.availability_snapshot_refs).issubset(by_ref)
    for snapshot_ref in ecosystem.availability_snapshot_refs:
        snapshot = by_ref[snapshot_ref]
        entry = next(
            item
            for item in ecosystem.entries
            if item.catalog_entry_ref == snapshot.source_ref
        )
        validation = next(
            item
            for item in ecosystem.developer_validation_results
            if item.catalog_entry_ref == entry.catalog_entry_ref
        )
        assert snapshot.compatibility_status.value == validation.compatibility_status
        assert snapshot.authority_posture.value == "blocked"
        assert snapshot.configuration_status.value == "not_configured"
        assert snapshot.health_status.value == "unknown"
        assert snapshot.resource_status.value == "unknown"
        assert snapshot.cost_posture.value == "unknown"
        assert snapshot.safe_disable_status.value == "unknown"
        assert snapshot.freshness_status.value == "current"
        assert snapshot.declared_or_observed_version_ref == validation.version_ref
        assert validation.validation_ref in snapshot.evidence_refs
        assert set(validation.blocker_codes).issubset(snapshot.blocker_codes)
        assert "EXTENSION_CATALOG_ENTRY_NOT_CALLABLE" in snapshot.blocker_codes


def test_reviewed_hash_mismatch_remains_inspectable_and_blocked() -> None:
    catalog = build_default_inspectable_extension_catalog()
    entry = catalog.entries[0]
    mismatched_hash = entry.file_hashes[0].model_copy(
        update={"hash_status": ExtensionHashStatus.mismatch}
    )
    changed = entry.model_copy(
        update={"file_hashes": [mismatched_hash, *entry.file_hashes[1:]]}
    )

    changed_catalog = catalog.model_copy(
        update={"entries": [changed, *catalog.entries[1:]]}
    )
    validate_inspectable_extension_catalog(changed_catalog)
    result = validate_extension_catalog_entry_for_development(changed)
    assert result.status == "blocked"
    assert result.compatibility_status == "unknown"
    assert result.hashes_verified_against_pinned_values is False
    assert "EXTENSION_PINNED_HASH_VALIDATION_FAILED" in result.blocker_codes


@pytest.mark.parametrize(
    "change",
    [
        {"manifest_ref": "plugin-skill-manifest:wrong"},
        {"version_ref": "version:known-but-unsupported"},
        {"source_ref": "source:wrong"},
        {"review_ref": "review:wrong"},
        {"publisher_ref": "publisher:other"},
        {"license_ref": "license:other"},
        {"risk_class": "high"},
        {"capability_ref": "capability:substituted"},
        {"grant_ref": "grant-request:substituted"},
        {"catalog_entry_ref": "inspectable-catalog-entry:substituted"},
        {"safe_disable_ref": "safe-disable-ref:substituted"},
        {"rollback_ref": "rollback-ref:substituted"},
        {"remove_file": True},
    ],
)
def test_developer_validation_requires_exact_pinned_identity(
    change: dict[str, object],
) -> None:
    entry = build_default_inspectable_extension_catalog().entries[0]
    if "manifest_ref" in change:
        entry = entry.model_copy(update={"manifest_ref": change["manifest_ref"]})
    if "version_ref" in change:
        entry = entry.model_copy(
            update={
                "package_identity": entry.package_identity.model_copy(
                    update={"version_ref": change["version_ref"]}
                )
            }
        )
    if "source_ref" in change or "review_ref" in change:
        entry = entry.model_copy(
            update={
                "provenance": entry.provenance.model_copy(
                    update={key: value for key, value in change.items()}
                )
            }
        )
    if "publisher_ref" in change:
        entry = entry.model_copy(
            update={
                "package_identity": entry.package_identity.model_copy(
                    update={"publisher_ref": change["publisher_ref"]}
                )
            }
        )
    if "license_ref" in change:
        entry = entry.model_copy(
            update={
                "provenance": entry.provenance.model_copy(
                    update={"license_ref": change["license_ref"]}
                )
            }
        )
    if "risk_class" in change:
        entry = entry.model_copy(update={"risk_class": change["risk_class"]})
    if "capability_ref" in change:
        entry = entry.model_copy(
            update={
                "declared_capabilities": [
                    entry.declared_capabilities[0].model_copy(
                        update={"capability_ref": change["capability_ref"]}
                    )
                ]
            }
        )
    if "grant_ref" in change:
        entry = entry.model_copy(
            update={
                "requested_grants": [
                    entry.requested_grants[0].model_copy(
                        update={"grant_ref": change["grant_ref"]}
                    )
                ]
            }
        )
    if "catalog_entry_ref" in change:
        entry = entry.model_copy(
            update={"catalog_entry_ref": change["catalog_entry_ref"]}
        )
    if "safe_disable_ref" in change:
        entry = entry.model_copy(
            update={"safe_disable_ref": change["safe_disable_ref"]}
        )
    if "rollback_ref" in change:
        entry = entry.model_copy(update={"rollback_ref": change["rollback_ref"]})
    if change.get("remove_file"):
        entry = entry.model_copy(update={"file_hashes": entry.file_hashes[:-1]})

    result = validate_extension_catalog_entry_for_development(entry)
    assert result.status == "blocked"
    assert result.compatibility_status == "unknown"
    assert result.blocker_codes


def test_ecosystem_rejects_same_count_substitution_and_duplicate_refs() -> None:
    ecosystem = build_default_extension_ecosystem_read_model()
    payload = ecosystem.model_dump(mode="json")
    with pytest.raises(
        ValueError,
        match="EXTENSION_ECOSYSTEM_AVAILABILITY_BINDING_DRIFT",
    ):
        ExtensionEcosystemReadModel.model_validate(
            payload
            | {
                "availability_snapshot_refs": [payload["availability_snapshot_refs"][0]]
                * payload["availability_snapshot_count"]
            }
        )
    rebound = dict(payload["developer_validation_results"][0])
    rebound["catalog_entry_ref"] = "inspectable-catalog-entry:substituted"
    with pytest.raises(
        ValueError,
        match="EXTENSION_ECOSYSTEM_VALIDATION_BINDING_DRIFT",
    ):
        ExtensionEcosystemReadModel.model_validate(
            payload
            | {
                "developer_validation_results": [
                    rebound,
                    *payload["developer_validation_results"][1:],
                ]
            }
        )


def test_developer_validation_result_rejects_contradictory_truth() -> None:
    result = (
        build_default_extension_ecosystem_read_model().developer_validation_results[0]
    )
    payload = result.model_dump(mode="json")
    with pytest.raises(
        ValueError,
        match="EXTENSION_DEVELOPER_VALIDATED_BLOCKERS_DENIED",
    ):
        ExtensionDeveloperValidationResult.model_validate(
            payload | {"blocker_codes": ["EXTENSION_UNEXPECTED_BLOCKER"]}
        )
    with pytest.raises(
        ValueError,
        match="EXTENSION_DEVELOPER_BLOCKED_COMPATIBILITY_INVALID",
    ):
        ExtensionDeveloperValidationResult.model_validate(
            payload
            | {
                "status": "blocked",
                "blocker_codes": ["EXTENSION_VERSION_COMPATIBILITY_UNKNOWN"],
            }
        )


def test_duplicate_extension_identity_is_rejected() -> None:
    catalog = build_default_inspectable_extension_catalog()
    duplicate = catalog.entries[1].model_copy(
        update={"catalog_entry_ref": catalog.entries[0].catalog_entry_ref}
    )
    with pytest.raises(ValueError, match="EXTENSION_CATALOG_DUPLICATE_ENTRY_REF"):
        validate_inspectable_extension_catalog(
            catalog.model_copy(update={"entries": [catalog.entries[0], duplicate]})
        )


def test_unsafe_catalog_refs_are_rejected() -> None:
    catalog = build_default_inspectable_extension_catalog()
    changed = catalog.entries[0].model_copy(
        update={"review_evidence_refs": ["/Users/private:path"]}
    )
    with pytest.raises(ValueError, match="EXTENSION_CATALOG_REVIEW_EVIDENCE"):
        validate_inspectable_extension_catalog(
            catalog.model_copy(update={"entries": [changed, *catalog.entries[1:]]})
        )

    hostname = catalog.entries[0].model_copy(
        update={"audit_refs": ["audit:private.example.com"]}
    )
    with pytest.raises(ValueError, match="EXTENSION_CATALOG_AUDIT_REF"):
        validate_inspectable_extension_catalog(
            catalog.model_copy(update={"entries": [hostname, *catalog.entries[1:]]})
        )


@pytest.mark.parametrize("substitution", ["symlink", "fifo"])
def test_catalog_hash_observation_rejects_special_file_races(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    substitution: str,
) -> None:
    rel_path = "docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md"
    path = tmp_path / rel_path
    path.parent.mkdir(parents=True)
    if substitution == "symlink":
        target = tmp_path / "target"
        target.write_text("untrusted", encoding="utf-8")
        path.symlink_to(target)
    else:
        os.mkfifo(path)
    monkeypatch.setattr(extension_runtime, "_REPO_ROOT", tmp_path)

    observed = extension_runtime._safe_file_hash(
        "file-ref:plugin-skill-ecosystem-boundary-doc",
        rel_path,
    )

    assert observed.hash_status == "mismatch"


def test_api_and_json_cli_expose_same_backend_owned_truth() -> None:
    expected = build_default_extension_ecosystem_read_model().model_dump(mode="json")
    response = TestClient(app).get("/extensions/catalog")
    assert response.status_code == 200
    assert response.json()["data"] == expected

    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "inspect-catalog",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert json.loads(completed.stdout) == expected


def test_extension_developer_cli_validates_one_entry_without_runtime_import() -> None:
    ecosystem = build_default_extension_ecosystem_read_model()
    expected = ecosystem.developer_validation_results[0]
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "validate-entry",
            expected.catalog_entry_ref,
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert "UAA extension developer validation" in completed.stdout
    assert expected.package_ref in completed.stdout
    assert "Runtime import: blocked" in completed.stdout

    json_completed = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "validate-entry",
            expected.catalog_entry_ref,
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    payload = json.loads(json_completed.stdout)
    assert payload == expected.model_dump(mode="json")
    assert payload["runtime_import_enabled"] is False
    assert payload["execution_enabled"] is False


def test_checked_in_schema_accepts_live_ecosystem_payload() -> None:
    schema = json.loads(
        Path("docs/schemas/extension_ecosystem_read_model.schema.json").read_text(
            encoding="utf-8"
        )
    )
    payload = build_default_extension_ecosystem_read_model().model_dump(mode="json")
    assert list(Draft202012Validator(schema).iter_errors(payload)) == []


def test_original_catalog_v1_still_matches_its_checked_in_schema() -> None:
    schema = json.loads(
        Path("docs/schemas/inspectable_extension_catalog.schema.json").read_text(
            encoding="utf-8"
        )
    )
    payload = build_default_inspectable_extension_catalog().model_dump(mode="json")
    assert list(Draft202012Validator(schema).iter_errors(payload)) == []


def test_openapi_does_not_advertise_client_approval_grants() -> None:
    schemas = app.openapi()["components"]["schemas"]
    for name in (
        "ExtensionInstallDisabledRecordIssueRequest",
        "ExtensionInstallDisabledRecordDeleteRequest",
    ):
        assert "approval_grants" not in schemas[name]["properties"]


def test_human_cli_makes_non_callable_boundary_primary() -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    completed = subprocess.run(
        [sys.executable, "scripts/dev/uaa_extensions.py", "inspect-catalog"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "Inspectable never means callable" in completed.stdout
    assert "compatibility=supported" in completed.stdout
    assert "manifest=plugin-skill-manifest:" in completed.stdout
    assert "version=version:" in completed.stdout
    assert "authority=blocked" in completed.stdout
    assert "provenance=reviewed" in completed.stdout
    assert "pinned-hashes=verified" in completed.stdout
    assert "signature=not_present" in completed.stdout
    assert "safe-disable=unknown" in completed.stdout
    assert "safe-disable-ref=safe-disable-ref:" in completed.stdout
    assert not completed.stdout.lstrip().startswith("{")


def test_client_supplied_extension_approval_grants_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Extra inputs are not permitted",
    ):
        ExtensionInstallDisabledRecordIssueRequest(
            approval_ref="approval:forged",
            approval_grants=[{"approval_ref": "approval:forged"}],
        )


def test_blocked_mutation_cli_emits_safe_denial_without_traceback(tmp_path) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "record-install-disabled-receipt",
            "--authority-state-dir",
            str(tmp_path),
            "--approval-ref",
            "approval-ref:extension-install-disabled:missing",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert completed.returncode == 1
    assert completed.stdout == ""
    assert (
        "EXTENSION_INSTALL_DISABLED_ATOMIC_AUTHORITY_STATE_REQUIRED" in completed.stderr
    )
    assert "Traceback" not in completed.stderr
    assert str(tmp_path) not in completed.stderr
