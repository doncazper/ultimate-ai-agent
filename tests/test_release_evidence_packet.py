import json
from pathlib import Path

import scripts.verify_release_evidence_packet as release_packet


ROOT = Path(__file__).resolve().parents[1]


def test_release_evidence_packet_verifier_passes():
    assert release_packet.validate_release_evidence_packet() == []


def test_release_evidence_packet_schema_and_template_cover_required_fields():
    schema = json.loads(
        (ROOT / "docs/schemas/release_evidence_packet.schema.json").read_text(
            encoding="utf-8"
        )
    )
    template = json.loads(
        (ROOT / "docs/production/RELEASE_EVIDENCE_PACKET_TEMPLATE.json").read_text(
            encoding="utf-8"
        )
    )

    assert schema["properties"]["schema_version"]["const"] == "uaa_release_evidence_packet.v1"
    assert schema["properties"]["task_ref"]["const"] == "UAA-P1-044"
    assert template["schema_version"] == "uaa_release_evidence_packet.v1"
    assert template["task_ref"] == "UAA-P1-044"
    assert set(template["status_semantics"]) == {
        "pass",
        "fail",
        "skipped",
        "blocked",
        "accepted_failure",
    }
    assert {lane["lane_id"] for lane in template["verification_lanes"]} == {
        "docs",
        "openapi",
        "api-safety",
        "security-redaction",
        "local-model-e2e",
        "durability",
        "frontend",
        "performance",
    }
    assert "accepted_failures" in template
    assert "artifact_hashes" in template
    assert "release_blockers" in template

    durability = next(
        lane for lane in template["verification_lanes"] if lane["lane_id"] == "durability"
    )
    assert "command:backup-restore.verify" in durability["command_refs"]
    assert "report:backup-restore:pending" in durability["report_refs"]


def test_release_evidence_packet_safety_flags_are_false():
    template = json.loads(
        (ROOT / "docs/production/RELEASE_EVIDENCE_PACKET_TEMPLATE.json").read_text(
            encoding="utf-8"
        )
    )

    assert template["packet_safety"] == {
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


def test_release_evidence_packet_script_does_not_execute_commands():
    script = release_packet.__file__
    assert script is not None
    text = Path(script).read_text(encoding="utf-8")

    assert "import subprocess" not in text
    assert "os.system" not in text
    assert "subprocess.run" not in text
