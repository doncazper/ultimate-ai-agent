import json
from pathlib import Path

import scripts.verify_backup_restore as backup_restore


def test_backup_restore_verifier_passes() -> None:
    assert backup_restore.validate_backup_restore_verification() == []


def test_backup_restore_report_covers_minimum_set_and_offline_restore() -> None:
    report = backup_restore.build_backup_restore_report()

    assert report["schema_version"] == "uaa_backup_restore_verification.v1"
    assert report["task_ref"] == "UAA-P1-045"
    assert report["overall_status"] == "pass"
    assert set(report["minimum_state_categories"]) == {
        "runs",
        "receipts",
        "approvals",
        "settings",
        "registry",
        "audit_summaries",
        "local_model_cache_refs",
    }
    assert report["backup_integrity_status"] == "pass"
    assert report["offline_restore_status"] == "pass"
    assert report["corruption_detection_status"] == "pass"
    assert report["live_restore_supported"] is False
    assert report["live_restore_status"] == "not_scoped"


def test_backup_restore_report_is_safe_ref_only() -> None:
    report = backup_restore.build_backup_restore_report()
    text = json.dumps(report, sort_keys=True).lower()

    assert "/users/" not in text
    assert "\\users\\" not in text
    assert "raw prompt:" not in text
    assert "raw response:" not in text
    assert "raw provider payload:" not in text
    assert "raw path:" not in text
    assert "raw log:" not in text
    assert "username:" not in text
    assert "hostname:" not in text
    assert "environment dump:" not in text
    assert "credential:" not in text
    assert all(value is False for value in report["report_safety"].values())


def test_backup_restore_corruption_detection_reports_mismatch(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    restore_dir = tmp_path / "restore"
    backup_restore._write_fixture_state(source_dir)
    manifest = backup_restore._manifest_for_directory(source_dir)
    backup_restore._copy_state_files(source_dir, restore_dir)

    restored_file = restore_dir / "runs.json"
    payload = json.loads(restored_file.read_text(encoding="utf-8"))
    payload["records"][0]["safe_summary"] = "Synthetic test corruption."
    backup_restore._write_json(restored_file, payload)

    failures = backup_restore._validate_directory_against_manifest(restore_dir, manifest)

    assert failures == ["integrity mismatch for category:runs"]


def test_backup_restore_script_does_not_execute_commands() -> None:
    script = backup_restore.__file__
    assert script is not None
    text = Path(script).read_text(encoding="utf-8")

    assert "import subprocess" not in text
    assert "os.system" not in text
    assert "subprocess.run" not in text
