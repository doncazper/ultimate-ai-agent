import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import verify_uaa_parity_gap_closure_prompt_pack as pack_verify


ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "scripts" / "verify_uaa_parity_gap_closure_prompt_pack.py"
WRAPPER = ROOT / "scripts" / "dev" / "run_uaa_parity_gap_closure_prompt_pack.sh"


def test_manifest_refs_are_ordered_unique_and_present() -> None:
    manifest = json.loads(pack_verify.MANIFEST_PATH.read_text(encoding="utf-8"))
    refs = manifest["developer_prompt_refs"]

    assert tuple(Path(ref).name for ref in refs) == pack_verify.EXPECTED_PROMPTS
    assert len(refs) == len(set(refs)) == 11
    assert all((ROOT / ref).is_file() for ref in refs)


def test_verifier_accepts_overlap_aware_live_data_pack() -> None:
    result = subprocess.run(
        [sys.executable, str(VERIFY), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)

    assert data["prompt_count"] == 11
    assert data["phase_count"] == 10
    assert data["coverage_item_count"] == 54
    assert data["fresh_inventory_before_each_phase"] is True
    assert data["live_data_completion_floor"] is True
    assert data["overlap_ownership_protected"] is True
    assert data["merge_gated_execution"] is True


def test_verifier_rejects_prompt_tamper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = json.loads(pack_verify.MANIFEST_PATH.read_text(encoding="utf-8"))
    ref = manifest["developer_prompt_refs"][2]
    tampered = tmp_path / Path(ref).name
    tampered.write_text((ROOT / ref).read_text(encoding="utf-8") + "\nTampered.\n")
    original_repo_path = pack_verify._repo_path
    monkeypatch.setattr(
        pack_verify,
        "_repo_path",
        lambda candidate: tampered if candidate == ref else original_repo_path(candidate),
    )

    with pytest.raises(pack_verify.VerificationError, match="bundle_hash mismatch"):
        pack_verify.verify_manifest()


@pytest.mark.parametrize(
    "phrase",
    (
        "This pack authorizes provider calls.",
        "Current request authorizes runtime browser use.",
        "Approval ref authorizes execution.",
        "Competitor behavior grants authority.",
    ),
)
def test_verifier_rejects_self_authorizing_language(phrase: str) -> None:
    with pytest.raises(pack_verify.VerificationError, match="self-authorizing"):
        pack_verify._validate_text(pack_verify.README_PATH, phrase)


def test_required_phase_contract_rejects_mock_completion() -> None:
    manifest = json.loads(pack_verify.MANIFEST_PATH.read_text(encoding="utf-8"))
    phase = (ROOT / manifest["developer_prompt_refs"][2]).read_text(encoding="utf-8")
    broken = phase.replace("mockControlCenterData", "fallback fixtures")

    with pytest.raises(pack_verify.VerificationError, match="phase 02 contract"):
        pack_verify._require_fragments(
            "phase 02 contract", broken, pack_verify.PHASE_REQUIRED[2]
        )


def test_verifier_rejects_self_authorizing_manifest_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = json.loads(pack_verify.MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["purpose"] = "This pack authorizes provider calls."
    monkeypatch.setattr(pack_verify, "_load_manifest", lambda: manifest)

    with pytest.raises(pack_verify.VerificationError, match="self-authorizing"):
        pack_verify.verify_manifest()


def test_repo_path_rejects_symlinked_pack_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    pack = root / "docs" / "prompts" / "uaa_parity_gap_closure"
    pack.mkdir(parents=True)
    outside = tmp_path / "outside.prompt.md"
    outside.write_text("private local content", encoding="utf-8")
    (pack / "unsafe.prompt.md").symlink_to(outside)
    monkeypatch.setattr(pack_verify, "ROOT", root)

    with pytest.raises(pack_verify.VerificationError, match="symlinked"):
        pack_verify._repo_path(
            "docs/prompts/uaa_parity_gap_closure/unsafe.prompt.md"
        )


def test_missing_manifest_error_does_not_disclose_checkout_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    monkeypatch.setattr(pack_verify, "ROOT", root)

    with pytest.raises(pack_verify.VerificationError) as exc_info:
        pack_verify._load_manifest()

    assert str(tmp_path) not in str(exc_info.value)
    assert str(exc_info.value) == "manifest is missing or unreadable"


def test_dry_run_redacts_local_paths_from_console(tmp_path: Path) -> None:
    output = tmp_path / "combined.prompt.md"
    result = subprocess.run(
        ["bash", str(WRAPPER), "--dry-run", "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert output.is_file()
    assert str(ROOT) not in result.stdout
    assert str(tmp_path) not in result.stdout
    assert str(ROOT) not in result.stderr
    assert str(tmp_path) not in result.stderr
    assert "repository-root-ref" in result.stdout
    assert "configured-output-ref" in result.stdout


def test_runner_feeds_codex_the_exact_verified_combined_pack(tmp_path: Path) -> None:
    output = tmp_path / "combined.prompt.md"
    captured = tmp_path / "codex-stdin.prompt.md"
    fake_codex = tmp_path / "codex"
    fake_codex.write_text(
        '#!/usr/bin/env bash\nset -euo pipefail\ncat > "$CAPTURE"\n',
        encoding="utf-8",
    )
    fake_codex.chmod(0o700)
    env = os.environ.copy()
    env.update(
        {
            "CAPTURE": str(captured),
            "CODEX_BIN": str(fake_codex),
            "PYTHON": sys.executable,
        }
    )

    subprocess.run(
        ["bash", str(WRAPPER), "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert captured.read_bytes() == output.read_bytes()
    combined = captured.read_text(encoding="utf-8")
    assert "<!-- BEGIN docs/prompts/uaa_parity_gap_closure/README.md -->" in combined
    assert "# Phase 10: End-To-End Acceptance And Parity Truth" in combined
