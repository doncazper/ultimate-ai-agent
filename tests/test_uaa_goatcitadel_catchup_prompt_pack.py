import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT / "docs" / "prompts" / "uaa_goatcitadel_catchup"
MANIFEST = PACK_DIR / "prompt_bundle_manifest.json"
VERIFY = ROOT / "scripts" / "verify_uaa_goatcitadel_catchup_prompt_pack.py"
WRAPPER = ROOT / "scripts" / "dev" / "run_uaa_goatcitadel_catchup_prompt_pack.sh"


def test_manifest_refs_are_ordered_and_present() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    refs = manifest["developer_prompt_refs"]
    assert len(refs) == 10
    assert refs[0].endswith("00_execute_uaa_goatcitadel_catchup_end_to_end.prompt.md")
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
    assert data["bundle_id"] == "uaa-goatcitadel-catchup-001"
    assert data["prompt_count"] == 10
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
    assert "UAA GoatCitadel Catch-Up Prompt Pack Combined Run" in text
    assert "00_execute_uaa_goatcitadel_catchup_end_to_end.prompt.md" in text
