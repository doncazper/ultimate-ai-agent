import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import verify_messenger_matrix_prompt_pack as pack_verify


ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT / "docs" / "prompts" / "messenger_matrix"
MANIFEST = PACK_DIR / "prompt_bundle_manifest.json"
VERIFY = ROOT / "scripts" / "verify_messenger_matrix_prompt_pack.py"


def test_manifest_refs_are_ordered_unique_and_present() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["version"] == "1.1.0"
    assert manifest["$schema"] == "../../schemas/prompt_bundle_manifest.schema.json"
    refs = manifest["developer_prompt_refs"]
    assert len(refs) == 13
    assert len(set(refs)) == 13
    for index, ref in enumerate(refs):
        assert not ref.startswith("/")
        assert ".." not in Path(ref).parts
        assert Path(ref).name.startswith(f"{index:02d}_")
        assert (ROOT / ref).is_file()


def test_verifier_accepts_pack_and_emits_expected_counts() -> None:
    result = subprocess.run(
        [sys.executable, str(VERIFY), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(result.stdout)

    assert report["prompt_count"] == 13
    assert report["desktop_only_count"] == 13
    assert report["no_new_authority_count"] == 4
    assert report["staged_authority_count"] == 7
    assert report["release_loop_count"] == 13
    assert report["readme_integrity_protected"] is True


def test_bundle_hash_frames_readme_design_sources_and_all_prompts() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    refs = manifest["developer_prompt_refs"]
    digest = hashlib.sha256()
    for ref in (pack_verify.README_REF, *pack_verify.DESIGN_REFS, *refs):
        digest.update(b"\n--UAA-PROMPT-PACK-FILE--\n")
        digest.update(ref.encode("utf-8"))
        digest.update(b"\n")
        digest.update((ROOT / ref).read_bytes())

    assert pack_verify.compute_bundle_hash(refs) == f"sha256:{digest.hexdigest()}"


def test_verifier_rejects_readme_tamper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tampered = tmp_path / "README.md"
    tampered.write_text(pack_verify.README_PATH.read_text() + "\nTampered.\n")
    original_repo_path = pack_verify._repo_path
    monkeypatch.setattr(pack_verify, "README_PATH", tampered)
    monkeypatch.setattr(
        pack_verify,
        "_repo_path",
        lambda ref: tampered if ref == pack_verify.README_REF else original_repo_path(ref),
    )

    with pytest.raises(pack_verify.VerificationError, match="bundle_hash mismatch"):
        pack_verify.verify_manifest()


@pytest.mark.parametrize("design_ref", pack_verify.DESIGN_REFS)
def test_verifier_rejects_canonical_design_tamper(
    design_ref: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tampered = tmp_path / Path(design_ref).name
    tampered.write_text((ROOT / design_ref).read_text() + "\nTampered.\n")
    original_repo_path = pack_verify._repo_path
    monkeypatch.setattr(
        pack_verify,
        "_repo_path",
        lambda ref: tampered if ref == design_ref else original_repo_path(ref),
    )

    with pytest.raises(pack_verify.VerificationError, match="bundle_hash mismatch"):
        pack_verify.verify_manifest()


def test_verifier_rejects_prompt_tamper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refs = json.loads(MANIFEST.read_text())["developer_prompt_refs"]
    ref = refs[5]
    tampered = tmp_path / Path(ref).name
    tampered.write_text((ROOT / ref).read_text() + "\nTampered.\n")
    original_repo_path = pack_verify._repo_path
    monkeypatch.setattr(
        pack_verify,
        "_repo_path",
        lambda candidate: tampered if candidate == ref else original_repo_path(candidate),
    )

    with pytest.raises(pack_verify.VerificationError, match="bundle_hash mismatch"):
        pack_verify.verify_manifest()


@pytest.mark.parametrize(
    "unsafe_path",
    (
        "/Users/example/private",
        "/home/example/private",
        "/tmp/private",
        "/private/tmp/private",
        "/var/folders/example/private",
        "/workspace/ultimate-ai-agent/private",
        "/workspaces/ultimate-ai-agent/private",
        "/mnt/private",
        "/Volumes/private",
        "C:\\Users\\example\\private",
    ),
)
def test_text_safety_rejects_absolute_user_paths(unsafe_path: str) -> None:
    with pytest.raises(pack_verify.VerificationError, match="absolute local user path"):
        pack_verify._validate_text_safety(pack_verify.README_PATH, unsafe_path)


def test_staged_authority_rejects_missing_fresh_evaluation() -> None:
    refs = json.loads(MANIFEST.read_text())["developer_prompt_refs"]
    ref = refs[6]
    text = (ROOT / ref).read_text().replace(
        "eligible for fresh request-scoped evaluation only",
        "eligible for execution",
    )
    with pytest.raises(pack_verify.VerificationError, match="staged authority"):
        pack_verify._validate_prompt(6, ref, text)


def test_staged_authority_rejects_missing_all_call_pre_start_evaluation() -> None:
    refs = json.loads(MANIFEST.read_text())["developer_prompt_refs"]
    ref = refs[10]
    text = (ROOT / ref).read_text().replace(
        "Immediately before every Stage B runtime call",
        "Before selected mutations",
    )
    with pytest.raises(pack_verify.VerificationError, match="pre-start authority"):
        pack_verify._validate_prompt(10, ref, text)


@pytest.mark.parametrize("index", (11, 12))
def test_hardening_and_acceptance_reject_incomplete_runtime_evaluation(index: int) -> None:
    refs = json.loads(MANIFEST.read_text())["developer_prompt_refs"]
    ref = refs[index]
    text = (ROOT / ref).read_text().replace(
        "Immediately before every runtime call",
        "Before selected repaired mutations",
    )
    with pytest.raises(pack_verify.VerificationError, match="exercised runtime authority"):
        pack_verify._validate_prompt(index, ref, text)


def test_release_loop_rejects_github_hosted_ci() -> None:
    refs = json.loads(MANIFEST.read_text())["developer_prompt_refs"]
    ref = refs[2]
    text = (ROOT / ref).read_text().replace(
        "repository-scoped self-hosted macOS CI",
        "GitHub-hosted CI",
    )
    with pytest.raises(pack_verify.VerificationError, match="release loop"):
        pack_verify._validate_prompt(2, ref, text)


def test_desktop_contract_rejects_mobile_scope() -> None:
    refs = json.loads(MANIFEST.read_text())["developer_prompt_refs"]
    ref = refs[9]
    text = (ROOT / ref).read_text().replace(
        "This milestone is desktop-only",
        "This milestone includes mobile",
    )
    with pytest.raises(pack_verify.VerificationError, match="desktop-only contract"):
        pack_verify._validate_prompt(9, ref, text)


def test_forbidden_global_authority_claim_fails_closed() -> None:
    with pytest.raises(pack_verify.VerificationError, match="forbidden claim"):
        pack_verify._validate_text_safety(
            pack_verify.README_PATH,
            "This bundle grants runtime authority.",
        )
