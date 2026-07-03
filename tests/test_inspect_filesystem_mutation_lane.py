from __future__ import annotations

import json

from scripts.inspect_filesystem_mutation_lane import (
    build_filesystem_mutation_lane_report,
)


def test_filesystem_mutation_lane_inspection_uses_safe_refs_only() -> None:
    report = build_filesystem_mutation_lane_report()

    assert report["schema_version"] == "filesystem_mutation_lane_inspection.v1"
    assert report["status"] == "core_exact_temp_workspace_verified"
    assert report["workspace_scope"] == "temporary_workspace_only"
    assert report["proposal"]["allowed"] is True
    assert report["apply"]["allowed"] is True
    assert report["apply"]["mutation_performed"] is True
    assert report["rollback"]["rollback_performed"] is True
    assert report["restored_to_preimage"] is True
    assert report["replay_guard"]["duplicate_apply_allowed"] is False
    assert "PATCH_IDEMPOTENCY_REPLAY_BLOCKED" in report["replay_guard"][
        "duplicate_apply_reason_codes"
    ]

    serialized = json.dumps(report, sort_keys=True)
    for forbidden in [
        "previous-private-text",
        "updated-private-text",
        "artifact.txt",
        "/tmp",
        "/var/",
        "/Users/",
        "uaa-filesystem-lane-",
    ]:
        assert forbidden not in serialized


def test_filesystem_mutation_lane_keeps_broad_authority_blocked() -> None:
    report = build_filesystem_mutation_lane_report()

    for flag in [
        "control_center_apply_route_enabled",
        "backend_apply_route_enabled",
        "broad_filesystem_authority_enabled",
        "home_directory_write_enabled",
        "delete_export_enabled",
        "shell_subprocess_execution_enabled",
        "unreviewed_generated_changes_enabled",
        "raw_content_persisted",
        "raw_path_persisted",
    ]:
        assert report[flag] is False
    assert report["apply"]["raw_content_stored"] is False
    assert report["apply"]["raw_path_stored"] is False
    assert report["rollback"]["raw_content_stored"] is False
    assert report["rollback"]["raw_path_stored"] is False
