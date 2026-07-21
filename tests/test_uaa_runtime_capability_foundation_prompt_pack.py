import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import verify_uaa_runtime_capability_foundation_prompt_pack as pack_verify

ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT / "docs" / "prompts" / "uaa_runtime_capability_foundation"
MANIFEST = PACK_DIR / "prompt_bundle_manifest.json"
MODULE_MANIFEST = PACK_DIR / "prompt_module_manifest.json"
MODULE_GOLDEN_RECEIPT = PACK_DIR / "prompt_module_golden_receipt.json"
VERIFY = ROOT / "scripts" / "verify_uaa_runtime_capability_foundation_prompt_pack.py"
WRAPPER = (
    ROOT / "scripts" / "dev" / "run_uaa_runtime_capability_foundation_prompt_pack.sh"
)


def test_manifest_refs_are_ordered_and_present() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["version"] == "1.2.0"
    assert (
        manifest["prompt_module_manifest_ref"]
        == "docs/prompts/uaa_runtime_capability_foundation/prompt_module_manifest.json"
    )
    refs = manifest["developer_prompt_refs"]
    assert len(refs) == 10
    assert refs[0].endswith(
        "00_execute_uaa_runtime_capability_foundation_end_to_end.prompt.md"
    )
    assert len(set(refs)) == len(refs)

    for index, ref in enumerate(refs):
        assert not ref.startswith("/")
        assert ".." not in Path(ref).parts
        if index > 0:
            assert Path(ref).name.startswith(f"0{index}_")
        assert (ROOT / ref).is_file()


def test_verifier_accepts_pack() -> None:
    result = subprocess.run(
        [sys.executable, str(VERIFY), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert data["bundle_id"] == "uaa-runtime-capability-foundation-001"
    assert data["version"] == "1.2.0"
    assert data["prompt_count"] == 10
    assert data["component_count"] == 16
    assert data["weakness_count"] == 19
    assert data["authority_milestone_count"] == 6
    assert data["finite_phase_count"] == 10
    assert data["repair_pass_limit"] == 2
    assert data["benchmark_scenario_count"] == 12
    assert data["readme_integrity_protected"] is True
    assert data["prompt_module_count"] == 11
    assert data["dependency_graph_hash"].startswith("sha256:")
    assert data["compiled_artifact_hash"].startswith("sha256:")
    assert data["golden_receipt_verified"] is True
    assert data["combined_output_written"] is False
    assert data["bundle_hash"].startswith("sha256:")


def test_verifier_redacts_combined_output_path(tmp_path: Path) -> None:
    output = tmp_path / "operator-private" / "combined.md"
    result = subprocess.run(
        [
            sys.executable,
            str(VERIFY),
            "--emit-combined",
            str(output),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    data = json.loads(result.stdout)
    assert data["combined_output_written"] is True
    assert str(output) not in result.stdout
    assert output.is_file()


def test_bundle_hash_protects_readme_and_all_prompts() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    refs = manifest["developer_prompt_refs"]
    digest = hashlib.sha256()
    for ref in (pack_verify.README_REF, *refs):
        digest.update(b"\n--UAA-PROMPT-PACK-FILE--\n")
        digest.update(ref.encode("utf-8"))
        digest.update(b"\n")
        digest.update((ROOT / ref).read_bytes())

    assert pack_verify.compute_bundle_hash(refs) == f"sha256:{digest.hexdigest()}"


def test_verifier_rejects_readme_tamper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tampered = tmp_path / "README.md"
    tampered.write_text(
        pack_verify.README_PATH.read_text(encoding="utf-8") + "\nTampered.\n"
    )
    original_repo_path = pack_verify._repo_path

    monkeypatch.setattr(pack_verify, "README_PATH", tampered)
    monkeypatch.setattr(
        pack_verify,
        "_repo_path",
        lambda ref: (
            tampered if ref == pack_verify.README_REF else original_repo_path(ref)
        ),
    )
    with pytest.raises(pack_verify.VerificationError, match="bundle_hash mismatch"):
        pack_verify.verify_manifest()


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
        lambda candidate: (
            tampered if candidate == ref else original_repo_path(candidate)
        ),
    )
    with pytest.raises(pack_verify.VerificationError, match="bundle_hash mismatch"):
        pack_verify.verify_manifest()


def test_prompt_module_manifest_and_golden_receipt_are_deterministic() -> None:
    artifact = pack_verify._verify_module_compilation()
    manifest = json.loads(MODULE_MANIFEST.read_text(encoding="utf-8"))
    golden = json.loads(MODULE_GOLDEN_RECEIPT.read_text(encoding="utf-8"))

    assert manifest["entry_module_ids"] == ["phase-09"]
    assert artifact.receipt.model_dump(mode="json") == golden
    assert artifact.receipt.ordered_module_ids == (
        "pack-readme",
        "orchestrator",
        "phase-01",
        "phase-02",
        "phase-03",
        "phase-04",
        "phase-05",
        "phase-06",
        "phase-07",
        "phase-08",
        "phase-09",
    )
    legacy_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert [item.source_ref for item in artifact.receipt.source_receipts] == [
        pack_verify.README_REF,
        *legacy_manifest["developer_prompt_refs"],
    ]
    assert artifact.receipt.runtime_model_calls is False
    assert artifact.receipt.automatic_skill_loading is False
    assert artifact.receipt.automatic_pr_creation is False


def test_verifier_rejects_prompt_module_golden_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = json.loads(MODULE_GOLDEN_RECEIPT.read_text(encoding="utf-8"))
    payload["compiled_artifact_hash"] = f"sha256:{'0' * 64}"
    drifted = tmp_path / "drifted-receipt.json"
    drifted.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(pack_verify, "MODULE_GOLDEN_RECEIPT_PATH", drifted)

    with pytest.raises(pack_verify.VerificationError, match="golden receipt"):
        pack_verify._verify_module_compilation()


@pytest.mark.parametrize(
    "unsafe_path",
    ("/Users/example/private", "/home/example/private", "C:\\Users\\example\\private"),
)
def test_prompt_safety_rejects_user_paths(unsafe_path: str) -> None:
    with pytest.raises(pack_verify.VerificationError, match="absolute local user path"):
        pack_verify._validate_text_safety(pack_verify.README_PATH, unsafe_path)


@pytest.mark.parametrize(
    "stale_phrase",
    (
        "stop after Phase 01",
        "Do not add live web fetch",
        "recommended next exact prompt",
        "generate unblock prompts",
        "authorized=true",
        "callable=true",
    ),
)
def test_finite_contract_rejects_stale_or_global_authority_phrases(
    stale_phrase: str,
) -> None:
    wrapper = (ROOT / pack_verify.WRAPPER_PROMPT).read_text(encoding="utf-8")
    readme = pack_verify.README_PATH.read_text(encoding="utf-8")

    with pytest.raises(pack_verify.VerificationError, match="stale or unsafe"):
        pack_verify._validate_finite_contract(
            readme,
            wrapper,
            f"{readme}\n{wrapper}\n{stale_phrase}",
        )


def test_finite_contract_rejects_missing_phase_heading() -> None:
    wrapper = (ROOT / pack_verify.WRAPPER_PROMPT).read_text(encoding="utf-8")
    readme = pack_verify.README_PATH.read_text(encoding="utf-8")
    broken = wrapper.replace("### Phase 09 \u2014", "### Final Phase \u2014", 1)

    with pytest.raises(pack_verify.VerificationError, match="exactly 00-09"):
        pack_verify._validate_finite_contract(readme, broken, f"{readme}\n{broken}")


def test_web_contract_requires_final_start_revalidation() -> None:
    readme = pack_verify.README_PATH.read_text(encoding="utf-8")
    phase_five = (
        ROOT / json.loads(MANIFEST.read_text())["developer_prompt_refs"][5]
    ).read_text(encoding="utf-8")
    broken = phase_five.replace(
        "inside the final locked transport-start boundary", "before use"
    )

    with pytest.raises(pack_verify.VerificationError, match="WEB-HYBRID"):
        pack_verify._validate_web_contract(readme, broken)


def test_phase_contract_rejects_semantic_mismatch() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    refs = manifest["developer_prompt_refs"]
    prompt_texts = {ref: (ROOT / ref).read_text(encoding="utf-8") for ref in refs}
    prompt_texts[refs[3]] = prompt_texts[refs[3]].replace(
        "corrections win deterministically",
        "corrections are considered",
    )

    with pytest.raises(pack_verify.VerificationError, match="Phase 03 semantic"):
        pack_verify._validate_phase_contracts(refs, prompt_texts)


def test_finite_contract_rejects_stale_readme_phase_map() -> None:
    wrapper = (ROOT / pack_verify.WRAPPER_PROMPT).read_text(encoding="utf-8")
    readme = pack_verify.README_PATH.read_text(encoding="utf-8").replace(
        "| 05 Web/provider observability |",
        "| 05 Memory/learning/context |",
    )
    with pytest.raises(pack_verify.VerificationError, match="README phase map"):
        pack_verify._validate_finite_contract(readme, wrapper, f"{readme}\n{wrapper}")


def test_wrapper_dry_run_emits_combined_prompt(tmp_path: Path) -> None:
    output = tmp_path / "combined.md"
    result = subprocess.run(
        ["bash", str(WRAPPER), "--dry-run", "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHON": sys.executable},
    )

    assert "Dry run complete" in result.stdout


def test_wrapper_without_codex_emits_manual_review_artifact(tmp_path: Path) -> None:
    output = tmp_path / "combined.md"

    result = subprocess.run(
        ["bash", str(WRAPPER), "--output", str(output)],
        check=False,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PYTHON": sys.executable,
            "CODEX_BIN": str(tmp_path / "missing-codex"),
        },
    )

    assert result.returncode == 127
    assert output.read_text(encoding="utf-8").startswith(
        "# Compiled UAA Prompt Module Bundle"
    )
    assert "validated combined prompt is available" in result.stderr
    text = output.read_text(encoding="utf-8")
    assert "Compiled UAA Prompt Module Bundle" in text
    assert "00_execute_uaa_runtime_capability_foundation_end_to_end.prompt.md" in text
    assert "W19 extension/plugin callable graduation" in text
    assert "M6 Extension/Plugin Callable Promotion" in text
    assert "exactly ten merge-gated phases" in text
    assert "at most two focused final repair passes" in text
    assert "bounded SearXNG search" in text
    assert "self-hosted Firecrawl one-page markdown extraction" in text
    assert "Do not automatically continue into another program" in " ".join(
        text.split()
    )
    assert str(tmp_path) not in result.stdout


def test_verifier_emits_the_exact_golden_verified_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    original_compile_file = pack_verify.PromptModuleCompiler.compile_file
    compile_calls = 0

    def counted_compile_file(*args: object, **kwargs: object):
        nonlocal compile_calls
        compile_calls += 1
        return original_compile_file(*args, **kwargs)

    monkeypatch.setattr(
        pack_verify.PromptModuleCompiler,
        "compile_file",
        counted_compile_file,
    )
    output = tmp_path / "combined.md"

    assert pack_verify.main(["--emit-combined", str(output), "--json"]) == 0

    data = json.loads(capsys.readouterr().out)
    assert compile_calls == 1
    assert data["combined_output_written"] is True
    assert data["compiled_artifact_hash"] == (
        f"sha256:{hashlib.sha256(output.read_bytes()).hexdigest()}"
    )


def test_stream_handoff_does_not_reopen_a_replaced_review_copy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "combined.md"
    original_emit = pack_verify.emit_combined_prompt

    def replace_review_copy(
        artifact: pack_verify.PromptCompilationArtifact,
        target: Path,
    ) -> None:
        original_emit(artifact, target)
        target.write_text("unverified replacement", encoding="utf-8")

    monkeypatch.setattr(pack_verify, "emit_combined_prompt", replace_review_copy)

    assert (
        pack_verify.main(
            ["--emit-combined", str(output), "--stream-combined"]
        )
        == 0
    )

    streamed = capsys.readouterr().out
    golden = json.loads(MODULE_GOLDEN_RECEIPT.read_text(encoding="utf-8"))
    assert (
        f"sha256:{hashlib.sha256(streamed.encode()).hexdigest()}"
        == golden["compiled_artifact_hash"]
    )
    assert output.read_text(encoding="utf-8") == "unverified replacement"


def test_wrapper_feeds_the_verified_combined_artifact_to_codex(
    tmp_path: Path,
) -> None:
    output = tmp_path / "combined.md"
    captured = tmp_path / "captured.md"
    fake_codex = tmp_path / "fake-codex"
    fake_codex.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\ncat > \"$UAA_TEST_CAPTURE\"\n",
        encoding="utf-8",
    )
    fake_codex.chmod(0o700)

    result = subprocess.run(
        ["bash", str(WRAPPER), "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PYTHON": sys.executable,
            "CODEX_BIN": str(fake_codex),
            "UAA_TEST_CAPTURE": str(captured),
        },
    )

    assert captured.read_bytes() == output.read_bytes()
    assert captured.read_text(encoding="utf-8").startswith(
        "# Compiled UAA Prompt Module Bundle"
    )
    assert str(tmp_path) not in result.stdout
