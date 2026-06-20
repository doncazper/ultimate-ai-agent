import json

import scripts.verify_release_lanes as release_lanes


def test_release_lanes_cover_required_categories():
    manifest = release_lanes.build_release_lane_manifest()

    assert manifest["schema_version"] == "uaa_release_verification_lanes.v1"
    assert manifest["task_ref"] == "UAA-P1-013"
    assert manifest["overall_status"] == "definition_pass"
    assert manifest["definition_status"] == "pass"
    assert manifest["command_execution_status"] == "not_executed"
    assert {lane["lane_id"] for lane in manifest["lanes"]} == {
        "docs",
        "openapi",
        "api-safety",
        "security-redaction",
        "local-model-e2e",
        "durability",
        "frontend",
        "visual-regression",
        "desktop-packaging",
        "performance",
    }
    assert manifest["accepted_failures"] == []


def test_release_lanes_define_status_semantics_and_commands():
    manifest = release_lanes.build_release_lane_manifest()

    assert set(manifest["status_semantics"]) == {
        "pass",
        "fail",
        "skipped",
        "blocked",
        "accepted_failure",
    }
    for lane in manifest["lanes"]:
        assert lane["commands"]
        assert lane["skipped_policy"]
        assert lane["blocked_policy"]
        assert lane["accepted_failure_policy"]
        for command in lane["commands"]:
            assert command["command_ref"].startswith("command:")
            assert command["display"]
            assert "/Users/" not in command["display"]
            assert command["argv"][0] in {".venv/bin/python", "make"}


def test_durability_lane_includes_backup_restore_verification():
    manifest = release_lanes.build_release_lane_manifest()
    durability = next(lane for lane in manifest["lanes"] if lane["lane_id"] == "durability")

    command_refs = {command["command_ref"] for command in durability["commands"]}

    assert "command:backup-restore.verify" in command_refs
    assert "docs/production/BACKUP_RESTORE_VERIFICATION.md" in durability["evidence_refs"]


def test_openapi_lane_includes_route_module_ownership_guard():
    manifest = release_lanes.build_release_lane_manifest()
    openapi = next(lane for lane in manifest["lanes"] if lane["lane_id"] == "openapi")

    command_refs = {command["command_ref"] for command in openapi["commands"]}

    assert "command:openapi.contract" in command_refs
    assert "command:api.manifest.tests" in command_refs
    assert "command:route-module.ownership" in command_refs
    assert "docs/api/UAA_P1_021_FASTAPI_ROUTE_GROUPING_MAP.md" in openapi["evidence_refs"]
    assert "docs/api/UAA_P1_052_SERVICE_MODULE_EXTRACTION_PLAN.md" in openapi["evidence_refs"]


def test_release_lane_manifest_is_report_safe():
    manifest = release_lanes.build_release_lane_manifest()

    safety = manifest["report_safety"]
    assert safety["raw_prompt_included"] is False
    assert safety["raw_response_included"] is False
    assert safety["raw_provider_payload_included"] is False
    assert safety["raw_path_included"] is False
    assert safety["raw_log_included"] is False
    assert safety["username_included"] is False
    assert safety["hostname_included"] is False
    assert safety["environment_dump_included"] is False
    assert safety["credential_material_included"] is False


def test_release_lane_script_emits_parseable_json(capsys):
    exit_code = release_lanes.main(["--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["overall_status"] == "definition_pass"
    assert payload["definition_status"] == "pass"
    assert payload["command_execution_status"] == "not_executed"
    assert payload["lane_count"] == 10


def test_release_lane_script_does_not_add_command_execution_imports():
    source = release_lanes.__file__
    assert source is not None
    with open(source, encoding="utf-8") as handle:
        text = handle.read()

    assert "import subprocess" not in text
    assert "os.system" not in text
    assert "subprocess.run" not in text
