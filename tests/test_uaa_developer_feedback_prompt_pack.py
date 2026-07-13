import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import verify_uaa_developer_feedback_prompt_pack as pack_verify


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = pack_verify.MANIFEST_PATH
VERIFY = ROOT / "scripts" / "verify_uaa_developer_feedback_prompt_pack.py"


def test_manifest_refs_are_ordered_and_present() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    refs = manifest["developer_prompt_refs"]

    assert len(refs) == 10
    assert tuple(Path(ref).name for ref in refs) == pack_verify.EXPECTED_PROMPTS
    assert len(set(refs)) == len(refs)
    assert all((ROOT / ref).is_file() for ref in refs)


def test_verifier_accepts_hardened_pack() -> None:
    result = subprocess.run(
        [sys.executable, str(VERIFY), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)

    assert data["prompt_count"] == 10
    assert data["phase_count"] == 9
    assert data["self_authorizing_phrases_rejected"] is True
    assert data["content_disclosure_gated"] is True
    assert data["merge_gated_release_loop"] is True


def test_verifier_rejects_prompt_tamper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ref = manifest["developer_prompt_refs"][1]
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


def test_verifier_rejects_readme_tamper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tampered = tmp_path / "README.md"
    tampered.write_text(
        pack_verify.README_PATH.read_text(encoding="utf-8") + "\nTampered.\n"
    )
    original_repo_path = pack_verify._repo_path
    monkeypatch.setattr(
        pack_verify,
        "_repo_path",
        lambda candidate: tampered
        if candidate == pack_verify.README_REF
        else original_repo_path(candidate),
    )

    with pytest.raises(pack_verify.VerificationError, match="bundle_hash mismatch"):
        pack_verify.verify_manifest()


def test_verifier_rejects_implementation_plan_tamper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ref = pack_verify.IMPLEMENTATION_PLAN_REF
    tampered = tmp_path / "UAA_DEVELOPER_FEEDBACK_IMPLEMENTATION_PLAN.md"
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
        "Current operator request authorizes",
        "Operator request authorizes the post-quit lane",
        "Privacy review is unnecessary",
    ),
)
def test_self_authorizing_language_is_rejected(phrase: str) -> None:
    with pytest.raises(pack_verify.VerificationError, match="self-authorizing"):
        pack_verify._validate_text(pack_verify.README_PATH, phrase)


def test_missing_disclosure_gate_is_rejected() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    phase = (ROOT / manifest["developer_prompt_refs"][7]).read_text(encoding="utf-8")
    broken = phase.replace("Approval refs alone never authorize", "Approval refs are recorded")

    with pytest.raises(pack_verify.VerificationError, match="phase 07 authority"):
        pack_verify._require_fragments(
            "phase 07 authority contract",
            broken,
            pack_verify.DISCLOSURE_PHASE_FRAGMENTS[7],
        )


def test_missing_release_gate_is_rejected() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    wrapper = (ROOT / manifest["developer_prompt_refs"][0]).read_text(encoding="utf-8")
    broken = wrapper.replace(
        "repository-scoped self-hosted macOS CI only",
        "available CI",
    )

    with pytest.raises(pack_verify.VerificationError, match="finite release loop"):
        pack_verify._require_fragments(
            "finite release loop",
            broken,
            pack_verify.WRAPPER_RELEASE_FRAGMENTS,
        )


@pytest.mark.parametrize(
    "unsafe_path",
    (
        "/Users/example/private",
        "/home/example/private",
        "/workspace/ultimate-ai-agent/private",
        "/tmp/feedback-artifact",
        "/var/folders/example/private",
        "C:\\Users\\example\\private",
    ),
)
def test_absolute_local_paths_are_rejected(unsafe_path: str) -> None:
    with pytest.raises(pack_verify.VerificationError, match="absolute local path"):
        pack_verify._validate_text(pack_verify.README_PATH, unsafe_path)
