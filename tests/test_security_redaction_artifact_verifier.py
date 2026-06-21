from typing import Any
from pathlib import Path
import pytest
import json

import scripts.verify_security_redaction_artifacts as verifier


def _write_text(root: Any, rel_path: str, text: str) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_security_redaction_artifact_verifier_clean_scopes_pass(tmp_path: Path) -> None:
    _write_text(
        tmp_path,
        "docs/security/SECURITY_TRIAGE_RUNBOOK.md",
        "Safe summary only. No raw material is included.",
    )
    _write_text(
        tmp_path,
        "reports/performance/latest_release_latency_baseline.json",
        json.dumps({"safe_summary": "p95 status refs only", "status": "passed"}),
    )
    _write_text(
        tmp_path,
        "apps/control-center/dist/index.html",
        "<html><body>Control Center safe static shell</body></html>",
    )

    findings = verifier.validate_security_redaction_artifacts(
        root=tmp_path,
        scopes=(
            "docs/security",
            "reports/performance",
            "apps/control-center/dist",
        ),
    )

    assert findings == []


def test_security_redaction_artifact_verifier_flags_private_material_safely(tmp_path: Path) -> None:
    secret_value = "abcdefghijklmnop"
    user_fragment = "private-user-name"
    _write_text(
        tmp_path,
        "reports/foundation_gate/latest_foundation_gate_report.md",
        "\n".join(
            [
                f"raw prompt: do the private thing token={secret_value}",
                f"raw path: /Users/{user_fragment}/workspace/file.txt",
                "hostname: private-host",
                "environment dump: PATH=/private/bin",
            ]
        ),
    )

    findings = verifier.validate_security_redaction_artifacts(
        root=tmp_path,
        scopes=("reports/foundation_gate",),
    )

    categories = {finding.category for finding in findings}
    assert "raw_prompt_content" in categories
    assert "secret_like_material" in categories
    assert "raw_path_material" in categories
    assert "hostname_material" in categories
    assert "environment_dump_material" in categories
    for finding in findings:
        assert secret_value not in finding.safe_message
        assert user_fragment not in finding.safe_message
        assert finding.evidence_hash.startswith("sha256:")


def test_security_redaction_artifact_verifier_covers_frontend_build_output(tmp_path: Path) -> None:
    _write_text(
        tmp_path,
        "apps/control-center/dist/assets/index.js",
        "fetch('/api', {headers: {Authorization: Bearer abcdefghijklmnop}})",
    )

    findings = verifier.validate_security_redaction_artifacts(
        root=tmp_path,
        scopes=("apps/control-center/dist",),
    )

    assert [finding.rel_path for finding in findings] == [
        "apps/control-center/dist/assets/index.js"
    ]
    assert {finding.category for finding in findings} == {"bearer_token_material"}


def test_security_redaction_artifact_verifier_blocks_unsafe_release_claims() -> None:
    findings = verifier.scan_text(
        "docs/production/unsafe.md",
        "\n".join(
            [
                "public distribution is available",
                "public beta is ready",
                "signed installer is ready",
                "external audit completed",
                "production authority is granted",
                "the app is production-ready",
            ]
        ),
    )

    assert {finding.category for finding in findings} == {
        "public_distribution_claim",
        "public_beta_claim",
        "signed_release_claim",
        "external_audit_claim",
        "production_authority_claim",
        "production_readiness_claim",
    }


def test_security_redaction_artifact_verifier_cli_redacts_failure_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    secret_value = "qrstuvwxyz123456"
    _write_text(
        tmp_path,
        "reports/performance/latest_release_latency_baseline.md",
        f"raw response: private output token={secret_value}",
    )

    exit_code = verifier.main(
        [
            "--root",
            str(tmp_path),
            "--scope",
            "reports/performance",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "raw_response_content" in output
    assert "secret_like_material" in output
    assert secret_value not in output
    assert "private output" not in output
