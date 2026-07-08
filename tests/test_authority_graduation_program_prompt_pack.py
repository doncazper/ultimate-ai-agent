import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT / "docs" / "prompts" / "authority_graduation_program"
MANIFEST = PACK_DIR / "prompt_bundle_manifest.json"
VERIFY = ROOT / "scripts" / "verify_authority_graduation_program_prompt_pack.py"
WRAPPER = ROOT / "scripts" / "dev" / "run_authority_graduation_program.sh"


def test_manifest_refs_are_ordered_and_present() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["version"] == "1.1.0"
    refs = manifest["developer_prompt_refs"]
    assert len(refs) == 17
    assert refs[0].endswith("00_execute_all_review_fix_merge.prompt.md")
    assert refs[15].endswith("15_extension_plugin_callable_lane.prompt.md")
    assert refs[-1].endswith("99_blocker_report_and_unblock_prompts.prompt.md")
    assert len(set(refs)) == len(refs)

    for index, ref in enumerate(refs[:-1]):
        assert not ref.startswith("/")
        assert ".." not in Path(ref).parts
        assert Path(ref).name.startswith(f"{index:02d}_")
        assert (ROOT / ref).is_file()


def test_verifier_accepts_pack() -> None:
    result = subprocess.run(
        [sys.executable, str(VERIFY), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert data["bundle_id"] == "authority-graduation-program-001"
    assert data["version"] == "1.1.0"
    assert data["prompt_count"] == 17
    assert data["bundle_hash"].startswith("sha256:")


def test_wrapper_dry_run_emits_combined_prompt(tmp_path: Path) -> None:
    output = tmp_path / "combined.md"
    result = subprocess.run(
        ["bash", str(WRAPPER), "--dry-run", "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Dry run complete" in result.stdout
    text = output.read_text(encoding="utf-8")
    assert "Authority Graduation Program Prompt Pack Combined Run" in text
    assert "00_execute_all_review_fix_merge.prompt.md" in text
    assert "15_extension_plugin_callable_lane.prompt.md" in text
    assert "Callable activation remains blocked" in text
